from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).with_name("daymap.db")

PRIORITIES = ("High", "Medium", "Low")
RECURRENCES = ("None", "Daily", "Weekly")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _today_text():
    from datetime import date

    return date.today().isoformat()


def _make_task_table(cursor, table_name, completed=False):
    completed_column = ", completed_at TEXT" if completed else ""
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT,
            priority TEXT NOT NULL DEFAULT 'Medium',
            recurrence TEXT NOT NULL DEFAULT 'None'
            {completed_column}
        )
        """
    )


def _columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row["name"] for row in cursor.fetchall()}


def _add_missing_column(cursor, table_name, column_name, column_sql):
    if column_name not in _columns(cursor, table_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def _task_sort_sql():
    return """
        ORDER BY
            date,
            CASE WHEN time IS NULL OR time = '' THEN 1 ELSE 0 END,
            time,
            CASE priority
                WHEN 'High' THEN 0
                WHEN 'Medium' THEN 1
                WHEN 'Low' THEN 2
                ELSE 3
            END,
            id
    """


def _clean_priority(priority):
    return priority if priority in PRIORITIES else "Medium"


def _clean_recurrence(recurrence):
    return recurrence if recurrence in RECURRENCES else "None"


def _rows_to_tasks(rows):
    return [dict(row) for row in rows]


def init_db():
    conn = _connect()
    cursor = conn.cursor()

    _make_task_table(cursor, "tasks")
    _make_task_table(cursor, "completed_tasks", completed=True)

    # Older copies of the app only had name and time. Keep those tasks and
    # quietly add the fields the planner uses now.
    _add_missing_column(cursor, "tasks", "date", "date TEXT")
    _add_missing_column(cursor, "tasks", "priority", "priority TEXT DEFAULT 'Medium'")
    _add_missing_column(cursor, "tasks", "recurrence", "recurrence TEXT DEFAULT 'None'")

    _add_missing_column(cursor, "completed_tasks", "date", "date TEXT")
    _add_missing_column(cursor, "completed_tasks", "priority", "priority TEXT DEFAULT 'Medium'")
    _add_missing_column(cursor, "completed_tasks", "recurrence", "recurrence TEXT DEFAULT 'None'")
    _add_missing_column(cursor, "completed_tasks", "completed_at", "completed_at TEXT")

    today = _today_text()
    for table_name in ("tasks", "completed_tasks"):
        cursor.execute(f"UPDATE {table_name} SET date = ? WHERE date IS NULL OR date = ''", (today,))
        cursor.execute(
            f"""
            UPDATE {table_name}
            SET priority = 'Medium'
            WHERE priority IS NULL OR priority NOT IN ('High', 'Medium', 'Low')
            """
        )
        cursor.execute(
            f"""
            UPDATE {table_name}
            SET recurrence = 'None'
            WHERE recurrence IS NULL OR recurrence NOT IN ('None', 'Daily', 'Weekly')
            """
        )

    conn.commit()
    conn.close()


def add_task(name, task_date=None, time=None, priority="Medium", recurrence="None"):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tasks (name, date, time, priority, recurrence)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            name,
            task_date or _today_text(),
            time,
            _clean_priority(priority),
            _clean_recurrence(recurrence),
        ),
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id


def add_many_tasks(tasks):
    added = 0
    for task in tasks:
        add_task(
            task["name"],
            task.get("date"),
            task.get("time"),
            task.get("priority", "Medium"),
            task.get("recurrence", "None"),
        )
        added += 1
    return added


def get_tasks(search_text=""):
    conn = _connect()
    cursor = conn.cursor()
    search = f"%{search_text.strip()}%" if search_text else "%"
    cursor.execute(
        f"""
        SELECT id, name, date, time, priority, recurrence
        FROM tasks
        WHERE name LIKE ?
        {_task_sort_sql()}
        """,
        (search,),
    )
    tasks = _rows_to_tasks(cursor.fetchall())
    conn.close()
    return tasks


def get_completed_tasks(search_text=""):
    conn = _connect()
    cursor = conn.cursor()
    search = f"%{search_text.strip()}%" if search_text else "%"
    cursor.execute(
        f"""
        SELECT id, name, date, time, priority, recurrence, completed_at
        FROM completed_tasks
        WHERE name LIKE ?
        {_task_sort_sql()}
        """,
        (search,),
    )
    tasks = _rows_to_tasks(cursor.fetchall())
    conn.close()
    return tasks


def edit_task(task_id, name, task_date=None, time=None, priority="Medium", recurrence="None"):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE tasks
        SET name = ?, date = ?, time = ?, priority = ?, recurrence = ?
        WHERE id = ?
        """,
        (
            name,
            task_date or _today_text(),
            time,
            _clean_priority(priority),
            _clean_recurrence(recurrence),
            task_id,
        ),
    )
    conn.commit()
    conn.close()


def _next_recurrence_date(task_date, recurrence):
    from datetime import date, timedelta

    if recurrence == "None":
        return None

    try:
        start = date.fromisoformat(task_date)
    except (TypeError, ValueError):
        start = date.today()

    step = timedelta(days=1 if recurrence == "Daily" else 7)
    next_day = start + step
    today = date.today()

    while next_day < today:
        next_day += step

    return next_day.isoformat()


def complete_task(task_id):
    from datetime import datetime

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    if task is None:
        conn.close()
        return None

    completed_at = datetime.now().isoformat(timespec="seconds")
    cursor.execute(
        """
        INSERT INTO completed_tasks (name, date, time, priority, recurrence, completed_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            task["name"],
            task["date"],
            task["time"],
            task["priority"],
            task["recurrence"],
            completed_at,
        ),
    )
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    next_date = _next_recurrence_date(task["date"], task["recurrence"])
    if next_date:
        cursor.execute(
            """
            INSERT INTO tasks (name, date, time, priority, recurrence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task["name"], next_date, task["time"], task["priority"], task["recurrence"]),
        )

    conn.commit()
    conn.close()
    return next_date


def delete_task(task_id):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def delete_completed_task(task_id):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM completed_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def restore_completed_task(task_id):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM completed_tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    if task is None:
        conn.close()
        return

    cursor.execute(
        """
        INSERT INTO tasks (name, date, time, priority, recurrence)
        VALUES (?, ?, ?, ?, ?)
        """,
        (task["name"], task["date"], task["time"], task["priority"], task["recurrence"]),
    )
    cursor.execute("DELETE FROM completed_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def clear_tasks():
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()


def clear_completed_tasks():
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM completed_tasks")
    conn.commit()
    conn.close()
