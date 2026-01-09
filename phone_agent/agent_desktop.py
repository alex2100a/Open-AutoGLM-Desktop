"""桌面自动化 Agent 类。"""

import json
import os
import platform
import traceback
from dataclasses import dataclass
from typing import Any, Callable

from phone_agent.actions.handler import do, finish, parse_action
from phone_agent.actions.handler_desktop import DesktopActionHandler
from phone_agent.config import get_messages
from phone_agent.config.prompts_desktop import SYSTEM_PROMPT as DESKTOP_SYSTEM_PROMPT
from phone_agent.desktop import (
    get_active_window_info,
    get_current_app,
    get_screenshot,
    home,
    minimize_all_windows,
)
from phone_agent.model import ModelClient, ModelConfig
from phone_agent.model.client import MessageBuilder
from phone_agent.utils import get_logger

logger = get_logger(__name__)


@dataclass
class DesktopAgentConfig:
    """桌面 Agent 配置。"""

    max_steps: int = 100
    display_id: int | None = None  # 指定显示器
    lang: str = "cn"
    system_prompt: str | None = None
    verbose: bool = True
    platform: str | None = None  # windows/macos/linux，如果为 None 则自动检测
    # 应用启动策略
    app_launch_mode: str = "reuse"  # "reuse" | "restart" | "new"
    # - reuse: 复用已有实例，切换到该窗口（推荐，更快）
    # - restart: 关闭已有实例，重新启动（确保干净状态）
    # - new: 启动新实例（不关闭已有）
    # 开始状态配置
    start_from_desktop: bool = False  # True: 先回到桌面，False: 从当前状态开始
    minimize_all_before_start: bool = False  # 开始前是否最小化所有窗口
    # 调试选项
    debug: bool = False  # 更详细的调试信息
    save_screenshots: bool = False  # 保存每步截图
    screenshot_dir: str = "./screenshots"  # 截图保存目录
    log_actions: bool = True  # 记录操作日志

    def __post_init__(self):
        if self.system_prompt is None:
            # 使用桌面专用提示词
            self.system_prompt = DESKTOP_SYSTEM_PROMPT

        if self.platform is None:
            system = platform.system().lower()
            if system == "darwin":
                self.platform = "macos"
            else:
                self.platform = system


@dataclass
class StepResult:
    """单步执行结果。"""

    success: bool
    finished: bool
    action: dict[str, Any] | None
    thinking: str
    message: str | None = None


class DesktopAgent:
    """
    基于 AI 的桌面自动化 Agent。

    Agent 使用视觉语言模型理解屏幕内容并决定操作以完成任务。

    Args:
        model_config: AI 模型配置。
        agent_config: Agent 行为配置。
        confirmation_callback: 可选的敏感操作确认回调。
        takeover_callback: 可选的接管请求回调。

    Example:
        >>> from phone_agent.agent_desktop import DesktopAgent, DesktopAgentConfig
        >>> from phone_agent.model import ModelConfig
        >>>
        >>> model_config = ModelConfig(base_url="http://localhost:8000/v1")
        >>> agent_config = DesktopAgentConfig()
        >>> agent = DesktopAgent(model_config, agent_config)
        >>> agent.run("打开记事本，输入Hello World")
    """

    def __init__(
        self,
        model_config: ModelConfig | None = None,
        agent_config: DesktopAgentConfig | None = None,
        confirmation_callback: Callable[[str], bool] | None = None,
        takeover_callback: Callable[[str], None] | None = None,
    ):
        self.model_config = model_config or ModelConfig()
        self.agent_config = agent_config or DesktopAgentConfig()

        self.model_client = ModelClient(self.model_config)

        self.action_handler = DesktopActionHandler(
            display_id=self.agent_config.display_id,
            confirmation_callback=confirmation_callback,
            takeover_callback=takeover_callback,
            app_launch_mode=self.agent_config.app_launch_mode,
        )

        self._context: list[dict[str, Any]] = []
        self._step_count = 0

    def run(self, task: str) -> str:
        """
        运行 Agent 完成任务。

        Args:
            task: 任务的自然语言描述。

        Returns:
            Agent 的最终消息。
        """
        self._context = []
        self._step_count = 0

        # 处理开始状态配置
        if self.agent_config.start_from_desktop or self.agent_config.minimize_all_before_start:
            if self.agent_config.verbose:
                logger.info("📋 准备开始状态...")
            if self.agent_config.minimize_all_before_start:
                minimize_all_windows()
                if self.agent_config.verbose:
                    logger.info("  ✓ 已最小化所有窗口")
            elif self.agent_config.start_from_desktop:
                home()
                if self.agent_config.verbose:
                    logger.info("  ✓ 已回到桌面")
            if self.agent_config.verbose:
                logger.info("")

        # 创建截图目录（如果需要保存截图）
        if self.agent_config.save_screenshots:
            os.makedirs(self.agent_config.screenshot_dir, exist_ok=True)

        # 第一步，包含用户提示
        result = self._execute_step(task, is_first=True)

        if result.finished:
            return result.message or "任务完成"

        # 继续直到完成或达到最大步数
        while self._step_count < self.agent_config.max_steps:
            result = self._execute_step(is_first=False)

            if result.finished:
                return result.message or "任务完成"

        return "达到最大步数"

    def step(self, task: str | None = None) -> StepResult:
        """
        执行 Agent 的单个步骤。

        用于手动控制或调试。

        Args:
            task: 任务描述（仅在第一步需要）。

        Returns:
            包含步骤详情的 StepResult。
        """
        is_first = len(self._context) == 0

        if is_first and not task:
            raise ValueError("第一步需要提供任务描述")

        return self._execute_step(task, is_first)

    def reset(self) -> None:
        """重置 Agent 状态以开始新任务。"""
        self._context = []
        self._step_count = 0

    def _execute_step(
        self, user_prompt: str | None = None, is_first: bool = False
    ) -> StepResult:
        """执行 Agent 循环的单个步骤。"""
        self._step_count += 1

        # 捕获当前屏幕状态
        screenshot = get_screenshot(display_id=self.agent_config.display_id)
        current_app = get_current_app()
        window_info = get_active_window_info()

        # 调试输出：当前状态信息
        if self.agent_config.debug:
            logger.info("\n🔍 [步骤 %s] 当前状态:", self._step_count)
            logger.info("  应用: %s", current_app)
            logger.info("  窗口标题: %s", window_info.get('title', 'Unknown'))
            logger.info("  进程: %s", window_info.get('process', 'Unknown'))
            logger.info("  屏幕尺寸: %sx%s", screenshot.width, screenshot.height)

        # 保存截图（如果启用）
        if self.agent_config.save_screenshots:
            import base64
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(
                self.agent_config.screenshot_dir,
                f"step_{self._step_count:03d}_{timestamp}.png",
            )
            try:
                img_data = base64.b64decode(screenshot.base64_data)
                with open(screenshot_path, "wb") as f:
                    f.write(img_data)
                if self.agent_config.debug:
                    logger.info("  截图已保存: %s", screenshot_path)
            except Exception as e:
                if self.agent_config.debug:
                    logger.info("  保存截图失败: %s", e)

        # 构建消息
        if is_first:
            self._context.append(
                MessageBuilder.create_system_message(self.agent_config.system_prompt)
            )

            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"{user_prompt}\n\n{screen_info}"

            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )
        else:
            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"** 屏幕信息 **\n\n{screen_info}"

            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )

        # 获取模型响应
        try:
            msgs = get_messages(self.agent_config.lang)
            if self.agent_config.verbose:
                logger.info("\n" + "=" * 50)
                logger.info("💭 %s:", msgs['thinking'])
                logger.info("-" * 50)
            response = self.model_client.request(self._context)
        except Exception as e:
            if self.agent_config.verbose:
                traceback.print_exc()
            return StepResult(
                success=False,
                finished=True,
                action=None,
                thinking="",
                message=f"模型错误: {e}",
            )

        # 从响应中解析操作
        try:
            action = parse_action(response.action)
        except ValueError:
            if self.agent_config.verbose:
                traceback.print_exc()
            action = finish(message=response.action)

        if self.agent_config.verbose:
            # 打印思考过程
            logger.info("-" * 50)
            logger.info("🎯 %s:", msgs['action'])
            logger.info(json.dumps(action, ensure_ascii=False, indent=2))
            logger.info("=" * 50 + "\n")

        # 调试输出：操作详情
        if self.agent_config.debug:
            logger.info("📝 执行操作: %s", action.get('action', 'Unknown'))
            if self.agent_config.log_actions:
                logger.info("   操作详情: %s", json.dumps(action, ensure_ascii=False))

        # 从上下文中移除图片以节省空间
        self._context[-1] = MessageBuilder.remove_images_from_message(
            self._context[-1]
        )

        # 执行操作
        try:
            result = self.action_handler.execute(
                action, screenshot.width, screenshot.height
            )

            # 调试输出：操作结果
            if self.agent_config.debug:
                logger.info("✅ 操作结果: %s", '成功' if result.success else '失败')
                if result.message:
                    logger.info("   消息: %s", result.message)
        except Exception as e:
            if self.agent_config.verbose:
                traceback.print_exc()
            if self.agent_config.debug:
                logger.info("❌ 操作异常: %s", e)
            result = self.action_handler.execute(
                finish(message=str(e)), screenshot.width, screenshot.height
            )

        # 将助手响应添加到上下文
        self._context.append(
            MessageBuilder.create_assistant_message(
                f"<think>{response.thinking}</think><answer>{response.action}</answer>"
            )
        )

        # 检查是否完成
        finished = action.get("_metadata") == "finish" or result.should_finish

        if finished and self.agent_config.verbose:
            msgs = get_messages(self.agent_config.lang)
            logger.info("\n" + "🎉 " + "=" * 48)
            logger.info("✅ %s: %s", msgs['task_completed'], result.message or action.get('message', msgs['done']))
            logger.info("=" * 50 + "\n")

        return StepResult(
            success=result.success,
            finished=finished,
            action=action,
            thinking=response.thinking,
            message=result.message or action.get("message"),
        )

    @property
    def context(self) -> list[dict[str, Any]]:
        """获取当前对话上下文。"""
        return self._context.copy()

    @property
    def step_count(self) -> int:
        """获取当前步数。"""
        return self._step_count
