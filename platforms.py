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