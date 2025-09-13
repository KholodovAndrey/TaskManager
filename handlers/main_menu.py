from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text="📁 Проекты"),
        types.KeyboardButton(text="✅ Задачи"),
        types.KeyboardButton(text="💸 Траты"),
        types.KeyboardButton(text="📊 Статистика")
    )
    builder.adjust(2)
    
    await message.answer(
        "Добро пожаловать в менеджер проектов!\nВыберите раздел:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@router.message(F.text == "📁 Проекты")
async def show_projects_menu(message: types.Message):
    from handlers.projects import projects_main_keyboard
    await message.answer("Управление проектами:", reply_markup=projects_main_keyboard())

@router.message(F.text == "✅ Задачи")
async def show_tasks_menu(message: types.Message):
    from handlers.tasks import tasks_main_keyboard
    await message.answer("Управление задачами:", reply_markup=tasks_main_keyboard())

@router.message(F.text == "💸 Траты")
async def show_expenses_menu(message: types.Message):
    from handlers.expenses import expenses_main_keyboard
    await message.answer("Управление расходами:", reply_markup=expenses_main_keyboard())

@router.message(F.text == "📊 Статистика")
async def show_statistics(message: types.Message, db):
    from handlers.statistics import send_statistics
    await send_statistics(message, db)

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    await cmd_start(callback.message)