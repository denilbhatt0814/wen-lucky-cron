import redis
import time
from redbeat import RedBeatSchedulerEntry as Entry
from celery_app import app
import os

# host = "localhost"
# port = 6379
# db = 4
host = os.environ["REDIS_REDBEAT_HOST"]
port = os.environ["REDIS_REDBEAT_PORT"]
db = os.environ["REDIS_REDBEAT_DB_NAME"]

def get_all_schedule_entries():
    client = redis.StrictRedis(host=host, port=port, db=db)
    schedules = client.zrange("redbeat::schedule",0,-1)
    client.close()
    return list(map(lambda x: x.decode()[len("redbeat:"):], schedules))
    
def get_schedule_entry(name, app):
    try:
        schedule_entry = Entry.from_key("redbeat:"+name, app=app)
        return schedule_entry
    except KeyError:
        return None
    
def add_new_schedule_entry(name, task, schedule, args, app):
    entry = Entry(name=name, task=task, schedule=schedule, args=args, app=app)
    return entry.save()

def delete_schedule_entry(name, app):
    entry = get_schedule_entry(name=name, app=app)
    if entry: 
        entry.delete()

def reset_schedule_timer(name, app=app):
    schedule_entry = get_schedule_entry(name, app)
    if schedule_entry:
        schedule_entry.reschedule()
        print("RESCHEDULED!!")
        return
    elif schedule_entry == None:
        print(f"reset_schedule_timer: schedule - {name} not found")
        return 
    
    
