import os
from pathlib import Path


def dir_empty(dir_path: Path):
    """
    Credit to https://stackoverflow.com/questions/57968829
    """
    return not next(os.scandir(dir_path), None)
