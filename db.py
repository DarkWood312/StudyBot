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

<b>Орфоэпия:</b>
/orthoepy - Запуск орфоэпии
/ostats - Топ проблемных слов среди <u>всех</u> пользователей

<b>Документы --> </b>/docs

<b>Кто автор? Исходный код? --> </b>/author
'''

owner_id = 493006916

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
