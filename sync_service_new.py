from celery_app import app
from datetime import timedelta
from SmartContractMongoRepo import SmartContractMongoRepo
from utils import redbeat_helper
from celery.schedules import schedule

def fetch_records():
    sc_repo = SmartContractMongoRepo()
    records = sc_repo.getAll()
    return records

def schedule_tasks(records):
    for record in records:
        
        record_id = str(record["_id"])
        task_name = f"sc_task_{record_id}"
        print(f"TASK: {task_name}")
        
        schedule_entry = redbeat_helper.get_schedule_entry(task_name, app)
        print(schedule_entry)
        if schedule_entry: 
            # check if needs update
            print("checking for updates")
            scheduled_address, abi, scheduled_time, _ = schedule_entry.args
            if scheduled_address != record["contractAddress"] or scheduled_time != record["duration"] or abi != record["abiJson"]:
                # updating schedule
                print("updating")
                schedule_entry.args = [record["contractAddress"], record["abiJson"], record["duration"], task_name]
                schedule_entry.schedule = schedule(run_every=timedelta(seconds=record["duration"]))
                schedule_entry.save()
                print(f"UPDATED: {task_name}")
        elif schedule_entry == None:
            # create new schedule
            print("creating new task")
            redbeat_helper.add_new_schedule_entry(
                name= task_name,
                task="main.test_contract",
                schedule=timedelta(seconds=record["duration"]),
                args=[record["contractAddress"], record["abiJson"],record["duration"], task_name],
                app=app
            )
            print(f"ADDED: {task_name}")

    return True

def remove_inactive_tasks(records):
    active_recordIds = {str(record["_id"]) for record in records}
    active_task_names = { "sc_task_" + recordId for recordId in active_recordIds }
    registered_tasks = list(filter(lambda task_name: "sc_task_" in task_name, redbeat_helper.get_all_schedule_entries()))
    for task_name in registered_tasks:
        if task_name not in active_task_names:
            redbeat_helper.delete_schedule_entry(task_name, app=app)
            print(f"REMOVED: {task_name}")
    
    return True

def sync_db_and_tasks():
    records = fetch_records()
    schedule_success = schedule_tasks(records=records)
    removal_success = remove_inactive_tasks(records=records)
    return (schedule_success, removal_success)