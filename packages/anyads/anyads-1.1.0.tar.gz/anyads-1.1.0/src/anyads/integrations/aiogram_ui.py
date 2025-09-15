# /src/anyads/integrations/aiogram_ui.py
import logging
from aiogram import Bot, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from anyads import get_sdk_instance

logger = logging.getLogger("anyads.sdk.integrations.aiogram")

async def handle_start_with_task(
    message: types.Message, 
    bot: Bot,
    fallback_handler: Optional[Callable[[], Coroutine[Any, Any, None]]] = None
):
    """
    Высокоуровневая функция-хелпер для Aiogram.
    Автоматически обрабатывает полный цикл показа задания на подписку.

    :param message: Объект `message` из обработчика /start.
    :param bot: Экземпляр вашего `Bot`.
    :param fallback_handler: (Опционально) Асинхронная функция, которая будет вызвана, если заданий нет.
    """
    sdk = get_sdk_instance()
    user_id = message.from_user.id
    
    loading_msg = await message.answer("⏳ Загрузка...")
    
    try:
        task = await sdk.tasks.get_subscription_task(user_id)

        if task:
            channels = task.get('channels_to_subscribe', [])
            channel_links = [f"• <a href='{ch['link']}'>{ch['link'].lstrip('@')}</a>" for ch in channels]
            message_text = (
                "<b>Для продолжения, пожалуйста, подпишитесь на каналы:</b>\n\n"
                + "\n".join(channel_links)
            )
            builder = InlineKeyboardBuilder()
            builder.button(
                text="✅ Я подписался",
                callback_data=f"anyads_confirm_subscription:{task['execution_id']}"
            )
            
            await loading_msg.edit_text(
                message_text, 
                reply_markup=builder.as_markup(), 
                parse_mode="HTML", 
                disable_web_page_preview=True
            )
        else:
            # Если заданий нет, удаляем "Загрузка..." и вызываем fallback
            await loading_msg.delete()
            if fallback_handler:
                await fallback_handler()
            
    except Exception as e:
        logger.error(f"Ошибка в handle_start_with_task: {e}", exc_info=True)
        try:
            await loading_msg.delete()
        except Exception:
            pass
        if fallback_handler:
            await fallback_handler()

def register_ui_handlers(dp: types.Dispatcher, bot: Bot, on_success: Optional[OnSuccessCallback] = None):
    """
    Регистрирует коллбэк-обработчик для кнопки "Я подписался".

    :param dp: Экземпляр aiogram.Dispatcher.
    :param bot: Экземпляр вашего Bot.
    :param on_success: (Опционально) Асинхронная функция, которая будет вызвана
                       после успешного выполнения задания. Принимает `CallbackQuery`.
    """
    sdk = get_sdk_instance()

    @dp.callback_query(lambda c: c.data and c.data.startswith("anyads_confirm_subscription:"))
    async def _handle_confirm_subscription(query: types.CallbackQuery):
        execution_id = int(query.data.split(":")[1])
        await query.answer("Проверяем подписку...")
        
        success = await sdk.tasks.complete_subscription_task(execution_id, query.from_user.id)
        
        if success:
            await query.message.edit_text("✅ Спасибо! Доступ предоставлен.")
            
            # Если разработчик передал нам свою функцию, вызываем ее
            if on_success:
                try:
                    await on_success(query)
                except Exception as e:
                    logger.error(f"Ошибка в пользовательском on_success коллбэке: {e}", exc_info=True)
        else:
            await query.answer("Вы еще не подписались на все каналы. Пожалуйста, проверьте и попробуйте снова.", show_alert=True)