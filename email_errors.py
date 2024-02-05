import json
import arrow
from pathlib import Path
import notify
import os
from my_logger import MyLogger

from i_o_utilities import create_files

# First direct error email, then error summary at the end of the day
# Then error summary on day 3, then day 7 etc.

SEND_INTERVALS = [0, 1, 2, 4, 7, 15]
FALLBACK_INTERVAL = 15
NOW = arrow.now()

def email_errors(exception, email, history_file='error_email.out', logger=None, log_file=None):
    log_file_path = os.path.abspath(log_file) if log_file else None
    log = logger
    if not log:
        log = MyLogger().add_handler().retrieve_logger()

    log.info("Checking for sent errors.")
    create_files(history_file)


    # TODO: What parameters does other scripts call this script with? What about exception parameter?

    log.info("Opening history file.")
    with open(history_file, 'r+') as fp:
        fp_content = fp.read()
        fp.seek(0)

        days_since_send = 0 

        log.info("Reading history")
        if fp_content == '':
            log.debug("Empty history file --> assume never sent error message. Create dict.")
            dates = {"error":[], "error_sent":[]} 
        else:
            log.debug("Not empty send-file")
            dates = json.loads(fp_content)
            last_send_date = arrow.get(dates["error_sent"][-1])
            days_since_send = (NOW - last_send_date).days
        log.info("History read.")

        dates["error"].append(NOW.format()) 
    
        next_send_limit = FALLBACK_INTERVAL
        num_sent = len(dates["error_sent"])
        if num_sent < len(SEND_INTERVALS):
            next_send_limit = SEND_INTERVALS[num_sent]

        # Send mail if more time passed than corresponding interval
        print(f'last: {days_since_send}, next: {next_send_limit}')
        if days_since_send >= next_send_limit:
            log.info("Day limit exceeded. Attempting to send email")
            try:
                body = f'Antall feilkjøringer siden nullstilling: {len(dates["error"])}.\nFeilmelding: {exception}'
                notify.mail(email, 'Feil under kjøring av skript', body, log_file_path)
            except Exception as e:
                # Exit before marking as send if error on send. Make sure fp is not corrupted.
                log.error(f'Could not send email. Wiping history.\nError:{e}')
                fp.seek(0)
                fp.write('')
                fp.close()

                exit(1)
            log.info("Email sent. Appending to list.")
            dates["error_sent"].append(NOW.format()) 
        fp.seek(0)
        log.info("Dumping updated dates to json")
        json.dump(dates, fp)

if __name__ == '__main__':
    # Test use case
    email_errors(None, 'landsverk.vegard@gmail.com', './send.history', log_file='./send.history')
    # notify.mail('landsverk.vegard@gmail.com', 'Test', 'Vi sender files',
    #             files=['/Users/vegardlandsverk/Downloads/unnamed.png'])
