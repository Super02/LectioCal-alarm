import re
from datetime import datetime, timedelta
from os import environ as environ
import logging

import lectio
from tqdm import tqdm

import caldav

log = logging.getLogger("LectioCalDAV")

def main(*, use_tqdm=False):
    # Create lectio obj
    lec = lectio.Lectio(environ.get("LECTIO_INST_ID"))

    # Creds from env vars
    lec.authenticate(
        environ.get('LECTIO_USERNAME'),
        environ.get('LECTIO_PASSWORD')
    )

    # Get calendar from CalDAV URL, username and password
    cal = caldav.CalDavClient(
        environ.get('CALDAV_USERNAME'),
        environ.get('CALDAV_PASSWORD'),
        environ.get('CALDAV_URL')
    )

    # Get start and end dates, without hour, minute, seconds
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start+timedelta(days=30)

    # Get schedule for student
    sched = lec.get_schedule_for_student(
        lec.get_user_id(),
        start,
        end
    )

    # List of uids, used later for deleting non-existent modules
    uids = []

    # Iterate over all modules
    sched_iter = sched
    if use_tqdm:
        sched_iter = tqdm(sched_iter, "Importing modules into CalDAV")
    else:
        print("Importing modules into CalDAV")

    for module in sched_iter:
        # Example: no title: 3.b Da; with title: 3.b Da - Never gonna give you up
        title = module.subject
        if module.title is not None:
            title += f' - {module.title}'
        
        # Get uid from module title get params, and append it to uids list
        uids.append("lecmod"+re.search(r"absid=(.*?)&", module.url)[1])
        
        # Add module url to event description, and optionally add extra info if present
        desc = re.match(r"(.*?)&", module.url)[1]
        if module.extra_info:
            desc += "\n\n" + module.extra_info
        
        # Color info (changed, deleted)
        color = None
        if module.status == 1: # Module changed
            color = "green"
        elif module.status == 2: # Module deleted
            color = "red"

        # Save the event
        cal.add_event(
            uid=uids[-1],
            start=module.start_time,
            end=module.end_time,
            summary=title,
            desc=desc,
            color=color
        )

    # Get all cal events within start, end
    events = cal.get_events(start, end)

    # Remove leftover events
    print("Checking if there are any untracked modules")
    for e in events:
        # Extract uid from ical
        uid = e.subcomponents[0].get("uid")

        if uid not in uids:
            # Get more info for logging
            component = e.subcomponents[0]

            start = component.get("dtstart")
            end = component.get("dtend")
            summary = component.get("summary")
            log.warning(f"Deleting module {uid}, start time: {start.dt.isoformat()}, end time: {end.dt.isoformat()}, summary: {summary}")

            cal.delete_event(uid)

if __name__ == '__main__':
    print("Starting Lectio.py ft. CalDAV")
    main(use_tqdm=True)
