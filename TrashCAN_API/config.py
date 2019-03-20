import sqlite3
#import logging
from flask import g

#Setup database
DATABASE = '/srv/trashcan/venv/database/database.db'

# Dict to hold configurations
conf = {}

def __init__():
    nonlocal conf
    load_config()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Without an option_name, this reloads all options. With an option name this reload a specific option
def load_config(option_name = ''):
    nonlocal conf
    conn = get_db()
    if option_name == '':
        conf.clear()
        result = conn.cursor().execute("SELECT * FROM System_Options")
    else:
        conf.pop(option_name)
        result = conn.cursor().execute("SELECT TOP 1 FROM System_Options WHERE option_name = ?",(option_name,))

    for row in result:
        conf[row[0]] = row
    conn.close()
    return

def get_last_change_id():
    conn = get_db()
    result = conn.cursor().execute("SELECT CAST(MAX(change_id)) AS INT FROM System_Option_Changes")
    conn.close()
    return result

def get_config(option_name = ''):
    conn = get_db()
    if option_name == '':
        result = conn.cursor().execute("SELECT * FROM System_Options")
    else:
        result = conn.cursor().execute("SELECT TOP 1 FROM System_Options WHERE option_name = ?", (option_name,))
    conn.close()
    return result

def set_config(option_name, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT TOP 1 FROM System_Options WHERE option_name = ?",(option_name,))
    if cur.rowcount == 0:
        conn.cursor().execute("INSERT INTO System_Options (option_name, option_value) VALUES(?, ?)",(option_name.uppper(), value,))
    else:
        conn.cursor().execute("UPDATE System_Options SET option_value = ? WHERE option_name = ?", (option_name.upper(),value,))
    conn.commit()
    conn.close()

def delete_config(option_name):
    conn = get_db()
    conn.cursor().execute("DELETE FROM System_Options WHERE option_name = ?",_(option_name,))
    conn.commit()
    conn.close()