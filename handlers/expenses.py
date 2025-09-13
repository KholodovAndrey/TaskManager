from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
from models import Expense
from sqlalchemy import select, func, delete
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from keyboards.calendar import get_calendar

router = Router()

class ExpenseForm(StatesGroup):
    amount = State()
    date = State()
    comment = State()

def expenses_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="💵 Добавить расход", callback_data="add_expense"),
        types.InlineKeyboardButton(text="📊 История расходов", callback_data="expenses_history"),
        types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()

def expense_actions_keyboard(expense_id):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="✏️ Редактировать", 
            callback_data=f"edit_expense_{expense_id}"
        ),
        types.InlineKeyboardButton(
            text="🗑️ Удалить", 
            callback_data=f"delete_expense_{expense_id}"
        ),
        types.InlineKeyboardButton(
            text="◀️ Назад", 
            callback_data="expenses_menu"
        )
    )
    builder.adjust(1)
    return builder.as_markup()

def get_skip_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Пропустить", callback_data="skip_comment"))
    return builder.as_markup()

@router.callback_query(F.data == "expenses_menu")
async def show_expenses_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Управление расходами:", reply_markup=expenses_main_keyboard())

@router.callback_query(F.data == "expenses_history")
async def show_expenses_history(callback: types.CallbackQuery, db):
    one_month_ago = datetime.now() - timedelta(days=30)
    
    result = await db.execute(
        select(Expense).where(
            Expense.user_id == callback.from_user.id,
            Expense.date >= one_month_ago
        ).order_by(Expense.date.desc())
    )
    expenses = result.scalars().all()
    
    if not expenses:
        await callback.message.edit_text("У вас нет расходов за последний месяц.", reply_markup=expenses_main_keyboard())
        return
    
    total = sum(expense.amount for expense in expenses)
    message_text = "Ваши расходы за последний месяц:\n\n"
    
    for expense in expenses:
        message_text += f"📅 {expense.date.strftime('%d.%m.%Y')}: {expense.amount} руб.\n"
        if expense.comment:
            message_text += f"   💬 {expense.comment}\n"
        message_text += f"   [ID: {expense.id}]\n\n"
    
    message_text += f"💵 Итого: {total} руб."
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="expenses_menu"))
    
    await callback.message.edit_text(message_text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("expense_"))
async def show_expense(callback: types.CallbackQuery, db):
    expense_id = int(callback.data.split("_")[1])
    
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id)
    )
    expense = result.scalar_one_or_none()
    
    if not expense:
        await callback.answer("Расход не найден!")
        return
    
    expense_text = f"""
💸 Расход: {expense.amount} руб.
📅 Дата: {expense.date.strftime('%d.%m.%Y')}
"""
    
    if expense.comment:
        expense_text += f"💬 Комментарий: {expense.comment}\n"
    
    await callback.message.edit_text(
        expense_text, 
        reply_markup=expense_actions_keyboard(expense_id)
    )

@router.callback_query(F.data.startswith("delete_expense_"))
async def delete_expense(callback: types.CallbackQuery, db):
    expense_id = int(callback.data.split("_")[2])
    
    await db.execute(
        delete(Expense).where(Expense.id == expense_id)
    )
    await db.commit()
    
    await callback.answer("Расход удален!")
    await show_expenses_menu(callback)

@router.callback_query(F.data == "add_expense")
async def start_add_expense(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ExpenseForm.amount)
    await callback.message.edit_text("Введите сумму расхода:")

@router.message(ExpenseForm.amount)
async def process_expense_amount(message: types.Message, state: FSMContext):
    try:
        # Заменяем запятую на точку для корректного преобразования
        amount_str = message.text.replace(',', '.')
        amount = float(amount_str)
        
        if amount <= 0:
            await message.answer("Сумма должна быть положительным числом. Попробуйте еще раз:")
            return
            
        await state.update_data(amount=amount)
        await state.set_state(ExpenseForm.date)
        await message.answer("Выберите дату расхода:", reply_markup=await get_calendar())
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму (число, например: 500 или 500.50):")

@router.callback_query(SimpleCalendarCallback.filter(), ExpenseForm.date)
async def process_expense_date(
    callback: types.CallbackQuery, 
    callback_data: SimpleCalendarCallback, 
    state: FSMContext
):
    calendar = SimpleCalendar()
    selected, date = await calendar.process_selection(callback, callback_data)
    
    if selected:
        await state.update_data(date=date)
        await state.set_state(ExpenseForm.comment)
        await callback.message.edit_text("Введите комментарий к расходу:", reply_markup=get_skip_keyboard())

@router.callback_query(F.data == "skip_date", ExpenseForm.date)
async def skip_expense_date(callback: types.CallbackQuery, state: FSMContext):
    # Устанавливаем текущую дату как дату расхода
    await state.update_data(date=datetime.now())
    await state.set_state(ExpenseForm.comment)
    await callback.message.edit_text("Введите комментарий к расходу:", reply_markup=get_skip_keyboard())

# Обработчик для кнопки "Пропустить" в комментарии
@router.callback_query(F.data == "skip_comment", ExpenseForm.comment)
async def skip_expense_comment(callback: types.CallbackQuery, state: FSMContext, db):
    data = await state.get_data()
    
    expense = Expense(
        user_id=callback.from_user.id,
        amount=data['amount'],
        date=data['date'],
        comment=None
    )
    
    db.add(expense)
    await db.commit()
    
    await state.clear()
    await callback.message.edit_text("Расход успешно добавлен!")
    await show_expenses_menu(callback)

# Обработчик для текстового комментария
@router.message(ExpenseForm.comment)
async def process_expense_comment(message: types.Message, state: FSMContext, db):
    data = await state.get_data()
    
    expense = Expense(
        user_id=message.from_user.id,
        amount=data['amount'],
        date=data['date'],
        comment=message.text
    )
    
    db.add(expense)
    await db.commit()
    
    await state.clear()
    await message.answer("Расход успешно добавлен!")
    await show_expenses_menu_from_message(message)

async def show_expenses_menu_from_message(message: types.Message):
    await message.answer("Управление расходами:", reply_markup=expenses_main_keyboard())