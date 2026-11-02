import os
import time

import pytest

from python_tools.i_o_utilities import create_files, remove_old_files


def test_create_files_creates_parent_directories_and_files(tmp_path):
    target = tmp_path / "nested" / "output.txt"

    create_files(str(target))

    assert target.is_file()


def test_create_files_does_not_change_existing_file_mtime(tmp_path):
    target = tmp_path / "output.txt"
    target.write_text("existing", encoding="utf-8")
    original_mtime = target.stat().st_mtime

    time.sleep(0.01)
    create_files(str(target))

    assert target.read_text(encoding="utf-8") == "existing"
    assert target.stat().st_mtime == original_mtime


def test_remove_old_files_removes_expired_files(tmp_path):
    old_file = tmp_path / "old.log"
    recent_file = tmp_path / "recent.log"
    old_file.touch()
    recent_file.touch()
    old_timestamp = time.time() - (3 * 24 * 3600)
    os.utime(old_file, (old_timestamp, old_timestamp))

    remove_old_files(str(tmp_path), exp_days=1)

    assert not old_file.exists()
    assert recent_file.exists()


def test_remove_old_files_applies_filename_pattern(tmp_path):
    matching = tmp_path / "old.log"
    other = tmp_path / "old.txt"
    for path in (matching, other):
        path.touch()
        old_timestamp = time.time() - (3 * 24 * 3600)
        os.utime(path, (old_timestamp, old_timestamp))

    remove_old_files(str(tmp_path), exp_days=1, re_pattern=r"\.log$")

    assert not matching.exists()
    assert other.exists()


def test_remove_old_files_wraps_invalid_path_errors(tmp_path):
    missing = tmp_path / "does-not-exist"

    with pytest.raises(FileNotFoundError, match="Could not delete files"):
        remove_old_files(str(missing), exp_days=1)
