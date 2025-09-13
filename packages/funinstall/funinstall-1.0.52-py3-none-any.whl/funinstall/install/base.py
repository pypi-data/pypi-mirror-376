import sys
from abc import abstractmethod

from funutil import getLogger

logger = getLogger("funinstall")


class BaseInstall:
    def __init__(self, *args, **kwargs):
        pass

    def install(self, *args, **kwargs) -> bool:
        if sys.platform.startswith("linux"):
            logger.info("当前系统为 Linux")
            return self.install_linux(*args, **kwargs)
        elif sys.platform.startswith("darwin"):
            logger.info("当前系统为 macOS")
            return self.install_macos(*args, **kwargs)
        elif sys.platform.startswith("win"):
            logger.info("当前系统为 Windows")
            return self.install_windows(*args, **kwargs)
        else:
            logger.error("无法识别当前系统")
            return False

    @abstractmethod
    def install_linux(self, *args, **kwargs) -> bool:
        pass

    def install_macos(self, *args, **kwargs) -> bool:
        return self.install_linux(*args, **kwargs)

    def install_windows(self, *args, **kwargs) -> bool:
        return self.install_windows(*args, **kwargs)

    def uninstall(self, *args, **kwargs) -> bool:
        if sys.platform.startswith("linux"):
            logger.info("当前系统为 Linux")
            return self.uninstall_linux(*args, **kwargs)
        elif sys.platform.startswith("darwin"):
            logger.info("当前系统为 macOS")
            return self.uninstall_macos(*args, **kwargs)
        elif sys.platform.startswith("win"):
            logger.info("当前系统为 Windows")
            return self.uninstall_windows(*args, **kwargs)
        else:
            logger.error("无法识别当前系统")
            return False

    def uninstall_linux(self, *args, **kwargs) -> bool:
        pass

    def uninstall_macos(self, *args, **kwargs) -> bool:
        return self.install_linux(*args, **kwargs)

    def uninstall_windows(self, *args, **kwargs) -> bool:
        return self.install_windows(*args, **kwargs)
