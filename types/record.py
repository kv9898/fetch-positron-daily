
from typing import TypedDict
from platforms import Platform
from .version import Version


class DailyRecord(TypedDict):
    version: Version
    fetched_at: str


class DailyAvailability:
    version: Version
    available_platforms: dict[Platform, bool]

    def __init__(
        self, version: Version, available_platforms: dict[Platform, bool]
    ) -> None:
        self.version = version
        self.available_platforms = available_platforms
        self._validate_platforms()

    def _validate_platforms(self) -> None:
        """Verify that available_platforms contains all elements of the Platform enum."""
        # Get all platform enum members
        all_platforms = set(Platform)
        provided_platforms = set(self.available_platforms.keys())

        missing_platforms = all_platforms - provided_platforms
        extra_platforms = provided_platforms - all_platforms

        if missing_platforms:
            raise ValueError(
                f"Missing platforms in available_platforms: {missing_platforms}. "
                f"Must include all platforms from Platform enum: {all_platforms}"
            )

        if extra_platforms:
            raise ValueError(
                f"Unknown platforms in available_platforms: {extra_platforms}. "
                f"Only platforms from Platform enum are allowed: {all_platforms}"
            )

        # Also verify all values are booleans
        for platform, is_available in self.available_platforms.items():
            if not isinstance(is_available, bool):
                raise TypeError(
                    f"Value for platform {platform} must be bool, got {type(is_available).__name__}"
                )

    def __eq__(self, other) -> bool:
        if not isinstance(other, DailyAvailability):
            return NotImplemented
        return self.version == other.version

    def __lt__(self, other) -> bool:
        if not isinstance(other, DailyAvailability):
            return NotImplemented
        return self.version < other.version

    def __le__(self, other) -> bool:
        if not isinstance(other, DailyAvailability):
            return NotImplemented
        return self.version <= other.version



