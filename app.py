import streamlit as st
import datetime

# i have a basic idea of what i want to do with this app, but i need to figure out how to make this really really helpful and get. apporved.

st.title("DayMap")
st.caption("A tool to help you plan your day and stay organized.")

st.sidebar.header("DayMap Modes")
mode = st.sidebar.selectbox("Select Mode", ["Home", "Add Task"])

if mode == "Home":
    today = datetime.date.today()

    left, right = st.columns(2)

    with left:
        st.header("Today's Date")
        st.write(today)
    with right:
        st.header("Your Schedule")
        st.write("You can add your schedule here.")

    st.header("\nWelcome to DayMap!")
    st.write("Make your schedule for today by using the sidebar to add tasks and events. You can also use the calendar to select a different date and plan for that day.")

if mode == "Add Task":
    st.header("Add a Task")
    task_name = st.text_input("Task Name")
    task_time = st.time_input("Task Time # optional")
    if st.button("Add Task"):
        if task_name and task_time:
            st.write(f"Task '{task_name} was added at {task_time}.")
        elif task_name:
            st.write(f"Task '{task_name}' was added.")
        else:
            st.warning("Please add task name atleast.")
