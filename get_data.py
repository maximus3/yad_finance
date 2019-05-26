import sqlite3
from config import monthR, monthRim, directory
from func import user_db, tday, lday
from diag import make_diag

import logging

logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO, filename = directory + 'fin_alice.log')

# Должники
# Вход: логин пользователя
# Выход: список должников пользователя [имя, сумма, дата], количество, общая сумма
def get_debts(login):
    debts = []
    
    kol = 0
    osum = 0

    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT cred, sz, time FROM credits")
    for row in cur:
        debts.append([row[0], row[1], row[2]])
        kol += 1
        osum += row[1]
    cur.close()
    conn.close()
    return debts, kol, osum

# Счета
# Вход: логин пользователя
# Выход: список счетов пользователя [название, сумма], количество, общая сумма
def get_banks(login):
    banks = []

    kol = 0
    osum = 0

    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT name, bal FROM bank")
    for row in cur:
        kol += 1
        banks.append([row[0].lower(), row[1]])
        osum += row[1]
    cur.close()
    conn.close()
    return banks, kol, osum

# Категории
# Вход: логин пользователя
# Выход: список счетов пользователя [название], количество
def get_categs(login, sect):
    categs = []

    kol = 0

    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    if sect == 'spend':
        cur.execute("SELECT cat FROM cats")
    elif sect == 'fin':
        cur.execute("SELECT cat FROM fcats")
    for row in cur:
        kol += 1
        categs.append(row[0].lower())
    cur.close()
    conn.close()
    return categs, kol

# Получение истории расходов/доходов
# Вход: ДД, ММ, ГГГГ, ДД, ММ, ГГГГ, флаг отправки данных по месяцам, флаг показа всех позиций, логин, флаг расход/доход, счет, категория, флаг показа диаграммы
# Выход: Строка отчета, флаг составлена ли диаграмма
def get_fin_his(sday, smon, syear, fday, fmon, fyear, kod_mon, show, login, sect, spend, categ, show_diag):
    if sect == 'spend':
        stroka = "Ваши расходы "
        title = "Расходы "
    elif sect == 'fin':
        stroka = "Ваши доходы "
        title = "Доходы "
    if sday == fday and smon == fmon and syear == fyear:
        if [sday, smon, syear] == tday():
            stroka += "за сегодня (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года) "
            title += "за сегодня (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)"
        elif [sday, smon, syear] == lday():
            stroka += "за вчера (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года) "
            title += "за вчера (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)"
        else:
            stroka += "за " + str(sday) + " " + monthR[smon] + " " + str(syear) + " года "
            title += "за " + str(sday) + " " + monthR[smon] + " " + str(syear) + " года"
    elif smon == fmon and sday == 1 and fday == 31:
        stroka += "за " + monthRim[smon] + " " + str(syear) + " года "
        title += "за " + monthRim[smon] + " " + str(syear) + " года"
    else:
        stroka += "с " + str(sday) + " " + monthR[smon] + " " + str(syear) + ' года, по ' + str(fday) + " " + monthR[fmon] + " " + str(fyear) + " года "
        title += "с " + str(sday) + " " + monthR[smon] + " " + str(syear) + ' года, по ' + str(fday) + " " + monthR[fmon] + " " + str(fyear) + " года"
    if spend != '#all':
        stroka += "со счета " + spend + " "
        title += "\nСчет: " + spend
    if categ != '#all':
        stroka += "в категории " + categ
    stroka += "\n"
    s_old = stroka
    year = syear
    mon = smon
    day = sday
    osum = 0
    kod = 0
    kodK = 0
    kol1 = 0
    cat_s = dict()
    mon_s = dict()
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    while kod == 0:
        if spend == '#all' and categ == '#all':
            if sect == 'spend':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d'"%(year,mon,day))
            elif sect == 'fin':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d'"%(year,mon,day))
        elif spend != '#all' and categ == '#all':
            if sect == 'spend':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(year,mon,day,spend))
            elif sect == 'fin':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(year,mon,day,spend))
        elif spend == '#all' and categ != '#all':
            if sect == 'spend':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(year,mon,day,categ))
            elif sect == 'fin':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(year,mon,day,categ))
        else:
            if sect == 'spend':
                cur.execute("SELECT name, sum FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(year,mon,day,spend,categ))
            elif sect == 'fin':
                cur.execute("SELECT name, sum FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(year,mon,day,spend,categ))
        if sday == fday and smon == fmon and syear == fyear:
            stroka1 = ''
        elif syear == fyear:
            stroka1 = str(day) + " " + monthR[mon] + ':\n'
        else:
            stroka1 = str(day) + " " + monthR[mon] + " " + str(year) + ' года:\n'
        kol = 0
        for row in cur:
            osum += round(row[1],2)
            kol += 1
            kol1 += 1
            if categ == '#all':
                stroka1 += row[2]
                if kod_mon == 1:
                    if mon_s.get(str(year) + ' ' + str(mon)) == None:
                        mon_s[str(year) + ' ' + str(mon)] = dict()
                if cat_s.get(row[2]) != None:
                    cat_s[row[2]] += round(row[1],2)
                else:
                    cat_s[row[2]] = round(row[1],2)
                if kod_mon == 1:
                    try:
                        mon_s[str(year) + ' ' + str(mon)][row[2]] += round(row[1],2)
                    except KeyError:
                        mon_s[str(year) + ' ' + str(mon)][row[2]] = round(row[1],2)
            else:
                try:
                    if kod_mon == 1:
                        mon_s[str(year) + ' ' + str(mon)] += round(row[1],2)
                except KeyError:
                    if kod_mon == 1:
                        mon_s[str(year) + ' ' + str(mon)] = round(row[1],2)
            if spend == '#all':
                if categ == '#all':
                    stroka1 += ', '
                stroka1 += row[3]
            stroka1 += "\n"
            txt = row[0]
            txt = txt.split('%')
            if len(txt[0]) == 0:
                stroka1 +=  str(round(row[1],2)) + " рублей\n\n"
            else:
                stroka1 +=  txt[0] + ' ' + str(round(row[1],2)) + " рублей\n\n"
  
        if kol > 0 and kodK == 0 and kod_mon != 1 and show == 1:
            stroka += stroka1 + "\n"
        if year == fyear and mon == fmon and day == fday:
            kod = 1
        day += 1
        if day > 31:
            day = 1
            mon += 1
            if mon > 12:
                mon = 1
                year += 1
        if len(stroka) >= 1000:
            stroka = s_old
            kodK = 1

    cur.close()
    conn.close()
    if kol1 == 0:
        if sect == 'spend':
            stroka = "У вас нет расходов "
        elif sect == 'fin':
            stroka = "У вас нет доходов "
        if sday == fday and smon == fmon and syear == fyear:
            if [sday, smon, syear] == tday():
                stroka += "за сегодня (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)\n"
            elif [sday, smon, syear] == lday():
                stroka += "за вчера (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)\n"
            else:
                stroka += "за " + str(sday) + " " + monthR[smon] + " " + str(syear) + " года\n"
        elif smon == fmon and sday == 1 and fday == 31:
            stroka += "за " + monthRim[smon] + " " + str(syear) + " года\n"
        else:
            stroka += "с " + str(sday) + " " + monthR[smon] + " " + str(syear) + ' года, по ' + str(fday) + " " + monthR[fmon] + " " + str(fyear) + " года\n"
        if spend != '#all' or categ != '#all':
            stroka +=  " по заданным категориям и счету"
        return stroka, 2
    
    if kod_mon == 1:
        if categ == '#all':
            for i in sorted(mon_s):
                stroka += 'Месяц: ' + i + '\n'
                osum1 = 0
                for j in sorted(mon_s[i]):
                    stroka += str(j) + ': ' + str(round(mon_s[i][j],2)) + '\n'
                    osum1 += mon_s[i][j]
                stroka += 'Итого за месяц: ' + str(round(osum1,2)) + '\n'
                stroka += '\n'
        else:
            for i in sorted(mon_s):
                stroka += 'Месяц: ' + i + '\n'
                stroka += 'Сумма: ' + str(round(mon_s[i],2)) + '\n'
                stroka += '\n'
    diag = 0
    if categ == '#all':
        diag = 1
        data_names = []
        data_values = []
        cat_s = list(cat_s.items())
        for i in range(len(cat_s)):
            cat_s[i] = list(cat_s[i])
            cat_s[i][0], cat_s[i][1] = cat_s[i][1], cat_s[i][0]
        cat_s.sort()
        cat_s.reverse()
        stroka += 'Всего по категориям:\n'
        for elem in cat_s:
            data_names.append(elem[1])
            data_values.append(round(elem[0],2))
            stroka += elem[1] + ': ' + str(round(elem[0],2)) + ' рублей\n'
        try:
            if show_diag:
                make_diag(login, title, data_names, data_values)
        except Exception as e:
            diag = -1       
    stroka += 'Итого: ' + str(round(osum,2))
    while len(stroka) >= 1000:
            #bot.send_message(mid, stroka[:4000], reply_markup = MUP[users[mid]])
            stroka = stroka[500:]
    return stroka, diag
