"""桌面输入控制模块。"""

import platform
import time

try:
    import pyautogui
    import pyperclip
except ImportError:
    pyautogui = None
    pyperclip = None

from phone_agent.config.timing import TIMING_CONFIG

from phone_agent.utils import get_logger

logger = get_logger(__name__)


def type_text(text: str, interval: float = 0.05) -> None:
    """
    模拟键盘输入文本。

    Args:
        text: 要输入的文本。
        interval: 每个字符之间的间隔（秒）。
    """
    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    # 对于中文或特殊字符，使用剪贴板方式更可靠
    if _needs_clipboard(text):
        _type_text_via_clipboard(text)
    else:
        pyautogui.write(text, interval=interval)
        time.sleep(TIMING_CONFIG.action.text_input_delay)


def _needs_clipboard(text: str) -> bool:
    """检查文本是否需要使用剪贴板方式输入。"""
    # 检查是否包含中文字符
    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            return True
    return False


def _type_text_via_clipboard(text: str) -> None:
    """通过剪贴板输入文本（用于中文等特殊字符）。"""
    if pyperclip is None:
        # 如果没有 pyperclip，尝试直接输入（可能失败）
        if pyautogui:
            pyautogui.write(text, interval=0.1)
        return

    try:
        # 保存当前剪贴板内容
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            old_clipboard = ""

        # 复制新文本到剪贴板
        pyperclip.copy(text)
        time.sleep(0.1)

        # 粘贴
        system = platform.system().lower()
        if system == "windows":
            pyautogui.hotkey("ctrl", "v")
        elif system == "darwin":  # macOS
            pyautogui.hotkey("command", "v")
        elif system == "linux":
            pyautogui.hotkey("ctrl", "v")

        time.sleep(0.1)

        # 恢复剪贴板（可选）
        # pyperclip.copy(old_clipboard)

        time.sleep(TIMING_CONFIG.action.text_input_delay)
    except Exception as e:
        logger.error(f"剪贴板输入失败: {e}，尝试直接输入")
        if pyautogui:
            pyautogui.write(text, interval=0.1)


def press_key(key: str) -> None:
    """
    模拟按键（支持组合键如 ctrl+c）。

    Args:
        key: 按键名称，如 "enter", "tab", "esc" 等。
    """
    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    pyautogui.press(key)
    time.sleep(0.1)


def hotkey(*keys: str) -> None:
    """
    模拟快捷键组合。

    Args:
        *keys: 按键组合，如 "ctrl", "c" 或 "alt", "f4"。
    """
    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    pyautogui.hotkey(*keys)
    time.sleep(0.2)


def clear_text() -> None:
    """
    清除当前输入（Ctrl+A + Delete）。

    注意：这会清除当前焦点输入框中的所有文本。
    """
    if pyautogui is None:
        raise ImportError("pyautogui 未安装，请运行: pip install pyautogui")

    system = platform.system().lower()

    # 全选
    if system == "windows" or system == "linux":
        pyautogui.hotkey("ctrl", "a")
    elif system == "darwin":  # macOS
        pyautogui.hotkey("command", "a")

    time.sleep(0.1)

    # 删除
    pyautogui.press("delete")
    time.sleep(TIMING_CONFIG.action.text_clear_delay)
