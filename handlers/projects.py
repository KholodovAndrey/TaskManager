from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from models import Project, ProjectType, ProjectStatus
from sqlalchemy import select, update, delete
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from keyboards.calendar import get_calendar
from aiogram.exceptions import TelegramBadRequest

router = Router()

class ProjectForm(StatesGroup):
    name = State()
    type = State()
    status = State()
    deadline = State()
    cost = State()

class EditProjectForm(StatesGroup):
    status = State()

def projects_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="📋 Мои проекты", callback_data="my_projects"),
        types.InlineKeyboardButton(text="💰 Заказы", callback_data="orders"),
        types.InlineKeyboardButton(text="✅ Завершенные", callback_data="completed_projects"),
        types.InlineKeyboardButton(text="➕ Добавить проект", callback_data="add_project"),
        types.InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    builder.adjust(2)
    return builder.as_markup()

def project_actions_keyboard(project_id, project_type, current_status):
    builder = InlineKeyboardBuilder()
    
    # Кнопки в зависимости от типа проекта и текущего статуса
    if current_status != ProjectStatus.COMPLETED:
        builder.add(types.InlineKeyboardButton(
            text="✅ Завершить", 
            callback_data=f"complete_project_{project_id}"
        ))
    
    builder.add(types.InlineKeyboardButton(
        text="📊 Изменить статус", 
        callback_data=f"change_status_{project_id}"
    ))
    
    builder.add(
        types.InlineKeyboardButton(
            text="✏️ Редактировать", 
            callback_data=f"edit_project_{project_id}"
        ),
        types.InlineKeyboardButton(
            text="🗑️ Удалить", 
            callback_data=f"delete_project_{project_id}"
        ),
        types.InlineKeyboardButton(
            text="◀️ Назад", 
            callback_data="projects_menu"
        )
    )
    builder.adjust(1)
    return builder.as_markup()

def get_status_keyboard(project_type):
    builder = InlineKeyboardBuilder()
    
    if project_type == ProjectType.PERSONAL:
        builder.add(
            types.InlineKeyboardButton(text="💡 Идея", callback_data="status_idea"),
            types.InlineKeyboardButton(text="🚀 В разработке", callback_data="status_in_progress"),
            types.InlineKeyboardButton(text="✅ Завершен", callback_data="status_completed")
        )
    else:  # ProjectType.ORDER
        builder.add(
            types.InlineKeyboardButton(text="📋 На согласовании", callback_data="status_agreement"),
            types.InlineKeyboardButton(text="🚀 В разработке", callback_data="status_in_progress"),
            types.InlineKeyboardButton(text="✅ Завершен", callback_data="status_completed")
        )
    
    builder.add(types.InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_status"))
    builder.adjust(1)
    return builder.as_markup()

async def safe_edit_message(message: types.Message, text: str, reply_markup=None):
    """Безопасное редактирование сообщения с обработкой ошибки 'message not modified'"""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise

@router.callback_query(F.data == "projects_menu")
async def show_projects_menu(callback: types.CallbackQuery):
    await safe_edit_message(callback.message, "Управление проектами:", projects_main_keyboard())

@router.callback_query(F.data == "my_projects")
async def show_my_projects(callback: types.CallbackQuery, db):
    result = await db.execute(
        select(Project).where(
            Project.user_id == callback.from_user.id,
            Project.type == ProjectType.PERSONAL,
            Project.status != ProjectStatus.COMPLETED
        )
    )
    projects = result.scalars().all()
    
    if not projects:
        await callback.message.answer("У вас нет активных личных проектов.", reply_markup=projects_main_keyboard())
        try:
            await callback.message.delete()
        except:
            pass
        return
    
    builder = InlineKeyboardBuilder()
    for project in projects:
        builder.add(types.InlineKeyboardButton(
            text=f"{project.name} ({project.status.value})", 
            callback_data=f"project_{project.id}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="projects_menu"))
    builder.adjust(1)
    
    await callback.message.answer("Ваши проекты:", reply_markup=builder.as_markup())
    try:
        await callback.message.delete()
    except:
        pass

@router.callback_query(F.data == "orders")
async def show_orders(callback: types.CallbackQuery, db):
    result = await db.execute(
        select(Project).where(
            Project.user_id == callback.from_user.id,
            Project.type == ProjectType.ORDER,
            Project.status != ProjectStatus.COMPLETED
        )
    )
    projects = result.scalars().all()
    
    if not projects:
        await callback.message.answer("У вас нет активных заказов.", reply_markup=projects_main_keyboard())
        try:
            await callback.message.delete()
        except:
            pass
        return
    
    builder = InlineKeyboardBuilder()
    for project in projects:
        builder.add(types.InlineKeyboardButton(
            text=f"{project.name} ({project.status.value})", 
            callback_data=f"project_{project.id}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="projects_menu"))
    builder.adjust(1)
    
    await callback.message.answer("Ваши заказы:", reply_markup=builder.as_markup())
    try:
        await callback.message.delete()
    except:
        pass

@router.callback_query(F.data == "completed_projects")
async def show_completed_projects(callback: types.CallbackQuery, db):
    result = await db.execute(
        select(Project).where(
            Project.user_id == callback.from_user.id,
            Project.status == ProjectStatus.COMPLETED
        )
    )
    projects = result.scalars().all()
    
    if not projects:
        await callback.message.answer("У вас нет завершенных проектов.", reply_markup=projects_main_keyboard())
        try:
            await callback.message.delete()
        except:
            pass
        return
    
    builder = InlineKeyboardBuilder()
    for project in projects:
        builder.add(types.InlineKeyboardButton(
            text=f"{project.name} ({project.type.value})", 
            callback_data=f"project_{project.id}"
        ))
    
    builder.add(types.InlineKeyboardButton(text="◀️ Назад", callback_data="projects_menu"))
    builder.adjust(1)
    
    await callback.message.answer("Завершенные проекты:", reply_markup=builder.as_markup())
    try:
        await callback.message.delete()
    except:
        pass

@router.callback_query(F.data.startswith("project_"))
async def show_project(callback: types.CallbackQuery, db):
    project_id = int(callback.data.split("_")[1])
    
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        await callback.answer("Проект не найден!")
        return
    
    project_text = f"""
📁 Проект: {project.name}
📝 Тип: {project.type.value}
📊 Статус: {project.status.value}
"""
    
    if project.deadline:
        project_text += f"⏰ Дедлайн: {project.deadline.strftime('%d.%m.%Y')}\n"
    
    if project.cost:
        project_text += f"💰 Стоимость: {project.cost} руб.\n"
    
    if project.completed_at:
        project_text += f"✅ Завершен: {project.completed_at.strftime('%d.%m.%Y')}\n"
    
    await callback.message.answer(
        project_text, 
        reply_markup=project_actions_keyboard(project_id, project.type, project.status)
    )
    try:
        await callback.message.delete()
    except:
        pass

@router.callback_query(F.data.startswith("complete_project_"))
async def complete_project(callback: types.CallbackQuery, db):
    project_id = int(callback.data.split("_")[2])
    
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        await callback.answer("Проект не найден!")
        return
    
    await db.execute(
        update(Project)
        .where(Project.id == project_id)
        .values(
            status=ProjectStatus.COMPLETED,
            completed_at=datetime.now()
        )
    )
    await db.commit()
    
    await callback.answer("Проект завершен!")
    await show_projects_menu(callback)

@router.callback_query(F.data.startswith("change_status_"))
async def start_change_status(callback: types.CallbackQuery, state: FSMContext, db):
    project_id = int(callback.data.split("_")[2])
    
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        await callback.answer("Проект не найден!")
        return
    
    await state.update_data(project_id=project_id)
    await state.set_state(EditProjectForm.status)
    
    await callback.message.answer(
        f"Выберите новый статус для проекта '{project.name}':",
        reply_markup=get_status_keyboard(project.type)
    )
    try:
        await callback.message.delete()
    except:
        pass

@router.callback_query(EditProjectForm.status, F.data.startswith("status_"))
async def process_change_status(callback: types.CallbackQuery, state: FSMContext, db):
    data = await state.get_data()
    project_id = data['project_id']
    
    # Определяем новый статус
    status_mapping = {
        "status_idea": ProjectStatus.IDEA,
        "status_agreement": ProjectStatus.AGREEMENT,
        "status_in_progress": ProjectStatus.IN_PROGRESS,
        "status_completed": ProjectStatus.COMPLETED
    }
    
    new_status = status_mapping.get(callback.data)
    
    if new_status:
        await db.execute(
            update(Project)
            .where(Project.id == project_id)
            .values(status=new_status)
        )
        await db.commit()
        
        await callback.answer(f"Статус изменен на: {new_status.value}")
    
    await state.clear()
    await show_projects_menu(callback)

@router.callback_query(EditProjectForm.status, F.data == "cancel_status")
async def cancel_change_status(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Изменение статуса отменено")
    await show_projects_menu(callback)

@router.callback_query(F.data.startswith("delete_project_"))
async def delete_project(callback: types.CallbackQuery, db):
    project_id = int(callback.data.split("_")[2])
    
    await db.execute(
        delete(Project).where(Project.id == project_id)
    )
    await db.commit()
    
    await callback.answer("Проект удален!")
    await show_projects_menu(callback)

@router.callback_query(F.data == "add_project")
async def start_add_project(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ProjectForm.name)
    await callback.message.answer("Введите название проекта:")
    try:
        await callback.message.delete()
    except:
        pass

@router.message(ProjectForm.name)
async def process_project_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ProjectForm.type)
    
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Личный проект", callback_data="personal"),
        types.InlineKeyboardButton(text="Заказ", callback_data="order")
    )
    builder.adjust(1)
    
    await message.answer("Выберите тип проекта:", reply_markup=builder.as_markup())

@router.callback_query(ProjectForm.type, F.data.in_(["personal", "order"]))
async def process_project_type(callback: types.CallbackQuery, state: FSMContext):
    project_type = ProjectType.PERSONAL if callback.data == "personal" else ProjectType.ORDER
    await state.update_data(type=project_type)
    
    # Устанавливаем начальный статус в зависимости от типа
    initial_status = ProjectStatus.IDEA if callback.data == "personal" else ProjectStatus.AGREEMENT
    await state.update_data(status=initial_status)
    
    # Если это заказ, запрашиваем стоимость
    if callback.data == "order":
        await state.set_state(ProjectForm.cost)
        await callback.message.answer("Введите стоимость заказа:")
    else:
        # Для личных проектов переходим к выбору дедлайна
        await state.set_state(ProjectForm.deadline)
        await callback.message.answer(
            "Выберите дедлайн (или нажмите 'Пропустить'):", 
            reply_markup=get_skip_keyboard()
        )

@router.message(ProjectForm.cost)
async def process_project_cost(message: types.Message, state: FSMContext):
    try:
        cost = float(message.text)
        await state.update_data(cost=cost)
        await state.set_state(ProjectForm.deadline)
        await message.answer(
            "Выберите дедлайн (или нажмите 'Пропустить'):", 
            reply_markup=get_skip_keyboard()
        )
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму:")

@router.callback_query(ProjectForm.deadline, F.data == "skip_deadline")
async def skip_deadline(callback: types.CallbackQuery, state: FSMContext, db):
    await process_project_data(callback, state, db, None)

@router.callback_query(SimpleCalendarCallback.filter(), ProjectForm.deadline)
async def process_deadline(
    callback: types.CallbackQuery, 
    callback_data: SimpleCalendarCallback, 
    state: FSMContext, 
    db
):
    calendar = SimpleCalendar()
    selected, date = await calendar.process_selection(callback, callback_data)
    
    if selected:
        await process_project_data(callback, state, db, date)

async def process_project_data(callback: types.CallbackQuery, state: FSMContext, db, deadline):
    data = await state.get_data()
    
    project = Project(
        user_id=callback.from_user.id,
        name=data['name'],
        type=data['type'],
        status=data['status'],
        deadline=deadline,
        cost=data.get('cost')
    )
    
    db.add(project)
    await db.commit()
    
    await state.clear()
    await callback.message.answer("Проект успешно создан!")
    await show_projects_menu(callback)

def get_skip_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Пропустить", callback_data="skip_deadline"))
    return builder.as_markup()