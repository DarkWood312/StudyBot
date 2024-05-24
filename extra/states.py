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

class RootExtr(StatesGroup):
    init = State()
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


class UchusOnlineState(StatesGroup):
    choose = State()
    ans = State()
    change_diff = State()


class Formulas(StatesGroup):
    formulas_list = State()
    formulas_out = State()


class AiState(StatesGroup):
    choose = State()
    llm_choose = State()
    llm = State()
    dalle = State()
    sd_choose = State()
    sd = State()
    text2gif = State()
    openai_chat = State()
    openai_dalle = State()


class WolframState(StatesGroup):
    main = State()


class EncryptionState(StatesGroup):
    encrypt_st = State()
    decrypt_st = State()
    final_st = State()
