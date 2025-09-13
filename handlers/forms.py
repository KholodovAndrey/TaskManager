from aiogram.fsm.state import State, StatesGroup

class ProjectForm(StatesGroup):
    name = State()
    type = State()
    status = State()
    deadline = State()
    cost = State()

class TaskForm(StatesGroup):
    title = State()
    description = State()
    project_id = State()
    deadline = State()

class ExpenseForm(StatesGroup):
    amount = State()
    date = State()
    comment = State()