from aiogram.fsm.state import State, StatesGroup


class AddMovie(StatesGroup):
    waiting_for_video = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_code = State()
