from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date


@dataclass
class Pet:
    name: str
    species: str
    age: int
    notes: str
    tasks: list[Task] = field(default_factory=list)

    def get_profile(self) -> str:
        """Return a formatted profile of the pet."""
        profile = "Pet Profile:\n"
        profile += f"  Name: {self.name}\n"
        profile += f"  Species: {self.species}\n"
        profile += f"  Age: {self.age} years\n"
        profile += f"  Notes: {self.notes}\n"
        profile += f"  Active Tasks: {len([t for t in self.tasks if not t.is_completed])}/{len(self.tasks)}\n"
        return profile

    def update_info(
        self,
        name: str,
        species: str,
        age: int,
        notes: str,
    ) -> None:
        """Update the pet's information."""
        self.name = name
        self.species = species
        self.age = age
        self.notes = notes


@dataclass
class Owner:
    name: str
    available_time: int
    preferences: list[str]
    pets: list[Pet] = field(default_factory=list)

    def update_availability(self, available_time: int) -> None:
        """Update the owner's available time."""
        self.available_time = available_time

    def set_preferences(self, preferences: list[str]) -> None:
        """Set the owner's preferences for pet care."""
        self.preferences = preferences

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's collection."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from the owner's collection."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_all_tasks(self) -> list[Task]:
        """Retrieve all tasks from all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def get_task_pet_map(self) -> dict[int, str]:
        """Return a mapping of task object IDs to pet names."""
        task_pet_map: dict[int, str] = {}
        for pet in self.pets:
            for task in pet.tasks:
                task_pet_map[id(task)] = pet.name
        return task_pet_map

    def filter_tasks(
        self,
        is_completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Filter tasks by completion status and/or pet name.

        If no filter is provided, all tasks are returned.
        """
        filtered_tasks: list[Task] = []
        normalized_pet_name = pet_name.strip().lower() if pet_name else None

        for pet in self.pets:
            if normalized_pet_name and pet.name.lower() != normalized_pet_name:
                continue

            for task in pet.tasks:
                if (
                    is_completed is not None
                    and task.is_completed != is_completed
                ):
                    continue
                filtered_tasks.append(task)

        return filtered_tasks


@dataclass
class Task:
    title: str
    duration: int
    priority: str
    category: str
    description: str = ""
    time: str = ""
    frequency: str = ""
    is_completed: bool = False

    @staticmethod
    def _shift_time_for_recurrence(time_value: str, frequency: str) -> str:
        """Return shifted time string when recurrence has a parseable date."""
        if not time_value:
            return time_value

        normalized_frequency = frequency.strip().lower()
        day_delta = 1 if normalized_frequency == "daily" else 7

        supported_formats = [
            "%Y-%m-%d %I:%M %p",
            "%Y-%m-%d %H:%M",
        ]

        for fmt in supported_formats:
            try:
                parsed_time = datetime.strptime(time_value, fmt)
                shifted_time = parsed_time + timedelta(days=day_delta)
                return shifted_time.strftime(fmt)
            except ValueError:
                continue

        return time_value

    def _create_next_occurrence(self) -> Task | None:
        """Create the next task occurrence for recurring tasks."""
        recurring_frequencies = {"daily", "weekly"}
        if self.frequency.strip().lower() not in recurring_frequencies:
            return None

        return Task(
            title=self.title,
            duration=self.duration,
            priority=self.priority,
            category=self.category,
            description=self.description,
            time=self._shift_time_for_recurrence(self.time, self.frequency),
            frequency=self.frequency,
            is_completed=False,
        )

    def mark_complete(self) -> Task | None:
        """Mark task complete and return next occurrence if recurring."""
        self.is_completed = True
        return self._create_next_occurrence()

    def update_task(
        self,
        title: str,
        duration: int,
        priority: str,
        category: str,
        description: str = "",
        time: str = "",
        frequency: str = "",
    ) -> None:
        """Update all task details."""
        self.title = title
        self.duration = duration
        self.priority = priority
        self.category = category
        self.description = description
        self.time = time
        self.frequency = frequency

    def get_task_info(self) -> str:
        """Return a formatted string with all task information."""
        info = f"Task: {self.title}\n"
        info += f"Description: {self.description}\n"
        info += f"Duration: {self.duration} minutes\n"
        info += f"Priority: {self.priority}\n"
        info += f"Category: {self.category}\n"
        info += f"Time: {self.time}\n"
        info += f"Frequency: {self.frequency}\n"
        info += f"Status: {'Completed' if self.is_completed else 'Pending'}\n"
        return info


@dataclass
class Scheduler:
    tasks: list[Task] = field(default_factory=list)
    available_time: int = 0
    generated_plan: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to the scheduler."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the scheduler."""
        if task in self.tasks:
            self.tasks.remove(task)

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task and auto-add the next recurring occurrence."""
        next_task = task.mark_complete()
        if next_task is not None:
            self.tasks.append(next_task)
        return next_task

    @staticmethod
    def _time_to_minutes(time_str: str) -> int | None:
        """Convert a time string (e.g., '8:00 AM') to minutes."""
        if not time_str:
            return None

        parsed_datetime = Scheduler._parse_task_datetime(time_str)
        if parsed_datetime is not None:
            return (parsed_datetime.hour * 60) + parsed_datetime.minute

        try:
            parts = time_str.split()
            time_parts = parts[0].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            period = parts[1].upper() if len(parts) > 1 else "AM"

            if period == "PM" and hour != 12:
                hour += 12
            elif period == "AM" and hour == 12:
                hour = 0

            return hour * 60 + minute
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _parse_task_datetime(time_str: str) -> datetime | None:
        """Parse supported task time formats into a datetime object."""
        if not time_str:
            return None

        supported_formats = [
            "%Y-%m-%d %I:%M %p",
            "%Y-%m-%d %H:%M",
            "%I:%M %p",
            "%H:%M",
        ]

        for fmt in supported_formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def _time_sort_key(time_str: str) -> tuple[int, int] | None:
        """Return sortable (day, minutes) key for task times."""
        parsed_datetime = Scheduler._parse_task_datetime(time_str)
        if parsed_datetime is None:
            return None

        has_explicit_date = "-" in time_str
        day_key = parsed_datetime.toordinal() if has_explicit_date else 0
        minutes = (parsed_datetime.hour * 60) + parsed_datetime.minute
        return (day_key, minutes)

    @staticmethod
    def _extract_explicit_task_date(time_str: str) -> date | None:
        """Return date when task time includes an explicit YYYY-MM-DD value."""
        if not time_str or "-" not in time_str:
            return None

        supported_formats = [
            "%Y-%m-%d %I:%M %p",
            "%Y-%m-%d %H:%M",
        ]

        for fmt in supported_formats:
            try:
                return datetime.strptime(time_str, fmt).date()
            except ValueError:
                continue

        return None

    def detect_time_conflicts(
        self,
        tasks: list[Task] | None = None,
        task_pet_map: dict[int, str] | None = None,
    ) -> list[str]:
        """Detect same-time task conflicts and return warning messages.

        This method is intentionally lightweight: it never raises for bad input
        and returns human-readable warnings instead.
        """
        warnings: list[str] = []
        tasks_to_check = tasks or self.generated_plan or self.tasks
        grouped_tasks: dict[tuple[int, int], list[Task]] = {}

        for task in tasks_to_check:
            sort_key = self._time_sort_key(task.time)
            if sort_key is None:
                if task.time:
                    warnings.append(
                        "Warning: Skipped invalid task time "
                        f"'{task.time}' for '{task.title}'."
                    )
                continue

            grouped_tasks.setdefault(sort_key, []).append(task)

        for conflicted_tasks in grouped_tasks.values():
            if len(conflicted_tasks) < 2:
                continue

            time_label = conflicted_tasks[0].time

            if task_pet_map:
                pet_names = [
                    task_pet_map.get(id(task), "Unknown Pet")
                    for task in conflicted_tasks
                ]
                conflict_scope = (
                    "same pet"
                    if len(set(pet_names)) == 1
                    else "different pets"
                )
                details = ", ".join(
                    (
                        f"{task.title} "
                        f"({task_pet_map.get(id(task), 'Unknown Pet')})"
                    )
                    for task in conflicted_tasks
                )
                warnings.append(
                    f"Warning: Time conflict at {time_label} "
                    f"({conflict_scope}): {details}."
                )
            else:
                task_titles = ", ".join(
                    task.title for task in conflicted_tasks
                )
                warnings.append(
                    f"Warning: Time conflict at {time_label}: {task_titles}."
                )

        return warnings

    def generate_plan(
        self,
        available_time: int,
        preferences: list[str],
        plan_date: date | None = None,
    ) -> list[Task]:
        """Generate an optimized plan based on available time and preferences.

        Tasks are prioritized by priority level, then sorted by duration.
        Tasks are added to the plan if they fit within available time.
        """
        self.available_time = available_time

        # Filter incomplete tasks for the selected day.
        incomplete_tasks: list[Task] = []
        for task in self.tasks:
            if task.is_completed:
                continue

            if plan_date is None:
                incomplete_tasks.append(task)
                continue

            task_date = self._extract_explicit_task_date(task.time)
            if task_date is None or task_date == plan_date:
                incomplete_tasks.append(task)

        # Sort by priority and duration
        priority_order = {"high": 1, "medium": 2, "low": 3}
        sorted_tasks = sorted(
            incomplete_tasks,
            key=lambda t: (priority_order.get(t.priority, 4), t.duration)
        )

        # Fit tasks into available time
        self.generated_plan = []
        total_time = 0
        for task in sorted_tasks:
            if total_time + task.duration <= available_time:
                self.generated_plan.append(task)
                total_time += task.duration

        return self.generated_plan

    def explain_plan(self, task_pet_map: dict[int, str] | None = None) -> str:
        """Return a formatted explanation of the generated plan."""
        if not self.generated_plan:
            return "No plan generated yet."

        explanation = "Generated Plan:\n"
        explanation += "=" * 40 + "\n"
        total_duration = 0
        for i, task in enumerate(self.generated_plan, 1):
            explanation += f"{i}. {task.title} ({task.duration} min)\n"
            if task_pet_map:
                explanation += (
                    f"   Pet: {task_pet_map.get(id(task), 'Unknown Pet')}\n"
                )
            explanation += f"   Scheduled: {task.time or 'No time set'}\n"
            explanation += f"   Priority: {task.priority}\n"
            total_duration += task.duration

        explanation += "=" * 40 + "\n"
        explanation += f"Total Duration: {total_duration}/{self.available_time} minutes\n"
        return explanation

    def get_plan(self) -> list[Task]:
        """Return the currently generated plan."""
        return self.generated_plan

    def get_plan_by_time(self) -> list[Task]:
        """Return the generated plan sorted chronologically by time."""
        def sort_key(task: Task) -> tuple[int, int]:
            parsed_key = self._time_sort_key(task.time)
            return parsed_key if parsed_key is not None else (10_000_000, 10_000)

        return sorted(
            self.generated_plan,
            key=sort_key,
        )
