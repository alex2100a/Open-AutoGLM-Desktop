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


def get_all_windows() -> list[dict[str, Any]]:
    """
    获取所有打开的窗口列表。

    Returns:
        窗口信息列表，每个窗口包含 title, process, pid, hwnd 等信息。
    """
    system = platform.system().lower()
    windows: list[dict[str, Any]] = []

    if system == "windows":
        try:
            import win32gui
            import win32process
            import psutil

            def enum_windows_callback(hwnd, windows_list):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:  # 只包含有标题的窗口
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            process = psutil.Process(pid)
                            process_name = process.name()
                            rect = win32gui.GetWindowRect(hwnd)
                            x, y, right, bottom = rect
                            windows_list.append(
                                {
                                    "hwnd": hwnd,
                                    "title": title,
                                    "process": process_name,
                                    "pid": pid,
                                    "x": x,
                                    "y": y,
                                    "width": right - x,
                                    "height": bottom - y,
                                }
                            )
                        except Exception:
                            pass
                return True

            win32gui.EnumWindows(enum_windows_callback, windows)
        except ImportError:
            pass
        except Exception as e:
            print(f"获取窗口列表失败: {e}")

    elif system == "darwin":  # macOS
        try:
            import subprocess

            script = """
            tell application "System Events"
                set windowList to {}
                repeat with proc in every application process
                    try
                        set procName to name of proc
                        repeat with win in windows of proc
                            try
                                set winTitle to title of win
                                set end of windowList to procName & "|" & winTitle
                            end try
                        end repeat
                    end try
                end repeat
                return windowList
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if "|" in line:
                        parts = line.split("|", 1)
                        windows.append(
                            {
                                "title": parts[1] if len(parts) > 1 else "",
                                "process": parts[0] if parts else "Unknown",
                                "pid": 0,
                            }
                        )
        except Exception as e:
            print(f"获取窗口列表失败: {e}")

    elif system == "linux":
        try:
            import subprocess

            # 使用 xdotool 获取窗口列表
            result = subprocess.run(
                ["xdotool", "search", "--onlyvisible", "--name", ".*"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                window_ids = result.stdout.strip().split("\n")
                for wid in window_ids:
                    if wid:
                        try:
                            # 获取窗口标题
                            title_result = subprocess.run(
                                ["xdotool", "getwindowname", wid],
                                capture_output=True,
                                text=True,
                                timeout=5,
                            )
                            title = (
                                title_result.stdout.strip()
                                if title_result.returncode == 0
                                else ""
                            )
                            if title:
                                windows.append({"title": title, "process": "Unknown", "pid": 0})
                        except Exception:
                            pass
        except Exception as e:
            print(f"获取窗口列表失败: {e}")

    return windows


def find_window_by_app(app_name: str) -> dict[str, Any] | None:
    """
    查找应用程序的窗口。

    Args:
        app_name: 应用名称（进程名）。

    Returns:
        窗口信息字典，如果未找到返回 None。
    """
    windows = get_all_windows()
    for window in windows:
        process_name = window.get("process", "").lower()
        if app_name.lower() in process_name or process_name in app_name.lower():
            return window
    return None


def switch_to_window(window_title: str | None = None, process_name: str | None = None) -> bool:
    """
    切换到指定窗口。

    Args:
        window_title: 窗口标题（部分匹配）。
        process_name: 进程名称。

    Returns:
        True 如果切换成功，False 如果未找到窗口。
    """
    system = platform.system().lower()

    if system == "windows":
        try:
            import win32gui
            import win32con

            def find_window_callback(hwnd, target):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if target["title"] and target["title"].lower() in title.lower():
                        target["hwnd"] = hwnd
                        return False
                    elif target["process"]:
                        try:
                            import win32process
                            import psutil

                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            process = psutil.Process(pid)
                            if target["process"].lower() in process.name().lower():
                                target["hwnd"] = hwnd
                                return False
                        except Exception:
                            pass
                return True

            target = {"title": window_title or "", "process": process_name or "", "hwnd": None}
            win32gui.EnumWindows(find_window_callback, target)

            if target["hwnd"]:
                win32gui.ShowWindow(target["hwnd"], win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(target["hwnd"])
                return True
        except ImportError:
            pass
        except Exception as e:
            print(f"切换窗口失败: {e}")

    elif system == "darwin":  # macOS
        try:
            import subprocess

            if process_name:
                script = f"""
                tell application "{process_name}"
                    activate
                end tell
                """
            elif window_title:
                script = f"""
                tell application "System Events"
                    set frontApp to first application process whose frontmost is true
                    repeat with proc in application processes
                        try
                            repeat with win in windows of proc
                                if title of win contains "{window_title}" then
                                    set frontmost of proc to true
                                    return
                                end if
                            end repeat
                        end try
                    end repeat
                end tell
                """
            else:
                return False

            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"切换窗口失败: {e}")

    elif system == "linux":
        try:
            import subprocess

            if window_title:
                result = subprocess.run(
                    ["xdotool", "search", "--name", window_title, "windowactivate"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return result.returncode == 0
        except Exception as e:
            print(f"切换窗口失败: {e}")

    return False
