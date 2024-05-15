from aiogram import html

left_arrow = '&lt;'
right_arrow = '&gt;'
gdz_help = f'''
<b>ГДЗ</b>:
<b>Список предметов</b>: <i>алгебра</i>(<code>алг</code>/<code>alg</code>), <i>алгебра мордкович</i>(<code>алгм</code>/<code>algm</code>), <i>геометрия</i>(<code>гео</code>/<code>geo</code>), <i>английcкий</i>(<code>анг</code>/<code>ang</code>), <i>химия</i>(<code>хим</code>/<code>him</code>), <i>контурки история</i> (<code>кист</code>/<code>kist</code>), <i>физика</i> (<code>физ</code>/<code>phiz</code>), <i>информатика поляков</i> (<code>инф</code>/<code>inf</code>)'
<b>Химия</b>: хим/him {left_arrow}тема{right_arrow} {left_arrow}работа{right_arrow} {left_arrow}вариант{right_arrow}
<b>Алгебра Мордковича</b>: алгм/algm {left_arrow}параграф{right_arrow} {left_arrow}номер задания{right_arrow} 
<i>Пример</i>: '<code>алг 24</code>'
<i>Пример ХИМИИ</i>: '<code>хим 8 1 4</code>'
<i>Пример АЛГЕБРЫ МОРДОКВИЧА</i>: '<code>алгм 5 1</code>'
<i>Пример ИНФОРМАТИКИ ПОЛЯКОВА</i>: '<code>инф 7-v 80</code>'
<i>Пример поиска нескольких ответов</i>: '<code>алг 51-55</code>' ИЛИ 'алг <code>51, 52, 53, 54, 55</code>'

<b>Средний балл</b>:
<i>Пример</i>: '<code>23525</code>' --> '<i>3.4</i>'
'''
main_message = f'''
<b>ГДЗ</b>:
/bind - Привязать / Добавить учебник ГДЗ
/aliases - Просмотр / Удаление учебников ГДЗ
/kit 11 - Автоматическое добавление алгебры, геометрии, английского и сборника Ершова (11 класс)

<b>Вычисление среднего балла и количества оценок для получения лучшей средней оценки</b>:
<i>Пример</i>: '<code>23525</code>' --> '<code>3.4</code>'

<b>Перевод баллов ЕГЭ:</b> /ep {html.quote("<кол-во первичных баллов>")}

<b>Калькулятор систем счисления(СС) --> </b>/base_converter

<b>Формулы --> </b>/formulas
<b>Для поиска формул(математика, физика) нужно просто написать название формулы или любые известные данные</b>:
<i>Пример</i>: '<code>энергия</code>' --> <code>*формулы для нахождения энергии или формулы, где нужна энергия*</code>

<b>Тренировка извлечения корня --> </b>/root_extraction

<b>Орфоэпия:</b>
/orthoepy - Запуск орфоэпии
/ostats - Топ проблемных слов среди <u>всех</u> пользователей

<b>Документы --> </b>/docs

<b>WolframAlpha --> </b>/wolfram

<b>AI --> </b>/ai

<b>Uchus.online --> </b>/uchus

<b>Шифрование --> </b>/encryption

<b>Для получения прямой ссылки на файл / фото и тд. нужно просто отправить боту файл. (До 20 МБ - ограничение ТГ ;( )</b>

<b>Кто автор? Исходный код? --> </b>/author
'''
# ^^^
# <b>Небольшой анализ текста + Облако Слов --> </b> *Отправить текст длинной более 50 символов*
# <b>Настройка облака слов --> </b>/wordcloud_settings

# kist_ids = {
#     'ist2': 'AgACAgIAAxkBAAICoWODq5zJeX6L2U5-Z6efHN1QM4MuAALxxjEbwWUgSFHg8XorGDFtAQADAgADcwADKwQ',
#     'ist4': 'AgACAgIAAxkBAAICpGODq7wR5Z87SBrq3cPZeDEoqX5DAALyxjEbwWUgSLXbG5jX4FJSAQADAgADcwADKwQ',
#     'ist6': 'AgACAgIAAxkBAAICpWODq7z1_yhOOsOaZoMqGBa9KcbzAALzxjEbwWUgSPcP33J1YOJdAQADAgADcwADKwQ',
#     'ist8': 'AgACAgIAAxkBAAICqWODq7zdtAABvc6UICiqwn5ZglHijgAC98YxG8FlIEhRUwTYCoiOxAEAAwIAA3MAAysE',
#     'ist10': 'AgACAgIAAxkBAAICp2ODq7xkCaXMA8o4GLK9hn9KyfOKAAL1xjEbwWUgSE2xipgZM8iYAQADAgADcwADKwQ',
#     'ist12': 'AgACAgIAAxkBAAICqGODq7yA8P367Oiza5PBhFRfmpnEAAL2xjEbwWUgSL5iZAGgCujJAQADAgADcwADKwQ',
#     'ist14': 'AgACAgIAAxkBAAICpmODq7zIl0ncr1dX2MOE5unMgBf0AAL0xjEbwWUgSMowdVUrZoMzAQADAgADcwADKwQ'
# }

video_note_answers = {
    'nikita_fu-1': 'DQACAgIAAxkBAAILj2Ulk9xVAwm0mrK6RM1yRkHEJYtPAALrOwACuqQwSW4vft0vJDsqMAQ',
    'nikita_fu-2': 'DQACAgIAAxkBAAILnmUlmXsbaqZacYeME0feaZ2kDNf6AAIXPAACuqQwSdFuGBi4CqVtMAQ',
    'nikita_fu-3': 'DQACAgIAAxkBAAILn2UlmXteFNzi4fQPdu4tM-mfWpErAAIcPAACuqQwSRx32BraeA_WMAQ',
    # 'nikita_ok-1': 'DQACAgIAAxkBAAILkmUllh8I5SXuOycfTAvjDKRvEE3JAAIEPAACuqQwST31KZolaO54MAQ',
    'nikita_less10-1': 'DQACAgIAAxkBAAILlWUllp5QYALnqdu9nIhPD9hnV7EsAAIIPAACuqQwSZT81LebYZC0MAQ',
    'nikita_less10-2': 'DQACAgIAAxkBAAILm2UlmNbuVFcVitVUj9_LzW-_seQxAAITPAACuqQwSVwZ5jyR0Y9EMAQ',
    'nikita_mid-1': 'DQACAgIAAxkBAAILmGUll1P1bsTgv2sRBeMyi3KKx0EvAAINPAACuqQwSaA6-6WIBOmrMAQ',
    'nikita_high-1': 'DQACAgIAAxkBAAILz2Ulm38-sM910XQqz7vZZj5cIHjiAAKlPAACuqQwSY4dWivYz6wJMAQ',
    'nikita_high-2': 'DQACAgIAAxkBAAIMaGUloRvpKI-d2sXLl9gXA_gfzCqDAALiPAACuqQwSZfR3ywfNskkMAQ',
    'nikita_lucky-1': 'DQACAgIAAxkBAAIMa2UloaiHELlDCX45vfDAlbOmXSrSAALsPAACuqQwSSUykmOY4d0oMAQ',
    'nikita_lucky-2': 'DQACAgIAAxkBAAIMkGUlo7ANGfaRBAIh5SHsZpG6UCV_AAL7PAACuqQwScNAJ42xlrtSMAQ',
    'nikita_lucky-3': 'DQACAgIAAxkBAAIPvGUoQKe657_oQqdNqib72YPiAYm-AAJKPAACMEI4SW67dGfocuGUMAQ',
    'nikita_lucky-4': 'DQACAgIAAxkBAAIl8GU1-K0ukJwjvEixEC4AAR8wLZ2BHAACwjgAAoe8sEkD50-Im7W4XjAE',
    'nikita_fake_100-1': 'DQACAgIAAxkBAAIMdWUlohiKJyYheN0zqsgSdUWidQplAALxPAACuqQwScEmvuyBeSdAMAQ',
    'nikita_fake_100-2': 'DQACAgIAAxkBAAIMeGUlonMXzo6rB7kd96Gq1QvcgQOYAALzPAACuqQwSYoTCz6zebNnMAQ',
    'holid_100-1': 'DQACAgIAAxkBAAInAmU6fCdTbvxyTqqvnqQLDNufg5jHAAIFIwACx2tQSOBUK13yqjbyMAQ'
}

doc_ids = {
    'ershov': 'BQACAgIAAxkBAAIj12UuzbR6BbCNGizyrOiG_7ol7gKCAALePAAChDp5SVkVF2PQSBRJMAQ',
    'ershovg': 'BQACAgIAAxkBAAIkSmUvXPw06acIoFdKhmPeew-DanSeAAJYMwAChDqBSWj7BrAM1XnmMAQ',
    'yashenkomatem': 'BQACAgIAAxkBAAIlUmUyfis3THfffJvFGuEVTTmSlodbAAJ4OwACnvGYSefCXJcpmq7KMAQ'
}

gl = ["у", "е", 'ё', "ы", "а", "о", "э", "я", "и", "ю"]

available_gdzs = {'gdz_putina': 'gdz-putina.fun'}

ege_points = (
    {"primitive": 1, "math": 6, "russian": 3, "biology": 3, "history": 4, "it science": 7, "social": 2, "chemistry": 4,
     "physics": 5, "english": 2, "geography": 5, "literature": 3},
    {"primitive": 2, "math": 11, "russian": 5, "biology": 5, "history": 8, "it science": 14, "social": 4,
     "chemistry": 7,
     "physics": 9, "english": 3, "geography": 9, "literature": 5},
    {"primitive": 3, "math": 17, "russian": 8, "biology": 7, "history": 12, "it science": 20, "social": 6,
     "chemistry": 10,
     "physics": 14, "english": 4, "geography": 13, "literature": 8},
    {"primitive": 4, "math": 22, "russian": 10, "biology": 10, "history": 16, "it science": 27, "social": 8,
     "chemistry": 14, "physics": 18, "english": 5, "geography": 17, "literature": 10},
    {"primitive": 5, "math": 27, "russian": 12, "biology": 12, "history": 20, "it science": 34, "social": 10,
     "chemistry": 17, "physics": 23, "english": 7, "geography": 21, "literature": 13},
    {"primitive": 6, "math": 34, "russian": 15, "biology": 14, "history": 24, "it science": 40, "social": 12,
     "chemistry": 20, "physics": 27, "english": 8, "geography": 25, "literature": 15},
    {"primitive": 7, "math": 40, "russian": 17, "biology": 17, "history": 28, "it science": 43, "social": 14,
     "chemistry": 23, "physics": 32, "english": 9, "geography": 29, "literature": 18},
    {"primitive": 8, "math": 46, "russian": 20, "biology": 19, "history": 32, "it science": 46, "social": 16,
     "chemistry": 27, "physics": 36, "english": 10, "geography": 33, "literature": 20},
    {"primitive": 9, "math": 52, "russian": 22, "biology": 21, "history": 34, "it science": 48, "social": 18,
     "chemistry": 30, "physics": 39, "english": 11, "geography": 37, "literature": 23},
    {"primitive": 10, "math": 58, "russian": 24, "biology": 24, "history": 36, "it science": 51, "social": 20,
     "chemistry": 33, "physics": 41, "english": 13, "geography": 39, "literature": 25},
    {"primitive": 11, "math": 64, "russian": 27, "biology": 26, "history": 38, "it science": 54, "social": 22,
     "chemistry": 36, "physics": 43, "english": 14, "geography": 40, "literature": 28},
    {"primitive": 12, "math": 70, "russian": 29, "biology": 28, "history": 40, "it science": 56, "social": 24,
     "chemistry": 38, "physics": 44, "english": 15, "geography": 41, "literature": 30},
    {"primitive": 13, "math": 72, "russian": 32, "biology": 31, "history": 42, "it science": 59, "social": 26,
     "chemistry": 39, "physics": 46, "english": 16, "geography": 43, "literature": 32},
    {"primitive": 14, "math": 74, "russian": 34, "biology": 33, "history": 44, "it science": 62, "social": 28,
     "chemistry": 40, "physics": 48, "english": 18, "geography": 44, "literature": 34},
    {"primitive": 15, "math": 76, "russian": 36, "biology": 36, "history": 45, "it science": 64, "social": 30,
     "chemistry": 42, "physics": 49, "english": 19, "geography": 45, "literature": 35},
    {"primitive": 16, "math": 78, "russian": 37, "biology": 38, "history": 47, "it science": 67, "social": 32,
     "chemistry": 43, "physics": 51, "english": 20, "geography": 47, "literature": 36},
    {"primitive": 17, "math": 80, "russian": 39, "biology": 40, "history": 49, "it science": 70, "social": 34,
     "chemistry": 44, "physics": 53, "english": 21, "geography": 48, "literature": 37},
    {"primitive": 18, "math": 82, "russian": 40, "biology": 41, "history": 51, "it science": 72, "social": 36,
     "chemistry": 46, "physics": 54, "english": 22, "geography": 49, "literature": 38},
    {"primitive": 19, "math": 84, "russian": 42, "biology": 43, "history": 53, "it science": 75, "social": 38,
     "chemistry": 47, "physics": 56, "english": 24, "geography": 51, "literature": 39},
    {"primitive": 20, "math": 86, "russian": 43, "biology": 45, "history": 55, "it science": 78, "social": 40,
     "chemistry": 48, "physics": 58, "english": 25, "geography": 53, "literature": 40},
    {"primitive": 21, "math": 88, "russian": 45, "biology": 46, "history": 57, "it science": 80, "social": 42,
     "chemistry": 49, "physics": 59, "english": 26, "geography": 54, "literature": 41},
    {"primitive": 22, "math": 90, "russian": 46, "biology": 48, "history": 58, "it science": 83, "social": 44,
     "chemistry": 51, "physics": 61, "english": 27, "geography": 55, "literature": 42},
    {"primitive": 23, "math": 92, "russian": 48, "biology": 50, "history": 60, "it science": 85, "social": 45,
     "chemistry": 52, "physics": 62, "english": 28, "geography": 57, "literature": 43},
    {"primitive": 24, "math": 94, "russian": 49, "biology": 51, "history": 62, "it science": 88, "social": 47,
     "chemistry": 53, "physics": 64, "english": 29, "geography": 58, "literature": 44},
    {"primitive": 25, "math": 95, "russian": 51, "biology": 53, "history": 64, "it science": 90, "social": 48,
     "chemistry": 55, "physics": 65, "english": 30, "geography": 59, "literature": 45},
    {"primitive": 26, "math": 96, "russian": 52, "biology": 55, "history": 66, "it science": 93, "social": 49,
     "chemistry": 56, "physics": 67, "english": 31, "geography": 61, "literature": 46},
    {"primitive": 27, "math": 97, "russian": 54, "biology": 56, "history": 68, "it science": 95, "social": 51,
     "chemistry": 57, "physics": 68, "english": 32, "geography": 62, "literature": 47},
    {"primitive": 28, "math": 98, "russian": 55, "biology": 58, "history": 70, "it science": 98, "social": 52,
     "chemistry": 58, "physics": 70, "english": 33, "geography": 63, "literature": 49},
    {"primitive": 29, "math": 99, "russian": 57, "biology": 60, "history": 72, "it science": 100, "social": 53,
     "chemistry": 60, "physics": 71, "english": 34, "geography": 65, "literature": 50},
    {"primitive": 30, "math": 100, "russian": 58, "biology": 61, "history": 74, "it science": False, "social": 55,
     "chemistry": 61, "physics": 73, "english": 36, "geography": 66, "literature": 51},
    {"primitive": 31, "math": 100, "russian": 60, "biology": 63, "history": 76, "it science": False, "social": 56,
     "chemistry": 62, "physics": 74, "english": 37, "geography": 68, "literature": 52},
    {"primitive": 32, "math": 100, "russian": 61, "biology": 65, "history": 78, "it science": False, "social": 57,
     "chemistry": 64, "physics": 76, "english": 38, "geography": 72, "literature": 53},
    {"primitive": 33, "math": False, "russian": 63, "biology": 66, "history": 80, "it science": False, "social": 59,
     "chemistry": 65, "physics": 77, "english": 39, "geography": 77, "literature": 54},
    {"primitive": 34, "math": False, "russian": 64, "biology": 68, "history": 82, "it science": False, "social": 60,
     "chemistry": 66, "physics": 79, "english": 40, "geography": 81, "literature": 55},
    {"primitive": 35, "math": False, "russian": 66, "biology": 70, "history": 84, "it science": False, "social": 62,
     "chemistry": 68, "physics": 80, "english": 41, "geography": 86, "literature": 56},
    {"primitive": 36, "math": False, "russian": 67, "biology": 71, "history": 87, "it science": False, "social": 63,
     "chemistry": 69, "physics": 82, "english": 42, "geography": 90, "literature": 57},
    {"primitive": 37, "math": False, "russian": 69, "biology": 72, "history": 89, "it science": False, "social": 64,
     "chemistry": 70, "physics": 84, "english": 43, "geography": 95, "literature": 58},
    {"primitive": 38, "math": False, "russian": 70, "biology": 73, "history": 91, "it science": False, "social": 66,
     "chemistry": 71, "physics": 86, "english": 44, "geography": 100, "literature": 59},
    {"primitive": 39, "math": False, "russian": 72, "biology": 74, "history": 93, "it science": False, "social": 67,
     "chemistry": 73, "physics": 88, "english": 45, "geography": False, "literature": 60},
    {"primitive": 40, "math": False, "russian": 73, "biology": 75, "history": 95, "it science": False, "social": 68,
     "chemistry": 74, "physics": 90, "english": 46, "geography": False, "literature": 61},
    {"primitive": 41, "math": False, "russian": 75, "biology": 76, "history": 97, "it science": False, "social": 70,
     "chemistry": 75, "physics": 92, "english": 48, "geography": False, "literature": 63},
    {"primitive": 42, "math": False, "russian": 78, "biology": 77, "history": 100, "it science": False, "social": 71,
     "chemistry": 77, "physics": 94, "english": 49, "geography": False, "literature": 68},
    {"primitive": 43, "math": False, "russian": 81, "biology": 78, "history": False, "it science": False, "social": 72,
     "chemistry": 78, "physics": 96, "english": 50, "geography": False, "literature": 73},
    {"primitive": 44, "math": False, "russian": 83, "biology": 79, "history": False, "it science": False, "social": 73,
     "chemistry": 79, "physics": 98, "english": 51, "geography": False, "literature": 78},
    {"primitive": 45, "math": False, "russian": 86, "biology": 80, "history": False, "it science": False, "social": 75,
     "chemistry": 80, "physics": 100, "english": 52, "geography": False, "literature": 84},
    {"primitive": 46, "math": False, "russian": 89, "biology": 81, "history": False, "it science": False, "social": 77,
     "chemistry": 82, "physics": False, "english": 53, "geography": False, "literature": 89},
    {"primitive": 47, "math": False, "russian": 91, "biology": 83, "history": False, "it science": False, "social": 79,
     "chemistry": 84, "physics": False, "english": 54, "geography": False, "literature": 94},
    {"primitive": 48, "math": False, "russian": 94, "biology": 85, "history": False, "it science": False, "social": 81,
     "chemistry": 86, "physics": False, "english": 55, "geography": False, "literature": 100},
    {"primitive": 49, "math": False, "russian": 97, "biology": 86, "history": False, "it science": False, "social": 83,
     "chemistry": 88, "physics": False, "english": 56, "geography": False, "literature": False},
    {"primitive": 50, "math": False, "russian": 100, "biology": 88, "history": False, "it science": False, "social": 85,
     "chemistry": 90, "physics": False, "english": 57, "geography": False, "literature": False},
    {"primitive": 51, "math": False, "russian": False, "biology": 90, "history": False, "it science": False,
     "social": 86,
     "chemistry": 91, "physics": False, "english": 58, "geography": False, "literature": False},
    {"primitive": 52, "math": False, "russian": False, "biology": 91, "history": False, "it science": False,
     "social": 88,
     "chemistry": 93, "physics": False, "english": 60, "geography": False, "literature": False},
    {"primitive": 53, "math": False, "russian": False, "biology": 93, "history": False, "it science": False,
     "social": 90,
     "chemistry": 95, "physics": False, "english": 61, "geography": False, "literature": False},
    {"primitive": 54, "math": False, "russian": False, "biology": 95, "history": False, "it science": False,
     "social": 92,
     "chemistry": 97, "physics": False, "english": 62, "geography": False, "literature": False},
    {"primitive": 55, "math": False, "russian": False, "biology": 96, "history": False, "it science": False,
     "social": 94,
     "chemistry": 99, "physics": False, "english": 63, "geography": False, "literature": False},
    {"primitive": 56, "math": False, "russian": False, "biology": 98, "history": False, "it science": False,
     "social": 96,
     "chemistry": 100, "physics": False, "english": 64, "geography": False, "literature": False},
    {"primitive": 57, "math": False, "russian": False, "biology": 100, "history": False, "it science": False,
     "social": 98,
     "chemistry": False, "physics": False, "english": 65, "geography": False, "literature": False},
    {"primitive": 58, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": 100, "chemistry": False, "physics": False, "english": 66, "geography": False, "literature": False},
    {"primitive": 59, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 67, "geography": False, "literature": False},
    {"primitive": 60, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 68, "geography": False, "literature": False},
    {"primitive": 61, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 69, "geography": False, "literature": False},
    {"primitive": 62, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 70, "geography": False, "literature": False},
    {"primitive": 63, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 71, "geography": False, "literature": False},
    {"primitive": 64, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 73, "geography": False, "literature": False},
    {"primitive": 65, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 74, "geography": False, "literature": False},
    {"primitive": 66, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 75, "geography": False, "literature": False},
    {"primitive": 67, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 76, "geography": False, "literature": False},
    {"primitive": 68, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 77, "geography": False, "literature": False},
    {"primitive": 69, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 78, "geography": False, "literature": False},
    {"primitive": 70, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 79, "geography": False, "literature": False},
    {"primitive": 71, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 80, "geography": False, "literature": False},
    {"primitive": 72, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 81, "geography": False, "literature": False},
    {"primitive": 73, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 82, "geography": False, "literature": False},
    {"primitive": 74, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 84, "geography": False, "literature": False},
    {"primitive": 75, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 86, "geography": False, "literature": False},
    {"primitive": 76, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 88, "geography": False, "literature": False},
    {"primitive": 77, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 90, "geography": False, "literature": False},
    {"primitive": 78, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 92, "geography": False, "literature": False},
    {"primitive": 79, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 94, "geography": False, "literature": False},
    {"primitive": 80, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 96, "geography": False, "literature": False},
    {"primitive": 81, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 98, "geography": False, "literature": False},
    {"primitive": 82, "math": False, "russian": False, "biology": False, "history": False, "it science": False,
     "social": False, "chemistry": False, "physics": False, "english": 100, "geography": False, "literature": False})
subjects = {'math': 'математика профиль', 'russian': 'русский язык', 'physics': 'физика', 'biology': 'биология',
            'it science': 'информатика', 'social': 'обществознание', 'chemistry': 'химия', 'english': 'английский язык',
            'geography': 'география', 'literature': 'литература', 'history': 'история'}
