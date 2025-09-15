# src/anyads/client.py
import asyncio
import hashlib
import logging
import platform
import uuid
from pathlib import Path
from typing import Callable, Coroutine, Any, Dict, Optional

import httpx
from getmac import get_mac_address

from .exceptions import InitializationError, APIError
from .post import PostHandler
from .task import TaskHandler

logger = logging.getLogger("anyads.sdk")

_sdk_instance: Optional['AnyAdsSDK'] = None

class AnyAdsSDK:
    def __init__(self, api_key: str, sdk_version: str = "py-1.1.6"):
        if hasattr(self, '_initialized'):
            return

        if not api_key or not api_key.startswith("anyads_"):
            raise InitializationError("Неверный формат API ключа.")
        
        self.api_key = api_key
        self.sdk_version = sdk_version
        self.api_base_url = "https://api.anyads.online/v1"
        self._instance_id_path = Path("./.anyads_instance_id")

        self._fingerprint = self._get_environment_fingerprint()
        
        self._http_client: Optional[httpx.AsyncClient] = None
        self._instance_id: Optional[str] = None
        self._capabilities_task: Optional[asyncio.Task] = None
        
        self.posts = PostHandler(self)
        self.tasks = TaskHandler(self)
        
        self._initialized = True

    async def _initialize_session(self):
        """Асинхронная инициализация, создает InstanceID и HTTP клиент."""
        if self._instance_id is None:
            self._instance_id = await self._get_or_create_instance_id()
        
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-Instance-ID": self._instance_id,
                    "X-Environment-Fingerprint": self._fingerprint,
                    "User-Agent": f"AnyAdsPythonSDK/{self.sdk_version}",
                },
                timeout=20.0
            )
        logger.info(f"SDK AnyAds инициализирован. Instance ID: {self._instance_id}")

    async def _get_or_create_instance_id(self) -> str:
        """Читает Instance ID из файла или создает новый и регистрирует его."""
        try:
            if self._instance_id_path.exists():
                instance_id = self._instance_id_path.read_text().strip()
                if instance_id:
                    logger.debug(f"Найден существующий Instance ID: {instance_id}")
                    return instance_id
            
            new_id = f"inst_{uuid.uuid4()}"
            self._instance_id_path.write_text(new_id)
            logger.info(f"Создан новый Instance ID: {new_id}. Регистрируем на сервере...")
            
            await self._register_instance(new_id)
            return new_id
        except Exception as e:
            raise InitializationError(f"Не удалось прочитать, записать или зарегистрировать Instance ID: {e}")
        
    async def _register_instance(self, instance_id: str):
        """Отправляет запрос на регистрацию нового инстанса на сервер."""
        try:
            async with httpx.AsyncClient(base_url=self.api_base_url, timeout=20.0) as temp_client:
                response = await temp_client.post(
                    "/sdk/register-instance",
                    json={
                        "api_key": self.api_key,
                        "instance_id": instance_id,
                        "fingerprint": self._fingerprint,
                        "sdk_version": self.sdk_version
                    }
                )
                response.raise_for_status()
                logger.info(f"Новый Instance ID {instance_id} успешно зарегистрирован.")
        except httpx.HTTPStatusError as e:
            logger.critical(f"Не удалось зарегистрировать Instance ID! Сервер ответил с ошибкой {e.response.status_code}: {e.response.text}")
            raise APIError(f"Ошибка регистрации инстанса: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.critical(f"Сетевая ошибка при регистрации Instance ID: {e}")
            raise APIError(f"Сетевая ошибка регистрации инстанса") from e

    def _get_environment_fingerprint(self) -> str:
        try:
            mac = get_mac_address()
            hostname = platform.node()
            system_info = f"{platform.system()}-{platform.release()}"
            raw_fingerprint = f"{mac}-{hostname}-{system_info}"
            return hashlib.sha256(raw_fingerprint.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Не удалось сгенерировать полный отпечаток системы: {e}")
            return "fingerprint_generation_failed"

    async def process_verification_code(self, code: str) -> bool:
        """Отправляет верификационный код на сервер."""
        if not self._http_client:
            await self._initialize_session()
        
        if not code or not code.startswith('/verify_anyads_'):
            return False
        
        verification_code = code.lstrip('/')
        logger.info(f"Получена верификационная команда: {verification_code}")
        
        try:
            response = await self._http_client.post(
                "/sdk/verify", 
                json={"verification_code": verification_code}
            )
            response.raise_for_status()
            logger.info("Код верификации успешно отправлен на сервер.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке кода верификации: {e}")
            return False

    async def _manage_polling_loops(self):
        """Периодически проверяет возможности площадки и запускает/останавливает нужные опросы."""
        while True:
            try:
                logger.debug("Проверка возможностей площадки...")
                response = await self._http_client.get("/platform/capabilities")
                response.raise_for_status()
                capabilities = response.json()

                if capabilities.get("accepts_newsletters"):
                    self.posts._start_polling()
                else:
                    self.posts._stop_polling()

                self.tasks._set_enabled(capabilities.get("accepts_tasks", False))

            except Exception as e:
                logger.error(f"Ошибка при проверке возможностей платформы: {e}")
            
            await asyncio.sleep(3600)

    async def start(self):
        """Инициализирует сессию и запускает менеджер опросов."""
        await self._initialize_session()
        if self._capabilities_task and not self._capabilities_task.done():
            logger.warning("Менеджер опросов уже запущен.")
            return
        self._capabilities_task = asyncio.create_task(self._manage_polling_loops())

    async def stop(self):
        """Останавливает все фоновые задачи и закрывает соединения."""
        if self._capabilities_task:
            self._capabilities_task.cancel()
        
        self.posts._stop_polling()
        
        if self._http_client:
            await self._http_client.aclose()
        logger.info("SDK AnyAds остановлен.")

def init(api_key: str, sdk_version: str = "py-1.1.6") -> AnyAdsSDK:
    global _sdk_instance
    if _sdk_instance is None:
        _sdk_instance = AnyAdsSDK(api_key, sdk_version)
    return _sdk_instance

def get_sdk_instance() -> AnyAdsSDK:
    if _sdk_instance is None:
        raise InitializationError("SDK не был инициализирован. Вызовите anyads.init() при старте.")
    return _sdk_instance