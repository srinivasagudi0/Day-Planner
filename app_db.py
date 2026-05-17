import sqlite3

def init_db():
    conn = sqlite3.connect('daymap.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_task(name, time=None):
    conn = sqlite3.connect("daymap.db")
    c = conn.cursor()
    c.execute("INSERT INTO tasks (name, time) VALUES (?, ?)", (name, time))
    conn.commit()
    conn.close()

def get_tasks():
    conn = sqlite3.connect("daymap.db")
    c = conn.cursor()
    c.execute("SELECT id, name, time FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks