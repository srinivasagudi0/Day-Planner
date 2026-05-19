from datetime import date, datetime, time, timedelta
import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def _time_text(value):
    if value is None:
        return "Anytime"
    if isinstance(value, time):
        return value.strftime("%I:%M %p").lstrip("0")
    try:
        parsed = time.fromisoformat(str(value))
        return parsed.strftime("%I:%M %p").lstrip("0")
    except ValueError:
        return str(value)


def _time_key(value):
    if value is None:
        return "99:99"
    if isinstance(value, time):
        return value.isoformat(timespec="minutes")
    return str(value)


def _saved_time(value):
    if value is None:
        return None
    if isinstance(value, time):
        return value.isoformat(timespec="minutes")
    return str(value)


def _add_minutes(start_time, minutes):
    if start_time is None:
        return None
    fake_day = datetime.combine(date.today(), start_time)
    return (fake_day + timedelta(minutes=minutes)).time().replace(second=0, microsecond=0)


def _split_items(raw_text):
    if not raw_text:
        return []
    pieces = raw_text.replace("\n", ",").split(",")
    return [piece.strip() for piece in pieces if piece.strip()]


def _add_row(rows, time_value, activity, duration, notes="", priority="Medium"):
    if not activity:
        return
    rows.append(
        {
            "time": _saved_time(time_value),
            "activity": activity,
            "duration": duration,
            "notes": notes,
            "priority": priority if priority in PRIORITY_ORDER else "Medium",
        }
    )


def build_local_plan(
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
    work_priority="Medium",
    flexibility="Moderate",
):
    rows = []

    _add_row(rows, wake_up_time, "Wake up", 15, "Start the day cleanly.", "Medium")
    _add_row(rows, breakfast_time, "Breakfast", 30, "Leave room for getting ready.", "Medium")

    if commute_time and school_start:
        _add_row(
            rows,
            _add_minutes(school_start, -commute_time),
            "Commute",
            commute_time,
            "Travel time before school or work.",
            "Medium",
        )

    if school_start and school_end:
        start = datetime.combine(date.today(), school_start)
        end = datetime.combine(date.today(), school_end)
        duration = max(0, int((end - start).total_seconds() / 60))
        _add_row(rows, school_start, "School / work block", duration, f"{flexibility.lower()} plan.", work_priority)

    for break_name in breaks or []:
        default_time = _add_minutes(school_start, 120) if "Morning" in break_name else _add_minutes(school_end, -90)
        duration = 15 if "Lunch" not in break_name else 30
        _add_row(rows, default_time, break_name, duration, "Protect this pause.", "Low")

    _add_row(rows, lunch_time, "Lunch", 30, "Step away from work if you can.", "Medium")

    if nap_time:
        _add_row(rows, nap_time, "Nap", 25, "Keep it short enough to wake up steady.", "Low")

    if exercise_time and exercise_duration:
        _add_row(rows, exercise_time, f"{exercise_type} exercise", exercise_duration, "Planned movement.", "Medium")

    if meal_prep_time:
        prep_time = _add_minutes(dinner_time, -meal_prep_time) if dinner_time else None
        _add_row(rows, prep_time, "Meal prep", meal_prep_time, "Set up dinner before the evening gets crowded.", "Low")

    _add_row(rows, dinner_time, "Dinner", 30, "Eat before the late-day tasks.", "Medium")
    _add_row(rows, break_time, "Mindfulness / break", 15, "Reset attention.", "Low")
    _add_row(rows, social_time, "Social time", 30, "Keep time for people.", "Low")

    personal_start = _add_minutes(school_end, max(buffer_time, 15)) if school_end else _add_minutes(dinner_time, 45)
    for index, task in enumerate(_split_items(personal_tasks)):
        _add_row(
            rows,
            _add_minutes(personal_start, index * max(focus_duration, 30)),
            task,
            focus_duration,
            "Personal task.",
            "Medium",
        )

    learning_start = _add_minutes(personal_start, len(_split_items(personal_tasks)) * max(focus_duration, 30) + buffer_time)
    for index, goal in enumerate(_split_items(learning_goals)):
        note = "Best earlier in the day." if energy_levels == "Morning Person" else "Use a quiet focus block."
        _add_row(
            rows,
            _add_minutes(learning_start, index * max(focus_duration, 30)),
            goal,
            focus_duration,
            note,
            "High",
        )

    _add_row(rows, sleep_time_start, "Sleep", 480, "End the day on purpose.", "High")

    return sorted(rows, key=lambda row: (_time_key(row["time"]), PRIORITY_ORDER.get(row["priority"], 3)))


def render_markdown_plan(rows):
    lines = ["| Time | Activity | Duration | Notes |", "| --- | --- | ---: | --- |"]
    for row in rows:
        lines.append(
            f"| {_time_text(row['time'])} | {row['activity']} | {row['duration']} min | {row['notes']} |"
        )
    return "\n".join(lines)


def generate_basic_plan(
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
    work_priority="Medium",
    flexibility="Moderate",
):
    local_rows = build_local_plan(
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

    if OpenAI is None or os.getenv("OPENAI_API_KEY") is None:
        return render_markdown_plan(local_rows)

    prompt = f"""
Create a practical daily plan for a student. Keep the schedule realistic and return only a markdown table with these columns:
Time, Activity, Duration, Notes.

Seed schedule:
{render_markdown_plan(local_rows)}
"""

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You write clear, practical student schedules. Keep the output concise and table-only.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception:
        return render_markdown_plan(local_rows)
