from enum import Enum
from cusTypes.version import Version

class System(Enum):
    WINDOWS_SYS = "Windows (System)"
    WINDOWS_USER = "Windows (User)"
    MACOS = "MacOS"
    DEBIAN = "Debian/Ubuntu Linux"
    REDHAT = "Red Hat Linux"

class Architecture(Enum):
    X64 = "x64"
    ARM = "ARM"

class Platform(Enum):
    WINDOWS_SYS = (
        System.WINDOWS_SYS,
        Architecture.X64,
        "Positron-{version}-Setup-x64.exe",
        "https://cdn.posit.co/positron/dailies/win/x86_64/Positron-{version}-Setup-x64.exe",
    )
    WINDOWS_SYS_ARM = (
        System.WINDOWS_SYS,
        Architecture.ARM,
        "Positron-{version}-Setup-arm64.exe",
        "https://cdn.posit.co/positron/dailies/win/arm64/Positron-{version}-Setup-arm64.exe",
    )
    WINDOWS_USER = (
        System.WINDOWS_USER,
        Architecture.X64,
        "Positron-{version}-UserSetup-x64.exe",
        "https://cdn.posit.co/positron/dailies/win/x86_64/Positron-{version}-UserSetup-x64.exe",
    )
    WINDOWS_USER_ARM = (
        System.WINDOWS_USER,
        Architecture.ARM,
        "Positron-{version}-UserSetup-arm64.exe",
        "https://cdn.posit.co/positron/dailies/win/arm64/Positron-{version}-UserSetup-arm64.exe",
    )
    MACOS_ARM = (
        System.MACOS,
        Architecture.ARM,
        "Positron-{version}-arm64.dmg",
        "https://cdn.posit.co/positron/dailies/mac/arm64/Positron-{version}-arm64.dmg",
    )
    MACOS_X64 = (
        System.MACOS,
        Architecture.X64,
        "Positron-{version}-x64.dmg",
        "https://cdn.posit.co/positron/dailies/mac/x64/Positron-{version}-x64.dmg",
    )
    DEBIAN_X64 = (
        System.DEBIAN,
        Architecture.X64,
        "Positron-{version}-x64.deb",
        "https://cdn.posit.co/positron/dailies/deb/x86_64/Positron-{version}-x64.deb",
    )
    DEBIAN_ARM = (
        System.DEBIAN,
        Architecture.ARM,
        "Positron-{version}-arm64.deb",
        "https://cdn.posit.co/positron/dailies/deb/arm64/Positron-{version}-arm64.deb",
    )
    REDHAT_X64 = (
        System.REDHAT,
        Architecture.X64,
        "Positron-{version}-x64.rpm",
        "https://cdn.posit.co/positron/dailies/rpm/x86_64/Positron-{version}-x64.rpm",
    )
    REDHAT_ARM = (
        System.REDHAT,
        Architecture.ARM,
        "Positron-{version}-arm64.rpm",
        "https://cdn.posit.co/positron/dailies/rpm/arm64/Positron-{version}-arm64.rpm",
    )

    def __init__(self, system: System, architecture: Architecture, checksum_template: str, url_template: str):
        self.system = system
        self.architecture = architecture
        self.checksum_template = checksum_template
        self.url_template = url_template

    @property
    def filename_template(self) -> str:
        """Get the checksum filename template for this platform."""
        return self.checksum_template

    def get_file_name(self, version: Version) -> str:
        """Format the checksum filename with the given version."""
        return self.checksum_template.format(version=version)

    def url(self, version: Version) -> str:
        """Generate the download URL for this platform with the given version."""
        return self.url_template.format(version=str(version))

    @classmethod
    def get(cls, system: System, architecture: Architecture) -> "Platform":
        """Get the Platform enum member for the given system and architecture."""
        for platform in cls:
            if platform.system == system and platform.architecture == architecture:
                return platform
        raise ValueError(f"No platform found for {system} {architecture}")
