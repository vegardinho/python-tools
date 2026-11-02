from pathlib import Path
import os.path
import os
import re
import arrow


__all__ = ["create_files", "remove_old_files"]

def create_files(*args):
    for file in args:
        file_path = Path(os.path.expanduser(file)) #expand tilde and load path
        if not file_path.exists(): # Check first, otherwise we change creation time of files/folders
            file_path.parents[0].mkdir(parents=True, exist_ok=True)
            file_path.touch()


def remove_old_files(path, exp_days, re_pattern=None):
    """Remove files older than ``exp_days`` from ``path``."""
    now = arrow.now().timestamp()
    exp_seconds = exp_days * 24 * 3600

    try:
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            if os.stat(file_path).st_mtime < now - exp_seconds:
                if os.path.isfile(file_path):
                    if re_pattern:
                        if re.search(re_pattern, os.path.basename(file_path)):
                            os.remove(file_path)
                    else:
                        os.remove(file_path)
    except Exception as err:
        raise FileNotFoundError(f"Could not delete files '{path}'.") from err
