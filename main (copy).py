import telebot
import datetime
import time
import sqlite3
import json
import os

from flask import Flask
from threading import Thread

# ================= БАЗА =================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS data (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()


def db_set(key, value):
    cursor.execute(
        "INSERT OR REPLACE INTO data (key, value) VALUES (?, ?)",
        (key, json.dumps(value))
    )
    conn.commit()


def db_get(key, default):
    cursor.execute("SELECT value FROM data WHERE key=?", (key,))
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    return default


# ================= WEB SERVER (Render) =================

app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is alive"


def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))


def keep_alive():
    t = Thread(target=run)
    t.start()


# ================= НАСТРОЙКИ =================

TOKEN = "ТВОЙ_ТОКЕН_БОТА"
OWNER_ID = 8402496361

bot = telebot.TeleBot(TOKEN)

admins = set(db_get("admins", [OWNER_ID]))

active_list = "restart"

lists = db_get("lists", {
    "restart": {},
    "payday": {}
})

owners = db_get("owners", {
    "restart": {},
    "payday": {}
})

usernames = db_get("usernames", {})

msg_ids = db_get("msg_ids", {
    "restart": None,
    "payday": None
})

chat_ids = db_get("chat_ids", {
    "restart": None,
    "payday": None
})

# ================= СЕРВЕРА =================

SERVERS = [
("❤️","RED","ред"),("💚","GREEN","грин"),("💙","BLUE","блу"),
("💛","YELLOW","еллоу"),("🧡","ORANGE","оранж"),("💜","PURPLE","пурпл"),
("🍏","LIME","лайм"),("🌸","PINK","пинк"),("🍒","CHERRY","черри"),
("🖤","BLACK","блэк"),("🔵","INDIGO","индиго"),("🤍","WHITE","вайт")
]

ALIASES = {}
for emoji, eng, rus in SERVERS:
    ALIASES[eng.lower()] = eng
    ALIASES[rus.lower()] = eng


def find_server(word):
    return ALIASES.get(word.lower())


# ================= ГЕНЕРАЦИЯ =================

def generate(name):

    date = datetime.datetime.now().strftime("%d.%m.%y")
    title = "⚡ RESTART LIST ⚡" if name == "restart" else "💰 PAYDAY LIST 💰"

    text = f"{title} [Дата: {date}]\n\n"

    for emoji, eng, rus in SERVERS:
        value = lists[name].get(eng, "")
        text += f"{emoji} {eng} - {value}\n"

    return text


def update(name):

    if msg_ids[name]:
        try:
            bot.edit_message_text(
                generate(name),
                chat_ids[name],
                msg_ids[name]
            )
        except:
            pass


# ================= СОЗДАНИЕ =================

def create_list(message, name):

    global active_list

    if message.from_user.id not in admins:
        return

    active_list = name

    lists[name].clear()
    owners[name].clear()

    msg = bot.send_message(message.chat.id, generate(name))

    msg_ids[name] = msg.message_id
    chat_ids[name] = message.chat.id

    bot.pin_chat_message(message.chat.id, msg.message_id)

    db_set("lists", lists)
    db_set("owners", owners)
    db_set("msg_ids", msg_ids)
    db_set("chat_ids", chat_ids)


# ================= КОМАНДЫ =================

@bot.message_handler(commands=['start', 'startlist'])
def start_list(message):
    create_list(message, "restart")


@bot.message_handler(commands=['payday'])
def payday_list(message):
    create_list(message, "payday")


# ================= ОСНОВНОЙ ОБРАБОТЧИК =================

@bot.message_handler(func=lambda m: True)
def handle(message):

    if not active_list:
        return

    text = message.text.strip()

    parts = text.split()

    if len(parts) < 2:
        return

    srv = find_server(parts[0])

    if not srv:
        return

    info = " ".join(parts[1:])
    username = message.from_user.username or message.from_user.first_name

    entry = f"{info} (@{username})"

    lists[active_list][srv] = entry
    owners[active_list][srv] = message.from_user.id

    usernames[message.from_user.id] = username
    db_set("usernames", usernames)

    bot.reply_to(message, "✅ Записано")

    db_set("lists", lists)
    db_set("owners", owners)

    update(active_list)


# ================= ВОССТАНОВЛЕНИЕ =================

def restore_messages():

    for name in ["restart", "payday"]:

        if not chat_ids.get(name):
            continue

        try:

            if msg_ids.get(name):

                bot.edit_message_text(
                    generate(name),
                    chat_ids[name],
                    msg_ids[name]
                )

            else:
                raise Exception("Нет сообщения")

        except:

            msg = bot.send_message(
                chat_ids[name],
                generate(name)
            )

            msg_ids[name] = msg.message_id

            bot.pin_chat_message(
                chat_ids[name],
                msg.message_id
            )

            db_set("msg_ids", msg_ids)
            db_set("chat_ids", chat_ids)


# ================= ЗАПУСК =================

print("Бот запущен")

keep_alive()
time.sleep(2)

restore_messages()

try:
    bot.send_message(OWNER_ID, "✅ Бот запущен")
except:
    pass


while True:
    try:
        bot.infinity_polling(
            skip_pending=True,
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:
        print("Ошибка:", e)

        try:
            bot.send_message(
                OWNER_ID,
                f"❌ Бот упал!\nОшибка:\n{e}"
            )
        except:
            pass

        time.sleep(5)import telebot
import datetime
import time

import sqlite3
import json

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS data (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()


def db_set(key, value):
    cursor.execute(
        "INSERT OR REPLACE INTO data (key, value) VALUES (?, ?)",
        (key, json.dumps(value))
    )
    conn.commit()


def db_get(key, default):
    cursor.execute("SELECT value FROM data WHERE key=?", (key,))
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    return default

from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

TOKEN = "8251028589:AAF2DkXC5sFF-0NnU4JmqTYuMIuHy0vaVXs"
OWNER_ID = 8402496361

bot = telebot.TeleBot(TOKEN)

admins = set(db_get("admins", [OWNER_ID]))

active_list = "restart"

lists = db_get("lists", {
    "restart": {},
    "payday": {}
})

owners = db_get("owners", {
    "restart": {},
    "payday": {}
})

usernames = db_get("usernames", {})

msg_ids = db_get("msg_ids", {
    "restart": None,
    "payday": None
})

chat_ids = db_get("chat_ids", {
    "restart": None,
    "payday": None
})

# ===== 90 СЕРВЕРОВ =====

SERVERS = [
("❤️","RED","ред"),("💚","GREEN","грин"),("💙","BLUE","блу"),
("💛","YELLOW","еллоу"),("🧡","ORANGE","оранж"),("💜","PURPLE","пурпл"),
("🍏","LIME","лайм"),("🌸","PINK","пинк"),("🍒","CHERRY","черри"),
("🖤","BLACK","блэк"),("🔵","INDIGO","индиго"),("🤍","WHITE","вайт"),
("🎀","MAGENTA","маджента"),("🩸","CRIMSON","кримсон"),("🥇","GOLD","голд"),
("🌐","AZURE","азур"),("💎","PLATINUM","платинум"),("🌊","AQUA","аква"),
("🌫","GRAY","грей"),("❄️","ICE","айс"),

("🌶","CHILLI","чили"),("🍫","CHOCO","чоко"),("🌇","MOSCOW","москва"),
("🌉","SPB","спб"),("🌪","UFA","уфа"),("🌊","SOCHI","сочи"),
("🏛","KAZAN","казань"),("🎧","SAMARA","самара"),("🍺","ROSTOV","ростов"),
("🏖","ANAPA","анапа"),

("📗","EKB","екб"),("🌴","KRASNODAR","краснодар"),("🪿","ARZAMAS","арзамас"),
("🍃","NOVOSIB","новосиб"),("🍙","GROZNY","грозный"),("🐉","SARATOV","саратов"),
("🪙","OMSK","омск"),("🌪","IRKUTSK","иркутск"),("🎒","VOLGOGRAD","волгоград"),
("👑","VORONEZH","воронеж"),

("🎓","BELGOROD","белгород"),("⛑️","MAKHACHKALA","махачкала"),
("🌂","VLADIKAVKAZ","владикавказ"),("🧶","VLADIVOSTOK","владивосток"),
("👒","KALININGRAD","калининград"),("🕊","CHELYABINSK","челябинск"),
("🖇","KRASNOYARSK","красноярск"),("🪄","CHEBOKSARY","чебоксары"),
("🐨","KHABAROVSK","хабаровск"),("🏟","PERM","пермь"),

("⛳","TULA","тула"),("🎭","RYAZAN","рязань"),("🎳","MURMANSK","мурманск"),
("🎷","PENZA","пенза"),("🃏","KURSK","курск"),("🥋","ARKHANGELSK","архангельск"),
("🍖","ORENBURG","оренбург"),("🔫","KIROV","киров"),("🌺","KEMEROVO","кемерово"),
("🐋","TYUMEN","тюмень"),

("🪸","TOLYATTI","тольятти"),("🪅","IVANOVO","иваново"),
("🪼","STAVROPOL","ставрополь"),("🫚","SMOLENSK","смоленск"),
("🪭","PSKOV","псков"),("🧸","BRYANSK","брянск"),
("🦅","OREL","орел"),("🏛","YAROSLAVL","ярославль"),
("💦","BARNAUL","барнаул"),("🎈","LIPETSK","липецк"),

("🍭","ULYANOVSK","ульяновск"),("🥽","YAKUTSK","якутск"),
("🥐","TAMBOV","тамбов"),("👜","BRATSK","братск"),
("🧣","ASTRAKHAN","астрахань"),("🦎","CHITA","чита"),
("🐲","KOSTROMA","кострома"),("😹","VLADIMIR","владимир"),
("🫐","KALUGA","калуга"),("🌼","NOVGOROD","новгород"),

("🦁","TAGANROG","таганрог"),("🐦","VOLOGDA","вологда"),
("🐿","TVER","тверь"),("🎄","TOMSK","томск"),
("🏍","IZHEVSK","ижевск"),("❄️","SURGUT","сургут"),
("🏰","PODOLSK","подольск"),("☠️","MAGADAN","магадан"),
("😤","CHEREPOVETS","череповец"),("🤡","NORILSK","норильск")
]

ALIASES = {}
for emoji, eng, rus in SERVERS:
    ALIASES[eng.lower()] = eng
    ALIASES[rus.lower()] = eng


def find_server(word):
    return ALIASES.get(word.lower())


def generate(name):

    date = datetime.datetime.now().strftime("%d.%m.%y")
    title = "⚡ RESTART LIST ⚡" if name == "restart" else "💰 PAYDAY LIST 💰"

    text = f"{title} [Дата: {date}]\n\n"

    for emoji, eng, rus in SERVERS:
        value = lists[name].get(eng, "")
        text += f"{emoji} {eng} - {value}\n"

    return text


def update(name):

    if msg_ids[name]:
        try:
            bot.edit_message_text(
                generate(name),
                chat_ids[name],
                msg_ids[name]
            )
        except:
            pass


def create_list(message, name):

    global active_list

    if message.from_user.id not in admins:
        return

    active_list = name

    lists[name].clear()
    owners[name].clear()

    msg = bot.send_message(message.chat.id, generate(name))

    msg_ids[name] = msg.message_id
    chat_ids[name] = message.chat.id

    bot.pin_chat_message(message.chat.id, msg.message_id)

    db_set("lists", lists)
    db_set("owners", owners)
    db_set("msg_ids", msg_ids)
    db_set("chat_ids", chat_ids)


# ===== КОМАНДЫ =====

@bot.message_handler(commands=['startlist','start'])
def start_list(message):
    create_list(message, "restart")


@bot.message_handler(commands=['payday'])
def payday_list(message):
    create_list(message, "payday")


@bot.message_handler(commands=['addadmin'])
def add_admin(message):

    if message.from_user.id != OWNER_ID:
        return

    try:
        new_id = int(message.text.split()[1])
        admins.add(new_id)
        db_set("admins",
list(admins))
        bot.reply_to(message, "✅ Админ добавлен")
    except:
        bot.reply_to(message, "❌ Ошибка")


@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):

    if message.from_user.id != OWNER_ID:
        return

    try:
        rem_id = int(message.text.split()[1])
        admins.discard(rem_id)
        db_set("admins", list(admins))
        bot.reply_to(message, "✅ Админ удалён")
    except:
        bot.reply_to(message, "❌ Ошибка")


@bot.message_handler(commands=['myservers'])
def my_servers(message):

    uid = message.from_user.id
    text = "📋 Твои серверы:\n\n"

    for lname in lists:
        for srv, owner in owners[lname].items():
            if owner == uid:
                text += f"{srv} ({lname})\n"

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['stats'])
def stats(message):

    stat = {}

    for lname in lists:
        for owner in owners[lname].values():
            stat[owner] = stat.get(owner, 0) + 1

    text = "📊 Статистика:\n\n"

    for uid, count in stat.items():

        name = usernames.get(uid, str(uid))
        text += f"{name} — {count}\n"

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['clear'])
def clear(message):

    if message.from_user.id not in admins:
        return

    lists[active_list].clear()
    owners[active_list].clear()

    db_set("lists", lists)
    db_set("owners", owners)

    update(active_list)


# ===== ОСНОВНОЙ =====

@bot.message_handler(func=lambda m: True)
def handle(message):

    if not active_list:
        return

    text = message.text.strip()

    # удаление
    if text.startswith("-"):

        srv = find_server(text[1:].strip())
        if not srv:
            return

        if srv in owners[active_list] and owners[active_list][srv] == message.from_user.id:

            lists[active_list].pop(srv, None)
            owners[active_list].pop(srv, None)

            bot.reply_to(message, "🗑 Удалено")

            db_set("lists", lists)
            db_set("owners", owners)
            update(active_list)

        else:
            bot.reply_to(message, "❌ Это не твоя запись")

        return

    parts = text.split()

    if len(parts) < 2:
        return

    srv = find_server(parts[0])

    if not srv:
        return

    if srv in owners[active_list]:

        if owners[active_list][srv] != message.from_user.id:
            bot.reply_to(message, "❌ Уже занято другим игроком")
            return

    info = " ".join(parts[1:])
    username = message.from_user.username or message.from_user.first_name

    entry = f"{info} (@{username})"

    lists[active_list][srv] = entry
    owners[active_list][srv] = message.from_user.id

    usernames[message.from_user.id] = username
    db_set("usernames", usernames)
    bot.reply_to(message, "✅ Записано")

    db_set("lists", lists)
    db_set("owners", owners)

    update(active_list)

def restore_messages():

    for name in ["restart", "payday"]:

        if not chat_ids.get(name):
            continue

        try:

            if msg_ids.get(name):

                bot.edit_message_text(
                    generate(name),
                    chat_ids[name],
                    msg_ids[name]
                )

            else:
                raise Exception("Нет сообщения")

        except:

            msg = bot.send_message(
                chat_ids[name],
                generate(name)
            )

            msg_ids[name] = msg.message_id

            bot.pin_chat_message(
                chat_ids[name],
                msg.message_id
            )

            db_set("msg_ids", msg_ids)
            db_set("chat_ids", chat_ids)
            
print("Бот запущен")

keep_alive()
time.sleep(2)

restore_messages()
bot.send_message(OWNER_ID, "✅ Бот запущен")

while True:
    try:
        bot.infinity_polling(
            skip_pending=True,
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:
        print("Ошибка:", e)

        try:
            bot.send_message(
                OWNER_ID,
                f"❌ Бот упал!\nОшибка:\n{e}"
            )
        except:
            pass 

        time.sleep(5) 
