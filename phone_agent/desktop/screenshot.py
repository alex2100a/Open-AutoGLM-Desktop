"""桌面截图功能模块。"""

import base64
import platform
from dataclasses import dataclass
from io import BytesIO

try:
    import mss
    import mss.tools
except ImportError:
    mss = None

try:
    from PIL import Image
except ImportError:
    Image = None


@dataclass
class Screenshot:
    """表示一个截取的屏幕截图。"""

    base64_data: str
    width: int
    height: int
    is_sensitive: bool = False


def get_screenshot(
    display_id: int | None = None,
    region: tuple[int, int, int, int] | None = None,
    timeout: int = 10,
) -> Screenshot:
    """
    获取屏幕截图。

    Args:
        display_id: 指定显示器，None 为主显示器。
        region: 指定区域 (x, y, width, height)，None 为全屏。
        timeout: 超时时间（秒）。

    Returns:
        Screenshot 对象，包含 base64 数据和尺寸。
    """
    if mss is None:
        # 回退到 pyautogui
        return _get_screenshot_pyautogui(region)

    try:
        with mss.mss() as sct:
            if region:
                # 指定区域截图
                monitor = {
                    "top": region[1],
                    "left": region[0],
                    "width": region[2],
                    "height": region[3],
                }
            elif display_id is not None:
                # 指定显示器
                monitors = sct.monitors
                if display_id + 1 < len(monitors):
                    monitor = monitors[display_id + 1]  # 索引0是所有显示器的组合
                else:
                    monitor = sct.monitors[1]  # 默认第一个显示器
            else:
                # 主显示器
                monitor = sct.monitors[1]

            # 截图
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # 转换为 base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            base64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

            return Screenshot(
                base64_data=base64_data,
                width=img.width,
                height=img.height,
                is_sensitive=False,
            )

    except Exception as e:
        print(f"截图失败: {e}")
        return _get_screenshot_pyautogui(region)


def _get_screenshot_pyautogui(region: tuple[int, int, int, int] | None = None) -> Screenshot:
    """使用 pyautogui 作为回退方案。"""
    try:
        import pyautogui

        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        # 转换为 base64
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        base64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return Screenshot(
            base64_data=base64_data,
            width=screenshot.width,
            height=screenshot.height,
            is_sensitive=False,
        )
    except Exception as e:
        print(f"pyautogui 截图失败: {e}")
        # 返回默认黑色图片
        return _create_fallback_screenshot()


def _create_fallback_screenshot() -> Screenshot:
    """创建默认的黑色回退图片。"""
    if Image is None:
        # 如果 PIL 不可用，返回一个最小的 base64 编码的黑色图片
        # 1x1 黑色 PNG
        black_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        return Screenshot(
            base64_data=black_png_base64,
            width=1,
            height=1,
            is_sensitive=False,
        )

    # 默认屏幕尺寸
    default_width, default_height = 1920, 1080

    black_img = Image.new("RGB", (default_width, default_height), color="black")
    buffered = BytesIO()
    black_img.save(buffered, format="PNG")
    base64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return Screenshot(
        base64_data=base64_data,
        width=default_width,
        height=default_height,
        is_sensitive=False,
    )
