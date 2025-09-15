# src/anyads/task.py
import logging
from typing import Dict, Optional

import httpx

from .exceptions import APIError, InitializationError

logger = logging.getLogger("anyads.sdk.tasks")

class TaskHandler:
    def __init__(self, parent_sdk):
        self._sdk = parent_sdk
        self._is_enabled = False

    def _set_enabled(self, status: bool):
        """
        Внутренний метод для включения/выключения модуля.
        Вызывается из "менеджера" в client.py.
        """
        if self._is_enabled != status:
            self._is_enabled = status
            logging.info(f"Прием заданий на подписку теперь {'ВКЛЮЧЕН' if status else 'ВЫКЛЮЧЕН'}.")

    async def get_subscription_task(self, user_id: int) -> Optional[Dict]:
        """
        Запрашивает у Ad Engine задание на подписку для конкретного пользователя.
        Возвращает словарь с данными задачи или None, если задач нет.
        """
        if not self._is_enabled:
            logger.debug("Прием заданий отключен, запрос на получение задачи проигнорирован.")
            return None
            
        if not self._sdk._http_client:
            raise InitializationError("SDK не был полностью инициализирован. Вызовите sdk.start() перед запросом задач.")
        
        logger.debug(f"Запрос задания на подписку для пользователя {user_id}...")
        try:
            response = await self._sdk._http_client.get(
                "/tasks/subscription",
                params={"user_id": user_id, "sdk_version": self._sdk.sdk_version}
            )

            if response.status_code == 204:
                logger.info(f"Для пользователя {user_id} нет доступных заданий.")
                return None
            
            response.raise_for_status()
            
            task_data = response.json()
            logger.info(f"Для пользователя {user_id} получено задание. Execution ID: {task_data.get('execution_id')}")
            return task_data

        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка API при получении задания: {e.response.status_code} - {e.response.text}")
            raise APIError(f"Ошибка API: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Сетевая ошибка при получении задания: {e}")
            raise APIError("Сетевая ошибка") from e
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при получении задания: {e}", exc_info=True)
            raise

    async def complete_subscription_task(self, execution_id: int, user_id: int) -> bool:
        """
        Сообщает Ad Engine, что пользователь нажал кнопку "Я подписался",
        и инициирует проверку.

        :param execution_id: ID выполнения, полученный от get_subscription_task.
        :param user_id: ID пользователя Telegram.
        :return: True, если все подписки подтверждены, иначе False.
        """
        if not self._is_enabled:
            return False
            
        if not self._sdk._http_client:
            raise InitializationError("SDK не был полностью инициализирован.")
            
        logger.debug(f"Отправка на проверку Execution ID {execution_id} для пользователя {user_id}...")
        try:
            response = await self._sdk._http_client.post(
                "/tasks/subscription/complete",
                json={"execution_id": execution_id, "user_id": user_id}
            )
            response.raise_for_status()
            
            result = response.json()
            all_subscribed = result.get("all_subscribed", False)
            
            if all_subscribed:
                logger.info(f"Проверка для Execution ID {execution_id} пройдена успешно.")
            else:
                logger.info(f"Проверка для Execution ID {execution_id} не пройдена (пользователь не на всех каналах).")

            return all_subscribed

        except Exception as e:
            logger.error(f"Ошибка при завершении задания {execution_id}: {e}")
            return False