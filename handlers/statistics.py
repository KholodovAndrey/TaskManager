from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from models import Project, Expense, ProjectStatus, ProjectType
from sqlalchemy import select, func

router = Router()

async def send_statistics(message: types.Message, db):
    user_id = message.from_user.id
    
    # Получаем статистику по проектам
    completed_projects = await db.execute(
        select(func.count()).where(
            Project.user_id == user_id,
            Project.status == ProjectStatus.COMPLETED
        )
    )
    completed_count = completed_projects.scalar()
    
    active_projects = await db.execute(
        select(func.count()).where(
            Project.user_id == user_id,
            Project.status != ProjectStatus.COMPLETED
        )
    )
    active_count = active_projects.scalar()
    
    # Получаем доходы (только завершенные заказы)
    income_result = await db.execute(
        select(func.sum(Project.cost)).where(
            Project.user_id == user_id,
            Project.type == ProjectType.ORDER,
            Project.status == ProjectStatus.COMPLETED
        )
    )
    income = income_result.scalar() or 0
    
    # Получаем расходы
    expenses_result = await db.execute(
        select(func.sum(Expense.amount)).where(Expense.user_id == user_id)
    )
    expenses = expenses_result.scalar() or 0
    
    # Рассчитываем прибыль
    profit = income - expenses
    
    message_text = (
        "📊 Ваша статистика:\n\n"
        f"✅ Завершенные проекты: {completed_count}\n"
        f"🚀 Активные проекты: {active_count}\n"
        f"💰 Доходы: {income} руб.\n"
        f"💸 Расходы: {expenses} руб.\n"
        f"💵 Прибыль: {profit} руб."
    )
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"))
    
    await message.answer(message_text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "statistics")
async def show_stats(callback: types.CallbackQuery, db):
    await send_statistics(callback.message, db)