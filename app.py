import datetime

import streamlit as st

from app_db import (
    add_task,
    clear_completed_tasks,
    delete_completed_task,
    delete_task,
    edit_task,
    get_completed_tasks,
    get_tasks,
    init_db,
    restore_completed_task,
)
from Planner import generate_basic_plan

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


def add_minutes(start_time, minutes):
    # datetime makes this less annoying
    fake_day = datetime.datetime.combine(datetime.date.today(), start_time)
    return (fake_day + datetime.timedelta(minutes=minutes)).time().replace(second=0, microsecond=0)


def put_task_in_plan(plan, name, time_value):
    if time_value:
        plan.append((name, saved_time(time_value)))


def add_list_tasks(plan, raw_text, first_time, gap_minutes):
    if not raw_text:
        return
    pieces = [x.strip() for x in raw_text.replace("\n", ",").split(",")]
    pieces = [x for x in pieces if x]
    for index, thing in enumerate(pieces):
        plan.append((thing, saved_time(add_minutes(first_time, gap_minutes * index))))


##############APPPP#################################################################### 
st.title("DayMap")
st.caption("Plan the tasks already on your mind and keep today's schedule visible.")

if st.session_state.pop("task_updated", False):
    st.success("Task updated.")

tasks = get_tasks()

st.sidebar.header("DayMap")
mode = st.sidebar.selectbox("Mode", ["Home", "Add Task", "Completed Tasks", "Schedule", "Schedule Planner"])

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
    left, right = st.columns(2)
    left.metric("Finished", len(completed_tasks))
    if right.button("Clear completed", disabled=not completed_tasks, use_container_width=True):
        clear_completed_tasks()
        st.success("Completed tasks cleared.")
        st.rerun()

    if completed_tasks:
        for task_id, task_name, task_time in completed_tasks:
            task_container = st.container(border=True)
            time_column, task_column, buttons_column = task_container.columns([1, 3, 2])
            time_column.markdown(f"**{format_time(task_time)}**")
            task_column.markdown(task_name)
            restore_clicked = buttons_column.button("Restore", key=f"restore_done_{task_id}", use_container_width=True)
            delete_clicked = buttons_column.button("Delete", key=f"delete_done_{task_id}", use_container_width=True)

            if restore_clicked:
                restore_completed_task(task_id)
                st.success("Task moved back to schedule.")
                st.rerun()

            if delete_clicked:
                delete_completed_task(task_id)
                st.success("Completed task deleted.")
                st.rerun()
    else:
        st.info("No completed tasks yet.")

if mode == "Schedule":
    st.header("Schedule")
    st.caption("Same tasks as Home, just more like a planner list.")

    if tasks:
        for task_id, task_name, task_time in tasks:
            status = task_status(task_time)
            st.markdown(f"- **{format_time(task_time)}** - {task_name} - {status}")
    else:
        st.info("No tasks yet. Generate a plan or add a task.")

if mode == "Schedule Planner":
    st.header("Schedule Planner")
    #time and sleep
    left, middle, right = st.columns(3)
    with left:
        wake_up_time = st.time_input("Wake Up Time", value=datetime.time(7, 0), step=datetime.timedelta(minutes=15))
    with middle:
        sleep_time_start = st.time_input("Sleep Time Start", value=datetime.time(22, 0), step=datetime.timedelta(minutes=15))
    with right:
        nap_time = st.time_input("Nap Time (optional)", value=None, step=datetime.timedelta(minutes=15))
    
    # work and study
    left, middle, right = st.columns(3)
    with left:
        school_start = st.time_input("School/Work Start Time", value=datetime.time(9, 0), step=datetime.timedelta(minutes=15))
    with middle:
        school_end = st.time_input("School/Work End Time", value=datetime.time(17, 0), step=datetime.timedelta(minutes=15))
        work_priority = st.selectbox("Work/Study Priority", ["Low", "Medium", "High"])
    with right:
        commute_time = st.slider("Commute Time (minutes)", min_value=0, max_value=120, value=30, step=5)
        breaks = st.multiselect("Breaks during work/school (optional)", ["Morning Break", "Lunch Break", "Afternoon Break"])

    # helth and fitness
    left, middle, right = st.columns(3)
    with left:
        exrsice_time = st.time_input("Exercise Time [preferred]", value=None, step=datetime.timedelta(minutes=15))
    with middle:
        exercise_duration = st.slider("Exercise Duration (minutes)", min_value=0, max_value=180, value=30, step=5)
    with right:
        exercise_type = st.selectbox("Exercise Type", ["Cardio", "Strength", "Yoga", "Sports", "Walking", "Other"])
    
    # meals
    left, middle, right = st.columns(3)
    with left:
        breakfast_time = st.time_input("Breakfast Time", value=datetime.time(8, 0), step=datetime.timedelta(minutes=15))
    with middle:
        lunch_time = st.time_input("Lunch Time", value=datetime.time(12, 0), step=datetime.timedelta(minutes=15))
    with right:
        dinner_time = st.time_input("Dinner Time", value=datetime.time(19, 0), step=datetime.timedelta(minutes=15))
    
    meal_prep_time = st.slider("Meal Prep Time (minutes)", min_value=0, max_value=120, value=30, step=5)

    # personal tasks
    left , middle, right = st.columns(3)
    with left:
        personal_tasks = st.text_area("Personal Tasks (optional)", placeholder="List any personal tasks you want to include, separated by commas)")
    # mindfulness and social
    with middle:
        break_time = st.time_input("Mindfulness/Break Time (optional)", value=None, step=datetime.timedelta(minutes=15))
    with right:
        social_time = st.time_input("Social Time (optional)", value=None, step=datetime.timedelta(minutes=15))
    
    # focus and flexibility
    left, middle, right = st.columns(3)
    with left:
        focus_duration = st.slider("Focus Block Duration (minutes)", min_value=15, max_value=120, value=45, step=5)
    with middle:
        buffer_time = st.slider("Buffer Time Between Tasks (minutes)", min_value=0, max_value=30, value=10, step=5)
    with right:
        flexibility = st.select_slider("Schedule Flexibility", ["Strict", "Moderate", "Flexible"])
    
    # learning and energy
    learning_goals = st.text_area("Learning Goals (optional)", placeholder="List any learning goals you have for the day, separated by commas)")
    energy_levels = st.selectbox("Energy Levels", ["Morning Person", "Evening Person", "Neutral", "Night Owl"])
    
    # generate button
    st.divider()
    if st.button("Generate My Schedule", use_container_width=True, type="primary"):
        generated_plan = generate_basic_plan(
            wake_up_time,
            sleep_time_start,
            nap_time,
            school_start,
            school_end,
            commute_time,
            breaks,
            exrsice_time,
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
            energy_levels
        )

        st.subheader("Your Generated Schedule")
        with st.spinner("Generating your schedule..."):
            st.markdown(generated_plan)

    
