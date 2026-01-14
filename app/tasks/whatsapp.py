from app.celery_app import celery_app
import time

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=10, retry_kwargs={'max_retries': 3})
def send_whatsapp_message(self, phone: str, message: str):
    print(f"Sending WhatsApp to {phone}")
    time.sleep(5)  # simulate API call
    print("Message sent")
