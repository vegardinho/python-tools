import os
import arrow
import re

TODAY = arrow.now()
NOW = TODAY.timestamp


# Only keep files x days old
def remove_old_files(path, exp_seconds, re_pattern=None):
    """
    :param path:        Where to search for files.
    :param exp_seconds: Seconds since creation to trigger deletion.
    :param pattern:     Optional. Pattern to match before deleting.
    """

    for f in os.listdir(path):
        f = os.path.join(path, f)
        if os.stat(f).st_mtime < NOW - exp_seconds:
            if os.path.isfile(f):
                if re_pattern:
                    if re.search(re_pattern, os.path.basename(f)):
                        os.remove(f)
                else:
                    os.remove(f)
