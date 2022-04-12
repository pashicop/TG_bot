import subprocess
import platform
import socket
import time
from datetime import datetime
import telebot
import re
import json
import mysql.connector

TOKEN = "5145450144:AAFSQcu9yLCcYKtxLExPaDZUnNLnf1RY_YI"
HELP = """
/help - напечатать справку
/add ip1 ip2 ... - добавить ip в pinger
/show - показать все ip
/status - показать ip со статусом
/alarm - показать недоступные ip
/normal - показать доступные ip
/remove ip1 ip2 ... - удалить ip в pinger
/set timeout - указать таймаут проверки (15-600сек)
"""
def connect_db():
    connection = None
    with open("input/credentials.json", encoding="UTF-8") as f:
        cred = json.load(f)
    try:
        connection = mysql.connector.connect(
            # host="mysql",
            host="localhost",
            user=cred["user"],
            password=cred["password"],
            database=cred["database"],
            port=cred["port"]
        )
        # print(connection)
        print(f'БД {cred["database"]} подключена!')
    except mysql.connector.Error as err:
        print(err)
    # time.sleep(120)
    if connection:
        return connection
    else:
        print("Нет соединения с БД")


def close_db(con_db):
    # time.sleep(20)
    con_db.close()
    print("БД отключена")


def ping_ok(s_host):
    try:
        subprocess.check_output(
            "ping -{} 1 {}".format('n' if platform.system().lower() == "windows" else 'c', s_host), shell=True)
    except Exception as err:
        print(err)
        return False
    return True


def check_ip(l_ip, con_db):
    ip_status = {}
    dict_out = {}
    for ip in l_ip:
        if ping_ok(ip):
            ip_status[ip] = "OK"
            print(f'{ip} - {ip_status[ip]}')
        else:
            ip_status[ip] = "ALARM!"
            print(f'{ip} - {ip_status[ip]}')
        write_to_db(ip, ip_status[ip], con_db)
    dict_out["date"] = str(datetime.now())
    dict_out.update(ip_status)
    # write_to_file(dict_out, file)
    return


def add_ip_row(list_ip, con_db):
    try:
        known_ip = []
        db_query_select = "SELECT * FROM ip"
        with con_db.cursor() as c_select:
            # print(db_query_select)
            c_select.execute(db_query_select)
            result = c_select.fetchall()
            for row in result:
                known_ip.append(row[1])
        for ip in list_ip:
            if ip not in known_ip:
                db_query_insert = "INSERT INTO ip(ip) VALUES ('" + ip + "')"
                # print(db_query_insert)
                with con_db.cursor() as c_insert:
                    c_insert.execute(db_query_insert)
                    con_db.commit()
    except mysql.connector.Error as err:
        print(err)


def write_to_db(change_ip, status, con_db):
    with con_db.cursor() as c_update:
        db_query_update = "UPDATE ip SET status = '" + status + "', date = NOW() WHERE ( ip = '" + change_ip + "')"
        c_update.execute(db_query_update)
        print(db_query_update)
        con_db.commit()

def add_one_ip(one_ip, con_db):
    try:
        known_ip = get_ip(con_db)
        if one_ip not in known_ip:
            db_query_insert = "INSERT INTO ip(ip) VALUES ('" + one_ip + "')"
            with con_db.cursor() as c_insert:
                c_insert.execute(db_query_insert)
                con_db.commit()
                return 1
        else:
            return 0
    except mysql.connector.Error as err:
        print(err)

def remove_one_ip(one_ip, con_db):
    try:
        known_ip = get_ip(con_db)
        if one_ip in known_ip:
            db_query_delete = "DELETE FROM ip WHERE ip ='" + one_ip + "'"
            with con_db.cursor() as c_delete:
                c_delete.execute(db_query_delete)
                con_db.commit()
                return 1
        else:
            return 0
    except mysql.connector.Error as err:
        print(err)

def get_ip(con_db):
    with con_db.cursor() as c_select:
        db_query_select = "SELECT ip from ip"
        c_select.execute(db_query_select)
        result = c_select.fetchall()
        if result:
            list_ip_from_db = []
            for row in result:
                list_ip_from_db.append(row[0])
            return list_ip_from_db

def get_alarm(con_db):
    with con_db.cursor() as c_select:
        db_query_select = "SELECT ip, status, date from ip WHERE status = 'ALARM!'"
        c_select.execute(db_query_select)
        result = c_select.fetchall()
        list_status = []
        if result:
            for row in result:
                ping_status = {}
                ping_status["ip"] = row[0]
                ping_status["status"] = row[1]
                ping_status["date"] = row[2]
                list_status.append(ping_status)
    return list_status

def get_normal(con_db):
    with con_db.cursor() as c_select:
        db_query_select = "SELECT ip, status, date from ip WHERE status = 'OK'"
        c_select.execute(db_query_select)
        result = c_select.fetchall()
        list_status = []
        if result:
            for row in result:
                ping_status = {}
                ping_status["ip"] = row[0]
                ping_status["status"] = row[1]
                ping_status["date"] = row[2]
                list_status.append(ping_status)
    return list_status

def get_status(con_db):
    with con_db.cursor() as c_select:
        db_query_select = "SELECT ip, status, date from ip"
        c_select.execute(db_query_select)
        result = c_select.fetchall()
        list_status = []
        if result:
            for row in result:
                ping_status = {}
                ping_status["ip"] = row[0]
                ping_status["status"] = row[1]
                ping_status["date"] = row[2]
                list_status.append(ping_status)
    return list_status

def send_message(group_id, message):
    bot.send_message(group_id, message)

def set_user_timeout(con_db, user_timeout):
    with con_db.cursor() as c_insert:
        db_query_insert = "INSERT INTO config(timeout) VALUES('" + str(user_timeout) + "')"
        c_insert.execute(db_query_insert)
        con_db.commit()

if __name__ == '__main__':
    bot = telebot.TeleBot(TOKEN, parse_mode=None)
    now = datetime.now()
    send_message('-735404296', 'Бот запустился ' + now.strftime('%d/%m/%Y %H:%M:%S'))
    # bot.send_message('-735404296', 'Бот запустился ' + now.strftime('%d/%m/%Y %H:%M:%S'))

    # check_ip(ip_list, conn)
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        bot.reply_to(message, HELP)

    # @bot.message_handler(commands=['id'])
    # def get_chat_id(message):
    #     bot.reply_to(message, message)

    @bot.message_handler(commands=['add'])
    def add_ip(message):
        ips: list = message.text.split()
        ips.remove('/add')
        if ips:
            for ip in ips:
                re_ip = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
                if re_ip.match(ip):
                    conn = connect_db()
                    result = add_one_ip(ip, conn)
                    if result:
                        bot.reply_to(message, ip + " добавлен в базу отслеживания")
                    else:
                        bot.reply_to(message, ip + " уже в базе")
                    close_db(conn)
                else:
                    bot.reply_to(message, ip + " некорректен")
        else:
            bot.reply_to(message, 'Введите /add ip1 ip2 ip3..')


    @bot.message_handler(commands=['remove'])
    def remove_ip(message):
        ips: list = message.text.split()
        ips.remove('/remove')
        if ips:
            for ip in ips:
                re_ip = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
                if re_ip.match(ip):
                    conn = connect_db()
                    result = remove_one_ip(ip, conn)
                    if result:
                        bot.reply_to(message, ip + " удалён из базы отслеживания")
                        # ip_list.append(ip)
                    else:
                        bot.reply_to(message, ip + " не было в базе")
                    close_db(conn)
                else:
                    bot.reply_to(message, ip + " некорректен")
        else:
            bot.reply_to(message, 'Введите /remove ip1 ip2 ip3..')

    @bot.message_handler(commands=['show'])
    def show_ip(message):
        conn = connect_db()
        ip_from_db = get_ip(conn)
        close_db(conn)
        print(ip_from_db)
        if ip_from_db:
            bot.reply_to(message, "\n".join(ip_from_db))
        else:
            bot.reply_to(message, "База пустая")


    @bot.message_handler(commands=['set'])
    def set_timeout(message):
        timeouts: list = message.text.split()
        timeouts.remove('/set')
        try:
            timeout = int(timeouts[0])
            if 15 <= timeout <= 600:
                conn = connect_db()
                set_user_timeout(conn, timeout)
                bot.reply_to(message, "Таймаут " + str(timeout) + " установлен")
                close_db(conn)
            else:
                bot.reply_to(message, timeouts[0] + " не число от 15 до 600 сек")
        except:
            bot.reply_to(message, "Введите число от 15 до 600 сек")


    @bot.message_handler(commands=['alarm'])
    def show_alarm(message):
        conn = connect_db()
        ip_status = get_alarm(conn)
        if ip_status:
            str_status = ""
            for ip in ip_status:
                str_status += ip["ip"] + " " + str(ip["status"]) + " " + ip["date"].strftime('%d/%m/%Y %H:%M:%S') + "\n"
            bot.reply_to(message, str_status)
        else:
            bot.reply_to(message, "База пустая")
        close_db(conn)


    @bot.message_handler(commands=['normal'])
    def show_alarm(message):
        conn = connect_db()
        ip_status = get_normal(conn)
        if ip_status:
            str_status = ""
            for ip in ip_status:
                str_status += ip["ip"] + " " + str(ip["status"]) + " " + ip["date"].strftime('%d/%m/%Y %H:%M:%S') + "\n"
            bot.reply_to(message, str_status)
        else:
            bot.reply_to(message, "База пустая")
        close_db(conn)


    @bot.message_handler(commands=['status'])
    def show_status(message):
        conn = connect_db()
        ip_status = get_status(conn)
        # ip_from_db = get_ip(conn)
        if ip_status:
            count_ok = 0
            str_status = ""
            for ip in ip_status:
                str_status += ip["ip"] + " " + str(ip["status"]) + " " + ip["date"].strftime('%d/%m/%Y %H:%M:%S') + "\n"
                if ip["status"] == "OK":
                    count_ok += 1
            str_status += str(count_ok) + " из " + str(len(ip_status)) + " в сети"
            bot.reply_to(message, str_status)
        else:
            bot.reply_to(message, "База пустая")
        close_db(conn)


    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        bot.reply_to(message, message.text)
    bot.infinity_polling()

