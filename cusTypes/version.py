from __future__ import annotations
from functools import total_ordering
import re

@total_ordering
class Version:
    year: int
    month: int
    type: int # 0 = beta, 1 = release
    number: int

    def __init__(self, year: int | str, month: int | str, type: int | str, number: int | str) -> None:
        """
        Construct either as:
          Version(2025, 3, 0, 2)
          Version("2025", "03", "0", "2")
          Version("2025", "3", "0", "2")
        """
        if year is None or month is None or type is None or number is None:
            raise TypeError("Version expects four values: year, month, type, number")

        try:
            self.year = int(year)
            self.month = int(month)
            self.type = int(type)
            self.number = int(number)
        except Exception as exc:
            raise ValueError(
                "year, month, type and number must be integers or numeric strings"
            ) from exc

        self._validate()

    @classmethod
    def from_string(cls, s: str) -> Version:
        RE = re.compile(r"^(\d{4})\.(\d{1,2})\.(\d{1})-(\d+)$")
        m = RE.fullmatch(s.strip())
        if not m:
            raise ValueError(f"invalid version string: {s!r}")
        return Version(m.group(1), m.group(2), m.group(3), m.group(4))

    def _validate(self):
        if not (1 <= self.month <= 12):
            raise ValueError(f"month must be in 1..12 (got {self.month})")
        if self.year < 1900:
            raise ValueError(f"year must be >= 1900 (got {self.year})")
        # if self.type not in (0, 1):
        #     raise ValueError(f"type must be 0 (beta) or 1 (release) (got {self.type})")
        if self.number < 0:
            raise ValueError(f"number must be non-negative (got {self.number})")

    def __str__(self) -> str:
        return f"{self.year}.{self.month:02d}.{self.type}-{self.number}"

    def __repr__(self) -> str:
        return f"Version(year={self.year}, month={self.month}, type={self.type}, number={self.number})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (self.year, self.month, self.type, self.number) == (
            other.year,
            other.month,
            other.type,
            other.number,
        )

    def __lt__(self, other) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (self.year, self.month, self.type, self.number) < (
            other.year,
            other.month,
            other.type,
            other.number,
        )

    def __hash__(self) -> int:
        """Return a hash consistent with equality.

        Uses the tuple of (year, month, type, number) so Version objects
        can be used as dict keys and in sets.
        """
        return hash((self.year, self.month, self.type, self.number))