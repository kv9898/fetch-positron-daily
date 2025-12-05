from enum import Enum
from cusTypes.version import Version


class Platform(Enum):
    WINDOWS_SYS = (
        "Win (System)",
        "Positron-{version}-Setup-x64.exe",
        "https://cdn.posit.co/positron/dailies/win/x86_64/Positron-{version}-Setup-x64.exe",
    )
    WINDOWS_USER = (
        "Win (User)",
        "Positron-{version}-UserSetup-x64.exe",
        "https://cdn.posit.co/positron/dailies/win/x86_64/Positron-{version}-UserSetup-x64.exe",
    )
    MACOS_ARM = (
        "MacOS (ARM)",
        "Positron-{version}-arm64.dmg",
        "https://cdn.posit.co/positron/dailies/mac/arm64/Positron-{version}-arm64.dmg",
    )
    MACOS_X64 = (
        "MacOS (x64)",
        "Positron-{version}-x64.dmg",
        "https://cdn.posit.co/positron/dailies/mac/x64/Positron-{version}-x64.dmg",
    )
    DEBIAN_X64 = (
        "Deb/Ubuntu (x64)",
        "Positron-{version}-x64.deb",
        "https://cdn.posit.co/positron/dailies/deb/x86_64/Positron-{version}-x64.deb",
    )
    DEBIAN_ARM = (
        "Deb/Ubuntu (ARM)",
        "Positron-{version}-arm64.deb",
        "https://cdn.posit.co/positron/dailies/deb/arm64/Positron-{version}-arm64.deb",
    )
    REDHAT_X64 = (
        "RHEL (x64)",
        "Positron-{version}-x64.rpm",
        "https://cdn.posit.co/positron/dailies/rpm/x86_64/Positron-{version}-x64.rpm",
    )
    REDHAT_ARM = (
        "RHEL (ARM)",
        "Positron-{version}-arm64.rpm",
        "https://cdn.posit.co/positron/dailies/rpm/arm64/Positron-{version}-arm64.rpm",
    )

    def __init__(self, display_name, checksum_template, url_template):
        self.display_name = display_name
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
