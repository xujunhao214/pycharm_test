# commons/enums.py
from enum import Enum
import pymysql


class Environment(Enum):
    TEST = "test"
    DEV = "dev"
