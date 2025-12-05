from enum import Enum

class Platform(Enum):
    WINDOWS_SYS = "windows_sys"
    WINDOWS_USER = "windows_user"
    MACOS_ARM = "macos_arm"
    MACOS_X64 = "macos_x64"
    DEBIAN_X64 = "debian_x64"
    DEBIAN_ARM = "debian_arm"
    REDHAT_X64 = "redhat_x64"
    REDHAT_ARM = "redhat_arm"

# Mapping from Platform enum to the checksum filename template
PLATFORM_CHECKSUM_FILES = {
    Platform.WINDOWS_SYS: "Positron-{version}-Setup-x64.exe",
    Platform.WINDOWS_USER: "Positron-{version}-UserSetup-x64.exe",
    Platform.MACOS_ARM: "Positron-{version}-arm64.dmg",
    Platform.MACOS_X64: "Positron-{version}-x64.dmg",
    Platform.DEBIAN_X64: "Positron-{version}-x64.deb",
    Platform.DEBIAN_ARM: "Positron-{version}-arm64.deb",
    Platform.REDHAT_X64: "Positron-{version}-x64.rpm",
    Platform.REDHAT_ARM: "Positron-{version}-arm64.rpm",
}