# refactor using ai to make it clean and finish the project fast, so thanks
import datetime
import re
from collections import defaultdict

import streamlit as st

from app_db import (
    PRIORITIES,
    RECURRENCES,
    add_many_tasks,
    add_task,
    clear_completed_tasks,
    clear_tasks,
    complete_task,
    delete_completed_task,
    delete_task,
    edit_task,
    get_completed_tasks,
    get_tasks,
    init_db,
    restore_completed_task,
)
from Planner import build_local_plan, generate_basic_plan


st.set_page_config(page_title="DayMap", layout="centered")
init_db()


BADGE_STYLES = {
    "red": "background:#fee2e2;color:#991b1b;border:1px solid #fecaca;",
    "yellow": "background:#fef3c7;color:#92400e;border:1px solid #fde68a;",
    "blue": "background:#dbeafe;color:#1e40af;border:1px solid #bfdbfe;",
    "green": "background:#dcfce7;color:#166534;border:1px solid #bbf7d0;",
    "gray": "background:#f3f4f6;color:#374151;border:1px solid #e5e7eb;",
}


def flash(message):
    st.session_state.flash = message


def parse_date(value):
    if isinstance(value, datetime.date):
        return value

    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return datetime.date.today()


def saved_date(value):
    return parse_date(value).isoformat()


def format_date(day):
    day = parse_date(day)
    today = datetime.date.today()

    if day == today:
        return f"Today, {day:%b} {day.day}"
    if day == today + datetime.timedelta(days=1):
        return f"Tomorrow, {day:%b} {day.day}"
    return f"{day:%a}, {day:%b} {day.day}, {day:%Y}"


def format_time(task_time):
    if not task_time:
        return "Anytime"

    try:
        parsed_time = datetime.time.fromisoformat(task_time)
    except ValueError:
        return task_time

    return parsed_time.strftime("%I:%M %p").lstrip("0")


def saved_time(task_time):
    if task_time is None:
        return None
    return task_time.isoformat(timespec="minutes")


def editable_time(task_time):
    if not task_time:
        return None

    try:
        return datetime.time.fromisoformat(task_time)
    except ValueError:
        return None


def choose_task_date(label, key, current_value=None):
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    current_date = parse_date(current_value)

    if current_date == today:
        starting_choice = 0
    elif current_date == tomorrow:
        starting_choice = 1
    else:
        starting_choice = 2

    choice = st.selectbox(
        label,
        ["Today", "Tomorrow", "Pick a date"],
        index=starting_choice,
        key=f"{key}_choice",
    )

    if choice == "Today":
        return today
    if choice == "Tomorrow":
        return tomorrow
    return st.date_input("Date", value=current_date, key=f"{key}_date")


def badge(text, color):
    style = BADGE_STYLES.get(color, BADGE_STYLES["gray"])
    return (
        f"<span style='display:inline-block;padding:2px 8px;border-radius:999px;"
        f"font-size:12px;font-weight:700;line-height:1.6;{style}'>{text}</span>"
    )


def task_status(task):
    task_day = parse_date(task.get("date"))
    task_time = editable_time(task.get("time"))
    today = datetime.date.today()
    now = datetime.datetime.now().replace(second=0, microsecond=0)

    if task_day < today:
        return "Overdue", "red"

    if task_day == today and task_time:
        task_moment = datetime.datetime.combine(task_day, task_time)
        if task_moment < now:
            return "Overdue", "red"
        if task_moment - now <= datetime.timedelta(hours=2):
            return "Due soon", "yellow"
        return "Today", "yellow"

    if task_day == today:
        return "Today", "yellow"

    if task_day == today + datetime.timedelta(days=1):
        return "Tomorrow", "blue"

    return "Upcoming", "blue"


def priority_badge(priority):
    colors = {"High": "red", "Medium": "yellow", "Low": "gray"}
    return badge(f"{priority} priority", colors.get(priority, "gray"))


def recurrence_text(recurrence):
    if recurrence == "None":
        return "One time"
    return recurrence


def quick_add_task(raw_text):
    # used ai to polish this and for regex functions so hopefully you understand.
    text = raw_text.strip()
    if not text:
        return None

    task_date = datetime.date.today()
    task_time = None
    priority = "Medium"
    recurrence = "None"
    name_text = text

    if re.search(r"\btomorrow\b", name_text, flags=re.IGNORECASE):
        task_date = datetime.date.today() + datetime.timedelta(days=1)
        name_text = re.sub(r"\btomorrow\b", " ", name_text, flags=re.IGNORECASE)
    elif re.search(r"\btoday\b", name_text, flags=re.IGNORECASE):
        task_date = datetime.date.today()
        name_text = re.sub(r"\btoday\b", " ", name_text, flags=re.IGNORECASE)

    date_match = re.search(r"\b(20\d{2}-\d{1,2}-\d{1,2})\b", name_text)
    if date_match:
        try:
            task_date = datetime.date.fromisoformat(date_match.group(1))
            name_text = name_text[: date_match.start()] + " " + name_text[date_match.end() :]
        except ValueError:
            pass

    short_date_match = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", name_text)
    if short_date_match:
        month = int(short_date_match.group(1))
        day = int(short_date_match.group(2))
        year_text = short_date_match.group(3)
        year = datetime.date.today().year if not year_text else int(year_text)
        if year < 100:
            year += 2000
        try:
            task_date = datetime.date(year, month, day)
            name_text = name_text[: short_date_match.start()] + " " + name_text[short_date_match.end() :]
        except ValueError:
            pass

    recurrence_match = re.search(r"\b(every day|daily|every week|weekly)\b", name_text, flags=re.IGNORECASE)
    if recurrence_match:
        picked = recurrence_match.group(1).lower()
        recurrence = "Daily" if picked in ("every day", "daily") else "Weekly"
        name_text = name_text[: recurrence_match.start()] + " " + name_text[recurrence_match.end() :]

    priority_match = re.search(
        r"\b(high|medium|low)\s+priority\b|\bpriority\s+(high|medium|low)\b",
        name_text,
        flags=re.IGNORECASE,
    )
    if priority_match:
        priority = (priority_match.group(1) or priority_match.group(2)).title()
        name_text = name_text[: priority_match.start()] + " " + name_text[priority_match.end() :]

    named_time = re.search(r"\b(noon|midnight)\b", name_text, flags=re.IGNORECASE)
    if named_time:
        task_time = datetime.time(12, 0) if named_time.group(1).lower() == "noon" else datetime.time(0, 0)
        name_text = name_text[: named_time.start()] + " " + name_text[named_time.end() :]

    time_match = re.search(r"\b(?:at\s*)?(\d{1,2})(?::([0-5]\d))?\s*(am|pm)\b", name_text, flags=re.IGNORECASE)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        meridian = time_match.group(3).lower()
        if hour <= 12:
            if meridian == "pm" and hour != 12:
                hour += 12
            if meridian == "am" and hour == 12:
                hour = 0
            task_time = datetime.time(hour, minute)
            name_text = name_text[: time_match.start()] + " " + name_text[time_match.end() :]

    if task_time is None:
        time_24_match = re.search(r"\b(?:at\s*)?([01]?\d|2[0-3]):([0-5]\d)\b", name_text, flags=re.IGNORECASE)
        if time_24_match:
            task_time = datetime.time(int(time_24_match.group(1)), int(time_24_match.group(2)))
            name_text = name_text[: time_24_match.start()] + " " + name_text[time_24_match.end() :]

    task_name = re.sub(r"\s+", " ", name_text).strip(" ,.-")
    task_name = re.sub(r"\b(at|on|for)$", "", task_name, flags=re.IGNORECASE).strip(" ,.-")

    return {
        "name": task_name or text,
        "date": saved_date(task_date),
        "time": saved_time(task_time),
        "priority": priority,
        "recurrence": recurrence,
    }


def filter_tasks(tasks, filter_name, completed=False):
    today = datetime.date.today()

    if filter_name == "Completed":
        return tasks if completed else []

    if filter_name == "Upcoming":
        return [task for task in tasks if parse_date(task.get("date")) > today]

    return [task for task in tasks if parse_date(task.get("date")) <= today]


def render_empty(message):
    st.info(message)


def render_pending_task(task, key_prefix):
    status_text, status_color = task_status(task)

    with st.container(border=True):
        time_column, detail_column, status_column = st.columns([1.1, 3, 1.2])
        time_column.markdown(f"**{format_time(task.get('time'))}**")
        time_column.caption(format_date(task.get("date")))

        detail_column.markdown(f"**{task['name']}**")
        detail_column.markdown(
            f"{priority_badge(task.get('priority', 'Medium'))} "
            f"{badge(recurrence_text(task.get('recurrence', 'None')), 'gray')}",
            unsafe_allow_html=True,
        )
        status_column.markdown(badge(status_text, status_color), unsafe_allow_html=True)

        action_column, delete_column = st.columns(2)
        if action_column.button("Complete", key=f"{key_prefix}_complete_{task['id']}", use_container_width=True):
            next_date = complete_task(task["id"])
            if next_date:
                flash(f"Completed. Next {task['recurrence'].lower()} copy is set for {format_date(next_date)}.")
            else:
                flash("Task completed.")
            st.rerun()

        if delete_column.button("Delete", key=f"{key_prefix}_delete_{task['id']}", use_container_width=True):
            delete_task(task["id"])
            flash("Task deleted.")
            st.rerun()

        with st.expander("Edit task"):
            with st.form(f"{key_prefix}_edit_form_{task['id']}"):
                edited_name = st.text_input("Task name", value=task["name"], key=f"{key_prefix}_name_{task['id']}")
                edited_date = choose_task_date("Date", f"{key_prefix}_date_{task['id']}", task.get("date"))
                edited_time = st.time_input(
                    "Time",
                    value=editable_time(task.get("time")),
                    step=datetime.timedelta(minutes=15),
                    key=f"{key_prefix}_time_{task['id']}",
                )
                edited_priority = st.selectbox(
                    "Priority",
                    list(PRIORITIES),
                    index=list(PRIORITIES).index(task.get("priority", "Medium")),
                    key=f"{key_prefix}_priority_{task['id']}",
                )
                edited_recurrence = st.selectbox(
                    "Recurrence",
                    list(RECURRENCES),
                    index=list(RECURRENCES).index(task.get("recurrence", "None")),
                    key=f"{key_prefix}_recurrence_{task['id']}",
                )
                saved = st.form_submit_button("Save", use_container_width=True)

            if saved:
                if not edited_name.strip():
                    st.warning("Please add a task name first.")
                else:
                    edit_task(
                        task["id"],
                        edited_name.strip(),
                        saved_date(edited_date),
                        saved_time(edited_time),
                        edited_priority,
                        edited_recurrence,
                    )
                    flash("Task updated.")
                    st.rerun()


def render_completed_task(task, key_prefix):
    with st.container(border=True):
        time_column, detail_column, status_column = st.columns([1.1, 3, 1.2])
        time_column.markdown(f"**{format_time(task.get('time'))}**")
        time_column.caption(format_date(task.get("date")))

        detail_column.markdown(f"**{task['name']}**")
        detail_column.markdown(
            f"{priority_badge(task.get('priority', 'Medium'))} "
            f"{badge(recurrence_text(task.get('recurrence', 'None')), 'gray')}",
            unsafe_allow_html=True,
        )
        status_column.markdown(badge("Done", "green"), unsafe_allow_html=True)

        restore_column, delete_column = st.columns(2)
        if restore_column.button("Mark incomplete", key=f"{key_prefix}_restore_{task['id']}", use_container_width=True):
            restore_completed_task(task["id"])
            flash("Task moved back to pending.")
            st.rerun()

        if delete_column.button("Delete", key=f"{key_prefix}_delete_completed_{task['id']}", use_container_width=True):
            delete_completed_task(task["id"])
            flash("Completed task deleted.")
            st.rerun()


def render_task_section(title, tasks, empty_message, completed=False, key_prefix="task"):
    st.subheader(title)
    if not tasks:
        render_empty(empty_message)
        return

    for task in tasks:
        if completed:
            render_completed_task(task, key_prefix)
        else:
            render_pending_task(task, key_prefix)


def grouped_by_date(tasks):
    grouped = defaultdict(list)
    for task in tasks:
        grouped[parse_date(task.get("date"))].append(task)
    return dict(sorted(grouped.items()))


def task_summary(tasks):
    overdue = 0
    for task in tasks:
        status_text, _ = task_status(task)
        if status_text == "Overdue":
            overdue += 1
    return overdue


st.title("DayMap")
st.caption("Plan the day, keep tomorrow visible, and close the loop on what got done.")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

all_pending = get_tasks()
all_completed = get_completed_tasks()

st.sidebar.header("DayMap")
mode = st.sidebar.selectbox("Mode", ["Home", "Add Task", "Completed Tasks", "Schedule", "Schedule Planner"])
st.sidebar.divider()
st.sidebar.metric("Pending", len(all_pending))
st.sidebar.metric("Completed", len(all_completed))

if st.sidebar.button("Clear pending tasks", disabled=not all_pending, use_container_width=True):
    clear_tasks()
    flash("Pending tasks cleared.")
    st.rerun()


if mode == "Home":
    today = datetime.date.today()
    overdue_count = task_summary(all_pending)

    metric_left, metric_middle, metric_right = st.columns(3)
    metric_left.metric("Today", f"{today:%b} {today.day}")
    metric_middle.metric("Pending", len(all_pending))
    metric_right.metric("Overdue", overdue_count)

    with st.form("quick_add_form", clear_on_submit=True):
        quick_text = st.text_input("Quick add", placeholder="Call mom at 6pm tomorrow")
        quick_submitted = st.form_submit_button("Add task", use_container_width=True, type="primary")

    if quick_submitted:
        parsed_task = quick_add_task(quick_text)
        if parsed_task is None or not parsed_task["name"].strip():
            st.warning("Please add a task name first.")
        else:
            add_task(
                parsed_task["name"],
                parsed_task["date"],
                parsed_task["time"],
                parsed_task["priority"],
                parsed_task["recurrence"],
            )
            flash(f"Added {parsed_task['name']} for {format_date(parsed_task['date'])}.")
            st.rerun()

    search_text = st.text_input("Search", placeholder="Find task by keyword")
    quick_filter = st.radio("Quick filters", ["Today", "Upcoming", "Completed"], horizontal=True)

    pending_tasks = filter_tasks(get_tasks(search_text), quick_filter, completed=False)
    completed_tasks = filter_tasks(get_completed_tasks(search_text), quick_filter, completed=True)

    if quick_filter == "Completed":
        render_task_section(
            "Completed",
            completed_tasks,
            "No completed tasks match this view.",
            completed=True,
            key_prefix="home_completed",
        )
    else:
        render_task_section(
            "Pending",
            pending_tasks,
            "No pending tasks match this view.",
            key_prefix="home_pending",
        )
        render_task_section(
            "Completed",
            completed_tasks,
            "No completed tasks match this view.",
            completed=True,
            key_prefix="home_completed",
        )


if mode == "Add Task":
    st.header("Add a Task")

    quick_tab, manual_tab = st.tabs(["Quick add", "Manual"])

    with quick_tab:
        with st.form("add_quick_task_form", clear_on_submit=True):
            quick_text = st.text_input("Task", placeholder="Call mom at 6pm tomorrow high priority")
            submitted = st.form_submit_button("Add task", use_container_width=True, type="primary")

        if submitted:
            parsed_task = quick_add_task(quick_text)
            if parsed_task is None or not parsed_task["name"].strip():
                st.warning("Please add a task name first.")
            else:
                add_task(
                    parsed_task["name"],
                    parsed_task["date"],
                    parsed_task["time"],
                    parsed_task["priority"],
                    parsed_task["recurrence"],
                )
                st.success(
                    f"Added {parsed_task['name']} for {format_date(parsed_task['date'])} at "
                    f"{format_time(parsed_task['time'])}."
                )

    with manual_tab:
        with st.form("add_task_form", clear_on_submit=True):
            task_name = st.text_input("Task name", placeholder="What do you need to do?")
            task_date = choose_task_date("Date", "new_task_date")
            task_time = st.time_input("Time", value=None, step=datetime.timedelta(minutes=15))
            priority = st.selectbox("Priority", list(PRIORITIES), index=1)
            recurrence = st.selectbox("Recurrence", list(RECURRENCES), index=0)
            submitted = st.form_submit_button("Add task", use_container_width=True, type="primary")

        if submitted:
            if not task_name.strip():
                st.warning("Please add a task name first.")
            else:
                add_task(task_name.strip(), saved_date(task_date), saved_time(task_time), priority, recurrence)
                st.success(f"Added {task_name.strip()} for {format_date(task_date)}.")


if mode == "Completed Tasks":
    st.header("Completed Tasks")
    search_text = st.text_input("Search completed tasks", placeholder="Find task by keyword")
    completed_tasks = get_completed_tasks(search_text)

    left, right = st.columns(2)
    left.metric("Finished", len(completed_tasks))
    if right.button("Clear completed", disabled=not completed_tasks, use_container_width=True):
        clear_completed_tasks()
        flash("Completed tasks cleared.")
        st.rerun()

    render_task_section(
        "Completed",
        completed_tasks,
        "No completed tasks yet.",
        completed=True,
        key_prefix="completed_page",
    )


if mode == "Schedule":
    st.header("Schedule")
    st.caption("A planner view sorted by date, time, and priority.")

    search_text = st.text_input("Search schedule", placeholder="Find task by keyword")
    start_date = st.date_input("Start date", value=datetime.date.today())
    days_to_show = st.slider("Days to show", min_value=1, max_value=30, value=7)
    include_completed = st.checkbox("Include completed tasks", value=True)

    end_date = start_date + datetime.timedelta(days=days_to_show - 1)
    pending_schedule = [
        task
        for task in get_tasks(search_text)
        if start_date <= parse_date(task.get("date")) <= end_date
    ]
    completed_schedule = [
        task
        for task in get_completed_tasks(search_text)
        if include_completed and start_date <= parse_date(task.get("date")) <= end_date
    ]

    pending_by_day = grouped_by_date(pending_schedule)
    completed_by_day = grouped_by_date(completed_schedule)
    shown_days = sorted(set(pending_by_day) | set(completed_by_day))

    if not shown_days:
        st.info("No tasks found in this date range.")
    else:
        for day in shown_days:
            st.subheader(format_date(day))
            if pending_by_day.get(day):
                st.caption("Pending")
                for task in pending_by_day[day]:
                    render_pending_task(task, f"schedule_pending_{day.isoformat()}")
            if include_completed and completed_by_day.get(day):
                st.caption("Completed")
                for task in completed_by_day[day]:
                    render_completed_task(task, f"schedule_completed_{day.isoformat()}")


if mode == "Schedule Planner":
    st.header("Schedule Planner")
    st.caption("Build a day plan, then add the generated blocks to your task list.")

    plan_date = st.date_input("Plan date", value=datetime.date.today())

    left, middle, right = st.columns(3)
    with left:
        wake_up_time = st.time_input("Wake up", value=datetime.time(7, 0), step=datetime.timedelta(minutes=15))
    with middle:
        sleep_time_start = st.time_input("Sleep", value=datetime.time(22, 0), step=datetime.timedelta(minutes=15))
    with right:
        nap_time = st.time_input("Nap", value=None, step=datetime.timedelta(minutes=15))

    left, middle, right = st.columns(3)
    with left:
        school_start = st.time_input("School/work start", value=datetime.time(9, 0), step=datetime.timedelta(minutes=15))
    with middle:
        school_end = st.time_input("School/work end", value=datetime.time(17, 0), step=datetime.timedelta(minutes=15))
        work_priority = st.selectbox("Work/study priority", list(PRIORITIES), index=1)
    with right:
        commute_time = st.slider("Commute minutes", min_value=0, max_value=120, value=30, step=5)
        breaks = st.multiselect("Breaks", ["Morning Break", "Lunch Break", "Afternoon Break"])

    left, middle, right = st.columns(3)
    with left:
        exercise_time = st.time_input("Exercise time", value=None, step=datetime.timedelta(minutes=15))
    with middle:
        exercise_duration = st.slider("Exercise minutes", min_value=0, max_value=180, value=30, step=5)
    with right:
        exercise_type = st.selectbox("Exercise type", ["Cardio", "Strength", "Yoga", "Sports", "Walking", "Other"])

    left, middle, right = st.columns(3)
    with left:
        breakfast_time = st.time_input("Breakfast", value=datetime.time(8, 0), step=datetime.timedelta(minutes=15))
    with middle:
        lunch_time = st.time_input("Lunch", value=datetime.time(12, 0), step=datetime.timedelta(minutes=15))
    with right:
        dinner_time = st.time_input("Dinner", value=datetime.time(19, 0), step=datetime.timedelta(minutes=15))

    meal_prep_time = st.slider("Meal prep minutes", min_value=0, max_value=120, value=30, step=5)

    left, middle, right = st.columns(3)
    with left:
        personal_tasks = st.text_area("Personal tasks", placeholder="Laundry, email adviser, clean room")
    with middle:
        break_time = st.time_input("Mindfulness/break", value=None, step=datetime.timedelta(minutes=15))
    with right:
        social_time = st.time_input("Social time", value=None, step=datetime.timedelta(minutes=15))

    left, middle, right = st.columns(3)
    with left:
        focus_duration = st.slider("Focus block minutes", min_value=15, max_value=120, value=45, step=5)
    with middle:
        buffer_time = st.slider("Buffer minutes", min_value=0, max_value=30, value=10, step=5)
    with right:
        flexibility = st.select_slider("Flexibility", ["Strict", "Moderate", "Flexible"])

    learning_goals = st.text_area("Learning goals", placeholder="Biology review, Python practice")
    energy_levels = st.selectbox("Energy", ["Morning Person", "Evening Person", "Neutral", "Night Owl"])

    st.divider()
    if st.button("Generate schedule", use_container_width=True, type="primary"):
        with st.spinner("Building your schedule..."):
            # i need this many to make a perfect plan.
            plan_rows = build_local_plan(
                wake_up_time,
                sleep_time_start,
                nap_time,
                school_start,
                school_end,
                commute_time,
                breaks,
                exercise_time,
                exercise_duration,
                exercise_type,
                breakfast_time,
                lunch_time,
                dinner_time,
                meal_prep_time,
                personal_tasks,
                break_time,
                social_time,
                focus_duration,
                buffer_time,
                learning_goals,
                energy_levels,
                work_priority,
                flexibility,
            )
            generated_plan = generate_basic_plan(
                wake_up_time,
                sleep_time_start,
                nap_time,
                school_start,
                school_end,
                commute_time,
                breaks,
                exercise_time,
                exercise_duration,
                exercise_type,
                breakfast_time,
                lunch_time,
                dinner_time,
                meal_prep_time,
                personal_tasks,
                break_time,
                social_time,
                focus_duration,
                buffer_time,
                learning_goals,
                energy_levels,
                work_priority,
                flexibility,
            )

        st.session_state.generated_plan = generated_plan
        st.session_state.generated_tasks = [
            {
                "name": row["activity"],
                "date": saved_date(plan_date),
                "time": row["time"],
                "priority": row["priority"],
                "recurrence": "None",
            }
            for row in plan_rows
        ]

    if st.session_state.get("generated_plan"):
        st.subheader("Generated Schedule")
        st.markdown(st.session_state.generated_plan)

        if st.button("Add generated schedule to tasks", use_container_width=True):
            added = add_many_tasks(st.session_state.get("generated_tasks", []))
            flash(f"Added {added} schedule blocks to your tasks.")
            del st.session_state.generated_plan
            del st.session_state.generated_tasks
            st.rerun()

 