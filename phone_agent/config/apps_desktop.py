"""桌面应用配置，支持 Windows、macOS、Linux。"""

import platform

# Windows 应用配置
APP_EXECUTABLES_WINDOWS: dict[str, str] = {
    # 系统应用
    "记事本": "notepad.exe",
    "计算器": "calc.exe",
    "文件管理器": "explorer.exe",
    "命令提示符": "cmd.exe",
    "PowerShell": "powershell.exe",
    "任务管理器": "taskmgr.exe",
    # 浏览器
    "浏览器": "chrome.exe",
    "Chrome": "chrome.exe",
    "Edge": "msedge.exe",
    "Firefox": "firefox.exe",
    # 开发工具
    "VS Code": "Code.exe",
    "Visual Studio Code": "Code.exe",
    "PyCharm": "pycharm64.exe",
    "IntelliJ IDEA": "idea64.exe",
    # 社交应用
    "微信": "WeChat.exe",
    "QQ": "QQ.exe",
    "钉钉": "DingTalk.exe",
    "飞书": "Feishu.exe",
    # 办公软件
    "Word": "WINWORD.EXE",
    "Excel": "EXCEL.EXE",
    "PowerPoint": "POWERPNT.EXE",
    "Outlook": "OUTLOOK.EXE",
    # 其他
    "画图": "mspaint.exe",
    "截图工具": "SnippingTool.exe",
}

# macOS 应用配置
APP_BUNDLES_MACOS: dict[str, str] = {
    # 系统应用
    "Safari": "com.apple.Safari",
    "Finder": "com.apple.finder",
    "Terminal": "com.apple.Terminal",
    "TextEdit": "com.apple.TextEdit",
    "Calculator": "com.apple.calculator",
    # 浏览器
    "Chrome": "com.google.Chrome",
    "Firefox": "org.mozilla.firefox",
    "Edge": "com.microsoft.edgemac",
    # 开发工具
    "VS Code": "com.microsoft.VSCode",
    "Xcode": "com.apple.dt.Xcode",
    # 社交应用
    "微信": "com.tencent.xinWeChat",
    "QQ": "com.tencent.qq",
    # 办公软件
    "Word": "com.microsoft.Word",
    "Excel": "com.microsoft.Excel",
    "PowerPoint": "com.microsoft.PowerPoint",
}

# Linux 应用配置
APP_EXECUTABLES_LINUX: dict[str, str] = {
    # 系统应用
    "文件管理器": "nautilus",
    "终端": "gnome-terminal",
    "文本编辑器": "gedit",
    "计算器": "gnome-calculator",
    # 浏览器
    "Chrome": "google-chrome",
    "Firefox": "firefox",
    "Edge": "microsoft-edge",
    # 开发工具
    "VS Code": "code",
    # 其他
    "截图工具": "gnome-screenshot",
}


def get_executable_path(app_name: str, platform_name: str | None = None) -> str | None:
    """
    根据应用名称和平台获取可执行文件路径。

    Args:
        app_name: 应用名称。
        platform_name: 平台名称（"windows", "darwin", "linux"），如果为 None 则自动检测。

    Returns:
        可执行文件路径或 Bundle ID，如果未找到则返回 None。
    """
    if platform_name is None:
        platform_name = platform.system().lower()

    if platform_name == "windows":
        return APP_EXECUTABLES_WINDOWS.get(app_name)
    elif platform_name == "darwin":  # macOS
        return APP_BUNDLES_MACOS.get(app_name)
    elif platform_name == "linux":
        return APP_EXECUTABLES_LINUX.get(app_name)

    return None


def list_supported_apps(platform_name: str | None = None) -> list[str]:
    """
    获取支持的应用列表。

    Args:
        platform_name: 平台名称，如果为 None 则自动检测。

    Returns:
        应用名称列表。
    """
    if platform_name is None:
        platform_name = platform.system().lower()

    if platform_name == "windows":
        return list(APP_EXECUTABLES_WINDOWS.keys())
    elif platform_name == "darwin":  # macOS
        return list(APP_BUNDLES_MACOS.keys())
    elif platform_name == "linux":
        return list(APP_EXECUTABLES_LINUX.keys())

    return []


def get_app_name(executable: str, platform_name: str | None = None) -> str | None:
    """
    根据可执行文件名获取应用名称。

    Args:
        executable: 可执行文件名或 Bundle ID。
        platform_name: 平台名称，如果为 None 则自动检测。

    Returns:
        应用名称，如果未找到则返回 None。
    """
    if platform_name is None:
        platform_name = platform.system().lower()

    if platform_name == "windows":
        for name, exe in APP_EXECUTABLES_WINDOWS.items():
            if exe.lower() == executable.lower():
                return name
    elif platform_name == "darwin":  # macOS
        for name, bundle_id in APP_BUNDLES_MACOS.items():
            if bundle_id == executable:
                return name
    elif platform_name == "linux":
        for name, exe in APP_EXECUTABLES_LINUX.items():
            if exe == executable:
                return name

    return None
