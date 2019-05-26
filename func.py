import time
import sqlite3
import logging
from config import month, mdays, days, monthRim, monthR
from config import db as data_base

# Настройка логгирования
logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO, filename = u'fin_alice.log')

# Проверка уже залогинившихся пользователей
# Вход: -
# Выход: словарь с логинами и шагами
def load_ids():
    sessionStorage = {}
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    cur.execute('SELECT id, login FROM zalog_alice')
    for row in cur:
        sessionStorage[row[0]] = {
            'step': 'main',
            'login': row[1],
            'fin': 'все'
        }
    cur.close()
    conn.close()
    return sessionStorage

# Проверка авторизации
# Вход:
# Выход: 
def check_session(user_id, login = None):
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    cur.execute('SELECT id, login FROM zalog_alice')
    for row in cur:
        if row[0] == user_id:
            if login == None:
                cur.close()
                conn.close()
                return row[1]
            if row[1] == login:
                cur.close()
                conn.close()
                return True
    cur.close()
    conn.close()
    return False

# Проверка фразы на существование в базе
# Вход: строка (искомая фраза)
# Выход: True если данная фраза есть в базе, False иначе
def phrase_in(text):
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    cur.execute("SELECT phrase, answer, login FROM alice")
    for row in cur:
        if row[0] == text:
            cur.close()
            conn.close()
            return True, row[1], row[2]
    cur.close()
    conn.close()
    return False, [], []

# Проверка вещественного числа (два знака после запятой)
# Вход: Строка
# Выход: 'NO' если это не число с двумя знаками после запятой, иначе само число
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

# База данных для определенного пользователя
# Вход: логин пользователя
# Выход: адрес базы данных данного пользователя
def user_db(login):
    return '/root/debt/users/' + login + '/data.db'

# Папка ресурсов определенного пользователя
# Вход: логин пользователя
# Выход: адрес адрес папки ресурсов данного пользователя
def user_res(login):
    return '/root/debt/users/' + login + '/'

# Предыдущий шаг
# Вход: текущий шаг (main_..._X_Y)
# Выход: предыдущий шаг (main_..._X)
def prev_step(text):
    text = text.split('_')
    text.pop()
    text = '_'.join(text)
    return text

# Дата сегодня в виде массива день-месяц-год
# Вход: -
# Выход: Список с элементами - ДД, ММ, ГГГГ (сегодня)
def tday():
    a = time.asctime()
    a = a.split()
    b = [int(a[2]),month[a[1]],int(a[4])]
    return b

# Дата вчера в виде массива ДД ММ ГГГГ
# Вход: (не обязательно) список вида time.asctime.split()
# Выход: список вида ДД, ММ, ГГГГ (вчера)
def lday(a = time.asctime().split()):
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
            if b[2]%4 == 0:
                v = 1
            else:
                v = 0
        b[0] = mdays[b[1]]
        if b[1] == 2:
            b[0] += v
    return b

# Дата сегодня в виде строки
# Вход: -
# Выход: Строка вида 'ДД.ММ.ГГГГ' (сегодня)
def stday():
    a = str(tday())
    a = a.replace('[','')
    a = a.replace(']','')
    a = a.replace(', ','.')
    return a

# Прошлый месяц
# Вход: -
# Выход: Список вида ММ, ГГГГ (предыдущий месяц)
def lmon():
    a = time.asctime()
    a = a.split()
    b = [month[a[1]],int(a[4])]
    b [0] -= 1
    if b[0] < 1:
        b[1] -= 1
        b[0] = 12
    return b

# Проверка текста, True если есть ошибка
# Вход: строка; ключ для проверки
# Выход: True если есть строка не соответствует нужному формату, False иначе
def check_text(text, tp):
    if tp == 'rus':
        for i in text:
            if (not (i >= 'а' and i <= 'я')) and i != ' ' and i != 'ё':
                return True
        return False
    elif tp == 'rus1':
        for i in text:
            if (not (i >= 'а' and i <= 'я')) and i != ' ' and (not (i >= '0' and i <= '9')) and i != 'ё':
                return True
        return False
    elif tp == 'eng1':
        for i in text:
            if (not (i >= 'A' and i <= 'Z')) and i != ' ' and (not (i >= '0' and i <= '9')) and (not (i >= 'a' and i <= 'z')):
                return True
        return False
    elif tp == 'login':
        if len(text) > 32:
            return True
        for i in text:
            if (not (i >= '0' and i <= '9')) and (not (i >= 'a' and i <= 'z')):
                return True
        return False
    elif tp == 'pass':
        if len(text) > 32:
            return True
        for i in text:
            if (not (i >= 'A' and i <= 'Z')) and (not (i >= '0' and i <= '9')) and (not (i >= 'a' and i <= 'z')):
                return True
        return False
    elif tp == 'ruseng1':
        for i in text:
            if (not (i >= 'A' and i <= 'Z')) and i != 'ё' and i != ' ' and (not (i >= '0' and i <= '9')) and (not (i >= 'a' and i <= 'z')) and (not (i >= 'а' and i <= 'я')) and (not (i >= 'А' and i <= 'Я')):
                return True
        return False

# Неделя от текущий даты - k в формате ДД ММ ГГГГ ДД ММ ГГГГ
# Вход: (не обязательно) число, на которое надо уменьшить текущую дату
# Выход: список вида ДД, ММ, ГГГГ, ДД, ММ, ГГГГ (неделя от и до)
def tweek(k = 0):
    a = time.asctime()
    a = a.split()
    a[0] = days[a[0]]
    b = day_min(k, a)
    a[1] = month[b[1]]
    a[2] = b[0]
    a[4] = b[2]
    while k > 0:
        a[0] -= 1
        k -= 1
        if a[0] == 0:
            a[0] = 7
    return day_min(a[0] - 1, a) + day_plus(7 - a[0], a)

# Отнять k дней
# Вход: Число k; (не обязательно) список вида time.asctime.split(); (не обязательно) список ДД, ММ, ГГГГ
# Выход: список вида ДД, ММ, ГГГГ (-k дней от даты a)
def day_min(k, a = time.asctime().split(), b = []):
    if b == []:
        b = [int(a[2]),month[a[1]],int(a[4])]
    v = 0
    if b[2]%4 == 0:
        v = 1
    for i in range(k):
        b [0] -= 1
        if b[0] < 1:
            b[1] -= 1
            if b[1] < 1:
                b[2] -= 1
                b[1] = 12
                if b[2]%4 == 0:
                    v = 1
                else:
                    v = 0
            b[0] = mdays[b[1]]
            if b[1] == 2:
                b[0] += v
    return b

# Прибавить k дней
# Вход: Число k; (не обязательно) список вида time.asctime.split()
# Выход: список вида ДД, ММ, ГГГГ (+k дней от даты a)
def day_plus(k, a = time.asctime().split()):
    b = [int(a[2]),month[a[1]],int(a[4])]
    v = 0
    if b[2]%4 == 0:
        v = 1
    for i in range(k):
        b [0] += 1
        if b[0] > mdays[b[1]]:
            if b[1] == 2 and v == 1:
                continue
            b[1] += 1
            if b[1] > 12:
                b[2] += 1
                b[1] = 1
                if b[2]%4 == 0:
                    v = 1
                else:
                    v = 0
            b[0] = 1
    return b

# Определение окончания
# Вход: число
# Выход: рубль/рублей/рубля в зависимости от числа
def get_rub(ch):
    try:
        ch = int(ch)
    except Exception:
        return 'рублей'
    if ch % 10 == 0 or ch % 10 > 4 or (ch % 100 > 10 and ch % 100 < 15):
        return 'рублей'
    elif ch % 10 == 1:
        return 'рубль'
    elif ch % 10 > 1 and ch % 10 < 5:
        return 'рубля'

# Функция созает token на основе user_id
# Вход: user_id
# Выход: token
def create_token(user_id):
    token = str(user_id)
    return token + 'q'*(64 - len(token))

# Функция возвращает кнопки
# Вход: шаг пользователя
# Выход: словарь с кнопками
def getBut(step, user_id=""):

    buttons = []
    
    if step == 'mainUS':
        url = "http://t.me/debt_m3bot?start=" + create_token(user_id)
        buttons = [
            {
                'title': "Помощь",
                'hide': True
            },
            {
                "title": "Новости",
                "payload": {},
                "url": "http://t.me/finance_m3news/",
                "hide": True
            },
            {
                "title": "Телеграм-бот",
                "payload": {},
                "url": "http://t.me/debt_m3bot/",
                "hide": True
            },
            {
                "title": "Быстрая авторизация",
                "payload": {},
                "url": url,
                "hide": True
            },
            {
                "title": "Обратная связь",
                "payload": {},
                "url": "http://t.me/m3prod/",
                "hide": True
            }
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
                    "title": "Смена счета",
                    "hide": True
                },
                {
                    "title": "Выход",
                    "hide": True
                }
            ]

    elif step in ['main_addfin','main_adddebt','main_editdebt']:
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

# Форматирование строки добавления расхода/дохода
# Вход: строка
# Выход: None, либо список с расходом/доходом
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
        logging.debug( u'check_fin ' )
        return None

# Форматирование строки добавления долга
# Вход: строка
# Выход: None, либо список с нужной позицией
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
# Вход: строка
# Выход: None, либо список с нужной позицией
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
# Вход: строка
# Выход: None, либо список с нужной позицией
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
