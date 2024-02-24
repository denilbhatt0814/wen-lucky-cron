import os
redbeat_redis_url = os.environ["REDIS_REDBEAT_URL"]

beat_scheduler = 'redbeat.RedBeatScheduler'