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

# Модуль для работы с датой (временем)
import time

# Настройка логгирования
logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG, filename = u'mylog.log')

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
    #logging.info('Request: %r', request.json)

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog(request.json, response)

    #logging.info('Response: %r', response)

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
            res['response']['tts'] = """
            Добро пожаловать!
            """
            res['response']['text'] += '\nВерсия: ' + version
            res['response']['tts'] += '\nВерсия: ' + version
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
        res['response']['tts'] = """
        Привет! Данный навык помогает в более удобном формате контролировать свои расходы.
        Данный навык связан с телеграм-ботом @debt_m3bot
        Авторизируйте ваше устройство при помощи кодовой фразы или используйте "Помощь"
        """
        res['response']['text'] += '\nВерсия: ' + version
        res['response']['tts'] += '\nВерсия: ' + version
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
                P.S. Навык находится в разработке, так что возможны ошибки, заранее прошу прощения.
                По всем вопросам и предложениям можно писать в телеграм-аккаунт @m3prod
            """
            res['response']['tts'] = """
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
            # Проверка наличия фразы в базе данных
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
                sessionStorage[user_id]['fin'] = 'все'
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
                sessionStorage[user_id]['fin'] = 'все'
                return
            sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
            res['response']['text'] = 'Вас не захотели добавлять'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        else:
            if check_session(user_id):
                sessionStorage[user_id]['step'] = 'main'
                res['response']['text'] = 'Авторизация успешно пройдена! Ваш аккаунт: ' + sessionStorage[user_id]['login']
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                sessionStorage[user_id]['fin'] = 'все'
                return
            res['response']['text'] = 'Я вас не понимаю'
            #logging.debug( u'%s: %s' % (sessionStorage[user_id]['step'], com) )
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
            Смена счета/поменяй счет [на *название*]- смена основного счета записи расходов/доходов (можно сразу с указанием нового счета)
            Текущий счет - узнать выбранный счет
            Добавь расход/доход + параметры - добавление расхода или дохода одной командой
            Баланс счета *название* - узнать баланс определенного счета
            Сумма долгов - узнать сумму задолженностей
            Добавить долг + параметры - добавление долга одной командой
            Фамилия имя вернул долг + параметры - редактирование долга
            Расходы за + параметры - суммарные расходы за определенный день или месяц
            
            P.S. Данный навык находится в разработке, поэтому новые функции будут появляться постепенно
            По всем вопросам и предложениям можно писать в телеграм-аккаунт @m3prod
            """
            res['response']['tts'] = """
            Вот список команд:
            Смена счета/поменяй счет [на *название*]- смена основного счета записи расходов/доходов (можно сразу с указанием нового счета)
            Текущий счет - узнать выбранный счет
            Добавь расход/доход + параметры - добавление расхода или дохода одной командой
            Баланс счета *название* - узнать баланс определенного счета
            Сумма долгов - узнать сумму задолженностей
            Добавить долг + параметры - добавление долга одной командой
            Фамилия имя вернул долг + параметры - редактирование долга
            Расходы за + параметры - суммарные расходы за определенный день или месяц
            """
            res['response']['text'] += '\nВерсия: ' + version
            res['response']['tts'] += '\nВерсия: ' + version
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        # Баланс конкретного счета
        elif 'баланс счета' in com:
            com = com.split()
            while com[0] != 'баланс':
                com.pop(0)
            com.pop(0)
            com.pop(0)
            if com == []:
                if sessionStorage[user_id]['fin'] == 'все':
                    res['response']['text'] = 'Вы не выбрали счет'
                    res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                    return
                else:
                    com = sessionStorage[user_id]['fin']
            else:
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
            com = com.split()
            while com[0] != 'баланс':
                com.pop(0)
            com.pop(0)
            if com == []:
                res['response']['text'] = watch_bank(user_id)
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return
            com = ' '.join(com)
            res['response']['text'] = watch_bank(user_id, com)
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
                Добавь расход продукты 200 рублей 50 копеек в категории еда за 20 мая 2018 года со счета кошелек
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
                res['response']['text'] = 'Неверный формат\n'
                res['response']['text'] += """
                Пример запроса:
                Добавь расход продукты 200 рублей 50 копеек в категории еда за 20 мая 2018 года со счета кошелек
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
                res['response']['tts'] = 'Неверный формат'
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
                Добавь долг Иванов Иван 200 рублей 50 копеек со счета кошелек
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

        # Пользоваель сказал спасибо, завершение сессии
        elif com == 'спасибо':
            res['response']['text'] = 'Всегда рада помочь!'
            res['response']['end_session'] = True
            return

        # Добавление долга
        elif 'добавить долг' in com or 'добавь долг' in com:
            login = sessionStorage[user_id]['login']
            udb = user_db(login)
            debt = check_debt(com)
            if debt == None:
                res['response']['text'] = 'Неверный формат'
                res['response']['text'] += """
                Пример запроса:
                Добавь долг Иванов Иван 200 рублей 50 копеек со счета кошелек
                Пример короткого запроса:
                Добавь долг Иванов Иван 200 рублей
                Если не указан счет, то позиция будет добавлена на основной счет (поменять командой "смена счета", проверить командой текущий счет)
                Структура запроса:
                Добавь долг *фамилия* *имя* *число* рублей [со счета *название*]
                """
                res['response']['tts'] = 'Неверный формат'
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

        # Расходы за какой-то период времени
        elif 'расходы за' in com or 'доходы за' in com:################################################
            login = sessionStorage[user_id]['login']
            udb = user_db(login)
            fin = check_hisfin(com)
            if fin == None:
                res['response']['text'] = 'Неверный формат\n'
                res['response']['text'] += """
                Пример запроса:
                Покажи мне расходы за 20 мая 2018 года в категории еда со счета кошелек
                Покажи мне расходы за 20 мая в категории еда со всех счетов
                Пример короткого запроса:
                Расходы за сегодня
                Если не указана категория, то будут показаны последние 10 расходов/доходов во всех категориях
                Если не указан счет, то будут показаны расходы/доходы с основного счета (поменять командой "смена счета", проверить командой текущий счет)
                Структура запроса:
                [Покажи мне] {расходы/доходы} за {сегодня/вчера/этот месяц/прошлый месяц/*месяц*/*месяц* *год*/*число* *месяц*/*число* *месяц* *год*} [в категории *название*] [со счета *название*]
                """
                res['response']['tts'] = 'Неверный формат'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return

            if fin[2] == 'all':
                fin[2] = sessionStorage[user_id]['fin']

            # Проверка правильности даты
            tm = [0]*3
            tm[2] = fin[5] #год
            tm[1] = fin[4] #месяц
            tm[0] = fin[3] #день
            if tm[1] < 1 or tm[1] > 12 or tm[0] < 0 or tm[0] > 31:
                res['response']['text'] = 'Неправильная дата'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return
            
            # Проверка существования категории
            if fin[1] != 'все':
                conn = sqlite3.connect(udb)
                cur = conn.cursor()
                if fin[0] == 'расходы':
                    cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(login))
                elif fin[0] == 'доходы':
                    cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(login))
                kod = 1
                for row in cur:
                    if row[0] == fin[1] or (fin[1] in row[0] and kod == 1):
                        kod = 0
                        fin[1] = row[0]
                cur.close()
                conn.close()
                if kod == 1:
                    res['response']['text'] = 'Неправильная категория'
                    res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])    
                    return

            # Проверка существования счета
            if fin[2] != 'все':
                conn = sqlite3.connect(udb)
                cur = conn.cursor()
                cur.execute("SELECT name FROM bank WHERE login = '%s'"%(login))
                kod = 1
                for row in cur:
                    if row[0] == fin[2] or ((fin[2] in row[0]) and kod == 1):
                        kod = 0
                        fin[2] = row[0]
                cur.close()
                conn.close()
                if kod == 1:
                    res['response']['text'] = 'Неправильный счет' 
                    res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                    return


            vr1[user_id] = fin
            res['response']['text'] = watch_his(user_id)
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return

        # Смена счета
        elif ('помен' in com or 'смен' in com) and 'счет' in com:
            login = sessionStorage[user_id]['login']
            udb = user_db(login)
            if ' на ' in com:
                com = com.split(' на ')
                com.pop(0)
                com = ' на '.join(com)
                if com == 'все':
                    sessionStorage[user_id]['fin'] = 'все'
                    res['response']['text'] = 'Выбраны все счета'
                    res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                    return
                conn = sqlite3.connect(udb)
                cur = conn.cursor()
                cur.execute("SELECT name FROM bank WHERE login = '%s'"%(login))
                kod = 1
                for row in cur:
                    if row[0] == com or (com in row[0] and kod == 1):
                        kod = 0
                        sessionStorage[user_id]['fin'] = row[0]
                cur.close()
                conn.close()
                if kod == 1:
                    res['response']['text'] = 'Такого счета нет'
                    res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                    return
                
                res['response']['text'] = 'Выбран счет ' + sessionStorage[user_id]['fin']
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

        # Редактирование долга
        elif 'вернул' in com or 'отдал' in com:
            login = sessionStorage[user_id]['login']
            udb = user_db(login)
            debt = check_eddebt(com)
            if debt == None:
                res['response']['tts'] = 'Неверный формат'
                res['response']['text'] = """
                Неверный формат
                Пример запроса:
                Иван Иванов вернул мне 150 рублей 90 копеек на счет кошелек
                Пример короткого запроса:
                Иван Иванов вернул мне 150 рублей
                Другой пример запроса:
                Иван Иванов вернул мне долг
                Если не указан счет, то позиция будет добавлена на основной счет (поменять командой "смена счета", проверить командой текущий счет)
                Запрос "венул долг" означает полное возвращение долга
                Структура запроса:
                *фамилия* *имя* вернул мне *число* рублей [*число* копеек] [на счет *название*]
                """
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return

            if debt[4] == 'все':
                debt[4] = sessionStorage[user_id]['fin']

            # Проверка существования счета
            conn = sqlite3.connect(udb)
            cur = conn.cursor()
            cur.execute("SELECT name FROM bank WHERE login = '%s'"%(login))
            kod = 1
            for row in cur:
                if row[0] == debt[4] or (debt[4] in row[0] and kod == 1):
                    kod = 0
                    debt[4] = row[0]
            if kod == 1:
                res['response']['text'] = 'Неправильный счет' 
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                cur.close()
                conn.close()
                return

            fam, im = debt[0], debt[1]
            fam, im = fam + ' ' + im, im + ' ' + fam
            if check_text(fam.lower(), 'rus'):
                res['response']['text'] = 'Используйте только русские буквы'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                cur.close()
                conn.close()
                return
            kod = 1
            cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(login))
            for row in cur:
                if (row[0].lower() == fam.lower()) or (row[0].lower() == im.lower()):
                    kod = 0
                    sz = row[1]
                    debt[0], debt[1] = row[0].split()
            cur.close()
            conn.close()
            if kod == 1:
                res['response']['text'] = 'Этого человека нет в списке' 
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                return
            if str(debt[2]) == 'all':
                debt[2] = sz

            debt.append(sz)

            sessionStorage[user_id]['step'] += '_editdebt'
            res['response']['text'] = 'Правильно ли я поняла, что ' + debt[0] + ' ' + debt[1] + ' вернул вам ' + str(debt[2]) + ' ' + debt[3] + ' на счет: ' + debt[4]
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            vr1[user_id] = debt
            return

        else:
            res['response']['text'] = 'Я вас не понимаю. Можете воспользоваться помощью.'
            #logging.debug( u'%s: %s' % (sessionStorage[user_id]['step'], com) )
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
            vr1.pop(user_id)
            return
        elif com not in vr1[user_id]:
            res['response']['text'] = 'Такого счета нет'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            vr1.pop(user_id)
            return
        else:
            sessionStorage[user_id]['fin'] = com
            res['response']['text'] = 'Выбран счет ' + sessionStorage[user_id]['fin']
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            vr1.pop(user_id)
            return
        
    # Редактирование долга
    elif sessionStorage[user_id]['step'] == 'main_editdebt':
        login = sessionStorage[user_id]['login']
        udb = user_db(login)
        debt = vr1[user_id]
        vr1.pop(user_id)
        sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
        if com == 'нет' or com != 'да':
            res['response']['text'] = 'Ладно, этот долг мы оставим как есть'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
        fam, dolg = debt[0] + ' ' + debt[1], str(debt[2])
        spn = debt[4]
        conn = sqlite3.connect(udb)
        cur = conn.cursor()
        cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(login,spn))
        for row in cur:
            if row[0] + round(float(dolg),2) < 0:
                res['response']['text'] = 'У вас нет столько денег'
                res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
                cur.close()
                conn.close()
                return
            sz = row[0]
        sz += round(float(dolg),2)
        cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(sz,login,spn))
        zn = debt[5] - debt[2]
        if zn == 0:
            cur.execute("DELETE FROM credits WHERE login = '%s' AND cred = '%s'"%(login,fam))
        else:
            cur.execute("UPDATE credits SET sz = '%f' WHERE login = '%s' AND cred = '%s'"%(zn,login,fam))
        conn.commit()
        cur.close()
        conn.close()
        res['response']['text'] = 'Долг успешно отредактирован, теперь ' + fam + ' должен вам ' + str(zn) + 'рублей'
        res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
        return

    # Добавление долга
    elif sessionStorage[user_id]['step'] == 'main_adddebt':
        login = sessionStorage[user_id]['login']
        udb = user_db(login)
        debt = vr1[user_id]
        vr1.pop(user_id)
        sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
        if com == 'нет' or com != 'да':
            res['response']['text'] = 'Ладно, этот долг мы добавлять не будем'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
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
        fin = vr1[user_id]
        vr1.pop(user_id)
        if com == 'нет' or com != 'да':
            if fin[0] == 'расход':
                res['response']['text'] = 'Ладно, этот расход мы добавлять не будем'
            elif fin[0] == 'доход':
                res['response']['text'] = 'Ладно, этот доход мы добавлять не будем'
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            return
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
            res['response']['text'] = 'Расход успешно добавлен, баланс счета ' + spn + ': ' + str(bal)
        elif fin[0] == 'доход':
            cur.execute("INSERT INTO inc (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%f')"%(login,tm[2],tm[1],tm[0],categ,spn,des,ras))
            res['response']['text'] = 'Доход успешно добавлен, баланс счета ' + spn + ': ' + str(bal)
        conn.commit()
        cur.close()
        conn.close()
        res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
        return
        
# Просмотр счетов
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

# Просмотр долгов
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

def watch_his(user_id):
    login = sessionStorage[user_id]['login']
    udb = user_db(login)
    fin = vr1[user_id]
    vr1.pop(user_id)
    #return 'Данная функция находится в разработке'#str(fin)##########################################
    if fin[0] == 'расходы':
        stroka = 'Ваши расходы за '
    elif fin[0] == 'доходы':
        stroka = 'Ваши доходы за '
    if fin[3] == 0:
        stroka += monthRim_rev[fin[4]] + ' ' + str(fin[5]) + '-го года'
    else:
        stroka += str(fin[3]) + ' ' + monthR_rev[fin[4]] + ' ' + str(fin[5]) + '-го года'
    spn = fin[2]
    categ = fin[1]
    if categ != 'все':
        stroka += " в категори " + categ
    if spn != 'все':
        stroka += " со счета " + spn 
    stroka += "\n"
    year = fin[5]
    mon = fin[4]
    if fin[3] == 0:
        sday = 1
        fday = 31
    else:
        fday = fin[3]
        sday = fin[3]
    day = sday
    osum = 0
    kod = 0
    kol = 0
    elem = []
    cat_s = dict()
    conn = sqlite3.connect(udb)
    cur = conn.cursor()
    while kod == 0:
        if spn == 'все' and categ == 'все':
            if fin[0] == 'расходы':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d'"%(login,year,mon,day))
            elif fin[0] == 'доходы':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d'"%(login,year,mon,day))
        elif spn != 'все' and categ == 'все':
            if fin[0] == 'расходы':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(login,year,mon,day,spn))
            elif fin[0] == 'доходы':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(login,year,mon,day,spn))
        elif spn == 'все' and categ != 'все':
            if fin[0] == 'расходы':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(login,year,mon,day,categ))
            elif fin[0] == 'доходы':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(login,year,mon,day,categ))
        elif spn != 'все' and categ != 'все':
            if fin[0] == 'расходы':
                cur.execute("SELECT name, sum FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(login,year,mon,day,spn,categ))
            elif fin[0] == 'доходы':
                cur.execute("SELECT name, sum FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(login,year,mon,day,spn,categ))
        for row in cur:
            if categ == 'все':
                try:
                    cat_s[row[2]] += row[1]
                except KeyError:
                    cat_s[row[2]] = row[1]
            txt = row[0]
            txt = txt.split('%')
            if spn != 'все' and categ != 'все':
                elem.append({'day':day,'name':txt[0],'sum':row[1]})
            else:
                elem.append({'day':day,'name':row[0],'sum':row[1],'cat':row[2],'bank':row[3]})
            if len(elem) > 10:
                elem.pop(0)
            osum += round(row[1],2)
            kol += 1
        if day == fday:
            kod = 1
        day += 1
    cur.close()
    conn.close()
    for i in elem:
        pass
    if categ == 'все':
        stroka += 'По категориям:\n'
        for i in cat_s:
            stroka += i + ': ' + str(round(cat_s[i],2)) + ' рублей\n'
    stroka += 'Итого: ' + str(round(osum,2))
    if kol == 0:
        stroka = "За выбранный период по данным категориям и счету ничего нет"
    return stroka

# Проверка авторизации
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
    
