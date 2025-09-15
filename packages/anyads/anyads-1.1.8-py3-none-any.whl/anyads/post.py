# src/anyads/post.py
import asyncio
import logging
from typing import Callable, Coroutine, Any, Dict, Optional

import httpx

from .exceptions import APIError

PostHandlerCallback = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]

logger = logging.getLogger("anyads.sdk.posts")

class PostHandler:
    def __init__(self, parent_sdk):
        self._sdk = parent_sdk
        self._polling_task: Optional[asyncio.Task] = None
        self._callback: Optional[PostHandlerCallback] = None
        self.interval_seconds = 600

    def configure(self, interval_seconds: int):
        """Позволяет настроить параметры обработчика постов."""
        self.interval_seconds = interval_seconds
        logger.info(f"Интервал опроса рассылок установлен на {interval_seconds} секунд.")

    def on_broadcast_received(self, handler: PostHandlerCallback):
        """
        Декоратор для регистрации коллбэка, который будет обрабатывать
        задачу на рассылку (newsletter).
        """
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError("Обработчик on_broadcast_received должен быть асинхронной функцией (async def).")
        self._callback = handler
        logger.info("Обработчик для рассылок (on_broadcast_received) успешно зарегистрирован.")
        return handler

    def _start_polling(self):
        """Внутренний метод для запуска фонового опроса. Вызывается из главного SDK."""
        if self._polling_task and not self._polling_task.done():
            return
        
        logger.info("Запуск фонового опроса для рекламных рассылок...")
        self._polling_task = asyncio.create_task(self._poll_loop())

    def _stop_polling(self):
        """Внутренний метод для остановки фонового опроса. Вызывается из главного SDK."""
        if self._polling_task:
            self._polling_task.cancel()
            self._polling_task = None
            logger.info("Фоновый опрос для рекламных рассылок остановлен.")

    async def _poll_loop(self):
        """
        Основной цикл, который периодически делает запросы к Ad Engine
        на эндпоинт для рассылок.
        """
        await asyncio.sleep(5)
        while True:
            try:
                if not self._sdk._http_client:
                    logger.warning("Ожидание инициализации HTTP клиента...")
                    await asyncio.sleep(self.interval_seconds)
                    continue

                logger.debug("Проверка наличия задач на рассылку...")
                response = await self._sdk._http_client.get(
                    "/tasks/bots/newsletters",
                    params={"sdk_version": self._sdk.sdk_version}
                )

                if update_header := response.headers.get("X-AnyAds-Update-Recommended"):
                    logger.warning(f"Доступна новая версия SDK: {update_header}. Пожалуйста, обновитесь: pip install --upgrade anyads")

                if response.status_code == 200:
                    ad_task = response.json()
                    if self._callback:
                        logger.info(f"Получена новая задача на рассылку: {ad_task.get('task_id')}")
                        asyncio.create_task(self._callback(ad_task))
                    else:
                        logger.warning("Получена задача на рассылку, но обработчик (on_broadcast_received) не зарегистрирован.")
                elif response.status_code == 204:
                    logger.debug("Нет активных задач на рассылку.")
                else:
                    response.raise_for_status()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 426:
                    logger.critical("Ваша версия SDK критически устарела! Опрос рассылок остановлен.")
                    break
                logger.error(f"Ошибка API при опросе рассылок: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                logger.error(f"Сетевая ошибка при опросе рассылок: {e}")
            except asyncio.CancelledError:
                logger.info("Цикл опроса рассылок был отменен.")
                break
            except Exception as e:
                logger.error(f"Непредвиденная ошибка в цикле опроса рассылок: {e}", exc_info=True)
            
            await asyncio.sleep(self.interval_seconds)