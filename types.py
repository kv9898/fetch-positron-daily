from typing import TypedDict

class DailyRecord(TypedDict):
    version: str
    month: str
    build_number: int
    fetched_at: str