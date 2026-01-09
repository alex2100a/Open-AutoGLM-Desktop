"""桌面连接和显示器管理模块。"""

import platform
from dataclasses import dataclass
from typing import Any

try:
    import mss
except ImportError:
    mss = None

try:
    import pyautogui
except ImportError:
    pyautogui = None


@dataclass
class DisplayInfo:
    """显示器信息。"""

    display_id: int
    width: int
    height: int
    x: int  # 多显示器位置
    y: int
    is_primary: bool


class DesktopConnection:
    """桌面连接管理类。"""

    def __init__(self, display_id: int | None = None):
        """
        初始化桌面连接。

        Args:
            display_id: 指定显示器ID，None 为主显示器。
        """
        self.display_id = display_id
        self.platform = platform.system().lower()

    def get_primary_display(self) -> DisplayInfo:
        """获取主显示器信息。"""
        displays = list_displays()
        for display in displays:
            if display.is_primary:
                return display
        return displays[0] if displays else DisplayInfo(0, 1920, 1080, 0, 0, True)

    def get_display(self, display_id: int | None = None) -> DisplayInfo:
        """
        获取指定显示器的信息。

        Args:
            display_id: 显示器ID，None 为当前设置的显示器。

        Returns:
            显示器信息。
        """
        if display_id is None:
            display_id = self.display_id

        displays = list_displays()
        if display_id is not None:
            for display in displays:
                if display.display_id == display_id:
                    return display

        return self.get_primary_display()


def list_displays() -> list[DisplayInfo]:
    """
    列出所有显示器。

    Returns:
        显示器信息列表。
    """
    displays: list[DisplayInfo] = []

    if mss is None:
        # 如果没有 mss，使用 pyautogui 获取屏幕尺寸
        if pyautogui:
            width, height = pyautogui.size()
            displays.append(DisplayInfo(0, width, height, 0, 0, True))
        else:
            # 默认值
            displays.append(DisplayInfo(0, 1920, 1080, 0, 0, True))
        return displays

    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            # monitors[0] 是所有显示器的组合，从索引1开始是各个显示器
            for i, monitor in enumerate(monitors[1:], start=0):
                displays.append(
                    DisplayInfo(
                        display_id=i,
                        width=monitor["width"],
                        height=monitor["height"],
                        x=monitor["left"],
                        y=monitor["top"],
                        is_primary=(i == 0),  # 第一个为主显示器
                    )
                )
    except Exception as e:
        print(f"获取显示器信息失败: {e}")
        # 返回默认值
        if pyautogui:
            width, height = pyautogui.size()
            displays.append(DisplayInfo(0, width, height, 0, 0, True))
        else:
            displays.append(DisplayInfo(0, 1920, 1080, 0, 0, True))

    return displays


def get_active_window_info() -> dict[str, Any]:
    """
    获取当前活动窗口信息（标题、进程、位置）。

    Returns:
        包含窗口信息的字典。
    """
    system = platform.system().lower()

    if system == "windows":
        try:
            import win32gui
            import win32process
            import psutil

            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name()

            rect = win32gui.GetWindowRect(hwnd)
            x, y, right, bottom = rect
            width = right - x
            height = bottom - y

            return {
                "title": title,
                "process": process_name,
                "pid": pid,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            }
        except ImportError:
            return {"title": "Unknown", "process": "Unknown", "pid": 0}
        except Exception as e:
            print(f"获取窗口信息失败: {e}")
            return {"title": "Unknown", "process": "Unknown", "pid": 0}

    elif system == "darwin":  # macOS
        try:
            import subprocess

            # 使用 AppleScript 获取活动窗口信息
            script = """
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set appName to name of frontApp
                set windowTitle to name of first window of frontApp
                return appName & "|" & windowTitle
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split("|", 1)
                return {
                    "title": parts[1] if len(parts) > 1 else "",
                    "process": parts[0] if parts else "Unknown",
                    "pid": 0,
                }
        except Exception as e:
            print(f"获取窗口信息失败: {e}")

    elif system == "linux":
        try:
            import subprocess

            # 使用 xdotool 获取活动窗口信息
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                title = result.stdout.strip()
                # 获取进程名
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowpid"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                pid = int(result.stdout.strip()) if result.returncode == 0 else 0
                return {"title": title, "process": "Unknown", "pid": pid}
        except Exception as e:
            print(f"获取窗口信息失败: {e}")

    return {"title": "Unknown", "process": "Unknown", "pid": 0}
