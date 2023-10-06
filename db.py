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

owner_id = 493006916

kist_ids = {
    'ist2': 'AgACAgIAAxkBAAICoWODq5zJeX6L2U5-Z6efHN1QM4MuAALxxjEbwWUgSFHg8XorGDFtAQADAgADcwADKwQ',
    'ist4': 'AgACAgIAAxkBAAICpGODq7wR5Z87SBrq3cPZeDEoqX5DAALyxjEbwWUgSLXbG5jX4FJSAQADAgADcwADKwQ',
    'ist6': 'AgACAgIAAxkBAAICpWODq7z1_yhOOsOaZoMqGBa9KcbzAALzxjEbwWUgSPcP33J1YOJdAQADAgADcwADKwQ',
    'ist8': 'AgACAgIAAxkBAAICqWODq7zdtAABvc6UICiqwn5ZglHijgAC98YxG8FlIEhRUwTYCoiOxAEAAwIAA3MAAysE',
    'ist10': 'AgACAgIAAxkBAAICp2ODq7xkCaXMA8o4GLK9hn9KyfOKAAL1xjEbwWUgSE2xipgZM8iYAQADAgADcwADKwQ',
    'ist12': 'AgACAgIAAxkBAAICqGODq7yA8P367Oiza5PBhFRfmpnEAAL2xjEbwWUgSL5iZAGgCujJAQADAgADcwADKwQ',
    'ist14': 'AgACAgIAAxkBAAICpmODq7zIl0ncr1dX2MOE5unMgBf0AAL0xjEbwWUgSMowdVUrZoMzAQADAgADcwADKwQ'
}

doc_ids = {
    'algm': 'BQACAgIAAxkBAAIDkGOQ6wYgKv3CSNOwOvUwDW01owNeAAJhJgAC10SISFwGRw3DwWxHKwQ'
}

gl = ["у", "е", 'ё', "ы", "а", "о", "э", "я", "и", "ю"]

available_gdzs = {'gdz_putina': 'gdz-putina.fun'}