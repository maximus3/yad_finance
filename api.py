# -*- coding: utf-8 -*-
# Импортирует поддержку UTF-8.
from __future__ import unicode_literals

# Импортируем файл config, func, get_data
from config import *
from func import *
from get_data import *
from metrik import *

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

# Google DialogFlow
import apiai

# Настройка логгирования
logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG, filename = u'fin_alice.log')

# Хранилище данных о сессиях.
sessionStorage = {}

# Нужные временные данные
vr1 = dict()

beta_send = """
P.S. Навык находится в разработке, так что возможны ошибки, заранее прошу прощения.
Все ваши комментарии, пожелания, предложения и жалобы можно писать в телеграм-аккаунт @m3prod
Обязательно подпишитесь на новости в телеграмме @finance_m3news, чтобы не пропускать новые обновления!
"""
    
sessionStorage = load_ids()

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
    session_id = req['session']['session_id']
    screen = 'screen' in req['meta']['interfaces']

    try:
        com = req['request']['command'].lower()
    except Exception:
        com = '#button'

    if com == "ping":
        res['response']['text'] = 'pong'
        return

    if sessionStorage.get(user_id) == None:
        sessionStorage[user_id] = {
            'step': 'mainUS',
            'login': '',
            'fin': 'все'
        }

    step = sessionStorage[user_id]['step']
    login = sessionStorage[user_id]['login']

    if req['session']['new'] and com =='#button':
        com = '#new_session'

    if req['session']['new'] and step == 'mainUS': 
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.

        # Если пользоваьель уже логинился
        #if step == 'mainUS':
        #    res['response']['text'] = """
        #    Добро пожаловать!
        #    """ + beta_send
        #    res['response']['tts'] = """
        #    Добро пожаловать!
        #    """
        #    res['response']['text'] += '\nВерсия: ' + version
        #    res['response']['tts'] += '\nВерсия: ' + version
        #    res['response']['buttons'] = getBut(step)
        #    return

        sessionStorage[user_id] = {
            'step': 'mainUS',
            'login': '',
            'fin': 'все'
        }
        res['response']['text'] = """
        Привет! Данный навык поможет вам в более удобном формате контролировать свои расходы.
        Если вы уже зарегистрировались в телеграм-боте @debt_m3bot, то скажите вашу кодовую фразу или используйте "Помощь".
        !!NEW!! Также, если вы уже зарегистрировались, вы можете авторизироваться нажав кнопку ниже. !!NEW!!
        """ + beta_send
        res['response']['tts'] = """
        Привет! Данный навык поможет вам в более удобном формате контролировать свои расходы.
        Если вы уже зарегистрировались в телеграм-боте @debt_m3bot, то скажите вашу кодовую фразу или используйте "Помощь".
        Также, если вы уже зарегистрировались, вы можете авторизироваться нажав кнопку ниже.
        """
        res['response']['text'] += '\nВерсия: ' + version
        res['response']['tts'] += '\nВерсия: ' + version
        res['response']['buttons'] = getBut(step, user_id)
        send_metrik('alice', user_id, com, step, False)
        return

    ai_action = ''
    ai_parameters = {}
    ai_contexts = []

    if com[0] != '#':
        
        # DIALOGFLOW_START

        logging.info('Connecting to DF')
        ai_request = apiai.ApiAI(TOKEN_AI).text_request() # Токен API к Dialogflow
        logging.info('Connected')
        ai_request.lang = 'ru' # На каком языке будет послан запрос
        ai_request.session_id = session_id # ID Сессии диалога (нужно, чтобы потом учить бота)
        logging.info('Sending text to DF')
        ai_request.query = com # Посылаем запрос к ИИ с сообщением от юзера
        logging.info('Sent')
        logging.info('Getting result from DF')
        responseJson = json.loads(ai_request.getresponse().read().decode('utf-8'))
        logging.info('Got')
        ai_response = responseJson['result']['fulfillment']['speech'] # Разбираем JSON и вытаскиваем ответ

        if 'action' in responseJson['result']:
            ai_action = responseJson['result']['action']
        if 'parameters' in responseJson['result']:
            ai_parameters = responseJson['result']['parameters']
        if 'contexts' in responseJson['result']:
            ai_contexts = responseJson['result']['contexts']
            
        # Если есть ответ от бота - присылаем юзеру, если нет - бот его не понял
        if not ai_response:
            ai_respone = '#no_answer'

        # DIALOGFLOW_FINISH

    # Пользователь не зарегистрирован
    if step == 'mainUS':

        login = check_session(user_id)
        
        # Проверка авторизации
        if login:
            step = 'main'
            sessionStorage[user_id]['login'] = login
            sessionStorage[user_id]['step'] = step
            res['response']['text'] = 'Авторизация успешно пройдена! Ваш аккаунт: ' + login
            res['response']['buttons'] = getBut(step)
            sessionStorage[user_id]['fin'] = 'все'
            return
        
        # Пользователь попросил помощь
        if ai_action == 'bot.description' or ai_action == 'bot.help':
            res['response']['text'] = """
Попробуйте аторизироваться в телеграм-боте @debt_m3bot и нажать кнопку "Быстрая авторизация" ниже.
Если у вас не получилось, то делайте следующее:
1) Авторизироваться в телеграм-боте @debt_m3bot и ввести команду /alice.
2) Запишите кодовую фразу-вопрос и фразу-ответ, используя телеграм-бота.
3) Скажите фразу-вопрос мне. Если все хорошо, то я скажу вам вашу фразу-ответ.
4) Скажите мне любую фразу, с помощью которой вы сможете авторизировать данное устройство. Эту фразу я отправлю в телеграм-бота.
5) Зайдите в телеграм-бота и введите команду /alice
6) Выберите пункт "Авторизация диалога"
7) Если бот прислал вам ту фразу, что вы сказали последней, то вам осталось всего лишь нажать кнопку "ДА" в телеграм-боте и начать пользоваться навыком!
Удачи!            
            """
            res['response']['tts'] = """
Попробуйте аторизироваться в телеграм-боте @debt_m3bot и нажать кнопку "Быстрая авторизация" ниже.
Если у вас не получилось, то делайте следующее:
1) Авторизироваться в телеграм-боте @debt_m3bot и ввести команду /alice.
2) Запишите кодовую фразу-вопрос и фразу-ответ, используя телеграм-бота.
3) Скажите фразу-вопрос мне. Если все хорошо, то я скажу вам вашу фразу-ответ.
4) Скажите мне любую фразу, с помощью которой вы сможете авторизировать данное устройство. Эту фразу я отправлю в телеграм-бота.
5) Зайдите в телеграм-бота и введите команду /alice
6) Выберите пункт "Авторизация диалога"
7) Если бот прислал вам ту фразу, что вы сказали последней, то вам осталось всего лишь нажать кнопку "ДА" в телеграм-боте и начать пользоваться навыком!
Удачи!         
            """
            res['response']['buttons'] = getBut(step, user_id)
            send_metrik('alice', user_id, com, step, False)
            return

        elif com == '#button':
            res['response']['text'] = """
                Будет что-то непонятно - обращайтесь!            
            """ + beta_send
            res['response']['tts'] = """
                Будет что-то непонятно - обращайтесь!
            """
            res['response']['buttons'] = getBut(step, user_id)
            return

        # Проверка фразы
        else:
            check, answer, login = phrase_in(com)
            if (check):
                send_metrik('alice', user_id, com, step, False)
                res['response']['text'] = answer + '\nТеперь я жду от вас фразу, которая будет отправлена в телеграм-бота и с помощью которой вы сможете авторизировать данное устройство'
                sessionStorage[user_id]['step'] += '_login'
                sessionStorage[user_id]['login'] = login
                return
            res['response']['text'] = "К сожалению, у меня не получилось найти такую фразу. Проверьте ее правильность (падежи и формы слов)"
            res['response']['buttons'] = getBut(step, user_id)
            send_metrik('alice', user_id, com, step, True)
            return

    # Переход в ожидание подтверждения регистрации
    elif step == 'mainUS_login':
        send_metrik('alice', user_id, com, step, False)
        conn = sqlite3.connect(user_db(login))
        cur = conn.cursor()
        cur.execute("INSERT INTO alice (id,phrase,login) VALUES ('%s','%s','%s')"%(user_id,com,login))
        conn.commit()
        cur.close()
        conn.close()
        step = prev_step(step)
        step += '_waiting'
        sessionStorage[user_id]['step'] = step
        res['response']['text'] = """Отлично! Теперь зайдите в телеграм-бота и подтвердите авторизацию. Для проверки или отмены используйте команды "Проверка авторизации" и "Отменить авторизацию" соответственно"""
        res['response']['buttons'] = getBut(step)
        return

    # Ожидание авторизации
    elif step == 'mainUS_waiting':
        
        # Пользователь отменяет авторизацию
        if ('отмени' in com) or ('отмена' in com):
            send_metrik('alice', user_id, com, step, False)
            if check_session(user_id, login):
                step = 'main'
                sessionStorage[user_id]['step'] = step
                res['response']['text'] = 'Отмена невозможна, авторизация уже пройдена! Ваш аккаунт: ' + login
                res['response']['buttons'] = getBut(step)
                sessionStorage[user_id]['fin'] = 'все'
                return
            
            conn = sqlite3.connect(user_db(login))
            cur = conn.cursor()
            cur.execute("DELETE FROM alice WHERE id = '%s'"%(user_id))
            conn.commit()
            cur.close()
            conn.close()
            step = prev_step(sessionStorage[user_id]['step'])
            sessionStorage[user_id]['step'] = step
            res['response']['text'] = "Авторизация отменена"
            res['response']['buttons'] = getBut(step)
            return

        # Пользователь проверяет авторизацию
        elif 'провер' in com:
            send_metrik('alice', user_id, com, step, False)
            conn = sqlite3.connect(user_db(login))
            cur = conn.cursor()
            cur.execute("SELECT * FROM alice WHERE id = '%s'"%(user_id))
            for row in cur:
                res['response']['text'] = 'Пока новостей нет)'
                res['response']['buttons'] = getBut(step)
                cur.close()
                conn.close()
                return
            if check_session(user_id, login):
                step = 'main'
                sessionStorage[user_id]['step'] = step
                res['response']['text'] = 'Авторизация успешно пройдена! Ваш аккаунт: ' + login
                res['response']['buttons'] = getBut(step)
                sessionStorage[user_id]['fin'] = 'все'
                return
            step = prev_step(step)
            sessionStorage[user_id]['step'] = step
            res['response']['text'] = 'Добавление отклонено. Попробуйте еще раз или воспользуйтесь помощью.'
            res['response']['buttons'] = getBut(step)
            return

        # Другое сообщение
        else:
            send_metrik('alice', user_id, com, step, True)
            if check_session(user_id, login):
                step = 'main'
                sessionStorage[user_id]['step'] = step
                res['response']['text'] = 'Авторизация успешно пройдена! Ваш аккаунт: ' + login
                res['response']['buttons'] = getBut(step)
                sessionStorage[user_id]['fin'] = 'все'
                return
            res['response']['text'] = 'К сожалению, я пока не понимаю такие команды.'
            #logging.debug( u'%s: %s' % (sessionStorage[user_id]['step'], com) )
            res['response']['buttons'] = getBut(step)
            return

    # Главное меню
    elif step == 'main':

        # Проверка на то, есть ли доступ к аккаунту
        if not (check_session(user_id, login)):
            res['response']['text'] = "Бот выполнил деаутентификацию."
            step = 'mainUS'
            sessionStorage[user_id]['step'] = step
            res['response']['buttons'] = getBut(step)
            send_metrik('alice', user_id, com, step, False)
            return

        if sessionStorage[user_id].get('fin') == None:
            sessionStorage[user_id]['fin'] = 'все'

        spend = sessionStorage[user_id]['fin']

        # Помощь
        if com == 'помощь':
            send_metrik('alice', user_id, com, step, False)
            res['response']['text'] = """
            Список основных команд:
            - Баланс [счета *название*]
            - Долги
            - Сумма долгов
            - Смена счета/поменяй счет [на *название*]
            - Текущий счет
            - Добавить расход/доход + параметры
            - Добавить долг + параметры
            - *Фамилия* *Имя* вернул долг + параметры
            - Расходы за + параметры
            - Выход

            В квадратных скобках указаны необязательные параметры
            """ + beta_send

            dsc = """
            Смена счета/поменяй счет [на *название*]- смена основного счета записи расходов/доходов (можно сразу с указанием нового счета)
            Текущий счет - узнать выбранный счет
            Добавь расход/доход + параметры - добавление расхода или дохода одной командой
            Баланс счета *название* - узнать баланс определенного счета
            Сумма долгов - узнать сумму задолженностей
            Добавить долг + параметры - добавление долга одной командой
            Фамилия имя вернул долг + параметры - редактирование долга
            Расходы за + параметры - суммарные расходы за определенный день или месяц
            """
            
            res['response']['tts'] = """
            Список команд:
            - Баланс
            - Долги
            - Сумма долгов
            - Смена счета
            - Текущий счет
            - Добавить расход/доход + параметры
            - Добавить долг + параметры
            - *Фамилия* *Имя* вернул долг + параметры
            - Расходы за + параметры
            - Выход
            """
            res['response']['text'] += '\nВерсия: ' + version
            res['response']['tts'] += '\nВерсия: ' + version
            res['response']['buttons'] = getBut(step)
            return

        # Баланс конкретного счета
        elif 'баланс счета' in com:
            send_metrik('alice', user_id, com, step, False)
            com = com.split()
            while com[0] != 'баланс':
                com.pop(0)
            com.pop(0)
            com.pop(0)
            if com == []:
                if spend == 'все':
                    res['response']['text'] = 'Вы не выбрали счет'
                    res['response']['buttons'] = getBut(step)
                    return
                else:
                    com = spend
            else:
                com = ' '.join(com)
            res['response']['text'] = watch_bank(user_id, com)
            res['response']['buttons'] = getBut(step)
            return

        # Сумма долгов
        elif 'сумм' in com and 'дол' in com:
            send_metrik('alice', user_id, com, step, False)
            res['response']['text'] = watch_debts(user_id, 'sum')
            res['response']['buttons'] = getBut(step)
            return

        # Просмотр баланса всех счетов
        elif 'баланс' in com:
            send_metrik('alice', user_id, com, step, False)
            com = com.split()
            while com[0] != 'баланс':
                com.pop(0)
            com.pop(0)
            if com == []:
                res['response']['text'] = watch_bank(user_id)
                res['response']['buttons'] = getBut(step)
                return
            com = ' '.join(com)
            res['response']['text'] = watch_bank(user_id, com)
            res['response']['buttons'] = getBut(step)
            return

        # Просмотр долгов
        elif 'долги' in com or 'должник' in com:
            send_metrik('alice', user_id, com, step, False)
            res['response']['text'] = watch_debts(user_id)
            res['response']['buttons'] = getBut(step)
            return

        # Выход из аккаунта
        elif 'выход' in com or 'выйти' in com:
            send_metrik('alice', user_id, com, step, False)
            conn = sqlite3.connect(data_base)
            cur = conn.cursor()
            cur.execute("DELETE FROM zalog_alice WHERE id = '%s'"%(user_id))
            conn.commit()
            cur.close()
            conn.close()
            step = 'mainUS'
            sessionStorage[user_id]['step'] = step
            res['response']['text'] = "Выход выполнен"
            res['response']['buttons'] = getBut(step)
            return

        # Текущий счет
        elif 'текущий счет' in com:
            send_metrik('alice', user_id, com, step, False)
            res['response']['text'] = 'Текущий счет: ' + spend
            res['response']['buttons'] = getBut(step)
            return

        elif com == 'новый расход' or com == 'новый доход':################################MARK#########################################################################################
            send_metrik('alice', user_id, com, step, False)
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
            send_metrik('alice', user_id, com, step, False)
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
            res['response']['text'] = 'Правильно ли я поняла, что надо добавить ' + fin[0] + ' ' + fin[1] + ' ' + str(fin[2]) + ' ' + fin[3] + ' в категории ' + fin[4] + ' за ' + str(fin[6]) + ' ' + monthR[fin[7]] + ' ' + str(fin[8]) + ' года, счет: ' + fin[5] 
            res['response']['buttons'] = getBut(sessionStorage[user_id]['step'])
            vr1[user_id] = fin
            return

        elif com == 'новый долг':##########################
            send_metrik('alice', user_id, com, step, False)
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
            send_metrik('alice', user_id, com, step, False)
            res['response']['text'] = 'Всегда рада помочь!'
            res['response']['end_session'] = True
            return

        # Добавление долга
        elif 'добавить долг' in com or 'добавь долг' in com:
            send_metrik('alice', user_id, com, step, False)
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
        elif 'расходы за' in com or 'доходы за' in com:
            send_metrik('alice', user_id, com, step, False)
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
            send_metrik('alice', user_id, com, step, False)
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
            send_metrik('alice', user_id, com, step, False)
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
            send_metrik('alice', user_id, com, step, True)
            res['response']['text'] = 'Я еще не понимаю такие команды. Можете воспользоваться помощью.'
            #logging.debug( u'%s: %s' % (sessionStorage[user_id]['step'], com) )
            res['response']['buttons'] = getBut(step)
            return

    # Обработка команды смена счета
    elif sessionStorage[user_id]['step'] == 'main_change':
        send_metrik('alice', user_id, com, step, False)
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
        send_metrik('alice', user_id, com, step, False)
        login = sessionStorage[user_id]['login']
        udb = user_db(login)
        debt = vr1[user_id]
        vr1.pop(user_id)
        sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
        if com != 'да':
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
        send_metrik('alice', user_id, com, step, False)
        login = sessionStorage[user_id]['login']
        udb = user_db(login)
        debt = vr1[user_id]
        vr1.pop(user_id)
        sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
        if com != 'да':
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
        send_metrik('alice', user_id, com, step, False)
        login = sessionStorage[user_id]['login']
        udb = user_db(login)
        sessionStorage[user_id]['step'] = prev_step(sessionStorage[user_id]['step'])
        fin = vr1[user_id]
        vr1.pop(user_id)
        if com != 'да':
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
# Вход: сообщение
# Выход: Сообщение со счетами
def watch_bank(user_id, spn = 'все'):
    login = sessionStorage[user_id]['login']
    
    banks, kol, osum = get_banks(login)
    
    stroka = 'Ваши счета:\n'

    for elem in banks:
        if spn == 'все':
            stroka += str(kol) + ') ' + elem[0] + '\nБаланс счета: ' + str(elem[1]) + ' рублей\n\n'
        elif spn == elem[0] or (stroka == "" and spn in elem[0]):
            stroka = 'Баланс счета ' + elem[0] + ': ' + str(elem[1]) + ' рублей'

    if spn == 'все':
        stroka += 'Сумма: ' + str(round(osum,2)) + ' рублей'
        debts, kol1, sdebt = get_debts(login)
        stroka += '\nСумма, учитывая долги: ' + str(round(osum+sdebt,2)) + ' рублей'

    if kol == 0:
        if spn == 'все':
            stroka = 'У вас нет счетов'
        else:
            stroka = 'Такого счета нет'
    return stroka

# Просмотр должников
# Вход: сообщение
# Выход: Сообщение с долгами
def watch_debts(user_id, tp = 'all'):
    login = sessionStorage[user_id]['login']
    
    stroka = 'Ваши должники:\n\n'
    debts, kol, osum = get_debts(login)
    if tp == 'sum':
        stroka = "Сумма долгов: " + str(osum) + ' рублей'
        return stroka
    
    for elem in debts:
        if elem[1] > 0:
            im = elem[0].split()
            im = im[0][-3:]
            if im == 'ова' or im == 'ева' or im == 'ина' or im == 'кая':
                stroka += elem[0] + ' должна вам ' + str(elem[1]) + ' рублей с ' + elem[2] + '\n'
            else:
                stroka += elem[0] + ' должен вам ' + str(elem[1]) + ' рублей с ' + elem[2] + '\n'
        else:
            stroka += elem[0] + ' ждет от вас ' + str(-elem[1]) + ' рублей с ' + elem[2] + '\n'
    stroka += 'Всего человек: ' + str(kol) + '\nОбщая сумма: ' + str(round(osum,2)) + ' рублей'

    if kol == 0:
        stroka = 'У вас нет должников'
        
    return stroka

# Просмотр истории операций
def watch_his(user_id):
    login = sessionStorage[user_id]['login']
    fin = vr1[user_id]
    spn = fin[2]
    categ = fin[1]
    if fin[3] == 0:
        sday = 1
        fday = 31
    else:
        fday = fin[3]
        sday = fin[3]
    smon = fin[4]
    syear = fin[5]
    fmon = fin[4]
    fyear = fin[5]
    udb = user_db(login)
    vr1.pop(user_id)
    if fin[0] == 'расходы':
        stroka = 'Ваши расходы за '
    elif fin[0] == 'доходы':
        stroka = 'Ваши доходы за '
    if fin[3] == 0:
        stroka += monthRim[fin[4]] + ' ' + str(fin[5]) + '-го года'
    else:
        stroka += str(fin[3]) + ' ' + monthR[fin[4]] + ' ' + str(fin[5]) + '-го года'
    if categ != 'все':
        stroka += " в категори " + categ
    if spn != 'все':
        stroka += " со счета " + spn 
    stroka += "\n"
    year = fin[5]
    mon = fin[4]
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

if __name__ == '__main__':
    app.run(host='0.0.0.0',ssl_context='adhoc',port=7771)
    
