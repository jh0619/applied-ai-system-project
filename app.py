from pawpal_system import Pet, Owner, Task, Scheduler
from datetime import datetime, date
import streamlit as st
from ai_client import AIClientError
from task_parser import TaskParseError, parse_tasks_from_text

st.set_page_config(
    page_title="PawPal+ · Smart Pet Care Planner",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Custom styling ----------
st.markdown(
    """
    <style>
    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #FFE8D6 0%, #FFD4A3 50%, #FFC6A0 100%);
        padding: 2.5rem 2rem;
        border-radius: 24px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(255, 180, 120, 0.2);
    }
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        color: #6B4423;
        margin: 0;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-size: 1.4rem;
        color: #8B5A3C;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    .hero-emojis {
        font-size: 3.5rem;
        letter-spacing: 0.5rem;
        margin-bottom: 0.5rem;
    }

    /* Feature pill row */
    .feature-row {
        display: flex;
        justify-content: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 1.2rem;
    }
    .feature-pill {
        background: rgba(255, 255, 255, 0.6);
        padding: 0.55rem 1.3rem;
        border-radius: 999px;
        font-size: 1.05rem;
        color: #6B4423;
        font-weight: 500;
        backdrop-filter: blur(4px);
    }

    /* Section card styling */
    .section-card {
        background: #FFFBF5;
        padding: 1.6rem 1.8rem;
        border-radius: 18px;
        margin-bottom: 1.5rem;
        border: 1px solid #F3E2C7;
        box-shadow: 0 2px 12px rgba(180, 120, 80, 0.06);
    }

    /* Step number badges in section titles */
    .step-badge {
        display: inline-block;
        background: linear-gradient(135deg, #FFB085 0%, #FF9B6A 100%);
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        text-align: center;
        line-height: 36px;
        font-weight: 700;
        margin-right: 0.6rem;
        box-shadow: 0 2px 6px rgba(255, 140, 90, 0.3);
    }

    /* Global font size bump */
    html, body, [class*="css"] {
        font-size: 17px;
    }
    .stMarkdown p, .stMarkdown li {
        font-size: 1.05rem;
        line-height: 1.7;
    }
    h1 { font-size: 2.2rem; }
    h2 { font-size: 1.8rem; }
    h3 { font-size: 1.4rem; }
    h4 { font-size: 1.2rem; }

    /* Section headers */
    h2, h3 {
        color: #6B4423;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px;
        font-weight: 500;
        font-size: 1rem;
        padding: 0.5rem 1.2rem;
    }

    /* Pet profile card */
    .pet-profile-card {
        background: linear-gradient(135deg, #FFF5E8 0%, #FFE8D0 100%);
        padding: 1.5rem 1.8rem;
        border-radius: 16px;
        border: 1px solid #F3E2C7;
        margin-top: 0.5rem;
    }
    .pet-profile-row {
        display: flex;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px dashed rgba(180, 120, 80, 0.2);
        font-size: 1.05rem;
    }
    .pet-profile-row:last-child {
        border-bottom: none;
    }
    .pet-profile-label {
        min-width: 140px;
        color: #8B5A3C;
        font-weight: 600;
    }
    .pet-profile-value {
        color: #4A3020;
        font-weight: 400;
    }

    /* Plan breakdown card */
    .plan-summary-card {
        background: linear-gradient(135deg, #FFF5E8 0%, #FFEAD0 100%);
        padding: 1.5rem 1.8rem;
        border-radius: 16px;
        border: 1px solid #F3E2C7;
        margin-top: 0.5rem;
    }
    .plan-task-item {
        background: white;
        padding: 1rem 1.2rem;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        border-left: 4px solid #FF9B6A;
        box-shadow: 0 1px 4px rgba(180, 120, 80, 0.05);
    }
    .plan-task-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #6B4423;
        margin-bottom: 0.4rem;
    }
    .plan-task-meta {
        display: flex;
        gap: 1.2rem;
        font-size: 0.95rem;
        color: #8B5A3C;
        flex-wrap: wrap;
    }
    .plan-task-meta span {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
    }
    .priority-high { border-left-color: #E8705A !important; }
    .priority-medium { border-left-color: #FFB085 !important; }
    .priority-low { border-left-color: #C8D8B0 !important; }
    .plan-totals {
        text-align: right;
        font-size: 1.05rem;
        color: #6B4423;
        font-weight: 600;
        margin-top: 0.8rem;
        padding-top: 0.8rem;
        border-top: 2px dashed rgba(180, 120, 80, 0.25);
    }

    /* Divider spacing */
    hr {
        margin: 2rem 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Hero banner ----------
st.markdown(
    """
    <div class="hero">
        <div class="hero-emojis">🐕 🐾 🐈</div>
        <h1 class="hero-title">PawPal+</h1>
        <p class="hero-subtitle">Your AI-powered pet care planner — plan smarter, care better 💛</p>
        <div class="feature-row">
            <span class="feature-pill">✨ Natural-language task input</span>
            <span class="feature-pill">🧠 AI-powered explanations</span>
            <span class="feature-pill">📚 Knowledge-grounded advice</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Initialize session state ----------
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", 120, ["efficient", "pet-friendly"])

if not st.session_state.owner.pets:
    st.session_state.owner.add_pet(Pet("Mochi", "dog", 2, "Friendly and energetic"))

if "selected_pet_name" not in st.session_state:
    st.session_state.selected_pet_name = ""

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()


# ---------- Helpers ----------
def parse_task_datetime_with_date_flag(time_value: str):
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


def extract_task_date(time_value: str):
    parsed = parse_task_datetime_with_date_flag(time_value)
    if parsed is None:
        return None
    parsed_datetime, has_explicit_date = parsed
    if not has_explicit_date:
        return None
    return parsed_datetime.date()


def format_scheduled_datetime(task_date, task_time):
    return datetime.combine(task_date, task_time).strftime("%Y-%m-%d %I:%M %p")


# =====================================================================
# SECTION 1 — OWNER PROFILE
# =====================================================================
st.markdown(
    '<h2><span class="step-badge">1</span>Your Profile</h2>',
    unsafe_allow_html=True,
)
st.caption("Tell PawPal+ about yourself so we can tailor your daily plan.")

with st.container():
    col_a, col_b, col_c = st.columns([2, 3, 2])
    with col_a:
        owner_name = st.text_input("Your name", value=st.session_state.owner.name)
    with col_b:
        preferences_text = st.text_input(
            "Your preferences (comma-separated)",
            value=", ".join(st.session_state.owner.preferences),
            help="e.g. morning routine, exercise, grooming",
        )
    with col_c:
        available_time = st.number_input(
            "Available time today (minutes)",
            min_value=1, max_value=480,
            value=st.session_state.owner.available_time,
        )

    st.session_state.owner.name = owner_name
    st.session_state.owner.update_availability(int(available_time))
    parsed_preferences = [p.strip() for p in preferences_text.split(",") if p.strip()]
    st.session_state.owner.set_preferences(parsed_preferences)

st.divider()


# =====================================================================
# SECTION 2 — PETS
# =====================================================================
st.markdown(
    '<h2><span class="step-badge">2</span>Your Pets</h2>',
    unsafe_allow_html=True,
)
st.caption("Select a pet to manage, or add a new companion to the family.")

if not st.session_state.selected_pet_name:
    st.session_state.selected_pet_name = st.session_state.owner.pets[0].name

pet_names = [pet.name for pet in st.session_state.owner.pets]
selected_pet_name = st.selectbox(
    "🐾 Select pet",
    options=pet_names,
    index=pet_names.index(st.session_state.selected_pet_name)
    if st.session_state.selected_pet_name in pet_names else 0,
)
st.session_state.selected_pet_name = selected_pet_name
selected_pet = next(
    pet for pet in st.session_state.owner.pets
    if pet.name == st.session_state.selected_pet_name
)

pet_tab, tasks_tab, add_tab = st.tabs([
    f"📋 {selected_pet.name}'s Profile",
    f"✅ {selected_pet.name}'s Tasks",
    "➕ Add a new pet",
])

# ---- Tab: Selected pet profile ----
with pet_tab:
    species_options = ["dog", "cat", "other"]

    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name", value=selected_pet.name)
        species = st.selectbox(
            "Species",
            species_options,
            index=species_options.index(selected_pet.species)
            if selected_pet.species in species_options
            else len(species_options) - 1,
        )
    with col2:
        age = st.number_input(
            "Age (years)",
            min_value=0, max_value=40,
            value=int(selected_pet.age),
        )
        st.markdown("&nbsp;", unsafe_allow_html=True)

    notes = st.text_area("Notes", value=selected_pet.notes, height=80)

    selected_pet.update_info(
        name=pet_name, species=species, age=int(age), notes=notes,
    )
    st.session_state.selected_pet_name = selected_pet.name

    with st.expander("📄 View full pet profile", expanded=False):
        active_tasks = len([t for t in selected_pet.tasks if not t.is_completed])
        total_tasks = len(selected_pet.tasks)
        species_emoji = {"dog": "🐕", "cat": "🐈"}.get(selected_pet.species, "🐾")
        notes_display = (
            selected_pet.notes
            if selected_pet.notes
            else '<i style="color:#B89878">(no notes yet)</i>'
        )

        st.markdown(
            f"""
            <div class="pet-profile-card">
                <div class="pet-profile-row">
                    <span class="pet-profile-label">{species_emoji} Name</span>
                    <span class="pet-profile-value">{selected_pet.name}</span>
                </div>
                <div class="pet-profile-row">
                    <span class="pet-profile-label">🐾 Species</span>
                    <span class="pet-profile-value">{selected_pet.species.capitalize()}</span>
                </div>
                <div class="pet-profile-row">
                    <span class="pet-profile-label">🎂 Age</span>
                    <span class="pet-profile-value">{selected_pet.age} year{'s' if selected_pet.age != 1 else ''}</span>
                </div>
                <div class="pet-profile-row">
                    <span class="pet-profile-label">📝 Notes</span>
                    <span class="pet-profile-value">{notes_display}</span>
                </div>
                <div class="pet-profile-row">
                    <span class="pet-profile-label">✅ Active tasks</span>
                    <span class="pet-profile-value">{active_tasks} pending / {total_tasks} total</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.button("🗑️ Remove this pet", type="secondary"):
        if len(st.session_state.owner.pets) == 1:
            st.warning("At least one pet is required.")
        else:
            removed_tasks = list(selected_pet.tasks)
            st.session_state.owner.remove_pet(selected_pet)
            st.session_state.scheduler.tasks = [
                t for t in st.session_state.scheduler.tasks
                if t not in removed_tasks
            ]
            st.session_state.scheduler.generated_plan = [
                t for t in st.session_state.scheduler.generated_plan
                if t not in removed_tasks
            ]
            st.session_state.selected_pet_name = st.session_state.owner.pets[0].name
            st.success("Pet removed.")
            st.rerun()

# ---- Tab: Tasks for selected pet ----
with tasks_tab:
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
                pet_names_list = [p.name for p in st.session_state.owner.pets]
                with st.spinner("Asking Gemini to parse your request..."):
                    try:
                        parsed = parse_tasks_from_text(ai_input, pet_names_list)
                        st.session_state["ai_parsed_tasks"] = parsed
                        st.success(f"Parsed {len(parsed)} task(s). Review below.")
                    except TaskParseError as exc:
                        st.error(f"Could not parse: {exc}")
                    except AIClientError as exc:
                        st.error(f"AI service error: {exc}")

        if st.session_state.get("ai_parsed_tasks"):
            st.markdown("**Review parsed tasks:**")
            st.table(st.session_state["ai_parsed_tasks"])
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Add all to schedule"):
                    added = 0
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
                    st.success(f"Added {added} task(s).")
                    st.rerun()
            with c2:
                if st.button("❌ Discard"):
                    st.session_state.pop("ai_parsed_tasks", None)
                    st.rerun()

    with st.expander("📝 Add a task manually", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
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
            frequency_choice = st.selectbox("Frequency", ["none", "daily", "weekly"], index=0)

        if st.button("Add task manually"):
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
                    existing_minutes = Scheduler._time_to_minutes(existing_task.time)
                    if existing_minutes is not None and existing_minutes == new_task_minutes:
                        conflicting_tasks.append(existing_task)

            if conflicting_tasks:
                pet_map = st.session_state.owner.get_task_pet_map()
                details = ", ".join(
                    f"{t.title} ({pet_map.get(id(t), 'Unknown Pet')})"
                    for t in conflicting_tasks
                )
                st.warning(f"Time conflict at {new_task.time}: {details}")
            else:
                selected_pet.tasks.append(new_task)
                st.session_state.scheduler.add_task(new_task)
                st.success(f"Added: {new_task.title}")
                st.rerun()

    all_tasks = st.session_state.owner.get_all_tasks()
    pending_tasks = st.session_state.owner.filter_tasks(is_completed=False)
    completed_tasks = st.session_state.owner.filter_tasks(is_completed=True)
    task_pet_map = st.session_state.owner.get_task_pet_map()

    if all_tasks:
        st.markdown(
            f"**{len(all_tasks)} task(s) total** — "
            f"{len(pending_tasks)} pending, {len(completed_tasks)} completed."
        )

        task_view = st.selectbox(
            "Filter by status",
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
            "Show only tasks for selected plan date", value=True,
        )
        if filter_to_plan_date:
            tasks_to_show = [
                t for t in tasks_to_show
                if (extract_task_date(t.time) is None
                    or extract_task_date(t.time) == selected_plan_date)
            ]
            st.caption(
                f"Filtered to {selected_plan_date.isoformat()} "
                "(plus tasks with no explicit date)."
            )

        priority_order = {"high": 1, "medium": 2, "low": 3}
        sorted_tasks = sorted(
            tasks_to_show,
            key=lambda t: (priority_order.get(t.priority, 4), t.duration, t.title.lower()),
        )

        st.table(
            [
                {
                    "title": t.title,
                    "pet": task_pet_map.get(id(t), "Unknown Pet"),
                    "duration": t.duration,
                    "priority": t.priority,
                    "category": t.category,
                    "time": t.time,
                    "status": "✅ Done" if t.is_completed else "⏳ Pending",
                }
                for t in sorted_tasks
            ]
        )

        conflicts = st.session_state.scheduler.detect_time_conflicts(
            tasks=all_tasks, task_pet_map=task_pet_map,
        )
        for w in conflicts:
            st.warning(w)

        with st.expander("✏️ Edit or remove a task", expanded=False):
            task_options = {
                id(t): f"{t.title} ({t.time or 'No time'}) — {task_pet_map.get(id(t), 'Unknown Pet')}"
                for t in all_tasks
            }
            task_id_to_edit = st.selectbox(
                "Select task to edit",
                options=list(task_options.keys()),
                format_func=lambda tid: task_options[tid],
                key="task_id_to_edit",
            )
            task_to_edit = next(t for t in all_tasks if id(t) == task_id_to_edit)

            with st.form(key=f"edit_task_form_{task_id_to_edit}"):
                was_completed_before = task_to_edit.is_completed
                edit_title = st.text_input("Title", value=task_to_edit.title)
                edit_duration = st.number_input(
                    "Duration (min)", min_value=1, max_value=240,
                    value=int(task_to_edit.duration),
                )
                edit_priority = st.selectbox(
                    "Priority", ["low", "medium", "high"],
                    index=["low", "medium", "high"].index(task_to_edit.priority)
                    if task_to_edit.priority in ["low", "medium", "high"] else 1,
                )
                edit_category = st.text_input("Category", value=task_to_edit.category)
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
                    "Date", value=default_edit_date,
                    key=f"edit_date_{task_id_to_edit}",
                )
                edit_time = st.time_input(
                    "Time", value=default_edit_time, step=60,
                    key=f"edit_time_{task_id_to_edit}",
                )
                edit_description = st.text_area("Description", value=task_to_edit.description)
                frequency_options = ["none", "daily", "weekly"]
                current_frequency = task_to_edit.frequency.strip().lower()
                selected_frequency = (
                    current_frequency if current_frequency in {"daily", "weekly"}
                    else "none"
                )
                edit_frequency_choice = st.selectbox(
                    "Frequency", options=frequency_options,
                    index=frequency_options.index(selected_frequency),
                )
                edit_is_completed = st.checkbox(
                    "Mark as completed", value=task_to_edit.is_completed,
                )

                if st.form_submit_button("💾 Save changes"):
                    task_to_edit.update_task(
                        title=edit_title, duration=int(edit_duration),
                        priority=edit_priority, category=edit_category,
                        description=edit_description,
                        time=format_scheduled_datetime(edit_date, edit_time),
                        frequency="" if edit_frequency_choice == "none"
                        else edit_frequency_choice,
                    )
                    if edit_is_completed and not was_completed_before:
                        next_task = st.session_state.scheduler.mark_task_complete(task_to_edit)
                        if next_task is not None:
                            owner_pet = next(
                                (pet for pet in st.session_state.owner.pets
                                 if task_to_edit in pet.tasks),
                                None,
                            )
                            if owner_pet is not None:
                                owner_pet.tasks.append(next_task)
                            st.success("Task updated; next recurring occurrence created.")
                        else:
                            st.success("Task updated and marked completed.")
                    else:
                        task_to_edit.is_completed = edit_is_completed
                        st.success("Task updated.")
                    st.rerun()

            task_id_to_remove = st.selectbox(
                "Select task to remove",
                options=list(task_options.keys()),
                format_func=lambda tid: task_options[tid],
                key="task_id_to_remove",
            )
            if st.button("🗑️ Remove selected task"):
                for pet in st.session_state.owner.pets:
                    pet.tasks = [t for t in pet.tasks if id(t) != task_id_to_remove]
                st.session_state.scheduler.tasks = [
                    t for t in st.session_state.scheduler.tasks
                    if id(t) != task_id_to_remove
                ]
                st.session_state.scheduler.generated_plan = [
                    t for t in st.session_state.scheduler.generated_plan
                    if id(t) != task_id_to_remove
                ]
                st.success("Task removed.")
                st.rerun()
    else:
        st.info("No tasks yet. Add one above — with AI or manually!")

# ---- Tab: Add new pet ----
with add_tab:
    species_options = ["dog", "cat", "other"]
    col1, col2 = st.columns(2)
    with col1:
        new_pet_name = st.text_input("New pet name", value="")
        new_pet_species = st.selectbox("Species", species_options, key="new_pet_species")
    with col2:
        new_pet_age = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
        new_pet_notes = st.text_input("Notes", value="")

    if st.button("🐾 Add pet"):
        normalized = new_pet_name.strip()
        existing = {p.name.lower() for p in st.session_state.owner.pets}
        if not normalized:
            st.warning("Please enter a name.")
        elif normalized.lower() in existing:
            st.warning("A pet with that name already exists.")
        else:
            created = Pet(
                name=normalized, species=new_pet_species,
                age=int(new_pet_age), notes=new_pet_notes,
            )
            st.session_state.owner.add_pet(created)
            st.session_state.selected_pet_name = created.name
            st.success(f"Added: {created.name} 🎉")
            st.rerun()

st.divider()


# =====================================================================
# SECTION 3 — GENERATE PLAN
# =====================================================================
st.markdown(
    '<h2><span class="step-badge">3</span>Generate Today\'s Plan</h2>',
    unsafe_allow_html=True,
)
st.caption("Let PawPal+ build and explain an optimized plan based on your constraints.")

plan_date = st.date_input(
    "Plan date",
    value=date.today(),
    key="plan_date",
)

if st.button("✨ Generate schedule", type="primary"):
    generated_plan = st.session_state.scheduler.generate_plan(
        available_time=st.session_state.owner.available_time,
        preferences=st.session_state.owner.preferences,
        plan_date=plan_date,
    )
    if generated_plan:
        total = sum(t.duration for t in generated_plan)
        st.success(
            f"Schedule generated for {plan_date.isoformat()}: "
            f"{len(generated_plan)} task(s), "
            f"{total}/{st.session_state.owner.available_time} min used."
        )
    else:
        st.warning(f"No tasks fit the available time for {plan_date.isoformat()}.")

    if generated_plan:
        task_pet_map = st.session_state.owner.get_task_pet_map()
        with st.spinner("Asking Gemini to explain today's plan..."):
            try:
                from plan_explainer import explain_plan_with_ai
                ai_explanation, knowledge_used = explain_plan_with_ai(
                    plan=generated_plan,
                    owner=st.session_state.owner,
                    task_pet_map=task_pet_map,
                )
                st.markdown("#### 🧠 AI Explanation")
                st.info(ai_explanation)

                if knowledge_used:
                    with st.expander(
                        f"📚 Knowledge sources used ({len(knowledge_used)})",
                        expanded=False,
                    ):
                        for snippet in knowledge_used:
                            st.markdown(
                                f"**{snippet['topic']}** (relevance: {snippet['score']})"
                            )
                            st.caption(snippet["content"])
            except AIClientError as exc:
                st.warning(
                    f"AI explanation unavailable ({exc}). "
                    "Falling back to rule-based summary."
                )
                st.text(st.session_state.scheduler.explain_plan(
                    task_pet_map=task_pet_map))

        # --- Pretty rule-based breakdown ---
        with st.expander("📋 Rule-based breakdown", expanded=False):
            total_duration = sum(t.duration for t in generated_plan)
            task_items_html = ""
            for idx, task in enumerate(generated_plan, 1):
                priority_class = f"priority-{task.priority}"
                pet_name = task_pet_map.get(id(task), "Unknown pet")
                time_label = task.time or "No time set"
                task_items_html += (
                    f'<div class="plan-task-item {priority_class}">'
                    f'<div class="plan-task-header">{idx}. {task.title}</div>'
                    f'<div class="plan-task-meta">'
                    f'<span>🐾 {pet_name}</span>'
                    f'<span>⏰ {time_label}</span>'
                    f'<span>⏱️ {task.duration} min</span>'
                    f'<span>🎯 {task.priority}</span>'
                    f'</div>'
                    f'</div>'
                )

            summary_html = (
                f'<div class="plan-summary-card">'
                f'{task_items_html}'
                f'<div class="plan-totals">'
                f'Total: {total_duration} / {st.session_state.owner.available_time} minutes'
                f'</div>'
                f'</div>'
            )
            st.markdown(summary_html, unsafe_allow_html=True)

        sorted_plan = st.session_state.scheduler.get_plan_by_time()
        if sorted_plan:
            st.markdown("#### 📅 Scheduled tasks (chronological)")
            st.table(
                [
                    {
                        "title": t.title,
                        "pet": task_pet_map.get(id(t), "Unknown Pet"),
                        "time": t.time,
                        "duration": t.duration,
                        "priority": t.priority,
                    }
                    for t in sorted_plan
                ]
            )
            conflicts = st.session_state.scheduler.detect_time_conflicts(
                tasks=sorted_plan, task_pet_map=task_pet_map,
            )
            for w in conflicts:
                st.warning(w)
