## simple database helpers for saving, editing, and clearing tasks.
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
    conn.commit()
    conn.close()


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
    tasks = c.fetchall()
    conn.close()
    return tasks

def delete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def edit_task(task_id, name, time=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE tasks SET name = ?, time = ? WHERE id = ?", (name, time, task_id))
    conn.commit()
    conn.close()
