# -*- coding: utf-8 -*-
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем модули для работы с JSON и логами.
import json
import logging

# Импортируем подмодули Flask для запуска веб-сервиса.
from flask import Flask, request
app = Flask(__name__)

# Импортируем модули для работы с базой данных.
import sqlite3

# Общая база данных
db = '/root/debt/my.db'

# Версия
version = '0.1.0 Beta'

# Описание
desc = """

"""

# База данных для определенного пользователя
def user_db(dat):
    return '/root/debt/users/' + dat + '/data.db'

def prev_step(text):
    text = text.split('_')
    text.pop()
    text = '_'.join(text)
    return text

logging.basicConfig(level=logging.DEBUG)

# Хранилище данных о сессиях.
sessionStorage = {}

# Проверка уже залогинившихся пользователей
def load_ids():
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT id, login FROM zalog_alice')
    for row in cur:
        sessionStorage[row[0]] = {
            'step': 'main',
            'login': row[1]
        }
    cur.close()
    conn.close()

load_ids()

# Задаем параметры приложения Flask.
@app.route("/", methods=['POST'])
def main():
# Функция получает тело запроса и возвращает ответ.
    logging.info('Request: %r', request.json)

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog(request.json, response)

    logging.info('Response: %r', response)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )

# Функция для непосредственной обработки диалога.
def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']: 
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.

        # Если пользоваьель уже логинился
        if sessionStorage.get(user_id) is not None:
            res['response']['text'] = "Добро пожаловать!\nP.S. Навык находится в разработке, так что возможны ошибки, заранее прошу прощения."
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        sessionStorage[user_id] = {
            'step': 'mainUS',
        }

        res['response']['text'] = """
        Привет! Данный навык помогает в более удобном формате контролировать свои расходы.
        Данный навык связан с телеграм-ботом @debt_m3bot
        Авторизируйте ваше устройство при помощи кодовой фразы или используйте "Помощь"
        P.S. Навык находится в разработке, так что возможны ошибки, заранее прошу прощения.
        """
        res['response']['text'] += '\nВерсия: ' + version
        res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
        return

    # Обрабатываем ответ пользователя.
    com = req['request']['command'].lower()
    
    if sessionStorage[user_id]['step'] == 'mainUS':
        # Пользователь попросил помощь
        if com == 'помощь':
            res['response']['text'] = """
                Итак, для начала вы должны авторизироваться в телеграм-боте и ввести команду /alice.
                После этого бот предложит вам записать кодовую фразу. Запишите ее.
                Далее вам необходимо сказать фразу-вопрос мне. Если все хорошо, то в я скажу вам вашу фразу-ответ.
                После этого вы опять долны мне сказать что-то, что я отправлю в телеграм-бота.
                Вы тоже должны зайти в телеграм и опять ввести команду /alice.
                Если бот прислал вам ту фразу, что вы сказали мне последней, то вам осталось всего лишь нажать кнопку "ДА" и пользоваться!
                Удачи!
            """
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])

        else:
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute('SELECT phrase, answer, login FROM alice')
            for row in cur:
                if com == row[0]:
                    res['response']['text'] = row[1] + '\nТеперь я жду от вас фразу, которая будет отправлена в телеграм-бота'
                    sessionStorage[user_id]['step'] += '_login'
                    sessionStorage[user_id]['login'] = row[2]
                    cur.close()
                    conn.close()
                    return
            cur.close()
            conn.close()
            res['response']['text'] = "К сожалению, у меня не получилось найти такую фразу. Проверьте ее правильность (падежи и формы слов)"
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

    elif sessionStorage[user_id]['step'] == 'mainUS_login':
        conn = sqlite3.connect(user_db(sessionStorage[user_id]['login']))
        cur = conn.cursor()
        cur.execute("INSERT INTO alice (id,phrase,login) VALUES ('%s','%s','%s')"%(user_id,com,sessionStorage[user_id]['login']))
        conn.commit()
        cur.close()
        conn.close()
        sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
        sessionStorage[user_id]['step'] += '_waiting'
        res['response']['text'] = """Отлично! Теперь зайдите в телеграм-бота и подтвердите авторизацию. Для проверки или отмены используйте команды "Проверка авторизации" и "Отменить авторизацию" соответственно"""
        res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
        return

    elif sessionStorage[user_id]['step'] == 'mainUS_waiting':
        if ('отмени' in com) or ('отмена' in com):
            if check_session(user_id):
                sessionStorage[user_id]['step'] = 'main'
                res['response']['text'] = 'Отмена невозможна, авторизация уже пройдена! Ваш аккаунт: ' + sessionStorage[user_id]['login']
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return
            
            conn = sqlite3.connect(user_db(sessionStorage[user_id]['login']))
            cur = conn.cursor()
            cur.execute("DELETE FROM alice WHERE id = '%s'"%(user_id))
            conn.commit()
            cur.close()
            conn.close()
            sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
            res['response']['text'] = "Авторизация отменена"
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        elif 'провер' in com:
            conn = sqlite3.connect(user_db(sessionStorage[user_id]['login']))
            cur = conn.cursor()
            cur.execute("SELECT * FROM alice WHERE id = '%s'"%(user_id))
            for row in cur:
                res['response']['text'] = 'Пока новостей нет)'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                cur.close()
                conn.close()
                return
            if check_session(user_id):
                sessionStorage[user_id]['step'] = 'main'
                res['response']['text'] = 'Авторизация успешно пройдена! Ваш аккаунт: ' + sessionStorage[user_id]['login']
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return
            sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
            res['response']['text'] = 'Вас не захотели добавлять'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        else:
            res['response']['text'] = 'Я вас не понимаю'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
            
        
        
    elif sessionStorage[user_id]['step'] == 'main':
        if not (check_session(user_id)):
            res['response']['text'] = "Бот выполнил деаутентификацию."
            sessionStorage[user_id]['step'] = 'mainUS'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
        
        if com == 'помощь':
            res['response']['text'] = """
            Вот список команд:
            Баланс - узнать баланс ваших счетов
            Долги - список ваших должников
            Выход - отвязать аккаунт
            P.S. Данный навык находится в разработке, поэтому функции будут появляться постепенно
            """
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
            
        elif 'баланс' in com:
            res['response']['text'] = watch_bank(user_id)
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        elif 'долги' in com or 'должник' in com:
            res['response']['text'] = watch_debts(user_id)
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        elif 'выход' in com or 'выйти' in com:
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("DELETE FROM zalog_alice WHERE id = '%s'"%(user_id))
            conn.commit()
            cur.close()
            conn.close()
            sessionStorage[user_id]['step'] = 'mainUS'
            res['response']['text'] = "Выход выполнен"
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        else:
            res['response']['text'] = """
            Я вас не понимаю. Можете воспользоваться помощью.
            """
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

# Функция возвращает кнопки.
def getBut(step):

    buttons = []
    
    # Выбираем части речи из массива
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
                }
            ]

    return buttons


def watch_bank(user_id):
    login = sessionStorage[user_id]['login']
    udb = user_db(login)
    kol = 0
    osum = 0
    sdebt = 0
    stroka = ""
    stroka += 'Ваши счета:\n'
    conn = sqlite3.connect(udb)
    cur = conn.cursor()
    cur.execute("SELECT name, bal FROM bank WHERE login = '%s'"%(login))
    for row in cur:
        kol += 1
        stroka += str(kol) + ') ' + row[0] + '\nБаланс счета: ' + str(row[1]) + ' рублей\n\n'
        osum += row[1]
    stroka += 'Сумма: ' + str(round(osum,2)) + ' рублей'

    cur.execute("SELECT sz FROM credits WHERE login = '%s'"%(login))    
    for row in cur:
        sdebt += row[0]
    cur.close()
    conn.close()
    stroka += '\nСумма, учитывая долги: ' + str(round(osum+sdebt,2)) + ' рублей'
    if kol == 0:
        stroka = 'У вас нет счетов'
    return stroka


def watch_debts(user_id):
    login = sessionStorage[user_id]['login']
    udb = user_db(login)
    kol = 0
    osum = 0
    stroka = ""
    stroka += 'Ваши должники:\n'
    conn = sqlite3.connect(udb)
    cur = conn.cursor()
    cur.execute("SELECT cred, sz, time FROM credits WHERE login = '%s'"%(login))
    for row in cur:
        if row[1] > 0:
            stroka += row[0] + ' должен вам ' + str(row[1]) + ' рублей с ' + row[2] + '\n'
        else:
            stroka += row[0] + ' ждет от вас ' + str(-row[1]) + ' рублей с ' + row[2] + '\n'
        kol = kol + 1
        osum += row[1]
    cur.close()
    conn.close()
    stroka += 'Всего человек: ' + str(kol) + '\nОбщая сумма: ' + str(round(osum,2)) + ' рублей'
    if kol == 0:
        stroka = 'У вас нет должников'
    return stroka

def check_session(user_id):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT id, login FROM zalog_alice')
    for row in cur:
        if row[0] == user_id:
            if row[1] == sessionStorage[user_id]['login']:
                cur.close()
                conn.close()
                return True
    cur.close()
    conn.close()
    return False
    

if __name__ == '__main__':
    app.run(host='0.0.0.0',ssl_context='adhoc',port=7771)
    
