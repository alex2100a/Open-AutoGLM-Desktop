"""桌面自动化工具模块，支持 Windows、macOS、Linux 桌面操作。"""

from phone_agent.desktop.connection import (
    DisplayInfo,
    DesktopConnection,
    get_active_window_info,
    list_displays,
)
from phone_agent.desktop.device import (
    back,
    double_tap,
    get_current_app,
    home,
    launch_app,
    long_press,
    right_click,
    scroll,
    swipe,
    tap,
)
from phone_agent.desktop.input import (
    clear_text,
    hotkey,
    press_key,
    type_text,
)
from phone_agent.desktop.screenshot import get_screenshot

__all__ = [
    # Screenshot
    "get_screenshot",
    # Input
    "type_text",
    "clear_text",
    "press_key",
    "hotkey",
    # Device control
    "get_current_app",
    "tap",
    "double_tap",
    "right_click",
    "swipe",
    "scroll",
    "back",
    "home",
    "long_press",
    "launch_app",
    # Connection management
    "DesktopConnection",
    "DisplayInfo",
    "list_displays",
    "get_active_window_info",
]
