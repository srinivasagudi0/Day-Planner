import datetime

import streamlit as st

from app_db import add_task, delete_task, edit_task, get_tasks, init_db, get_completed_tasks

st.set_page_config(page_title="DayMap", layout="centered")

init_db()

## deal with time formatting to make it look nice in the Ui and be stored safe in the db.
def format_date(day):
    return f"{day:%A, %B} {day.day}, {day:%Y}"


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


# task status stuff. keeping it here for now because its just display logic. WIll later refactor all this logic into a sefarate file.
def task_status(task_time):
    if not task_time:
        return "pending"

    try:
        real_time = datetime.time.fromisoformat(task_time)
    except ValueError:
        return "pending"

    now_time = datetime.datetime.now().time().replace(second=0, microsecond=0)

    if real_time < now_time:
        return "overdue"
    
    if real_time == now_time:
        return "pending"

    return "upcoming"


def status_badge(status):
    if status == "overdue":
        return ":red[overdue]"
    if status == "upcoming":
        return ":blue[upcoming]"
    return ":orange[pending]"

##############APPPP#################################################################### 
st.title("DayMap")
st.caption("Plan the tasks already on your mind and keep today's schedule visible.")

if st.session_state.pop("task_updated", False):
    st.success("Task updated.")

tasks = get_tasks()

st.sidebar.header("DayMap")
mode = st.sidebar.selectbox("Mode", ["Home", "Add Task", "Completed Tasks"])

st.sidebar.divider()
if st.sidebar.button("Clear Tasks", disabled=not tasks, use_container_width=True):
    for task in tasks:
        delete_task(task[0])

    st.sidebar.success("All tasks cleared.")
    st.rerun()

if mode == "Home":
    today = datetime.date.today()

    left, right = st.columns(2)

    with left:
        st.metric("Today", format_date(today))
   
    with right:
        st.metric("Tasks", len(tasks))

    st.header("Your Schedule")
    if tasks:
        for task_id, task_name, task_time in tasks:
            status = task_status(task_time)
            task_container = st.container(border=True)
            time_column, task_column, status_column = task_container.columns([1, 3, 1])
            time_column.markdown(f"**{format_time(task_time)}**")
            status_column.markdown(status_badge(status))
            if task_column.checkbox(task_name, key=f"done_task_{task_id}"):
                delete_task(task_id)
                st.rerun()

            with task_container.expander("Edit"):
                with st.form(f"edit_task_form_{task_id}"):
                    edited_name = st.text_input(
                        "Task Name",
                        value=task_name,
                        key=f"edit_task_name_{task_id}",
                    )
                    edited_time = st.time_input(
                        "Task Time (optional)",
                        value=editable_time(task_time),
                        step=datetime.timedelta(minutes=15),
                        key=f"edit_task_time_{task_id}",
                    )
                    saved = st.form_submit_button("Save", use_container_width=True)

                if saved:
                    if not edited_name.strip():
                        st.warning("Please add a task name first.")
                    else:
                        edit_task(task_id, edited_name.strip(), saved_time(edited_time))
                        st.session_state.task_updated = True
                        st.rerun()
            
    else:
        st.info("No tasks yet. Use Add Task in the sidebar to start your schedule.")

    st.write("Use the sidebar to add tasks. Your schedule stays saved between app sessions.")

if mode == "Add Task":
    st.header("Add a Task")
    
    with st.form("add_task_form", clear_on_submit=True):
        
        task_name = st.text_input("Task Name", placeholder="What do you need to do?")
        task_time = st.time_input(
            "Task Time (optional)",
            value=None,
            step=datetime.timedelta(minutes=15),
        )
        submitted = st.form_submit_button("Add Task", use_container_width=True)

    if submitted:

        if not task_name.strip():
            st.warning("Please add a task name first.")
        else:
            add_task(task_name, saved_time(task_time))
            if task_time:
                task_time_text = format_time(saved_time(task_time))
                st.success(f"Task '{task_name}' was added for {task_time_text}.")
            else:
                st.success(f"Task '{task_name}' was added.")

if mode == "Completed Tasks":
    st.header("Completed Tasks")
    completed_tasks = get_completed_tasks()
    for task_id, task_name, task_time in completed_tasks:
        time_text = format_time(task_time)
        st.markdown(f"- **{task_name}** at {time_text}")

if mode == "AI Planner":
    st.header("AI Planner")
    st.info("This feature is coming soon! It will help you plan your day by suggesting optimal times for your tasks based on your schedule and preferences.")