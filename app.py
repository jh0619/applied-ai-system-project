from pawpal_system import Pet, Owner, Task, Scheduler
from datetime import datetime, date
import streamlit as st
from ai_client import AIClientError
from task_parser import TaskParseError, parse_tasks_from_text

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Initialize session state objects if they don't exist
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", 120, ["efficient", "pet-friendly"])

if not st.session_state.owner.pets:
    st.session_state.owner.add_pet(Pet("Mochi", "dog", 2, "Friendly and energetic"))

if "selected_pet_name" not in st.session_state:
    st.session_state.selected_pet_name = ""

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()


def parse_task_datetime_with_date_flag(
    time_value: str,
) -> tuple[datetime, bool] | None:
    """Parse task time and return (datetime, has_explicit_date)."""
    if not time_value:
        return None

    formats = [
        ("%Y-%m-%d %I:%M %p", True),
        ("%Y-%m-%d %H:%M", True),
        ("%I:%M %p", False),
        ("%H:%M", False),
    ]
    for fmt, has_date in formats:
        try:
            return datetime.strptime(time_value, fmt), has_date
        except ValueError:
            continue
    return None


def extract_task_date(time_value: str) -> date | None:
    """Return explicit task date when present in task time string."""
    parsed = parse_task_datetime_with_date_flag(time_value)
    if parsed is None:
        return None

    parsed_datetime, has_explicit_date = parsed
    if not has_explicit_date:
        return None
    return parsed_datetime.date()


def format_scheduled_datetime(task_date: date, task_time: datetime.time) -> str:
    """Format date/time values to the scheduler's stored datetime string."""
    return datetime.combine(task_date, task_time).strftime("%Y-%m-%d %I:%M %p")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
preferences_text = st.text_input(
    "Owner preferences (comma-separated)",
    value=", ".join(st.session_state.owner.preferences),
)
available_time = st.number_input("Available time (minutes)", min_value=1, max_value=480, value=120)

st.session_state.owner.name = owner_name
st.session_state.owner.update_availability(int(available_time))
parsed_preferences = [
    item.strip()
    for item in preferences_text.split(",")
    if item.strip()
]
st.session_state.owner.set_preferences(parsed_preferences)

if not st.session_state.selected_pet_name:
    st.session_state.selected_pet_name = st.session_state.owner.pets[0].name

pet_names = [pet.name for pet in st.session_state.owner.pets]
selected_pet_name = st.selectbox(
    "Select pet",
    options=pet_names,
    index=pet_names.index(st.session_state.selected_pet_name) if st.session_state.selected_pet_name in pet_names else 0,
)
st.session_state.selected_pet_name = selected_pet_name
selected_pet = next(
    pet for pet in st.session_state.owner.pets if pet.name == st.session_state.selected_pet_name
)

st.markdown("#### Edit Selected Pet")
pet_name = st.text_input("Pet name", value=selected_pet.name)
species_options = ["dog", "cat", "other"]
species = st.selectbox(
    "Species",
    species_options,
    index=species_options.index(selected_pet.species) if selected_pet.species in species_options else len(species_options) - 1,
)
age = st.number_input("Pet age (years)", min_value=0, max_value=40, value=int(selected_pet.age))
notes = st.text_area("Pet notes", value=selected_pet.notes)

selected_pet.update_info(
    name=pet_name,
    species=species,
    age=int(age),
    notes=notes,
)
st.session_state.selected_pet_name = selected_pet.name

if st.button("Remove selected pet"):
    if len(st.session_state.owner.pets) == 1:
        st.warning("At least one pet is required.")
    else:
        removed_tasks = list(selected_pet.tasks)
        st.session_state.owner.remove_pet(selected_pet)
        st.session_state.scheduler.tasks = [
            task for task in st.session_state.scheduler.tasks if task not in removed_tasks
        ]
        st.session_state.scheduler.generated_plan = [
            task for task in st.session_state.scheduler.generated_plan if task not in removed_tasks
        ]
        st.session_state.selected_pet_name = st.session_state.owner.pets[0].name
        st.success("Selected pet removed.")
        st.rerun()

st.markdown("#### Add Another Pet")
new_pet_name = st.text_input("New pet name", value="")
new_pet_species = st.selectbox("New pet species", species_options, key="new_pet_species")
new_pet_age = st.number_input("New pet age (years)", min_value=0, max_value=40, value=1)
new_pet_notes = st.text_input("New pet notes", value="")

if st.button("Add pet"):
    normalized_new_name = new_pet_name.strip()
    existing_names = {pet.name.lower() for pet in st.session_state.owner.pets}
    if not normalized_new_name:
        st.warning("Please enter a name for the new pet.")
    elif normalized_new_name.lower() in existing_names:
        st.warning("A pet with that name already exists.")
    else:
        created_pet = Pet(
            name=normalized_new_name,
            species=new_pet_species,
            age=int(new_pet_age),
            notes=new_pet_notes,
        )
        st.session_state.owner.add_pet(created_pet)
        st.session_state.selected_pet_name = created_pet.name
        st.success(f"Added pet: {created_pet.name}")
        st.rerun()

with st.expander("Current Pet Profile", expanded=False):
    st.text(selected_pet.get_profile())

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

with st.expander("✨ Add tasks with AI (natural language)", expanded=True):
    st.caption(
        "Describe what you want to do in plain English. "
        "Example: *Tomorrow 8am walk Mochi for 30 min, then feed him at 8:30, high priority.*"
    )
    ai_input = st.text_area(
        "Describe tasks",
        key="ai_task_input",
        placeholder="e.g. Walk Mochi tomorrow morning at 8 for 30 minutes, high priority.",
        height=80,
    )
    if st.button("🪄 Parse with AI"):
        if not ai_input.strip():
            st.warning("Please enter a description first.")
        else:
            pet_names_list = [pet.name for pet in st.session_state.owner.pets]
            with st.spinner("Asking Gemini to parse your request..."):
                try:
                    parsed = parse_tasks_from_text(ai_input, pet_names_list)
                    st.session_state["ai_parsed_tasks"] = parsed
                    st.success(f"Parsed {len(parsed)} task(s). Review below and confirm.")
                except TaskParseError as exc:
                    st.error(f"Could not parse your request: {exc}")
                except AIClientError as exc:
                    st.error(f"AI service error: {exc}")

    # Review & confirm step
    if st.session_state.get("ai_parsed_tasks"):
        st.markdown("**Review parsed tasks:**")
        st.table(st.session_state["ai_parsed_tasks"])

        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button("✅ Add all to schedule"):
                added = 0
                skipped = 0
                for task_dict in st.session_state["ai_parsed_tasks"]:
                    target_pet_name = task_dict.get("pet_name") or selected_pet.name
                    target_pet = next(
                        (p for p in st.session_state.owner.pets
                         if p.name == target_pet_name),
                        selected_pet,
                    )
                    new_task = Task(
                        title=task_dict["title"],
                        duration=task_dict["duration"],
                        priority=task_dict["priority"],
                        category=task_dict["category"],
                        description=task_dict.get("description", ""),
                        time=task_dict["time"],
                        frequency=task_dict["frequency"],
                    )
                    target_pet.tasks.append(new_task)
                    st.session_state.scheduler.add_task(new_task)
                    added += 1
                st.session_state.pop("ai_parsed_tasks", None)
                st.success(f"Added {added} task(s) to the schedule.")
                st.rerun()
        with cancel_col:
            if st.button("❌ Discard"):
                st.session_state.pop("ai_parsed_tasks", None)
                st.rerun()

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5, col6, col7 = st.columns([2, 2, 2, 1])
with col4:
    category = st.text_input("Category", value="exercise")
with col5:
    task_date = st.date_input("Date", value=date.today())
with col6:
    task_time = st.time_input(
        "Time",
        value=datetime.strptime("8:00 AM", "%I:%M %p").time(),
        step=60,
    )
with col7:
    frequency_choice = st.selectbox(
        "Frequency",
        ["none", "daily", "weekly"],
        index=0,
    )

if st.button("Add task"):
    new_task = Task(
        title=task_title,
        duration=int(duration),
        priority=priority,
        category=category,
        time=format_scheduled_datetime(task_date, task_time),
        frequency="" if frequency_choice == "none" else frequency_choice,
    )
    new_task_minutes = Scheduler._time_to_minutes(new_task.time)
    conflicting_tasks = []

    if new_task_minutes is not None:
        for existing_task in st.session_state.owner.get_all_tasks():
            existing_task_minutes = Scheduler._time_to_minutes(existing_task.time)
            if (
                existing_task_minutes is not None
                and existing_task_minutes == new_task_minutes
            ):
                conflicting_tasks.append(existing_task)

    if conflicting_tasks:
        existing_task_pet_map = st.session_state.owner.get_task_pet_map()
        all_pet_names = [
            existing_task_pet_map.get(id(task), "Unknown Pet")
            for task in conflicting_tasks
        ] + [selected_pet.name]
        conflict_scope = "same pet" if len(set(all_pet_names)) == 1 else "different pets"

        conflict_details = ", ".join(
            f"{task.title} ({existing_task_pet_map.get(id(task), 'Unknown Pet')})"
            for task in conflicting_tasks
        )
        st.warning(
            f"Warning: Time conflict at {new_task.time} ({conflict_scope}): "
            f"{new_task.title} ({selected_pet.name}), {conflict_details}."
        )
    else:
        selected_pet.tasks.append(new_task)
        st.session_state.scheduler.add_task(new_task)

all_tasks = st.session_state.owner.get_all_tasks()
pending_tasks = st.session_state.owner.filter_tasks(is_completed=False)
completed_tasks = st.session_state.owner.filter_tasks(is_completed=True)
task_pet_map = st.session_state.owner.get_task_pet_map()

if all_tasks:
    st.success(
        f"Loaded {len(all_tasks)} task(s): "
        f"{len(pending_tasks)} pending, {len(completed_tasks)} completed."
    )

    task_view = st.selectbox(
        "Filter tasks by status",
        ["All", "Pending", "Completed"],
        index=0,
    )
    if task_view == "Pending":
        tasks_to_show = pending_tasks
    elif task_view == "Completed":
        tasks_to_show = completed_tasks
    else:
        tasks_to_show = all_tasks

    selected_plan_date = st.session_state.get("plan_date", date.today())
    filter_to_plan_date = st.checkbox(
        "Show only tasks for selected plan date",
        value=True,
    )
    if filter_to_plan_date:
        tasks_to_show = [
            task
            for task in tasks_to_show
            if (
                extract_task_date(task.time) is None
                or extract_task_date(task.time) == selected_plan_date
            )
        ]
        st.caption(
            "Task table filtered to selected plan date "
            f"({selected_plan_date.isoformat()}) plus tasks with no explicit date."
        )

    priority_order = {"high": 1, "medium": 2, "low": 3}
    sorted_tasks = sorted(
        tasks_to_show,
        key=lambda t: (priority_order.get(t.priority, 4), t.duration, t.title.lower()),
    )

    task_options = {
        id(task): (
            f"{task.title} ({task.time or 'No time'}) — "
            f"{task_pet_map.get(id(task), 'Unknown Pet')}"
        )
        for task in all_tasks
    }

    st.markdown("#### Edit Existing Task")
    task_id_to_edit = st.selectbox(
        "Select task to edit",
        options=list(task_options.keys()),
        format_func=lambda task_id: task_options[task_id],
        key="task_id_to_edit",
    )
    task_to_edit = next(
        task for task in all_tasks if id(task) == task_id_to_edit
    )

    with st.form(key=f"edit_task_form_{task_id_to_edit}"):
        was_completed_before = task_to_edit.is_completed
        edit_title = st.text_input("Edit title", value=task_to_edit.title)
        edit_duration = st.number_input(
            "Edit duration (minutes)",
            min_value=1,
            max_value=240,
            value=int(task_to_edit.duration),
        )
        edit_priority = st.selectbox(
            "Edit priority",
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(task_to_edit.priority)
            if task_to_edit.priority in ["low", "medium", "high"]
            else 1,
        )
        edit_category = st.text_input("Edit category", value=task_to_edit.category)
        parsed_time = parse_task_datetime_with_date_flag(task_to_edit.time)
        if parsed_time is None:
            default_edit_date = date.today()
            default_edit_time = datetime.strptime("8:00 AM", "%I:%M %p").time()
        else:
            parsed_datetime, has_explicit_date = parsed_time
            default_edit_date = (
                parsed_datetime.date() if has_explicit_date else date.today()
            )
            default_edit_time = parsed_datetime.time()

        edit_date = st.date_input(
            "Edit date",
            value=default_edit_date,
            key=f"edit_date_{task_id_to_edit}",
        )
        edit_time = st.time_input(
            "Edit time",
            value=default_edit_time,
            step=60,
            key=f"edit_time_{task_id_to_edit}",
        )
        edit_description = st.text_area(
            "Edit description",
            value=task_to_edit.description,
        )
        frequency_options = ["none", "daily", "weekly"]
        current_frequency = task_to_edit.frequency.strip().lower()
        selected_frequency = (
            current_frequency if current_frequency in {"daily", "weekly"}
            else "none"
        )
        edit_frequency_choice = st.selectbox(
            "Edit frequency",
            options=frequency_options,
            index=frequency_options.index(selected_frequency),
        )
        edit_is_completed = st.checkbox(
            "Mark as completed",
            value=task_to_edit.is_completed,
        )

        if st.form_submit_button("Save task changes"):
            task_to_edit.update_task(
                title=edit_title,
                duration=int(edit_duration),
                priority=edit_priority,
                category=edit_category,
                description=edit_description,
                time=format_scheduled_datetime(edit_date, edit_time),
                frequency=(
                    "" if edit_frequency_choice == "none"
                    else edit_frequency_choice
                ),
            )

            if edit_is_completed and not was_completed_before:
                next_task = st.session_state.scheduler.mark_task_complete(
                    task_to_edit
                )
                if next_task is not None:
                    owner_pet = next(
                        (
                            pet
                            for pet in st.session_state.owner.pets
                            if task_to_edit in pet.tasks
                        ),
                        None,
                    )
                    if owner_pet is not None:
                        owner_pet.tasks.append(next_task)
                    st.success(
                        "Task updated and next recurring occurrence created."
                    )
                else:
                    st.success("Task updated and marked completed.")
            else:
                task_to_edit.is_completed = edit_is_completed
                st.success("Task updated.")
            st.rerun()

    task_id_to_remove = st.selectbox(
        "Select task to remove",
        options=list(task_options.keys()),
        format_func=lambda task_id: task_options[task_id],
    )

    if st.button("Remove task"):
        remove_task_id = task_id_to_remove
        for pet in st.session_state.owner.pets:
            pet.tasks = [task for task in pet.tasks if id(task) != remove_task_id]
        st.session_state.scheduler.tasks = [
            task for task in st.session_state.scheduler.tasks if id(task) != remove_task_id
        ]
        st.session_state.scheduler.generated_plan = [
            task for task in st.session_state.scheduler.generated_plan if id(task) != remove_task_id
        ]
        st.success("Task removed.")
        st.rerun()

    st.write("Current tasks:")
    st.table(
        [
            {
                "title": t.title,
                "pet": task_pet_map.get(id(t), "Unknown Pet"),
                "duration": t.duration,
                "priority": t.priority,
                "category": t.category,
                "time": t.time,
                "status": "Completed" if t.is_completed else "Pending",
            }
            for t in sorted_tasks
        ]
    )

    conflict_warnings = st.session_state.scheduler.detect_time_conflicts(
        tasks=all_tasks,
        task_pet_map=task_pet_map,
    )
    for warning in conflict_warnings:
        st.warning(warning)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button uses your scheduling logic to build and explain a plan.")

plan_date = st.date_input(
    "Plan date",
    value=date.today(),
    key="plan_date",
)

if st.button("Generate schedule"):
    generated_plan = st.session_state.scheduler.generate_plan(
        available_time=st.session_state.owner.available_time,
        preferences=st.session_state.owner.preferences,
        plan_date=plan_date,
    )
    if generated_plan:
        total_plan_time = sum(task.duration for task in generated_plan)
        st.success(
            f"Schedule generated for {plan_date.isoformat()}: "
            f"{len(generated_plan)} task(s), "
            f"{total_plan_time}/{st.session_state.owner.available_time} minutes used."
        )
    else:
        st.warning(
            f"No tasks scheduled for {plan_date.isoformat()} fit the current available time."
        )

    # --- AI-powered explanation with fallback to deterministic text ---
    if generated_plan:
        task_pet_map = st.session_state.owner.get_task_pet_map()
        with st.spinner("Asking Gemini to explain today's plan..."):
            try:
                from plan_explainer import explain_plan_with_ai
                ai_explanation = explain_plan_with_ai(
                    plan=generated_plan,
                    owner=st.session_state.owner,
                    task_pet_map=task_pet_map,
                )
                st.markdown("#### 🧠 AI Explanation")
                st.info(ai_explanation)
            except AIClientError as exc:
                st.warning(
                    f"AI explanation unavailable ({exc}). "
                    "Falling back to rule-based summary."
                )
                st.text(
                    st.session_state.scheduler.explain_plan(
                        task_pet_map=task_pet_map
                    )
                )

        with st.expander("📋 Rule-based breakdown", expanded=False):
            st.text(
                st.session_state.scheduler.explain_plan(
                    task_pet_map=task_pet_map
                )
            )
    else:
        st.text(
            st.session_state.scheduler.explain_plan(
                task_pet_map=st.session_state.owner.get_task_pet_map()
            )
        )

    sorted_plan = st.session_state.scheduler.get_plan_by_time()
    if sorted_plan:
        plan_task_pet_map = st.session_state.owner.get_task_pet_map()
        st.write("Scheduled tasks (chronological):")
        st.table(
            [
                {
                    "title": task.title,
                    "pet": plan_task_pet_map.get(id(task), "Unknown Pet"),
                    "time": task.time,
                    "duration": task.duration,
                    "priority": task.priority,
                }
                for task in sorted_plan
            ]
        )

        schedule_conflicts = st.session_state.scheduler.detect_time_conflicts(
            tasks=sorted_plan,
            task_pet_map=st.session_state.owner.get_task_pet_map(),
        )
        for warning in schedule_conflicts:
            st.warning(warning)
    else:
        st.info("No tasks fit the current available time.")
