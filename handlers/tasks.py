from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from models import Task, Project, ProjectStatus
from sqlalchemy import select, update, delete
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from keyboards.calendar import get_calendar


class TaskForm(StatesGroup):
    title = State()
    description = State()
    project_id = State()
    deadline = State()

router = Router()

def tasks_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="📋 Мои задачи", callback_data="my_tasks"),
        types.InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task"),
        types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()

def task_actions_keyboard(task_id):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="✅ Выполнить", 
            callback_data=f"complete_task_{task_id}"
        ),
        types.InlineKeyboardButton(
            text="✏️ Редактировать", 
            callback_data=f"edit_task_{task_id}"
        ),
        types.InlineKeyboardButton(
            text="🗑️ Удалить", 
            callback_data=f"delete_task_{task_id}"
        ),
        types.InlineKeyboardButton(
            text="◀️ Назад", 
            callback_data="tasks_menu"
        )
    )
    builder.adjust(1)
    return builder.as_markup()

def get_skip_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Пропустить", callback_data="skip_description"))
    return builder.as_markup()

async def show_projects_for_selection(message: types.Message, db):
    # Получаем активные проекты пользователя
    result = await db.execute(
        select(Project).where(
            Project.user_id == message.from_user.id,
            Project.status != ProjectStatus.COMPLETED
        )
    )
    projects = result.scalars().all()
    
    builder = InlineKeyboardBuilder()
    for project in projects:
        builder.add(types.InlineKeyboardButton(
            text=project.name, 
            callback_data=f"select_project_{project.id}"  # Изменили префикс
        ))
    
    builder.add(types.InlineKeyboardButton(text="Без проекта", callback_data="select_no_project"))
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="tasks_menu"))
    builder.adjust(1)
    
    await message.answer("Выберите проект для задачи:", reply_markup=builder.as_markup())

async def process_task_data(callback: types.CallbackQuery, state: FSMContext, db, deadline):
    data = await state.get_data()
    
    task = Task(
        user_id=callback.from_user.id,
        title=data['title'],
        description=data.get('description'),
        project_id=data.get('project_id'),
        deadline=deadline
    )
    
    db.add(task)
    await db.commit()
    
    await state.clear()
    await callback.message.edit_text("Задача успешно создана!")
    await show_tasks_menu(callback)

@router.callback_query(F.data == "tasks_menu")
async def show_tasks_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Управление задачами:", reply_markup=tasks_main_keyboard())

@router.callback_query(F.data == "my_tasks")
async def show_my_tasks(callback: types.CallbackQuery, db):
    result = await db.execute(
        select(Task).where(
            Task.user_id == callback.from_user.id,
            Task.is_completed == False
        )
    )
    tasks = result.scalars().all()
    
    if not tasks:
        await callback.message.edit_text("У вас нет активных задач.", reply_markup=tasks_main_keyboard())
        return
    
    builder = InlineKeyboardBuilder()
    for task in tasks:
        project_name = "Без проекта"
        if task.project_id:
            project_result = await db.execute(select(Project.name).where(Project.id == task.project_id))
            project_name = project_result.scalar()
        
        builder.add(types.InlineKeyboardButton(
            text=f"{task.title} ({project_name})", 
            callback_data=f"task_{task.id}"  # Оставляем старый формат для отображения задач
        ))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="tasks_menu"))
    builder.adjust(1)
    
    await callback.message.edit_text("Ваши задачи:", reply_markup=builder.as_markup())

@router.callback_query(F.data.regexp(r'^task_\d+$'))
async def show_task(callback: types.CallbackQuery, db):
    task_id = int(callback.data.split("_")[1])
    
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        await callback.answer("Задача не найдена!")
        return
    
    task_text = f"""
✅ Задача: {task.title}
"""
    
    if task.description:
        task_text += f"📝 Описание: {task.description}\n"
    
    if task.project_id:
        project_result = await db.execute(select(Project.name).where(Project.id == task.project_id))
        project_name = project_result.scalar()
        task_text += f"📁 Проект: {project_name}\n"
    
    if task.deadline:
        task_text += f"⏰ Дедлайн: {task.deadline.strftime('%d.%m.%Y')}\n"
    
    task_text += f"📊 Статус: {'Выполнена' if task.is_completed else 'Активна'}\n"
    
    await callback.message.edit_text(
        task_text, 
        reply_markup=task_actions_keyboard(task_id)
    )

@router.callback_query(F.data.startswith("complete_task_"))
async def complete_task(callback: types.CallbackQuery, db):
    task_id = int(callback.data.split("_")[2])
    
    await db.execute(
        update(Task)
        .where(Task.id == task_id)
        .values(
            is_completed=True,
            completed_at=datetime.now()
        )
    )
    await db.commit()
    
    await callback.answer("Задача выполнена!")
    await show_tasks_menu(callback)

@router.callback_query(F.data.startswith("delete_task_"))
async def delete_task(callback: types.CallbackQuery, db):
    task_id = int(callback.data.split("_")[2])
    
    await db.execute(
        delete(Task).where(Task.id == task_id)
    )
    await db.commit()
    
    await callback.answer("Задача удалена!")
    await show_tasks_menu(callback)

@router.callback_query(F.data == "add_task")
async def start_add_task(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TaskForm.title)
    await callback.message.edit_text("Введите название задачи:")

@router.message(TaskForm.title)
async def process_task_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(TaskForm.description)
    await message.answer("Введите описание задачи:", reply_markup=get_skip_keyboard())

@router.callback_query(F.data == "skip_description", TaskForm.description)
async def skip_task_description(callback: types.CallbackQuery, state: FSMContext, db):
    await state.update_data(description=None)
    await state.set_state(TaskForm.project_id)
    await show_projects_for_selection(callback.message, db)

@router.message(TaskForm.description)
async def process_task_description(message: types.Message, state: FSMContext, db):
    if message.text != "Пропустить":
        await state.update_data(description=message.text)
    else:
        await state.update_data(description=None)
    
    await state.set_state(TaskForm.project_id)
    await show_projects_for_selection(message, db)

@router.callback_query(F.data.startswith("select_"), TaskForm.project_id)
async def process_task_project(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "select_no_project":
        project_id = None
    else:
        project_id = int(callback.data.split("_")[2])  # Теперь индекс 2, так как префикс из двух частей
    
    await state.update_data(project_id=project_id)
    await state.set_state(TaskForm.deadline)
    
    await callback.message.edit_text(
        "Выберите дедлайн (или нажмите 'Пропустить'):", 
        reply_markup=await get_calendar()
    )

@router.callback_query(F.data == "skip", TaskForm.deadline)
async def skip_task_deadline(callback: types.CallbackQuery, state: FSMContext, db):
    await process_task_data(callback, state, db, None)

@router.callback_query(SimpleCalendarCallback.filter(), TaskForm.deadline)
async def process_task_deadline(
    callback: types.CallbackQuery, 
    callback_data: SimpleCalendarCallback, 
    state: FSMContext, 
    db
):
    calendar = SimpleCalendar()
    selected, date = await calendar.process_selection(callback, callback_data)
    
    if selected:
        await process_task_data(callback, state, db, date)