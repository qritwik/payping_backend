from celery import Celery

celery_app = Celery(
    "payping",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["app.tasks.whatsapp"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
)
