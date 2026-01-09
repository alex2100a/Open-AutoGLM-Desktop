#!/usr/bin/env python3
"""
桌面自动化 CLI - AI 驱动的桌面自动化。

Usage:
    python desktop.py [OPTIONS]

Environment Variables:
    PHONE_AGENT_BASE_URL: 模型 API 基础 URL (default: http://localhost:8000/v1)
    PHONE_AGENT_MODEL: 模型名称 (default: autoglm-phone-9b)
    PHONE_AGENT_API_KEY: 模型 API 密钥 (default: EMPTY)
    PHONE_AGENT_MAX_STEPS: 每个任务的最大步数 (default: 100)
    PHONE_AGENT_DISPLAY_ID: 显示器 ID（多显示器设置）
"""

import argparse
import os
import platform
import sys

from openai import OpenAI

from phone_agent.agent_desktop import DesktopAgent, DesktopAgentConfig
from phone_agent.config.apps_desktop import list_supported_apps
from phone_agent.desktop import list_displays
from phone_agent.model import ModelConfig


def check_system_requirements() -> bool:
    """
    检查系统要求。

    检查:
    1. 必要的 Python 库是否安装
    2. 平台是否支持

    Returns:
        如果所有检查通过返回 True，否则返回 False。
    """
    print("🔍 检查系统要求...")
    print("-" * 50)

    all_passed = True

    # 检查 1: pyautogui
    print("1. 检查 pyautogui 安装...", end=" ")
    try:
        import pyautogui

        print("✅ OK")
    except ImportError:
        print("❌ 失败")
        print("   错误: pyautogui 未安装或不在 PATH 中。")
        print("   解决方案: 安装 pyautogui:")
        print("     pip install pyautogui")
        all_passed = False

    # 检查 2: mss (可选但推荐)
    print("2. 检查 mss 安装（推荐）...", end=" ")
    try:
        import mss

        print("✅ OK")
    except ImportError:
        print("⚠️  未安装（可选）")
        print("   提示: 安装 mss 可获得更好的截图性能:")
        print("     pip install mss")

    # 检查 3: 平台支持
    print("3. 检查平台支持...", end=" ")
    system = platform.system().lower()
    if system in ["windows", "darwin", "linux"]:
        print(f"✅ OK ({system})")
    else:
        print(f"⚠️  未知平台 ({system})")
        print("   可能无法正常工作")

    # Windows 特定检查
    if system == "windows":
        print("4. 检查 Windows 特定库...", end=" ")
        try:
            import win32gui
            import win32process

            print("✅ OK (pywin32)")
        except ImportError:
            print("⚠️  未安装（可选）")
            print("   提示: 安装 pywin32 可获得更好的窗口管理:")
            print("     pip install pywin32")

    print("-" * 50)

    if all_passed:
        print("✅ 所有系统检查通过！\n")
    else:
        print("❌ 系统检查失败。请修复上述问题。")

    return all_passed


def check_model_api(base_url: str, model_name: str, api_key: str = "EMPTY") -> bool:
    """
    检查模型 API 是否可访问。

    Checks:
    1. 网络连接到 API 端点
    2. 模型是否存在

    Args:
        base_url: API 基础 URL
        model_name: 模型名称
        api_key: API 密钥

    Returns:
        如果所有检查通过返回 True，否则返回 False。
    """
    print("🔍 检查模型 API...")
    print("-" * 50)

    all_passed = True

    # 检查 1: 网络连接
    print(f"1. 检查 API 连接 ({base_url})...", end=" ")
    try:
        client = OpenAI(base_url=base_url, api_key=api_key, timeout=30.0)

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
            temperature=0.0,
            stream=False,
        )

        if response.choices and len(response.choices) > 0:
            print("✅ OK")
        else:
            print("❌ 失败")
            print("   错误: API 返回空响应")
            all_passed = False

    except Exception as e:
        print("❌ 失败")
        error_msg = str(e)

        if "Connection refused" in error_msg or "Connection error" in error_msg:
            print(f"   错误: 无法连接到 {base_url}")
            print("   解决方案:")
            print("     1. 检查模型服务器是否运行")
            print("     2. 验证基础 URL 是否正确")
            print(f"     3. 尝试: curl {base_url}/chat/completions")
        elif "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            print(f"   错误: 连接到 {base_url} 超时")
            print("   解决方案:")
            print("     1. 检查网络连接")
            print("     2. 验证服务器是否响应")
        else:
            print(f"   错误: {error_msg}")

        all_passed = False

    print("-" * 50)

    if all_passed:
        print("✅ 模型 API 检查通过！\n")
    else:
        print("❌ 模型 API 检查失败。请修复上述问题。")

    return all_passed


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="桌面自动化 - AI 驱动的桌面自动化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 使用默认设置运行
    python desktop.py

    # 指定模型端点
    python desktop.py --base-url http://localhost:8000/v1

    # 使用 API 密钥
    python desktop.py --apikey sk-xxxxx

    # 指定显示器
    python desktop.py --display-id 1

    # 列出显示器
    python desktop.py --list-displays

    # 列出支持的应用
    python desktop.py --list-apps

    # 运行特定任务
    python desktop.py "打开记事本，输入Hello World"
        """,
    )

    # 模型选项
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.getenv("PHONE_AGENT_BASE_URL", "http://localhost:8000/v1"),
        help="模型 API 基础 URL",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("PHONE_AGENT_MODEL", "autoglm-phone-9b"),
        help="模型名称",
    )

    parser.add_argument(
        "--apikey",
        type=str,
        default=os.getenv("PHONE_AGENT_API_KEY", "EMPTY"),
        help="模型 API 密钥",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=int(os.getenv("PHONE_AGENT_MAX_STEPS", "100")),
        help="每个任务的最大步数",
    )

    # 桌面选项
    parser.add_argument(
        "--display-id",
        type=int,
        default=os.getenv("PHONE_AGENT_DISPLAY_ID"),
        help="显示器 ID（多显示器设置）",
    )

    parser.add_argument(
        "--list-displays",
        action="store_true",
        help="列出所有显示器并退出",
    )

    # 其他选项
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="抑制详细输出"
    )

    parser.add_argument(
        "--list-apps", action="store_true", help="列出支持的应用并退出"
    )

    parser.add_argument(
        "--lang",
        type=str,
        choices=["cn", "en"],
        default=os.getenv("PHONE_AGENT_LANG", "cn"),
        help="系统提示语言 (cn 或 en, 默认: cn)",
    )

    # 应用启动模式
    parser.add_argument(
        "--app-mode",
        type=str,
        choices=["reuse", "restart", "new"],
        default=os.getenv("PHONE_AGENT_APP_MODE", "reuse"),
        help="应用启动模式: reuse=复用已有(推荐), restart=重启, new=新开",
    )

    # 开始状态配置
    parser.add_argument(
        "--start-from-desktop",
        action="store_true",
        help="任务开始前先回到桌面",
    )

    parser.add_argument(
        "--minimize-all",
        action="store_true",
        help="任务开始前最小化所有窗口",
    )

    # 调试选项
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用详细调试输出",
    )

    parser.add_argument(
        "--save-screenshots",
        action="store_true",
        help="保存每步截图到 ./screenshots 目录",
    )

    parser.add_argument(
        "--screenshot-dir",
        type=str,
        default="./screenshots",
        help="截图保存目录（默认: ./screenshots）",
    )

    parser.add_argument(
        "task",
        nargs="?",
        type=str,
        help="要执行的任务（如果未提供则进入交互模式）",
    )

    return parser.parse_args()


def handle_display_commands(args) -> bool:
    """
    处理显示器相关命令。

    Returns:
        如果处理了命令（应退出）返回 True，否则返回 False。
    """
    # 处理 --list-displays
    if args.list_displays:
        displays = list_displays()
        if not displays:
            print("未检测到显示器。")
        else:
            print("检测到的显示器:")
            print("-" * 70)
            for display in displays:
                primary_mark = " (主显示器)" if display.is_primary else ""
                print(f"  ✓ 显示器 {display.display_id}{primary_mark}")
                print(f"    分辨率: {display.width} x {display.height}")
                print(f"    位置: ({display.x}, {display.y})")
                print("-" * 70)
        return True

    return False


def main():
    """主入口点。"""
    args = parse_args()

    # 处理 --list-apps（不需要系统检查）
    if args.list_apps:
        system = platform.system().lower()
        if system == "darwin":
            platform_name = "macos"
        else:
            platform_name = system

        print(f"支持的应用 ({platform_name}):")
        apps = list_supported_apps(platform_name)
        for app in sorted(apps):
            print(f"  - {app}")
        return

    # 处理显示器命令
    if handle_display_commands(args):
        return

    # 运行系统要求检查
    if not check_system_requirements():
        sys.exit(1)

    # 检查模型 API 连接
    if not check_model_api(args.base_url, args.model, args.apikey):
        sys.exit(1)

    # 创建配置和 Agent
    model_config = ModelConfig(
        base_url=args.base_url,
        model_name=args.model,
        api_key=args.apikey,
        lang=args.lang,
    )

    agent_config = DesktopAgentConfig(
        max_steps=args.max_steps,
        display_id=args.display_id,
        verbose=not args.quiet,
        lang=args.lang,
        app_launch_mode=args.app_mode,
        start_from_desktop=args.start_from_desktop,
        minimize_all_before_start=args.minimize_all,
        debug=args.debug,
        save_screenshots=args.save_screenshots,
        screenshot_dir=args.screenshot_dir,
    )

    agent = DesktopAgent(
        model_config=model_config,
        agent_config=agent_config,
    )

    # 打印标题
    print("=" * 50)
    print("桌面自动化 - AI 驱动的桌面自动化")
    print("=" * 50)
    print(f"模型: {model_config.model_name}")
    print(f"基础 URL: {model_config.base_url}")
    print(f"最大步数: {agent_config.max_steps}")
    print(f"语言: {agent_config.lang}")
    print(f"平台: {agent_config.platform}")
    print(f"应用启动模式: {agent_config.app_launch_mode}")
    if agent_config.start_from_desktop:
        print(f"开始状态: 从桌面开始")
    elif agent_config.minimize_all_before_start:
        print(f"开始状态: 最小化所有窗口")
    if agent_config.debug:
        print(f"调试模式: 已启用")
    if agent_config.save_screenshots:
        print(f"截图保存: {agent_config.screenshot_dir}")

    # 显示显示器信息
    if agent_config.display_id is not None:
        print(f"显示器: {agent_config.display_id}")
    else:
        displays = list_displays()
        if displays:
            primary = next((d for d in displays if d.is_primary), displays[0])
            print(f"显示器: {primary.display_id} (主显示器, {primary.width}x{primary.height})")

    print("=" * 50)

    # 运行提供的任务或进入交互模式
    if args.task:
        print(f"\n任务: {args.task}\n")
        result = agent.run(args.task)
        print(f"\n结果: {result}")
    else:
        # 交互模式
        print("\n进入交互模式。输入 'quit' 退出。\n")

        while True:
            try:
                task = input("输入您的任务: ").strip()

                if task.lower() in ("quit", "exit", "q"):
                    print("再见！")
                    break

                if not task:
                    continue

                print()
                result = agent.run(task)
                print(f"\n结果: {result}\n")
                agent.reset()

            except KeyboardInterrupt:
                print("\n\n中断。再见！")
                break
            except Exception as e:
                print(f"\n错误: {e}\n")


if __name__ == "__main__":
    main()
