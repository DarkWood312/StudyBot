from aiogram.types import ParseMode


async def gdz_sender(var, gdz, message, subject_name: str, tem=None, work=None):
    if '-' in str(var):
        f, s = str(var).split('-')
        vars_list = [*range(int(f.strip()), int(s.strip()) + 1)]
    elif ',' in str(var):
        vars_list = str(var).split(',')
        vars_list = list(dict.fromkeys([int(i.strip()) for i in vars_list]))
    else:
        var = int(var)
        vars_list = [var]
    for one_var in vars_list:
        if tem is not None:
            response, link = await gdz(tem, work, one_var)
        else:
            response, link = await gdz(one_var)
        for group in response:
            if tem is not None:
                group[0]['caption'] = f'<b>{subject_name}</b>: <a href="{link}">Тема {tem}, Работа {work}, Вариант {one_var}</a>'
            else:
                group[0]['caption'] = f'<b>{subject_name}</b>: <a href="{link}">{one_var}</a>'
            group[0]['parse_mode'] = ParseMode.HTML
            await message.answer_media_group(group)
