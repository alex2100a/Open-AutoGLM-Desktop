"""桌面设备控制模块。"""

import platform
import subprocess
import time

try:
    import pyautogui
except ImportError:
    pyautogui = None

from phone_agent.config.apps_desktop import get_executable_path
from phone_agent.config.timing import TIMING_CONFIG


def tap(x: int, y: int, delay: float | None = None) -> None:
    """
    模拟鼠标左键点击。

    Args:
        x: X 坐标。
        y: Y 坐标。
        delay: 点击后的延迟（秒）。如果为 None，使用配置的默认值。
    """
    if delay is None:
        delay = TIMING_CONFIG.device.default_tap_delay

    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    pyautogui.click(x, y)
    time.sleep(delay)


def double_tap(x: int, y: int, delay: float | None = None) -> None:
    """
    模拟双击。

    Args:
        x: X 坐标。
        y: Y 坐标。
        delay: 双击后的延迟（秒）。如果为 None，使用配置的默认值。
    """
    if delay is None:
        delay = TIMING_CONFIG.device.default_double_tap_delay

    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    pyautogui.doubleClick(x, y)
    time.sleep(delay)


def right_click(x: int, y: int, delay: float | None = None) -> None:
    """
    模拟右键点击（桌面特有）。

    Args:
        x: X 坐标。
        y: Y 坐标。
        delay: 点击后的延迟（秒）。
    """
    if delay is None:
        delay = TIMING_CONFIG.device.default_tap_delay

    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    pyautogui.rightClick(x, y)
    time.sleep(delay)


def swipe(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration_ms: int | None = None,
    delay: float | None = None,
) -> None:
    """
    模拟鼠标拖拽。

    Args:
        start_x: 起始 X 坐标。
        start_y: 起始 Y 坐标。
        end_x: 结束 X 坐标。
        end_y: 结束 Y 坐标。
        duration_ms: 拖拽持续时间（毫秒）。如果为 None，自动计算。
        delay: 拖拽后的延迟（秒）。如果为 None，使用配置的默认值。
    """
    if delay is None:
        delay = TIMING_CONFIG.device.default_swipe_delay

    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    if duration_ms is None:
        # 根据距离自动计算持续时间
        dist = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
        duration_ms = max(100, min(int(dist / 10), 2000))  # 100-2000ms

    pyautogui.drag(start_x, start_y, end_x - start_x, end_y - start_y, duration=duration_ms / 1000.0, button="left")
    time.sleep(delay)


def scroll(x: int, y: int, clicks: int = 3, direction: str = "down") -> None:
    """
    模拟滚轮（桌面特有）。

    Args:
        x: X 坐标。
        y: Y 坐标。
        clicks: 滚动次数（正数向下，负数向上）。
        direction: 滚动方向，"down" 或 "up"。
    """
    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    scroll_amount = clicks if direction == "down" else -clicks
    pyautogui.scroll(scroll_amount, x=x, y=y)
    time.sleep(0.5)


def get_current_app() -> str:
    """
    获取当前活动窗口的应用名称。

    Returns:
        应用名称，如果无法获取则返回 "Desktop"。
    """
    system = platform.system().lower()

    if system == "windows":
        try:
            import win32gui
            import win32process
            import psutil

            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name()
        except ImportError:
            return "Desktop"
        except Exception:
            return "Desktop"

    elif system == "darwin":  # macOS
        try:
            import subprocess

            script = """
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                return name of frontApp
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

    elif system == "linux":
        try:
            import subprocess

            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowclassname"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

    return "Desktop"


def launch_app(app_name: str) -> bool:
    """
    启动应用程序。

    Args:
        app_name: 应用名称（必须在 apps_desktop.py 中配置）。

    Returns:
        True 如果应用启动成功，False 如果应用未找到。
    """
    system = platform.system().lower()
    executable = get_executable_path(app_name, system)

    if not executable:
        return False

    try:
        if system == "windows":
            # Windows: 直接启动可执行文件
            subprocess.Popen(executable, shell=True)
        elif system == "darwin":  # macOS
            # macOS: 使用 open 命令
            subprocess.Popen(["open", "-a", executable])
        elif system == "linux":
            # Linux: 使用 xdg-open 或直接执行
            subprocess.Popen([executable])
        else:
            return False

        time.sleep(TIMING_CONFIG.device.default_launch_delay)
        return True
    except Exception as e:
        print(f"启动应用失败: {e}")
        return False


def back(delay: float | None = None) -> None:
    """
    模拟返回（Alt+Left 或 ESC）。

    Args:
        delay: 操作后的延迟（秒）。如果为 None，使用配置的默认值。
    """
    if delay is None:
        delay = TIMING_CONFIG.device.default_back_delay

    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    system = platform.system().lower()
    if system == "windows":
        # 尝试 Alt+Left（浏览器返回）
        pyautogui.hotkey("alt", "left")
    else:
        # macOS/Linux: 使用 ESC
        pyautogui.press("esc")

    time.sleep(delay)


def home(delay: float | None = None) -> None:
    """
    最小化所有窗口/显示桌面。

    Args:
        delay: 操作后的延迟（秒）。如果为 None，使用配置的默认值。
    """
    if delay is None:
        delay = TIMING_CONFIG.device.default_home_delay

    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    system = platform.system().lower()
    if system == "windows":
        # Windows: Win+D 显示桌面
        pyautogui.hotkey("win", "d")
    elif system == "darwin":  # macOS
        # macOS: Cmd+H 隐藏当前应用，或 F11 显示桌面
        pyautogui.hotkey("command", "h")
    elif system == "linux":
        # Linux: 使用 Super+D（如果支持）
        pyautogui.hotkey("super", "d")

    time.sleep(delay)


def long_press(
    x: int,
    y: int,
    duration_ms: int = 3000,
    delay: float | None = None,
) -> None:
    """
    长按（桌面实现为右键点击）。

    Args:
        x: X 坐标。
        y: Y 坐标。
        duration_ms: 长按持续时间（毫秒）。
        delay: 操作后的延迟（秒）。如果为 None，使用配置的默认值。
    """
    if delay is None:
        delay = TIMING_CONFIG.device.default_long_press_delay

    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    # 桌面上的长按通常用右键点击实现
    pyautogui.rightClick(x, y)
    time.sleep(delay)
