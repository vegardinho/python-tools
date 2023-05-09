from pathlib import Path


def create_files(files):
    for file in files:
        Path(file).parents[0].mkdir(parents=True, exist_ok=True)
        Path(file).touch(exist_ok=True)
