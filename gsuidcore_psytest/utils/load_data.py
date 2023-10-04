from pathlib import Path
from typing import Optional

import aiofiles
from msgspec import json as msgjson

from .models import TestData

LIB_PATH = Path(__file__).parent / 'test_lib'


async def load_test(name: str) -> Optional[TestData]:
    path = LIB_PATH / name / 'data.json'
    if path.exists():
        async with aiofiles.open(path, 'r', encoding='UTF-8') as f:
            return msgjson.decode(await f.read(), type=TestData)
    return None
