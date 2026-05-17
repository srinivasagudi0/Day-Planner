import streamlit as st
import datetime

# i have a basic idea of what i want to do with this app, but i need to figure out how to make this really really helpful and get. apporved.

st.title("DayMap")

st.caption("A tool to help you plan your day and stay organized.")

today = datetime.date.today()

left, right = st.columns(2)

with left:
    st.header("Today's Date")
    st.write(today)
with right:
    st.header("Your Schedule")
    st.write("You can add your schedule here.")