from celery import Celery

# Ensure your Redis server is running. Replace with your broker URL if different.
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

celery_app = Celery(
    "worker", # Name of the Celery application
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"] # List of modules to import when the worker starts
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Optional: acks_late = True, task_reject_on_worker_lost = True for more robust task handling
)

if __name__ == "__main__":
    # This is for running celery directly, not usually needed when managed by a process manager
    celery_app.start()