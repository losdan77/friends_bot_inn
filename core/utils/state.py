from aiogram.fsm.state import StatesGroup, State


class UsersSteps(StatesGroup):
    GET_INN = State()