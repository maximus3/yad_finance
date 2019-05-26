import sqlite3
import time

# Общая база данных
db = '/root/debt/my.db'

# Версия
version = '0.2.0 Beta'

month = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
monthR = {'января':1,'февраля':2,'марта':3,'апреля':4,'мая':5,'июня':6,'июля':7,'августа':8,'сентября':9,'октября':10,'ноября':11,'декабря':12}
monthR_rev = {1:'января',2:'февраля',3:'марта',4:'апреля',5:'мая',6:'июня',7:'июля',8:'августа',9:'сентября',10:'октября',11:'ноября',12:'декабря'}
mdays = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}

# Описание
desc = """
Добавлены новые функции:
Запись расходов
"""

# База данных для определенного пользователя
def user_db(dat):
    return '/root/debt/users/' + dat + '/data.db'

# Предыдущий шаг
def prev_step(text):
    text = text.split('_')
    text.pop()
    text = '_'.join(text)
    return text

# Функция возвращает кнопки.
def getBut(step):

    buttons = []
    
    if step == 'mainUS':
        buttons = [
            {'title': "Помощь", 'hide': True}
        ]
        
    elif step == 'mainUS_waiting':
        buttons = [
                {
                    "title": "Проверка авторизации",
                    "hide": True
                },
                {
                    "title": "Отменить авторизацию",
                    "hide": True
                }
            ]

    elif step == 'main':
        buttons = [
                {
                    "title": "Баланс",
                    "hide": True
                },
                {
                    "title": "Долги",
                    "hide": True
                },
                {
                    "title": "Помощь",
                    "hide": True
                },
                {
                    "title": "Выход",
                    "hide": True
                },
                {
                    "title": "Текущий счет",
                    "hide": True
                },
                {
                    "title": "Смена счета",
                    "hide": True
                }
            ]

    elif step == 'main_addfin':
        buttons = [
                {
                    "title": "Да",
                    "hide": True
                },
                {
                    "title": "Нет",
                    "hide": True
                }
            ]

    return buttons

def check_num(a):#проверка числа
    a = a.replace(',','.')
    try:
        a = float(a)
        a = str(a)
    except Exception:
        return 'NO'
    k = a
    a = a.split('.')
    if len(a[1])>2:
        return 'NO'
    return k

def check_fin(text):
    try:
        text = text.split()
        fin = [0]*6
        if text[0] != 'добавить' and text[0] != 'добавь':
            return None
        text.pop(0)
        if text[0] != 'расход' and text[0] != 'доход':
            return None
        fin[0] = text.pop(0)
        fin[1] = ""
        if 'рублей' not in text and 'рубля' not in text and 'рубль' not in text:
            return None
        while text[1] != 'рублей' and text[1] != 'рубль' and text[1] != 'рубля':
            fin[1] += text.pop(0)
            if text[1] != 'рублей' and text[1] != 'рубль' and text[1] != 'рубля':
                fin[1] += ' '
        fin[2] = round(float(check_num((text[0]))),2)
        text.pop(0)
        if fin[2] < 0:
            return None
        fin[3] = text.pop(0)
        if text[0] != 'в' or text[1] != 'категории':
            if text[0] != 'категории':
                return None
        else:
            text.pop(0)
        text.pop(0)
        fin[4] = text.pop(0)
        if text == []:
            fin += tday()
            fin[5] = 'все'
            return fin
        if text[0] != 'за':
            if (text[0] != 'со' and fin[0] == 'расход') or (text[0] != 'на' and fin[0] == 'доход'):
                return None
            text.pop(0)
            if 'счет' not in text.pop(0):
                return None
            fin[5] = ' '.join(text)
            fin += tday()
            return fin
        text.pop(0)
        if text[0] == 'сегодня':
            text.pop(0)
            fin += tday()
        elif text[0] == 'вчера':
            text.pop(0)
            fin += lday()
        else:
            fin.append(int(text[0]))
            text.pop(0)
            fin.append(monthR[text[0]])
            text.pop(0)
            try:
                fin.append(int(text[0]))
                text.pop(0)
                if text[0] == 'года':
                    text.pop(0)
            except Exception:
                year = tday()
                fin.append(year[2])
        if text == []:
            fin[5] = 'все'
            return fin
        if (text[0] != 'со' and fin[0] == 'расход') or (text[0] != 'на' and fin[0] == 'доход'):
            return None
        text.pop(0)
        if 'счет' not in text.pop(0):
            return None
        fin[5] = ' '.join(text)
        return fin
    except Exception:
        return None

def tday():#дата сегодня в виде массива
    a = time.asctime()
    a = a.split()
    b = [int(a[2]),month[a[1]],int(a[4])]
    return b

def lday():#дата вчера в виде массива
    a = time.asctime()
    a = a.split()
    b = [int(a[2]),month[a[1]],int(a[4])]
    v = 0
    if b[2]%4 == 0:
        v = 1
    b [0] -= 1
    if b[0] < 1:
        b[1] -= 1
        if b[1] < 1:
            b[2] -= 1
            b[1] = 12
        if b[1] != 2:
            v = 0
        b[0] = mdays[b[1]] + v
    return b

