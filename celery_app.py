from celery import Celery, Task
import celeryconf
import os

celery_broker_url = os.environ["REDIS_CELERY_BROKER_URL"] 
celery_backend_url = os.environ["REDIS_CELERY_BACKEND_URL"]

app = Celery("testing_celery_app", broker=celery_broker_url, backend=celery_backend_url)
app.config_from_object(celeryconf)