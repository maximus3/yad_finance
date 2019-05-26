import sqlite3
import time
import logging

logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG)#, filename = u'mylog.log')

# ChatBase
metrik_key = 'TOKEN_HERE'

# Общая база данных
db = '/root/debt/my.db'

# Версия
version = '0.5.3 Beta'

month = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
monthRim = {'январь':1,'февраль':2,'март':3,'апрель':4,'май':5,'июнь':6,'июль':7,'август':8,'сентябрь':9,'октябрь':10,'ноябрь':11,'декабрь':12}
monthRim_rev = {1:'январь',2:'февраль',3:'март',4:'апрель',5:'май',6:'июнь',7:'июль',8:'август',9:'сентябрь',10:'октябрь',11:'ноябрь',12:'декабрь'}
monthR = {'января':1,'февраля':2,'марта':3,'апреля':4,'мая':5,'июня':6,'июля':7,'августа':8,'сентября':9,'октября':10,'ноября':11,'декабря':12}
monthR_rev = {1:'января',2:'февраля',3:'марта',4:'апреля',5:'мая',6:'июня',7:'июля',8:'августа',9:'сентября',10:'октября',11:'ноября',12:'декабря'}
mdays = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}

# Описание
desc_uo = """
0.5.0:
Добавлено минимальное логгирование
Добавлена функция редактирования долгов
0.5.1:
Небольшие фиксы
0.5.2:
Небольшие фиксы
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
                    "title": "Текущий счет",
                    "hide": True
                },
                {
                    "title": "Смена счета",
                    "hide": True
                },
                {
                    "title": "Выход",
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

    elif step == 'main_adddebt':
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

    elif step == 'main_editdebt':
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

# Проверка числа (деньги, 2 знака после запятой)
def check_num(a):
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

# Форматирование строки добавления расхода/дохода
def check_fin(text):
    try:
        text = text.split()
        fin = [0]*6
        if text[0] != 'добавить' and text[0] != 'добавь':
            logging.debug( u'check_fin - 1' )
            return None
        text.pop(0)
        if text[0] != 'расход' and text[0] != 'доход':
            logging.debug( u'check_fin - 2' )
            return None
        fin[0] = text.pop(0)
        fin[1] = ""
        if 'рублей' not in text and 'рубля' not in text and 'рубль' not in text:
            logging.debug( u'check_fin - 3' )
            return None
        while text[1] != 'рублей' and text[1] != 'рубль' and text[1] != 'рубля':
            fin[1] += text.pop(0)
            if text[1] != 'рублей' and text[1] != 'рубль' and text[1] != 'рубля':
                fin[1] += ' '
        fin[2] = round(float(int(text[0])),2)
        text.pop(0)
        fin[3] = text.pop(0)
        if text[1] == 'копеек' or text[1] == 'копейки' or text[1] == 'копейка':
            fin[2] += round(float(int(text[0]))/100,2)
            text.pop(0)
            text.pop(0)
        if fin[2] < 0:
            logging.debug( u'check_fin - 4' )
            return None
        if text[0] != 'в' or text[1] != 'категории':
            if text[0] != 'категории':
                logging.debug( u'check_fin - 5' )
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
                logging.debug( u'check_fin - 6' )
                return None
            text.pop(0)
            if 'счет' not in text.pop(0):
                logging.debug( u'check_fin - 7' )
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
            logging.debug( u'check_fin - 8' )
            return None
        text.pop(0)
        if 'счет' not in text.pop(0):
            logging.debug( u'check_fin - 9' )
            return None
        fin[5] = ' '.join(text)
        return fin
    except Exception:
        logging.debug( u'check_fin - 0' )
        return None

# Форматирование строки добавления долга
def check_debt(text):
    try:
        text = text.split()
        debt = [0]*5
        if text[0] != 'добавить' and text[0] != 'добавь':
            logging.debug( u'check_debt - 1' )
            return None
        text.pop(0)
        if text.pop(0) != 'долг':
            logging.debug( u'check_debt - 2' )
            return None
        debt[0] = text.pop(0)
        debt[1] = text.pop(0)
        mn = 0
        if text[0] == 'минус':
            mn = 1
            text.pop(0)
            debt[2] = round(float(int(text.pop(0))),2)
        else:
            debt[2] = round(float(int(text.pop(0))),2)
        debt[4] = text.pop(0)
        if text == []:
            debt[3] = 'все'
            if mn == 1:
                debt[2] = -debt[2]
            return debt
        if text[1] == 'копеек' or text[1] == 'копейки' or text[1] == 'копейка':
            debt[2] += round(float(int(text[0]))/100,2)
            text.pop(0)
            text.pop(0)
        if mn == 1:
            debt[2] = -debt[2]
        if text == []:
            debt[3] = 'все'
            return debt
        if text[0] != 'со' and text[0] != 'на':
            logging.debug( u'check_debt - 3' )
            return None
        text.pop(0)
        if 'счет' not in text.pop(0):
            logging.debug( u'check_debt - 4' )
            return None
        debt[3] = ' '.join(text)
        return debt
    except Exception:
        logging.debug( u'check_debt - 0' )
        return None

# Форматирование строки редактирования долга
def check_eddebt(text):
    try:
        text = text.split()
        debt = [0]*5
        debt[0], debt[1] = text[0], text[1]
        text.pop(0)
        text.pop(0)
        while not text[0].isdigit() and 'долг' not in text[0] and 'минус' not in text[0]:
            text.pop(0)
        mn = 0
        if 'долг' in text[0]:
            debt[2] = 'all'
            debt[3] = 'рублей'
            text.pop(0)
        elif text[0] == 'минус':
            text.pop(0)
            mn = 1
            debt[2] = round(float(check_num((text.pop(0)))),2)
            debt[3] = text.pop(0)
        else:
            debt[2] = round(float(check_num((text.pop(0)))),2)
            debt[3] = text.pop(0)
        if text == []:
            if mn == 1:
                debt[2] = -debt[2]
            debt[4] = 'все'
            return debt
        if text[1] == 'копеек' or text[1] == 'копейки' or text[1] == 'копейка':
            debt[2] += round(float(int(text.pop(0)))/100,2)
            text.pop(0)
        if mn == 1:
            debt[2] = -debt[2]
        if text == []:
            debt[4] = 'все'
            return debt
        if text[0] != 'со' and text[0] != 'на':
            logging.debug( u'check_eddebt - 1' )
            return None
        text.pop(0)
        if 'счет' not in text.pop(0):
            logging.debug( u'check_eddebt - 2' )
            return None
        debt[4] = ' '.join(text)
        return debt
    except Exception:
        logging.debug( u'check_eddebt - 0' )
        return None

# Форматирование строки просмотра расходов/доходов за период
def check_hisfin(text):
    try:
        text = text.split()
        fin = [0]*3
        while text[0] != 'расходы' and text[0] != 'доходы' :
            text.pop(0)
        fin[0] = text.pop(0)
        if text.pop(0) != 'за':
            logging.debug( u'check_hisfin - 1' )
            return None
        if text[0] == 'сегодня':
            text.pop(0)
            fin += tday()
        elif text[0] == 'вчера':
            text.pop(0)
            fin += lday()
        elif text[0] == 'этот' and text[1] == 'месяц':
            text.pop(0)
            text.pop(0)
            fin.append(0)
            tme = tday()
            fin.append(tme[1])
            fin.append(tme[2])
        elif text[0] == 'прошлый' and text[1] == 'месяц':
            text.pop(0)
            text.pop(0)
            fin.append(0)
            tme = lmon()
            fin.append(tme[0])
            fin.append(tme[1])
        elif not text[0].isdigit():
            fin.append(0)
            fin.append(monthRim[text.pop(0)])
            if text != [] and text[0].isdigit():
                fin.append(int(text.pop(0)))
                if text != [] and 'год' in text[0]:
                    text.pop(0)
            else:
                tme = tday()
                if fin[4] > tme[1]:
                    fin.append(tme[2] - 1)
                else:
                    fin.append(tme[2])
        else:
            fin.append(int(text[0]))
            text.pop(0)
            fin.append(monthR[text[0]])
            text.pop(0)
            try:
                fin.append(int(text[0]))
                text.pop(0)
                if text != [] and 'год' in text[0]:
                    text.pop(0)
            except Exception:
                year = tday()
                fin.append(year[2])
        if text == []:
            fin[1] = 'все'
            fin[2] = 'all'
            return fin
        if text[0] != 'в' or text[1] != 'категории':
            if text[0] != 'категории':
                fin[1] = 'все'
                if text.pop(0) != 'со':
                    logging.debug( u'check_hisfin - 2' )
                    return None
                if text[0] == 'всех' and 'счет' in text[1]:
                    fin[2] = 'все'
                    return fin
                if 'счет' not in text.pop(0):
                    logging.debug( u'check_hisfin - 3' )
                    return None
                fin[2] = text.pop(0)
                return fin
        else:
            text.pop(0)            
        text.pop(0)
        fin[1] = text.pop(0)
        if text == []:
            fin[2] = 'all'
            return fin
        if text.pop(0) != 'со':
            logging.debug( u'check_hisfin - 4' )
            return None
        if text[0] == 'всех' and 'счет' in text[1]:
            fin[2] = 'все'
            return fin
        if 'счет' not in text.pop(0):
            logging.debug( u'check_hisfin - 5' )
            return None
        fin[2] = text.pop(0)
        return fin
    except Exception:
        logging.debug( u'check_hisfin - 0' )
        return None

# Дата сегодня в виде массива
def tday():
    a = time.asctime()
    a = a.split()
    b = [int(a[2]),month[a[1]],int(a[4])]
    return b

# Дата вчера в виде массива
def lday():
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

# Дата сегодня в виде строки
def stday():
    a = str(tday())
    a = a.replace('[','')
    a = a.replace(']','')
    a = a.replace(', ','.')
    return a

# Проверка текста, True если есть ошибка
def check_text(text, tp):
    if tp == 'rus':
        for i in text:
            if (not (i >= 'а' and i <= 'я')) and i != ' ':
                return True
        return False
    elif tp == 'rus1':
        for i in text:
            if (not (i >= 'а' and i <= 'я')) and i != ' ' and (not (i >= '0' and i <= '9')):
                return True
        return False
    elif tp == 'eng1':
        for i in text:
            if (not (i >= 'A' and i <= 'Z')) and i != ' ' and (not (i >= '0' and i <= '9')) and (not (i >= 'a' and i <= 'z')):
                return True
        return False

# Прошлый месяц
def lmon():
    a = time.asctime()
    a = a.split()
    b = [month[a[1]],int(a[4])]
    b [0] -= 1
    if b[0] < 1:
        b[1] -= 1
        b[0] = 12
    return b
