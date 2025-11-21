from enum import Enum
from functools import total_ordering
from typing import TypedDict
import re

class Platform(Enum):
    WINDOWS_SYS = "windows_sys"
    WINDOWS_USER = "windows_user"
    MACOS_ARM = "macos_arm"
    MACOS_X64 = "macos_x64"
    DEBIAN_X64 = "debian_x64"
    DEBIAN_ARM = "debian_arm"
    REDHAT_X64 = "redhat_x64"
    REDHAT_ARM = "redhat_arm"

class DailyRecord(TypedDict):
    version: Version
    fetched_at: str

@total_ordering
class Version:
    year: int
    month: int
    number: int

    def __init__(self, year: int | str, month: int | str, number: int | str) -> None:
        """
        Construct either as:
          Version(2025, 3, 2)
          Version("2025", "03", "2")
          Version("2025", "3", "2")
        """
        if year is None or month is None or number is None:
            raise TypeError(
                "Version expects three values: year, month, number"
            )

        try:
            self.year = int(year)
            self.month = int(month)
            self.number = int(number)
        except Exception as exc:
            raise ValueError(
                "year, month and number must be integers or numeric strings"
            ) from exc

        self._validate()

    @classmethod
    def from_string(cls, s: str) -> Version:
        RE = re.compile(r"^(\d{4})\.(\d{1,2})\.0-(\d+)$")
        m = RE.fullmatch(s.strip())
        if not m:
            raise ValueError(f"invalid version string: {s!r}")
        return Version(m.group(1), m.group(2), m.group(3))

    def _validate(self):
        if not (1 <= self.month <= 12):
            raise ValueError(f"month must be in 1..12 (got {self.month})")
        if self.year < 1900:
            raise ValueError(f"year must be >= 1900 (got {self.year})")
        if self.number < 0:
            raise ValueError(f"number must be non-negative (got {self.number})")

    def __str__(self) -> str:
        return f"{self.year}.{self.month:02d}.0-{self.number}"

    def __repr__(self) -> str:
        return f"Version(year={self.year}, month={self.month}, number={self.number})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (self.year, self.month, self.number) == (
            other.year,
            other.month,
            other.number,
        )

    def __lt__(self, other) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (self.year, self.month, self.number) < (
            other.year,
            other.month,
            other.number,
        )

    def __hash__(self) -> int:
        """Return a hash consistent with equality.

        Uses the tuple of (year, month, number) so Version objects
        can be used as dict keys and in sets.
        """
        return hash((self.year, self.month, self.number))
