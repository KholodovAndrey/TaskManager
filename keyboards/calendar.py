from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram_calendar import SimpleCalendar

async def get_calendar():
    calendar = SimpleCalendar()
    keyboard = await calendar.start_calendar()
    # Добавляем кнопку "Пропустить" к календарю
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Пропустить", callback_data="skip_date")])
    return keyboard