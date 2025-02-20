import os
import arrow
import re

TODAY = arrow.now()
NOW = TODAY.timestamp


# Only keep files x days old
def remove_old_files(path, exp_days, re_pattern=None):
    """
    :param path:        Where to search for files.
    :param exp_days:    Days since creation to trigger deletion.
    :param re_pattern:     Optional. Pattern to match before deleting.
    """
    exp_seconds = exp_days * 24 * 3600

    try:
        for f in os.listdir(path):
            f = os.path.join(path, f)
            if os.stat(f).st_mtime < NOW - exp_seconds:
                if os.path.isfile(f):
                    if re_pattern:
                        if re.search(re_pattern, os.path.basename(f)):
                            os.remove(f)
                    else:
                        os.remove(f)
    except Exception as err:
        raise FileNotFoundError(f"Could not delete files '{path}'.")

