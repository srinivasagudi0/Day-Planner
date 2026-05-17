from openai import OpenAI
import os

def generate_basic_plan(
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
        ):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""    Create a daily plan for a student based on the following parameters:
    - Wake-up time: {wake_up_time}
    - Sleep time start: {sleep_time_start}
    - Nap time: {nap_time}
    - School start: {school_start}
    - School end: {school_end}
    - Commute time: {commute_time}
    - Breaks: {breaks}
    - Exercise time: {exrsice_time}
    - Exercise duration: {exercise_duration}
    - Exercise type: {exercise_type}
    - Breakfast time: {breakfast_time}
    - Lunch time: {lunch_time}
    - Dinner time: {dinner_time}
    - Meal prep time: {meal_prep_time}
    - Personal tasks: {personal_tasks}
    - Break time: {break_time}
    - Social time: {social_time}
    - Focus duration: {focus_duration}
    - Buffer time: {buffer_time}
    - Learning goals: {learning_goals}
    - Energy levels: {energy_levels}"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that creates daily plans for students based on their preferences and schedules.Return a perfect table in markdown format with the following columns: Time, Activity, Duration, and Notes. Make sure to include all the activities mentioned in the prompt and organize them in a logical order throughout the day. Ensure that the total duration of activities does not exceed 24 hours and that there are appropriate breaks and buffer times included."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # forgot to return the response conten
    return response.choices[0].message.content