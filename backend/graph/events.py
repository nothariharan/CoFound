from datetime import datetime, timedelta
from typing import Any

from pymongo import MongoClient
from pymongo.results import UpdateResult

from backend.graph.schema import BuildEvent, ObserveEvent, Task, TaskStatus


class EventStore:
    """
    Manages interactions with MongoDB for storing build events, observe events,
    and handling a task queue.

    Args:
        mongo_uri (str): The MongoDB connection URI.
        db_name (str): The name of the database to use. Defaults to "cofound".
    """

    def __init__(self, mongo_uri: str, db_name: str = "cofound") -> None:
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.build_events_collection = self.db["build_events"]
        self.observe_events_collection = self.db["observe_events"]
        self.task_queue_collection = self.db["task_queue"]

        # Ensure indexes for efficient querying
        self.task_queue_collection.create_index(
            [("status", 1), ("created_at", 1)], name="status_created_at_idx"
        )
        self.task_queue_collection.create_index(
            [("status", 1), ("updated_at", 1)], name="status_updated_at_idx"
        )
        self.task_queue_collection.create_index(
            [("idea_id", 1)], name="idea_id_idx"
        )

    def insert_build_event(self, event: BuildEvent) -> str:
        """
        Inserts a build event into the 'build_events' collection.

        Args:
            event (BuildEvent): The build event to insert.

        Returns:
            str: The ID of the inserted document.
        """
        event_dict = event.model_dump(by_alias=True)
        result = self.build_events_collection.insert_one(event_dict)
        return str(result.inserted_id)

    def insert_observe_event(self, event: ObserveEvent) -> str:
        """
        Inserts an observe event into the 'observe_events' collection.

        Args:
            event (ObserveEvent): The observe event to insert.

        Returns:
            str: The ID of the inserted document.
        """
        event_dict = event.model_dump(by_alias=True)
        result = self.observe_events_collection.insert_one(event_dict)
        return str(result.inserted_id)

    def enqueue_task(self, task: Task) -> str:
        """
        Enqueues a new task into the 'task_queue' collection.

        Args:
            task (Task): The task to enqueue.

        Returns:
            str: The ID of the inserted task document.
        """
        task_dict = task.model_dump(by_alias=True)
        result = self.task_queue_collection.insert_one(task_dict)
        return str(result.inserted_id)

    def pop_pending_task(self, idea_id: str | None = None) -> Task | None:
        """
        Atomically finds and retrieves the oldest pending task, marking it as 'in_progress'.

        Args:
            idea_id (str | None): If provided, filters tasks for a specific idea_id.

        Returns:
            Task | None: The retrieved task, or None if no pending tasks are found.
        """
        query = {"status": TaskStatus.PENDING}
        if idea_id:
            query["idea_id"] = idea_id

        # Atomically find a pending task and mark it as in_progress
        task_dict = self.task_queue_collection.find_one_and_update(
            query,
            {"$set": {"status": TaskStatus.IN_PROGRESS, "updated_at": datetime.utcnow()}},
            sort=[("created_at", 1)],  # Process oldest tasks first
            return_document=True,
        )
        if task_dict:
            return Task(**task_dict)
        return None

    def mark_task_done(self, task_id: str) -> UpdateResult:
        """
        Marks a task as 'completed'.

        Args:
            task_id (str): The ID of the task to mark as done.

        Returns:
            UpdateResult: The result of the MongoDB update operation.
        """
        return self.task_queue_collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": TaskStatus.COMPLETED, "updated_at": datetime.utcnow()}},
        )

    def mark_task_dead_end(self, task_id: str, error_message: str | None = None) -> UpdateResult:
        """
        Marks a task as 'dead_end', indicating it cannot be processed further.

        Args:
            task_id (str): The ID of the task to mark as dead_end.
            error_message (str | None): An optional error message explaining why the task
                                         reached a dead end.

        Returns:
            UpdateResult: The result of the MongoDB update operation.
        """
        return self.task_queue_collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": TaskStatus.DEAD_END,
                    "updated_at": datetime.utcnow(),
                    "error_message": error_message,
                }
            },
        )

    def requeue_task(self, task_id: str, max_retries: int = 3) -> UpdateResult | None:
        """
        Requeues a task if it hasn't exceeded the maximum number of retries.
        If max retries are reached, the task is marked as 'dead_end'.

        Args:
            task_id (str): The ID of the task to requeue.
            max_retries (int): The maximum number of times a task can be retried.

        Returns:
            UpdateResult | None: The result of the MongoDB update operation, or None if task not found.
        """
        task = self.task_queue_collection.find_one({"task_id": task_id})
        if not task:
            return None

        current_retries = task.get("retries", 0)
        if current_retries < max_retries:
            return self.task_queue_collection.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": TaskStatus.PENDING,
                        "updated_at": datetime.utcnow(),
                        "retries": current_retries + 1,
                        "error_message": None,  # Clear error message on requeue
                    }
                },
            )
        else:
            # If max retries reached, mark as dead_end
            return self.mark_task_dead_end(task_id, "Max retries reached")

    def get_task(self, task_id: str) -> Task | None:
        """
        Retrieves a single task by its ID.

        Args:
            task_id (str): The ID of the task to retrieve.

        Returns:
            Task | None: The retrieved task, or None if not found.
        """
        task_dict = self.task_queue_collection.find_one({"task_id": task_id})
        if task_dict:
            return Task(**task_dict)
        return None

    def get_pending_tasks(self, idea_id: str | None = None) -> list[Task]:
        """
        Retrieves all tasks with 'pending' status.

        Args:
            idea_id (str | None): If provided, filters tasks for a specific idea_id.

        Returns:
            list[Task]: A list of pending tasks, ordered by creation time.
        """
        query = {"status": TaskStatus.PENDING}
        if idea_id:
            query["idea_id"] = idea_id
        tasks = self.task_queue_collection.find(query).sort("created_at", 1)
        return [Task(**task) for task in tasks]

    def get_in_progress_tasks(self, idea_id: str | None = None) -> list[Task]:
        """
        Retrieves all tasks with 'in_progress' status.

        Args:
            idea_id (str | None): If provided, filters tasks for a specific idea_id.

        Returns:
            list[Task]: A list of in-progress tasks, ordered by last update time.
        """
        query = {"status": TaskStatus.IN_PROGRESS}
        if idea_id:
            query["idea_id"] = idea_id
        tasks = self.task_queue_collection.find(query).sort("updated_at", 1)
        return [Task(**task) for task in tasks]

    def get_dead_end_tasks(self, idea_id: str | None = None) -> list[Task]:
        """
        Retrieves all tasks with 'dead_end' status.

        Args:
            idea_id (str | None): If provided, filters tasks for a specific idea_id.

        Returns:
            list[Task]: A list of dead-end tasks, ordered by last update time (descending).
        """
        query = {"status": TaskStatus.DEAD_END}
        if idea_id:
            query["idea_id"] = idea_id
        tasks = self.task_queue_collection.find(query).sort("updated_at", -1)
        return [Task(**task) for task in tasks]

    def get_completed_tasks(self, idea_id: str | None = None) -> list[Task]:
        """
        Retrieves all tasks with 'completed' status.

        Args:
            idea_id (str | None): If provided, filters tasks for a specific idea_id.

        Returns:
            list[Task]: A list of completed tasks, ordered by last update time (descending).
        """
        query = {"status": TaskStatus.COMPLETED}
        if idea_id:
            query["idea_id"] = idea_id
        tasks = self.task_queue_collection.find(query).sort("updated_at", -1)
        return [Task(**task) for task in tasks]

    def get_all_tasks(self, idea_id: str | None = None) -> list[Task]:
        """
        Retrieves all tasks regardless of status.

        Args:
            idea_id (str | None): If provided, filters tasks for a specific idea_id.

        Returns:
            list[Task]: A list of all tasks, ordered by creation time.
        """
        query = {}
        if idea_id:
            query["idea_id"] = idea_id
        tasks = self.task_queue_collection.find(query).sort("created_at", 1)
        return [Task(**task) for task in tasks]

    def clean_old_dead_end_tasks(self, days_old: int = 30) -> int:
        """
        Deletes dead-end tasks older than a specified number of days.

        Args:
            days_old (int): The number of days after which dead-end tasks should be deleted.

        Returns:
            int: The number of deleted documents.
        """
        threshold_date = datetime.utcnow() - timedelta(days=days_old)
        result = self.task_queue_collection.delete_many(
            {"status": TaskStatus.DEAD_END, "updated_at": {"$lt": threshold_date}}
        )
        return result.deleted_count

    def clean_old_completed_tasks(self, days_old: int = 7) -> int:
        """
        Deletes completed tasks older than a specified number of days.

        Args:
            days_old (int): The number of days after which completed tasks should be deleted.

        Returns:
            int: The number of deleted documents.
        """
        threshold_date = datetime.utcnow() - timedelta(days=days_old)
        result = self.task_queue_collection.delete_many(
            {"status": TaskStatus.COMPLETED, "updated_at": {"$lt": threshold_date}}
        )
        return result.deleted_count
