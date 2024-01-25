from aiogram.fsm.state import StatesGroup, State


class Marks(StatesGroup):
    is_continue = State()
    continue_ = State()


class NetSchoolState(StatesGroup):
    login = State()
    password = State()


class SendMessage(StatesGroup):
    receiver = State()
    message = State()


class Bind(StatesGroup):
    picked_source = State()
    picked_grade = State()
    picked_subject = State()
    picked_book = State()
    picked_alias = State()


class Orthoepy(StatesGroup):
    main = State()


class Test(StatesGroup):
    credentials = State()


class Aliases(StatesGroup):
    main = State()


class WordCloud(StatesGroup):
    settings_input = State()


class BaseConverter(StatesGroup):
    num = State()
    base = State()


class Formulas(StatesGroup):
    formulas_list = State()
    formulas_out = State()


class AiState(StatesGroup):
    choose = State()
    chatgpt_turbo = State()
    gemini_pro = State()
    midjourney_v4 = State()
    midjourney_v6 = State()
    kandinsky = State()
    playground_v2 = State()
    stable_diffusion_xl_turbo = State()
    claude = State()
    mistral_medium = State()
    dalle3 = State()
    photomaker = State()
    hcrt = State()


class WolframState(StatesGroup):
    main = State()
