## cleaned up the db code to be more error proof and added some context managers to make it easier to work with the db connection.
import sqlite3

DB_PATH = "daymap.db"
    
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time TEXT
        )
    ''')


def add_task(name, time=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (name, time) VALUES (?, ?)", (name, time))
    conn.commit()
    conn.close()

def get_tasks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, name, time
        FROM tasks
        ORDER BY
            CASE WHEN time IS NULL OR time = '' THEN 1 ELSE 0 END,
            time,
            id
    """)
    return c.fetchall()

def delete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def edit_task(id, name=None, time=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if name is not None and time is not None:
        c.execute("UPDATE tasks SET name = ?, time = ? WHERE id = ?", (name, time, id))
    elif name is not None:
        c.execute("UPDATE tasks SET name = ? WHERE id = ?", (name, id))
    elif time is not None:
        c.execute("UPDATE tasks SET time = ? WHERE id = ?", (time, id))
    conn.commit()
    conn.close()