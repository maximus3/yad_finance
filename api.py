# -*- coding: utf-8 -*-
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем файл config
from config import *

# Импортируем модули для работы с JSON и логами.
import json
import logging

# Импортируем подмодули Flask для запуска веб-сервиса.
from flask import Flask, request
app = Flask(__name__)

# Импортируем модули для работы с базой данных.
import sqlite3

import time

logging.basicConfig(level=logging.DEBUG)

# Хранилище данных о сессиях.
sessionStorage = {}

# Нужные временные данные
vr1 = dict()

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

   
    com = req['request']['command'].lower()

    if req['session']['new']: 
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.

        # Если пользоваьель уже логинился
        if sessionStorage.get(user_id) is not None:
            res['response']['text'] = """
                Добро пожаловать!\nP.S. Навык находится в разработке, так что возможны ошибки, заранее прошу прощения.
                По всем вопросам и предложениям можно писать в телеграм-аккаунт @m3prod
            """
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        sessionStorage[user_id] = {
            'step': 'mainUS',
            'login': '',
            'fin': 'все'
        }

        res['response']['text'] = """
        Привет! Данный навык помогает в более удобном формате контролировать свои расходы.
        Данный навык связан с телеграм-ботом @debt_m3bot
        Авторизируйте ваше устройство при помощи кодовой фразы или используйте "Помощь"
        P.S. Навык находится в разработке, так что возможны ошибки, заранее прошу прощения.
        По всем вопросам и предложениям можно писать в телеграм-аккаунт @m3prod
        """
        res['response']['text'] += '\nВерсия: ' + version
        res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
        return

    
    # Обрабатываем ответ пользователя.
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
                sessionStorage[user_id]['fin'] = 'ВСЕ'
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
                sessionStorage[user_id]['fin'] = 'ВСЕ'
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
        # Проверка на то, есть ли доступ к аккаунту
        if not (check_session(user_id)):
            res['response']['text'] = "Бот выполнил деаутентификацию."
            sessionStorage[user_id]['step'] = 'mainUS'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        if sessionStorage[user_id].get('fin') == None:
            sessionStorage[user_id]['fin'] = 'все'
        
        if com == 'помощь':
            res['response']['text'] = """
            Вот список команд:
            Баланс - узнать баланс ваших счетов
            Долги - список ваших должников
            Выход - отвязать аккаунт
            Смена счета/поменяй счет [на *название*]- смена основного счета записи расходов/доходов (можно сразу с указанием нового счета)
            Текущий счет - узнать выбранный счет
            Новый расход/доход - добавление расхода или дохода
            Добавь расход/доход + параметры - добавление расхода или дохода одной командой
            Баланс счета *название* - узнать баланс определенного счета
            Сумма долгов - узнать сумму задолженностей
            Новый долг - добавление долга
            Добавить долг + параметры - добавление долга одной командой
            
            P.S. Данный навык находится в разработке, поэтому новые функции будут появляться постепенно
            По всем вопросам и предложениям можно писать в телеграм-аккаунт @m3prod
            """
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        # Баланс конкретного счета
        elif 'баланс счета' in com:
            com = com.split()
            while com[0] != 'баланс':
                com.pop(0)
            com.pop(0)
            com.pop(0)
            com = ' '.join(com)
            res['response']['text'] = watch_bank(user_id, com)
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        # Сумма долгов
        elif 'сумм' in com and 'дол' in com:
            res['response']['text'] = watch_debts(user_id, 'sum')
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        # Просмотр баланса всех счетов
        elif 'баланс' in com:
            res['response']['text'] = watch_bank(user_id)
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        # Просмотр долгов
        elif 'долги' in com or 'должник' in com:
            res['response']['text'] = watch_debts(user_id)
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        # Выход из аккаунта
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

        # Текущий счет
        elif 'текущий счет' in com:
            res['response']['text'] = 'Текущий счет: ' + sessionStorage[user_id]['fin']
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        elif com == 'новый расход' or com == 'новый доход':################################
            res['response']['text'] = """
                Пока добавить позицию можно только командой "Добавь" + параметры
                Пример запроса:
                Добавь расход продукты 200 рублей в категории еда за 20 мая 2018 года со счета кошелек
                Пример короткого запроса:
                Добавь расход 200 рублей в категории еда
                Комментарий не обязателен
                Если не указано число, то позиция будет добавлена сегодняшним числом
                Если не указан счет, то позиция будет добавлена на основной счет (поменять командой "смена счета", проверить командой текущий счет)
                Структура запроса:
                Добавь {расход/доход} [комментарий] *число* рублей в категории *название* [за] [сегодня/вчера/*число* *месяц*/*число* *месяц* *год*] [{со счета/на счет} *название*]
                "со счета" для расхода
                "на счет" для дохода
            """
            res['response']['tts'] = """
                Пока добавить позицию можно только командой "Добавь" + параметры
                Пример запроса:
                Добавь расход продукты 200 рублей в категории еда за 20 мая 2018 года со счета кошелек
                Пример короткого запроса:
                Добавь расход 200 рублей в категории еда
            """
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        # Обработка добавления расхода/дохода
        elif 'добавить расход' in com or 'добавить доход' in com or 'добавь расход' in com or 'добавь доход' in com:
            login = sessionStorage[user_id]['login']
            udb = user_db(login)
            fin = check_fin(com)
            if fin == None:
                res['response']['text'] = 'Неверный формат'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return
            if fin[5] == 'все':
                fin[5] = sessionStorage[user_id]['fin']

            # Проверка правильности даты
            tm = [0]*3
            tm[2] = fin[8] #год
            tm[1] = fin[7] #месяц
            tm[0] = fin[6] #день
            if tm[1] < 1 or tm[1] > 12 or tm[0] < 1 or tm[0] > 31:
                res['response']['text'] = 'Неправильная дата'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return
            
            # Проверка существования категории
            conn = sqlite3.connect(udb)
            cur = conn.cursor()
            if fin[0] == 'расход':
                cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(login))
            elif fin[0] == 'доход':
                cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(login))
            kod = 1
            for row in cur:
                if row[0] == fin[4] or (fin[4] in row[0] and kod == 1):
                    kod = 0
                    fin[4] = row[0]
            if kod == 1:
                res['response']['text'] = 'Неправильная категория'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                cur.close()
                conn.close()
                return
            
            # Проверка существования счета
            cur.execute("SELECT name FROM bank WHERE login = '%s'"%(login))
            kod = 1
            for row in cur:
                if row[0] == fin[5] or (fin[5] in row[0] and kod == 1):
                    kod = 0
                    fin[5] = row[0]
            cur.close()
            conn.close()
            if kod == 1:
                res['response']['text'] = 'Неправильный счет' 
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return

            sessionStorage[user_id]['step'] += '_addfin'
            res['response']['text'] = 'Правильно ли я поняла, что надо добавить ' + fin[0] + ' ' + fin[1] + ' ' + str(fin[2]) + ' ' + fin[3] + ' в категории ' + fin[4] + ' за ' + str(fin[6]) + ' ' + monthR_rev[fin[7]] + ' ' + str(fin[8]) + ' года, счет: ' + fin[5] 
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            vr1[user_id] = fin
            return

        elif com == 'новый долг':##########################
            res['response']['text'] = """
                Пока добавить долг можно только командой "Добавь долг" + параметры
                Пример запроса:
                Добавь долг Иванов Иван 200 рублей со счета кошелек
                Пример короткого запроса:
                Добавь долг Иванов Иван 200 рублей
                Если не указан счет, то позиция будет добавлена на основной счет (поменять командой "смена счета", проверить командой текущий счет)
                Структура запроса:
                Добавь долг *фамилия* *имя* *число* рублей [со счета *название*]
            """
            res['response']['tts'] = """
                Пока добавить долг можно только командой "Добавь долг" + параметры
                Пример запроса:
                Добавь долг Иванов Иван 200 рублей со счета кошелек
                Пример короткого запроса:
                Добавь долг Иванов Иван 200 рублей
            """
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        # Добавление долга
        elif 'добавить долг' in com or 'добавь долг' in com:
            login = sessionStorage[user_id]['login']
            udb = user_db(login)
            debt = check_debt(com)
            if debt == None:
                res['response']['text'] = 'Неверный формат'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return

            if debt[3] == 'все':
                debt[3] = sessionStorage[user_id]['fin']

            # Проверка существования счета
            conn = sqlite3.connect(udb)
            cur = conn.cursor()
            cur.execute("SELECT name FROM bank WHERE login = '%s'"%(login))
            kod = 1
            for row in cur:
                if row[0] == debt[3] or (debt[3] in row[0] and kod == 1):
                    kod = 0
                    debt[3] = row[0]
            cur.close()
            conn.close()
            if kod == 1:
                res['response']['text'] = 'Неправильный счет' 
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return

            sessionStorage[user_id]['step'] += '_adddebt'
            res['response']['text'] = 'Правильно ли я поняла, что надо добавить долг ' + debt[0] + ' ' + debt[1] + ' ' + str(debt[2]) + ' ' + debt[4] + ' со счета: ' + debt[3] 
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            vr1[user_id] = debt
            return
            

        # Удаление долга
        elif 'удалить долг' in com:###########################################################3
            return

        # Пользоваель сказал спасибо, завершение сессии
        elif com == 'спасибо':
            res['response']['text'] = 'Всегда рада помочь!'
            res['response']['end_session'] = True
            return

        # Расходы за какой-то период времени
        elif 'расходы за' in com or 'доходы за' in com:################################################
            return

        # Смена счета
        elif 'мен' in com and 'счет' in com:
            login = sessionStorage[user_id]['login']
            udb = user_db(login)
            if ' на ' in com:
                com = com.split(' на ')
                com.pop(0)
                com = ' на '.join(com)
                conn = sqlite3.connect(udb)
                cur = conn.cursor()
                cur.execute("SELECT name FROM bank WHERE login = '%s'"%(login))
                for row in cur:
                    if row[0] == com or (com in row[0]):################# названия похожи
                        sessionStorage[user_id]['fin'] = row[0]
                        res['response']['text'] = 'Выбран счет ' + sessionStorage[user_id]['fin']
                        res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                        cur.close()
                        conn.close()
                        return
                cur.close()
                conn.close()
                res['response']['text'] = 'Такого счета нет'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return
            sessionStorage[user_id]['step'] += '_change'
                
            res['response']['buttons'] = [
                {'title': "Все", 'hide': True}
            ]
            conn = sqlite3.connect(udb)
            cur = conn.cursor()
            vr1[user_id] = []
            cur.execute("SELECT name FROM bank WHERE login = '%s'"%(login))
            for row in cur:
                res['response']['buttons'].append({
                    "title": row[0],
                    "hide": True
                })
                vr1[user_id].append(row[0].lower())
            cur.close()
            conn.close()
            res['response']['text'] = 'Выберите другой счет'
            return

        else:
            res['response']['text'] = 'Я вас не понимаю. Можете воспользоваться помощью.'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

    # Обработка команды смена счета
    elif sessionStorage[user_id]['step'] == 'main_change':
        login = sessionStorage[user_id]['login']
        udb = user_db(login)
        sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
        if com == 'все':
            sessionStorage[user_id]['fin'] = 'все'
            res['response']['text'] = 'Выбраны все счета'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
        elif com not in vr1[user_id]:
            res['response']['text'] = 'Такого счета нет'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
        else:
            sessionStorage[user_id]['fin'] = com
            res['response']['text'] = 'Выбран счет ' + sessionStorage[user_id]['fin']
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
        vr1.pop(user_id)

    # Добавление долга
    elif sessionStorage[user_id]['step'] == 'main_adddebt':
        login = sessionStorage[user_id]['login']
        udb = user_db(login)
        sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
        if com == 'нет' or com != 'да':
            res['response']['text'] = 'Ладно, этот долг мы добавлять не будем'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
        debt = vr1[user_id]
        vr1.pop(user_id)
        fam, im, dolg = debt[0], debt[1], str(debt[2])
        fam, im = fam + ' ' + im, im + ' ' + fam
        if check_text(fam.lower(), 'rus'):
            res['response']['text'] = 'Используйте только русские буквы'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
        conn = sqlite3.connect(udb)
        cur = conn.cursor()
        cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(login))
        for row in cur:
            if (row[0].lower() == fam.lower()) or (row[0].lower() == im.lower()):
                res['response']['text'] = 'Данный участник уже есть в базе'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                cur.close()
                conn.close()
                return
        cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(login,debt[3]))
        for row in cur:
            if row[0] < round(float(dolg),2):
                res['response']['text'] = 'У вас нет столько денег'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                cur.close()
                conn.close()
                return
            sz = row[0]
        sz -= round(float(dolg),2)
        cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(sz,login,debt[3]))
        tme = stday()
        cur.execute("INSERT INTO credits (login,cred,time,sz) VALUES ('%s','%s','%s','%f' )"%(login,fam,tme,round(float(dolg),2)))
        conn.commit()
        cur.close()
        conn.close()
        res['response']['text'] = 'Долг успешно добавлен'
        res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
        return



        

    # Добавление расхода/дохода
    elif sessionStorage[user_id]['step'] == 'main_addfin':
        login = sessionStorage[user_id]['login']
        udb = user_db(login)
        sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
        if com == 'нет' or com != 'да':
            res['response']['text'] = 'Ладно, этот расход мы добавлять не будем'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
        fin = vr1[user_id]
        vr1.pop(user_id)
        tm = [0]*3
        tm[2] = fin[8] #год
        tm[1] = fin[7] #месяц
        tm[0] = fin[6] #день
        categ = fin[4] #категория
        spn = fin[5] #счет
        des = fin[1] #описание
        ras = fin[2]
        
        # Проверка баланса
        conn = sqlite3.connect(udb)
        cur = conn.cursor()
        cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(login,spn))
        for row in cur:
            bal = round(float(row[0]),2)
        if fin[0] == 'расход':
            bal -= ras
        elif fin[0] == 'доход':
            bal += ras
        if bal < 0:
            res['response']['text'] = 'У вас нет столько денег'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            cur.close()
            conn.close()
            return

        # Запись расхода
        cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(bal,login,spn))
        if fin[0] == 'расход':
            cur.execute("INSERT INTO spend (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%f')"%(login,tm[2],tm[1],tm[0],categ,spn,des,ras))
        elif fin[0] == 'доход':
            cur.execute("INSERT INTO inc (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%f')"%(login,tm[2],tm[1],tm[0],categ,spn,des,ras))
        conn.commit()
        cur.close()
        conn.close()
        res['response']['text'] = 'Расход успешно добавлен'
        res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
        return
        

def watch_bank(user_id, spn = 'все'):
    login = sessionStorage[user_id]['login']
    udb = user_db(login)
    kol = 0
    osum = 0
    sdebt = 0
    stroka = ""
    if spn == 'все':
        stroka = "Ваши счета:\n"
    conn = sqlite3.connect(udb)
    cur = conn.cursor()
    cur.execute("SELECT name, bal FROM bank WHERE login = '%s'"%(login))
    for row in cur:
        if spn == 'все':
            kol += 1
            stroka += str(kol) + ') ' + row[0] + '\nБаланс счета: ' + str(row[1]) + ' рублей\n\n'
            osum += row[1]
        elif spn == row[0] or (stroka == "" and spn in row[0]):
            kol += 1
            stroka = 'Баланс счета ' + row[0] + ': ' + str(row[1]) + ' рублей'
    if spn == 'все':
        stroka += 'Сумма: ' + str(round(osum,2)) + ' рублей'
        cur.execute("SELECT sz FROM credits WHERE login = '%s'"%(login))    
        for row in cur:
            sdebt += row[0]
        stroka += '\nСумма, учитывая долги: ' + str(round(osum+sdebt,2)) + ' рублей'
    cur.close()
    conn.close()
    if kol == 0:
        if spn == 'все':
            stroka = 'У вас нет счетов'
        else:
            stroka = 'Такого счета нет'
    return stroka


def watch_debts(user_id, tp = 'all'):
    login = sessionStorage[user_id]['login']
    udb = user_db(login)
    if tp == 'sum':
        osum = 0
        conn = sqlite3.connect(udb)
        cur = conn.cursor()
        cur.execute("SELECT sz FROM credits WHERE login = '%s'"%(login))
        for row in cur:
            osum += row[0]
        cur.close()
        conn.close()
        stroka = "Сумма долгов: " + str(osum)
        if osum % 10 == 0 or osum % 10 > 4 or (osum % 100 > 10 and osum % 100 < 15):
            stroka += ' рублей'
        elif osum % 10 == 1:
            stroka += ' рубль'
        elif osum % 10 > 1 and osum % 10 < 5:
            stroka += ' рубля'
        return stroka
    kol = 0
    osum = 0
    stroka = ""
    stroka += 'Ваши должники:\n'
    conn = sqlite3.connect(udb)
    cur = conn.cursor()
    cur.execute("SELECT cred, sz, time FROM credits WHERE login = '%s'"%(login))
    for row in cur:
        if row[1] > 0:
            im = row[0].split()
            im = im[0][-3:]
            if im == 'ова' or im == 'ева' or im == 'ина' or im == 'кая':
                stroka += row[0] + ' должна вам ' + str(row[1]) + ' рублей с ' + row[2] + '\n'
            else:
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
    
