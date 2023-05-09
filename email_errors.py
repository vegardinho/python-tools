import json
import arrow
from pathlib import Path
import notify
import os

from i_o_utilities import create_files

# First direct error email, then error summary at the end of the day
# Then error summary on day 3, then day 7 etc.

SEND_DAYS = [0, 1, 3, 7, 14, 31]


def email_errors(exception, email, history_file='email.out', log_file=None):
    create_files([history_file])

    if not exception:
        # clean sendDates

    with open(history_file, 'r') as fp:
        if fp.read() == '':
            datedelta = 0
        else:
            dates = json.load(fp)

            delta = arrow.get(dates[0].date()) - arrow.get(dates[-1].date())
            datedelta = delta.days

    if datedelta >= SEND_DAYS[len(dates)]:
        notify.mail(email, 'Feil under kjøring av skript', exception, os.path.abspath(log_file))

    # Read json file with arrow dates in list (or create if not exists)
    # Then calculate whether to send or not
    # Send
    # Dump updated json object

    # TODO: If run without sending, mark somehow
    # TODO: How many errors lately? Include in email.

    # {sendDates: [], errors: {count: int, lastError: date}}

if __name__ == '__main__':
    # Test use case
    # email_errors('./all.log', './send.history')
    notify.mail('landsverk.vegard@gmail.com', 'Test', 'Vi sender files',
                files=['/Users/vegardlandsverk/Downloads/unnamed.png'])
