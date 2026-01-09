"""桌面操作处理器，用于处理 AI 模型输出的桌面操作。"""

import time
from dataclasses import dataclass
from typing import Any, Callable

from phone_agent.desktop import (
    back,
    clear_text,
    double_tap,
    get_current_app,
    home,
    hotkey,
    launch_app,
    long_press,
    press_key,
    right_click,
    scroll,
    swipe,
    tap,
    type_text,
)


@dataclass
class ActionResult:
    """操作执行结果。"""

    success: bool
    should_finish: bool
    message: str | None = None
    requires_confirmation: bool = False


class DesktopActionHandler:
    """
    处理桌面自动化操作的处理器。

    Args:
        display_id: 可选的显示器 ID。
        confirmation_callback: 敏感操作确认回调，应返回 True 继续，False 取消。
        takeover_callback: 接管请求回调（登录、验证码等）。
    """

    def __init__(
        self,
        display_id: int | None = None,
        confirmation_callback: Callable[[str], bool] | None = None,
        takeover_callback: Callable[[str], None] | None = None,
    ):
        self.display_id = display_id
        self.confirmation_callback = confirmation_callback or self._default_confirmation
        self.takeover_callback = takeover_callback or self._default_takeover

    def execute(
        self, action: dict[str, Any], screen_width: int, screen_height: int
    ) -> ActionResult:
        """
        执行 AI 模型输出的操作。

        Args:
            action: 模型输出的操作字典。
            screen_width: 当前屏幕宽度（像素）。
            screen_height: 当前屏幕高度（像素）。

        Returns:
            ActionResult 表示成功与否以及是否完成。
        """
        action_type = action.get("_metadata")

        if action_type == "finish":
            return ActionResult(
                success=True, should_finish=True, message=action.get("message")
            )

        if action_type != "do":
            return ActionResult(
                success=False,
                should_finish=True,
                message=f"未知操作类型: {action_type}",
            )

        action_name = action.get("action")
        handler_method = self._get_handler(action_name)

        if handler_method is None:
            return ActionResult(
                success=False,
                should_finish=False,
                message=f"未知操作: {action_name}",
            )

        try:
            return handler_method(action, screen_width, screen_height)
        except Exception as e:
            return ActionResult(
                success=False, should_finish=False, message=f"操作失败: {e}"
            )

    def _get_handler(self, action_name: str) -> Callable | None:
        """获取操作的处理方法。"""
        handlers = {
            # 共有操作
            "Launch": self._handle_launch,
            "Tap": self._handle_tap,
            "Type": self._handle_type,
            "Type_Name": self._handle_type,
            "Swipe": self._handle_swipe,
            "Back": self._handle_back,
            "Home": self._handle_home,
            "Double Tap": self._handle_double_tap,
            "Long Press": self._handle_long_press,
            "Wait": self._handle_wait,
            "Take_over": self._handle_takeover,
            "Note": self._handle_note,
            "Call_API": self._handle_call_api,
            "Interact": self._handle_interact,
            # 桌面特有操作
            "Right Click": self._handle_right_click,
            "Scroll": self._handle_scroll,
            "Hotkey": self._handle_hotkey,
            "Minimize": self._handle_minimize,
            "Maximize": self._handle_maximize,
            "Close Window": self._handle_close_window,
        }
        return handlers.get(action_name)

    def _convert_relative_to_absolute(
        self, element: list[int], screen_width: int, screen_height: int
    ) -> tuple[int, int]:
        """将相对坐标（0-1000）转换为绝对像素坐标。"""
        x = int(element[0] / 1000 * screen_width)
        y = int(element[1] / 1000 * screen_height)
        return x, y

    def _handle_launch(self, action: dict, width: int, height: int) -> ActionResult:
        """处理应用启动操作。"""
        app_name = action.get("app")
        if not app_name:
            return ActionResult(False, False, "未指定应用名称")

        success = launch_app(app_name)
        if success:
            return ActionResult(True, False)
        return ActionResult(False, False, f"应用未找到: {app_name}")

    def _handle_tap(self, action: dict, width: int, height: int) -> ActionResult:
        """处理点击操作。"""
        element = action.get("element")
        if not element:
            return ActionResult(False, False, "未指定坐标")

        x, y = self._convert_relative_to_absolute(element, width, height)

        # 检查敏感操作
        if "message" in action:
            if not self.confirmation_callback(action["message"]):
                return ActionResult(
                    success=False,
                    should_finish=True,
                    message="用户取消了敏感操作",
                )

        tap(x, y)
        return ActionResult(True, False)

    def _handle_type(self, action: dict, width: int, height: int) -> ActionResult:
        """处理文本输入操作。"""
        text = action.get("text", "")

        # 清除现有文本并输入新文本
        clear_text()
        time.sleep(0.2)

        type_text(text)
        time.sleep(0.5)

        return ActionResult(True, False)

    def _handle_swipe(self, action: dict, width: int, height: int) -> ActionResult:
        """处理拖拽操作。"""
        start = action.get("start")
        end = action.get("end")

        if not start or not end:
            return ActionResult(False, False, "缺少拖拽坐标")

        start_x, start_y = self._convert_relative_to_absolute(start, width, height)
        end_x, end_y = self._convert_relative_to_absolute(end, width, height)

        swipe(start_x, start_y, end_x, end_y)
        return ActionResult(True, False)

    def _handle_back(self, action: dict, width: int, height: int) -> ActionResult:
        """处理返回操作。"""
        back()
        return ActionResult(True, False)

    def _handle_home(self, action: dict, width: int, height: int) -> ActionResult:
        """处理回到桌面操作。"""
        home()
        return ActionResult(True, False)

    def _handle_double_tap(
        self, action: dict, width: int, height: int
    ) -> ActionResult:
        """处理双击操作。"""
        element = action.get("element")
        if not element:
            return ActionResult(False, False, "未指定坐标")

        x, y = self._convert_relative_to_absolute(element, width, height)
        double_tap(x, y)
        return ActionResult(True, False)

    def _handle_long_press(
        self, action: dict, width: int, height: int
    ) -> ActionResult:
        """处理长按操作（桌面实现为右键点击）。"""
        element = action.get("element")
        if not element:
            return ActionResult(False, False, "未指定坐标")

        x, y = self._convert_relative_to_absolute(element, width, height)
        long_press(x, y)
        return ActionResult(True, False)

    def _handle_wait(self, action: dict, width: int, height: int) -> ActionResult:
        """处理等待操作。"""
        duration_str = action.get("duration", "1 seconds")
        try:
            duration = float(duration_str.replace("seconds", "").strip())
        except ValueError:
            duration = 1.0

        time.sleep(duration)
        return ActionResult(True, False)

    def _handle_takeover(
        self, action: dict, width: int, height: int
    ) -> ActionResult:
        """处理接管请求（登录、验证码等）。"""
        message = action.get("message", "需要用户干预")
        self.takeover_callback(message)
        return ActionResult(True, False)

    def _handle_note(self, action: dict, width: int, height: int) -> ActionResult:
        """处理记录操作（用于记录页面内容）。"""
        # 此操作通常用于记录页面内容
        # 具体实现取决于需求
        return ActionResult(True, False)

    def _handle_call_api(
        self, action: dict, width: int, height: int
    ) -> ActionResult:
        """处理 API 调用操作（用于内容总结）。"""
        # 此操作通常用于内容总结
        # 具体实现取决于需求
        return ActionResult(True, False)

    def _handle_interact(
        self, action: dict, width: int, height: int
    ) -> ActionResult:
        """处理交互请求（需要用户选择）。"""
        # 此操作表示需要用户输入
        return ActionResult(True, False, message="需要用户交互")

    def _handle_right_click(
        self, action: dict, width: int, height: int
    ) -> ActionResult:
        """处理右键点击操作（桌面特有）。"""
        element = action.get("element")
        if not element:
            return ActionResult(False, False, "未指定坐标")

        x, y = self._convert_relative_to_absolute(element, width, height)
        right_click(x, y)
        return ActionResult(True, False)

    def _handle_scroll(self, action: dict, width: int, height: int) -> ActionResult:
        """处理滚轮操作（桌面特有）。"""
        element = action.get("element")
        if not element:
            return ActionResult(False, False, "未指定坐标")

        x, y = self._convert_relative_to_absolute(element, width, height)
        clicks = action.get("clicks", 3)
        direction = action.get("direction", "down")

        scroll(x, y, clicks, direction)
        return ActionResult(True, False)

    def _handle_hotkey(self, action: dict, width: int, height: int) -> ActionResult:
        """处理快捷键操作（桌面特有）。"""
        keys = action.get("keys", [])
        if not keys:
            return ActionResult(False, False, "未指定按键")

        if isinstance(keys, str):
            keys = keys.split("+")

        hotkey(*keys)
        return ActionResult(True, False)

    def _handle_minimize(
        self, action: dict, width: int, height: int
    ) -> ActionResult:
        """处理最小化窗口操作（桌面特有）。"""
        try:
            import platform

            system = platform.system().lower()
            if system == "windows":
                hotkey("win", "down")
            elif system == "darwin":  # macOS
                hotkey("command", "m")
            elif system == "linux":
                hotkey("super", "down")
            return ActionResult(True, False)
        except Exception as e:
            return ActionResult(False, False, f"最小化失败: {e}")

    def _handle_maximize(
        self, action: dict, width: int, height: int
    ) -> ActionResult:
        """处理最大化窗口操作（桌面特有）。"""
        try:
            import platform

            system = platform.system().lower()
            if system == "windows":
                hotkey("win", "up")
            elif system == "darwin":  # macOS
                hotkey("command", "ctrl", "f")
            elif system == "linux":
                hotkey("super", "up")
            return ActionResult(True, False)
        except Exception as e:
            return ActionResult(False, False, f"最大化失败: {e}")

    def _handle_close_window(
        self, action: dict, width: int, height: int
    ) -> ActionResult:
        """处理关闭窗口操作（桌面特有）。"""
        try:
            import platform

            system = platform.system().lower()
            if system == "windows":
                hotkey("alt", "f4")
            elif system == "darwin":  # macOS
                hotkey("command", "w")
            elif system == "linux":
                hotkey("alt", "f4")
            return ActionResult(True, False)
        except Exception as e:
            return ActionResult(False, False, f"关闭窗口失败: {e}")

    @staticmethod
    def _default_confirmation(message: str) -> bool:
        """默认确认回调，使用控制台输入。"""
        response = input(f"敏感操作: {message}\n确认? (Y/N): ")
        return response.upper() == "Y"

    @staticmethod
    def _default_takeover(message: str) -> None:
        """默认接管回调，使用控制台输入。"""
        input(f"{message}\n完成手动操作后按 Enter...")
