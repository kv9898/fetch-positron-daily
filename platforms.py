from enum import Enum


class Platform(Enum):
    WINDOWS_SYS = (
        "windows_sys",
        "Positron-{version}-Setup-x64.exe",
        "https://cdn.posit.co/positron/dailies/win/x86_64/Positron-{version}-Setup-x64.exe",
    )
    WINDOWS_USER = (
        "windows_user",
        "Positron-{version}-UserSetup-x64.exe",
        "https://cdn.posit.co/positron/dailies/win/x86_64/Positron-{version}-UserSetup-x64.exe",
    )
    MACOS_ARM = (
        "macos_arm",
        "Positron-{version}-arm64.dmg",
        "https://cdn.posit.co/positron/dailies/mac/arm64/Positron-{version}-arm64.dmg",
    )
    MACOS_X64 = (
        "macos_x64",
        "Positron-{version}-x64.dmg",
        "https://cdn.posit.co/positron/dailies/mac/x64/Positron-{version}-x64.dmg",
    )
    DEBIAN_X64 = (
        "debian_x64",
        "Positron-{version}-x64.deb",
        "https://cdn.posit.co/positron/dailies/deb/x86_64/Positron-{version}-x64.deb",
    )
    DEBIAN_ARM = (
        "debian_arm",
        "Positron-{version}-arm64.deb",
        "https://cdn.posit.co/positron/dailies/deb/arm64/Positron-{version}-arm64.deb",
    )
    REDHAT_X64 = (
        "redhat_x64",
        "Positron-{version}-x64.rpm",
        "https://cdn.posit.co/positron/dailies/rpm/x86_64/Positron-{version}-x64.rpm",
    )
    REDHAT_ARM = (
        "redhat_arm",
        "Positron-{version}-arm64.rpm",
        "https://cdn.posit.co/positron/dailies/rpm/arm64/Positron-{version}-arm64.rpm",
    )

    def __init__(self, platform_id, checksum_template, url_template):
        self.platform_id = platform_id
        self.checksum_template = checksum_template
        self.url_template = url_template

    @property
    def filename_template(self):
        """Get the checksum filename template for this platform."""
        return self.checksum_template

    def get_file_name(self, version):
        """Format the checksum filename with the given version."""
        return self.checksum_template.format(version=version)
