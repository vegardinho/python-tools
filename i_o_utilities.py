from pathlib import Path
import os.path

def create_files(*args):
    for file in args:
        file_path = Path(os.path.expanduser(file)) #expand tilde and load path
        file_path.parents[0].mkdir(parents=True, exist_ok=True)
        file_path.touch(exist_ok=True)

# TESTING
if __name__ == '__main__':
    create_files('~/Downloads/arne/går/mot/enfil.txt')
