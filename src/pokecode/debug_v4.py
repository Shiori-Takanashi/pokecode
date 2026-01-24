from pathlib import Path
import shutil


def makedir(dirname: str) -> None:
    project = Path(__file__).parents[2]
    dirpath = project / dirname
    if dirpath.exists():
        shutil.rmtree(dirpath)
    dirpath.mkdir(parents=True, exist_ok=False)
