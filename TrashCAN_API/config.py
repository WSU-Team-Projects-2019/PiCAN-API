import sqlite3
#import logging
from flask import g

#Setup database
DATABASE = '/srv/trashcan/venv/database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def get_config(option_name = ''):
    config_items = []
    conn = get_db()
    if option_name == '':
        result = conn.cursor().execute("SELECT * FROM [System_Options]")
    else:
        result = conn.cursor().execute("SELECT TOP 1 FROM [System_Options] WHERE option_name = ?",(option_name,))

    for row in result:
        config_items.append({'option_name' : row[0], 'value' : row[1]})
    conn.close()
    return config_items

def get_last_change_id():
    conn = get_db()
    result = conn.cursor().execute("SELECT MAX([option_name]) FROM System_Option_Changes")
    conn.close()
    return result

def store_config(option_name, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT TOP 1 FROM System_Options WHERE option_name = ?",(value,))
    if cur.rowcount == 0:
        conn.cursor().execute("INSERT INTO System_Options ([option_name], [value]) VALUES(?, ?)",(option_name, value,))
    else:
        conn.cursor().execute("UPDATE [System_Options] SET [Value] = ? WHERE [option_name] = ?", (option_name,))
    conn.commit()
    conn.close()