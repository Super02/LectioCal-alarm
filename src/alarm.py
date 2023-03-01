import os, requests
from datetime import timedelta, datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time
from pytz import timezone
alarms = []
ignore = ["Alle", "Frivillig"]
jobs = {}

scheduler = BackgroundScheduler()
scheduler.start()
TIMEZONE = timezone('Europe/Copenhagen')
debug = False

def activateAlarm():
    if(debug):
        print("Activating alarm")
        requests.post("https://discord.com/api/webhooks/1078046103867502632/xOND4H1UJS4NZn0bUgcG2ctp4y4FggAdvyAwMoZBxa9aEOmwhgYE3j_3lWHAk55k5ILZ", json={"content": "LectioPy alarm activated! (DEBUG)"})
    else:
        requests.get("https://api.voicemonkey.io/trigger?access_token=" + os.environ["monkey_access_token"] + "&secret_token=" + os.environ["monkey_secret_token"] + "&monkey=lectiopy")
        requests.post("https://discord.com/api/webhooks/1078046103867502632/xOND4H1UJS4NZn0bUgcG2ctp4y4FggAdvyAwMoZBxa9aEOmwhgYE3j_3lWHAk55k5ILZ", json={"content": "LectioPy alarm activated!"})

def updateAlarm(schedule: list):
    print("Updating alarms")
    sched = schedule.keys()
    temp = []
    # Make an alarm system that runs activateAlarm() 75 minutes before the first module in the day starts. Sort out modules that are not in the 8-15 time range and are not on weekdays. Also sort out modules that are in the ignore list.
    for module in sched:
        if module.start_time.hour >= 8 and module.start_time.hour <= 15 and module.start_time.weekday() <= 4 and [ign in (module.subject or "") or ign in (module.title or "") for ign in ignore].count(True) < 1 and module.status != 2:
            # Check if the module is the first in the day
            if module.start_time.date() not in [x.start_time.date() for x in temp]:
                temp.append(module)
    alarms = []
    if len(temp) > 0:
        for i in range(len(temp)):
            if(temp[i].subject == "L vf ps 1 3g" and temp[i].start_time.hour == 8 and temp[i].start_time.minute == 15):
                alarms.append([temp[i].start_time - timedelta(minutes=55), schedule.get(temp[i])])
                continue
            alarms.append([temp[i].start_time - timedelta(minutes=75), schedule.get(temp[i])])
    alarms.sort()
    # Remove all jobs that does not have an id in the alarms list
    for job in jobs:
        if job not in [x[1] for x in alarms]:
            try:
                scheduler.remove_job(job)
                jobs[job].remove()
            except Exception as e:
                pass
    for alarm in alarms:
        jobs[alarm[1]] = scheduler.add_job(activateAlarm, 'date', run_date=alarm[0], id=alarm[1], replace_existing=True)