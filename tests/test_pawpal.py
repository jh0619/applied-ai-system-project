from pawpal_system import Task, Pet, Scheduler, Owner
from datetime import date


def test_mark_complete():
    """Test that calling mark_complete() changes the task's status."""
    task = Task("Feed the dog", 10, "high", "feeding")
    assert task.is_completed == False, "Task should start as incomplete"

    task.mark_complete()
    assert task.is_completed == True, "Task status should be True after calling mark_complete()"


def test_mark_complete_creates_next_for_daily_task():
    """Daily tasks should generate a new pending occurrence when completed."""
    task = Task("Feed", 10, "high", "feeding", frequency="daily")

    next_task = task.mark_complete()

    assert task.is_completed == True
    assert next_task is not None
    assert next_task.title == task.title
    assert next_task.frequency == "daily"
    assert next_task.is_completed == False


def test_mark_complete_daily_task_moves_to_following_day_when_date_exists():
    """Daily recurrence should shift dated task time forward by one day."""
    task = Task(
        "Feed",
        10,
        "high",
        "feeding",
        time="2026-03-28 08:00 AM",
        frequency="daily",
    )

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.time == "2026-03-29 08:00 AM"


def test_mark_complete_creates_next_for_weekly_task():
    """Weekly tasks should generate a new pending occurrence when completed."""
    task = Task("Groom", 30, "medium", "care", frequency="weekly")

    next_task = task.mark_complete()

    assert task.is_completed == True
    assert next_task is not None
    assert next_task.frequency == "weekly"
    assert next_task.is_completed == False


def test_mark_complete_weekly_task_moves_forward_seven_days_when_date_exists():
    """Weekly recurrence should shift dated task time forward by seven days."""
    task = Task(
        "Bath",
        20,
        "medium",
        "grooming",
        time="2026-03-28 05:00 PM",
        frequency="weekly",
    )

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.time == "2026-04-04 05:00 PM"


def test_mark_complete_non_recurring_returns_none():
    """Non-recurring tasks should not generate new occurrences."""
    task = Task("Play", 15, "low", "exercise", frequency="once")

    next_task = task.mark_complete()

    assert task.is_completed == True
    assert next_task is None


def test_scheduler_mark_task_complete_appends_next_occurrence():
    """Scheduler completion should auto-add the next recurring task."""
    scheduler = Scheduler()
    task = Task("Feed", 10, "high", "feeding", frequency="daily")
    scheduler.add_task(task)

    next_task = scheduler.mark_task_complete(task)

    assert next_task is not None
    assert len(scheduler.tasks) == 2
    assert scheduler.tasks[0].is_completed == True
    assert scheduler.tasks[1].is_completed == False


def test_detect_time_conflicts_same_pet_warning():
    """Scheduler should warn on overlapping task times for the same pet."""
    owner = Owner("Sam", 120, [])
    pet = Pet("Buddy", "Dog", 3, "friendly")
    owner.add_pet(pet)

    task1 = Task("Feed", 10, "high", "feeding", time="8:00 AM")
    task2 = Task("Walk", 20, "medium", "exercise", time="8:00 AM")
    pet.tasks.extend([task1, task2])

    scheduler = Scheduler(tasks=[task1, task2])
    warnings = scheduler.detect_time_conflicts(
        task_pet_map=owner.get_task_pet_map()
    )

    assert len(warnings) == 1
    assert "same pet" in warnings[0]


def test_conflict_detection_flags_duplicate_times_without_pet_map():
    """Duplicate times should still be flagged without a pet map."""
    task1 = Task("Feed", 10, "high", "feeding", time="8:00 AM")
    task2 = Task("Medication", 5, "high", "health", time="8:00 AM")

    scheduler = Scheduler(tasks=[task1, task2])
    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "Time conflict" in warnings[0]
    assert "Feed" in warnings[0]
    assert "Medication" in warnings[0]


def test_detect_time_conflicts_different_pets_warning():
    """Scheduler should warn on overlapping task times for different pets."""
    owner = Owner("Sam", 120, [])
    dog = Pet("Buddy", "Dog", 3, "friendly")
    cat = Pet("Luna", "Cat", 2, "calm")
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog_task = Task("Feed Buddy", 10, "high", "feeding", time="8:00 AM")
    cat_task = Task("Feed Luna", 10, "high", "feeding", time="8:00 AM")
    dog.tasks.append(dog_task)
    cat.tasks.append(cat_task)

    scheduler = Scheduler(tasks=[dog_task, cat_task])
    warnings = scheduler.detect_time_conflicts(
        task_pet_map=owner.get_task_pet_map()
    )

    assert len(warnings) == 1
    assert "different pets" in warnings[0]


def test_detect_time_conflicts_invalid_time_returns_warning():
    """Invalid task time should return warning and not crash."""
    scheduler = Scheduler(
        tasks=[Task("Feed", 10, "high", "feeding", time="not-a-time")]
    )

    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "Skipped invalid task time" in warnings[0]


def test_partial_overlap_is_detected():
    """9:00 (30min) and 9:20 should be flagged as overlapping."""
    task1 = Task("Walk", 30, "high", "exercise", time="9:00 AM")
    task2 = Task("Feed", 10, "high", "feeding", time="9:20 AM")

    scheduler = Scheduler(tasks=[task1, task2])
    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Feed" in warnings[0]


def test_back_to_back_tasks_are_not_flagged():
    """9:00 (30min) ending at 9:30 and 9:30 starting fresh = no conflict."""
    task1 = Task("Walk", 30, "high", "exercise", time="9:00 AM")
    task2 = Task("Feed", 10, "high", "feeding", time="9:30 AM")

    scheduler = Scheduler(tasks=[task1, task2])
    warnings = scheduler.detect_time_conflicts()

    assert warnings == []


def test_three_overlapping_tasks_each_pair_reported_once():
    """Three overlapping tasks should produce 3 conflict pairs (C(3,2))."""
    task1 = Task("A", 60, "high", "exercise", time="9:00 AM")
    task2 = Task("B", 30, "high", "exercise", time="9:15 AM")
    task3 = Task("C", 30, "high", "exercise", time="9:30 AM")

    scheduler = Scheduler(tasks=[task1, task2, task3])
    warnings = scheduler.detect_time_conflicts()

    assert len(warnings) == 3


def test_overlap_on_different_days_is_not_flagged():
    """Same clock time on different dates should not conflict."""
    task1 = Task("A", 30, "high", "exercise", time="2026-04-25 09:00 AM")
    task2 = Task("B", 30, "high", "exercise", time="2026-04-26 09:15 AM")

    scheduler = Scheduler(tasks=[task1, task2])
    warnings = scheduler.detect_time_conflicts()

    assert warnings == []


def test_add_task_to_pet():
    """Test that adding a task to a Pet increases that pet's task count."""
    pet = Pet("Buddy", "Dog", 3, "friendly")
    assert len(pet.tasks) == 0, "Pet should start with 0 tasks"

    task1 = Task("Feed", 10, "high", "feeding")
    pet.tasks.append(task1)
    assert len(pet.tasks) == 1, "Pet should have 1 task after adding"

    task2 = Task("Walk", 20, "medium", "exercise")
    pet.tasks.append(task2)
    assert len(pet.tasks) == 2, "Pet should have 2 tasks after adding another task"


def test_sorting_correctness_returns_chronological_order():
    """Generated plan should be returned in ascending chronological order."""
    scheduler = Scheduler()
    task_late = Task("Evening Walk", 20, "high", "exercise", time="6:00 PM")
    task_early = Task("Breakfast", 10, "high", "feeding", time="8:00 AM")
    task_mid = Task("Noon Meds", 5, "high", "health", time="12:00 PM")

    for task in [task_late, task_early, task_mid]:
        scheduler.add_task(task)

    scheduler.generate_plan(available_time=60, preferences=[])
    sorted_plan = scheduler.get_plan_by_time()

    assert [task.title for task in sorted_plan] == [
        "Breakfast",
        "Noon Meds",
        "Evening Walk",
    ]


def test_sorting_places_tasks_with_invalid_or_missing_time_last():
    """Tasks with invalid/missing time should be placed after valid times."""
    scheduler = Scheduler()
    timed = Task("Walk", 20, "high", "exercise", time="9:00 AM")
    invalid_time = Task("Brush", 10, "high", "grooming", time="not-a-time")
    empty_time = Task("Play", 15, "high", "enrichment", time="")

    for task in [invalid_time, timed, empty_time]:
        scheduler.add_task(task)

    scheduler.generate_plan(available_time=60, preferences=[])
    sorted_plan = scheduler.get_plan_by_time()

    assert sorted_plan[0].title == "Walk"
    assert {sorted_plan[1].title, sorted_plan[2].title} == {"Brush", "Play"}


def test_sorting_handles_midnight_and_noon_edges_correctly():
    """Time parsing should order midnight before noon and afternoon times."""
    scheduler = Scheduler(
        tasks=[
            Task("Lunch", 15, "high", "feeding", time="12:00 PM"),
            Task("Midnight Med", 5, "high", "health", time="12:00 AM"),
            Task("Afternoon Play", 20, "high", "enrichment", time="1:00 PM"),
        ]
    )

    scheduler.generate_plan(available_time=60, preferences=[])
    sorted_plan = scheduler.get_plan_by_time()

    assert [task.title for task in sorted_plan] == [
        "Midnight Med",
        "Lunch",
        "Afternoon Play",
    ]


def test_sorting_with_dates_orders_by_date_then_time():
    """Date-time sorting should order earlier days before later days."""
    scheduler = Scheduler(
        tasks=[
            Task("Tomorrow Walk", 20, "high", "exercise", time="2026-03-29 08:00 AM"),
            Task("Today Lunch", 15, "high", "feeding", time="2026-03-28 12:00 PM"),
            Task("Today Breakfast", 10, "high", "feeding", time="2026-03-28 08:00 AM"),
        ]
    )

    scheduler.generate_plan(available_time=90, preferences=[])
    sorted_plan = scheduler.get_plan_by_time()

    assert [task.title for task in sorted_plan] == [
        "Today Breakfast",
        "Today Lunch",
        "Tomorrow Walk",
    ]


def test_conflict_detection_does_not_flag_same_clock_time_on_different_dates():
    """Date-aware conflicts should not flag tasks on different calendar days."""
    scheduler = Scheduler(
        tasks=[
            Task("Saturday Feed", 10, "high", "feeding", time="2026-03-28 08:00 AM"),
            Task("Sunday Feed", 10, "high", "feeding", time="2026-03-29 08:00 AM"),
        ]
    )

    warnings = scheduler.detect_time_conflicts()

    assert warnings == []


def test_generate_plan_filters_tasks_by_selected_date():
    """Planner should include only tasks scheduled for the selected date."""
    scheduler = Scheduler(
        tasks=[
            Task("Today Feed", 10, "high", "feeding", time="2026-03-28 08:00 AM"),
            Task("Tomorrow Walk", 20, "high", "exercise", time="2026-03-29 08:00 AM"),
        ]
    )

    plan = scheduler.generate_plan(
        available_time=60,
        preferences=[],
        plan_date=date(2026, 3, 28),
    )

    assert [task.title for task in plan] == ["Today Feed"]


def test_generate_plan_without_date_keeps_all_pending_tasks():
    """Planner should keep previous global behavior when no plan_date is provided."""
    scheduler = Scheduler(
        tasks=[
            Task("Today Feed", 10, "high", "feeding", time="2026-03-28 08:00 AM"),
            Task("Tomorrow Walk", 20, "high", "exercise", time="2026-03-29 08:00 AM"),
        ]
    )

    plan = scheduler.generate_plan(
        available_time=60,
        preferences=[],
    )

    assert {task.title for task in plan} == {"Today Feed", "Tomorrow Walk"}


def test_daily_recurrence_keeps_time_when_no_date_is_provided():
    """Daily recurring tasks without a date should keep original time."""
    task = Task(
        "Feed",
        10,
        "high",
        "feeding",
        time="8:00 AM",
        frequency="daily",
    )

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.time == "8:00 AM"


def test_daily_recurrence_accepts_mixed_case_and_whitespace_frequency():
    """Normalization should treat spaced/mixed-case daily as recurring."""
    task = Task("Feed", 10, "high", "feeding", frequency="  DaIlY  ")

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.frequency == "  DaIlY  "
