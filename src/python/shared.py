import appdirs
import os
from pathlib import Path
import atexit
import shutil
from dotenv import load_dotenv

from .engine.db import Db
try:
    load_dotenv()
except OSError:
    pass


def resource_path(relative_path: str) -> str:
    base_path = os.getenv("ROOT_PATH", str(Path(__file__).joinpath("../../..")))
    return str(Path(base_path).joinpath(relative_path).resolve())


class Config:
    PORT = int(os.getenv("PORT", "34972"))

    COLLECTION = os.getenv("COLLECTION", os.path.join(appdirs.user_data_dir("rep2recall-sqlite"), "user.db"))
    Path(COLLECTION).parent.mkdir(parents=True, exist_ok=True)

    DIR = Path(COLLECTION).parent.resolve()
    UPLOAD_FOLDER = DIR.joinpath("tmp")
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    atexit.register(shutil.rmtree, str(UPLOAD_FOLDER))

    DB = Db(COLLECTION)
    atexit.register(DB.close)

    MEDIA_FOLDER = DIR.joinpath("media")
    MEDIA_FOLDER.mkdir(exist_ok=True)
