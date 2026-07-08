"""项目配置：从 .env 读取设置。"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

# Kaggle credentials
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_KEY = os.getenv("KAGGLE_KEY")

# Paths
DATA_RAW_PATH = BASE_DIR / os.getenv("DATA_RAW_PATH", "data/raw")
DATA_PROCESSED_PATH = BASE_DIR / os.getenv("DATA_PROCESSED_PATH", "data/processed")

DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)