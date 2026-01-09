#!/usr/bin/env python3
"""
Phone Agent iOS CLI - AI-powered iOS phone automation.

Usage:
    python ios.py [OPTIONS]

Environment Variables:
    PHONE_AGENT_BASE_URL: Model API base URL (default: http://localhost:8000/v1)
    PHONE_AGENT_MODEL: Model name (default: autoglm-phone-9b)
    PHONE_AGENT_MAX_STEPS: Maximum steps per task (default: 100)
    PHONE_AGENT_WDA_URL: WebDriverAgent URL (default: http://localhost:8100)
    PHONE_AGENT_DEVICE_ID: iOS device UDID for multi-device setups
"""

import argparse
import os
import shutil
import subprocess
import sys
from urllib.parse import urlparse

from openai import OpenAI

from phone_agent.agent_ios import IOSAgentConfig, IOSPhoneAgent
from phone_agent.config.apps_ios import list_supported_apps
from phone_agent.model import ModelConfig
from phone_agent.utils import get_logger
from phone_agent.xctest import XCTestConnection, list_devices

logger = get_logger(__name__)


def check_system_requirements(wda_url: str = "http://localhost:8100") -> bool:
    """
    Check system requirements before running the agent.

    Checks:
    1. libimobiledevice tools installed
    2. At least one iOS device connected
    3. WebDriverAgent is running

    Args:
        wda_url: WebDriverAgent URL to check.

    Returns:
        True if all checks pass, False otherwise.
    """
    logger.info("🔍 Checking system requirements...")
    logger.info("-" * 50)

    all_passed = True

    # Check 1: libimobiledevice installed
    logger.info("1. Checking libimobiledevice installation...")
    if shutil.which("idevice_id") is None:
        logger.info("❌ FAILED")
        logger.info("   Error: libimobiledevice is not installed or not in PATH.")
        logger.info("   Solution: Install libimobiledevice:")
        logger.info("     - macOS: brew install libimobiledevice")
        logger.info("     - Linux: sudo apt-get install libimobiledevice-utils")
        all_passed = False
    else:
        # Double check by running idevice_id
        try:
            result = subprocess.run(
                ["idevice_id", "-ln"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("✅ OK")
            else:
                logger.info("❌ FAILED")
                logger.info("   Error: idevice_id command failed to run.")
                all_passed = False
        except FileNotFoundError:
            logger.info("❌ FAILED")
            logger.info("   Error: idevice_id command not found.")
            all_passed = False
        except subprocess.TimeoutExpired:
            logger.info("❌ FAILED")
            logger.info("   Error: idevice_id command timed out.")
            all_passed = False

    # If libimobiledevice is not installed, skip remaining checks
    if not all_passed:
        logger.info("-" * 50)
        logger.info("❌ System check failed. Please fix the issues above.")
        return False

    # Check 2: iOS Device connected
    logger.info("2. Checking connected iOS devices...")
    try:
        devices = list_devices()

        if not devices:
            logger.info("❌ FAILED")
            logger.info("   Error: No iOS devices connected.")
            logger.info("   Solution:")
            logger.info("     1. Connect your iOS device via USB")
            logger.info("     2. Unlock the device and tap 'Trust This Computer'")
            logger.info("     3. Verify connection: idevice_id -l")
            logger.info("     4. Or connect via WiFi using device IP")
            all_passed = False
        else:
            device_names = [
                d.device_name or d.device_id[:8] + "..." for d in devices
            ]
            logger.info("✅ OK (%d device(s): %s)", len(devices), ', '.join(device_names))
    except Exception as e:
        logger.info("❌ FAILED")
        logger.info("   Error: %s", e)
        all_passed = False

    # If no device connected, skip WebDriverAgent check
    if not all_passed:
        logger.info("-" * 50)
        logger.info("❌ System check failed. Please fix the issues above.")
        return False

    # Check 3: WebDriverAgent running
    logger.info("3. Checking WebDriverAgent (%s)...", wda_url)
    try:
        conn = XCTestConnection(wda_url=wda_url)

        if conn.is_wda_ready():
            logger.info("✅ OK")
            # Get WDA status for additional info
            status = conn.get_wda_status()
            if status:
                session_id = status.get("sessionId", "N/A")
                logger.info("   Session ID: %s", session_id)
        else:
            logger.info("❌ FAILED")
            logger.info("   Error: WebDriverAgent is not running or not accessible.")
            logger.info("   Solution:")
            logger.info("     1. Run WebDriverAgent on your iOS device via Xcode")
            logger.info("     2. For USB: Set up port forwarding: iproxy 8100 8100")
            logger.info("     3. For WiFi: Use device IP, e.g., --wda-url http://192.168.1.100:8100")
            logger.info("     4. Verify in browser: open http://localhost:8100/status")
            logger.info("\n   Quick setup guide:")
            logger.info("     git clone https://github.com/appium/WebDriverAgent.git && cd WebDriverAgent")
            logger.info("     ./Scripts/bootstrap.sh")
            logger.info("     open WebDriverAgent.xcodeproj")
            logger.info("     # Configure signing, then Product > Test (Cmd+U)")
            all_passed = False
    except Exception as e:
        logger.info("❌ FAILED")
        logger.info("   Error: %s", e)
        all_passed = False

    logger.info("-" * 50)

    if all_passed:
        logger.info("✅ All system checks passed!\n")
    else:
        logger.info("❌ System check failed. Please fix the issues above.")

    return all_passed


def check_model_api(base_url: str, api_key: str, model_name: str) -> bool:
    """
    Check if the model API is accessible and the specified model exists.

    Checks:
    1. Network connectivity to the API endpoint
    2. Model exists in the available models list

    Args:
        base_url: The API base URL
        model_name: The model name to check

    Returns:
        True if all checks pass, False otherwise.
    """
    logger.info("🔍 Checking model API...")
    logger.info("-" * 50)

    all_passed = True

    # Check 1: Network connectivity
    logger.info("1. Checking API connectivity (%s)...", base_url)
    try:
        # Parse the URL to get host and port
        parsed = urlparse(base_url)

        # Create OpenAI client
        client = OpenAI(base_url=base_url, api_key=api_key, timeout=10.0)

        # Try to list models (this tests connectivity)
        models_response = client.models.list()
        available_models = [model.id for model in models_response.data]

        logger.info("✅ OK")

        # Check 2: Model exists
        logger.info("2. Checking model '%s'...", model_name)
        if model_name in available_models:
            logger.info("✅ OK")
        else:
            logger.info("❌ FAILED")
            logger.info("   Error: Model '%s' not found.", model_name)
            logger.info("   Available models:")
            for m in available_models[:10]:  # Show first 10 models
                logger.info("     - %s", m)
            if len(available_models) > 10:
                logger.info("     ... and %d more", len(available_models) - 10)
            all_passed = False

    except Exception as e:
        logger.info("❌ FAILED")
        error_msg = str(e)

        # Provide more specific error messages
        if "Connection refused" in error_msg or "Connection error" in error_msg:
            logger.info("   Error: Cannot connect to %s", base_url)
            logger.info("   Solution:")
            logger.info("     1. Check if the model server is running")
            logger.info("     2. Verify the base URL is correct")
            logger.info("     3. Try: curl %s/models", base_url)
        elif "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            logger.info("   Error: Connection to %s timed out", base_url)
            logger.info("   Solution:")
            logger.info("     1. Check your network connection")
            logger.info("     2. Verify the server is responding")
        elif (
            "Name or service not known" in error_msg
            or "nodename nor servname" in error_msg
        ):
            logger.info("   Error: Cannot resolve hostname")
            logger.info("   Solution:")
            logger.info("     1. Check the URL is correct")
            logger.info("     2. Verify DNS settings")
        else:
            logger.info("   Error: %s", error_msg)

        all_passed = False

    logger.info("-" * 50)

    if all_passed:
        logger.info("✅ Model API checks passed!\n")
    else:
        logger.info("❌ Model API check failed. Please fix the issues above.")

    return all_passed


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Phone Agent iOS - AI-powered iOS phone automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with default settings
    python ios.py

    # Specify model endpoint
    python ios.py --base-url http://localhost:8000/v1

    # Run with specific device
    python ios.py --device-id <UDID>

    # Use WiFi connection
    python ios.py --wda-url http://192.168.1.100:8100

    # List connected devices
    python ios.py --list-devices

    # Check device pairing status
    python ios.py --pair

    # List supported apps
    python ios.py --list-apps

    # Run a specific task
    python ios.py "Open Safari and search for iPhone tips"
        """,
    )

    # Model options
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.getenv("PHONE_AGENT_BASE_URL", "http://localhost:8000/v1"),
        help="Model API base URL",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default="EMPTY",
        help="Model API KEY",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("PHONE_AGENT_MODEL", "autoglm-phone-9b"),
        help="Model name",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=int(os.getenv("PHONE_AGENT_MAX_STEPS", "100")),
        help="Maximum steps per task",
    )

    # iOS Device options
    parser.add_argument(
        "--device-id",
        "-d",
        type=str,
        default=os.getenv("PHONE_AGENT_DEVICE_ID"),
        help="iOS device UDID",
    )

    parser.add_argument(
        "--wda-url",
        type=str,
        default=os.getenv("PHONE_AGENT_WDA_URL", "http://localhost:8100"),
        help="WebDriverAgent URL (default: http://localhost:8100)",
    )

    parser.add_argument(
        "--list-devices", action="store_true", help="List connected iOS devices and exit"
    )

    parser.add_argument(
        "--pair",
        action="store_true",
        help="Pair with iOS device (required for some operations)",
    )

    parser.add_argument(
        "--wda-status",
        action="store_true",
        help="Show WebDriverAgent status and exit",
    )

    # Other options
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress verbose output"
    )

    parser.add_argument(
        "--list-apps", action="store_true", help="List supported apps and exit"
    )

    parser.add_argument(
        "--lang",
        type=str,
        choices=["cn", "en"],
        default=os.getenv("PHONE_AGENT_LANG", "cn"),
        help="Language for system prompt (cn or en, default: cn)",
    )

    parser.add_argument(
        "task",
        nargs="?",
        type=str,
        help="Task to execute (interactive mode if not provided)",
    )

    return parser.parse_args()


def handle_device_commands(args) -> bool:
    """
    Handle iOS device-related commands.

    Returns:
        True if a device command was handled (should exit), False otherwise.
    """
    conn = XCTestConnection(wda_url=args.wda_url)

    # Handle --list-devices
    if args.list_devices:
        devices = list_devices()
        if not devices:
            logger.info("No iOS devices connected.")
            logger.info("\nTroubleshooting:")
            logger.info("  1. Connect device via USB")
            logger.info("  2. Unlock device and trust this computer")
            logger.info("  3. Run: idevice_id -l")
        else:
            logger.info("Connected iOS devices:")
            logger.info("-" * 70)
            for device in devices:
                conn_type = device.connection_type.value
                model_info = "%s" % device.model if device.model else "Unknown"
                ios_info = "iOS %s" % device.ios_version if device.ios_version else ""
                name_info = device.device_name or "Unnamed"

                logger.info("  ✓ %s", name_info)
                logger.info("    UDID: %s", device.device_id)
                logger.info("    Model: %s", model_info)
                logger.info("    OS: %s", ios_info)
                logger.info("    Connection: %s", conn_type)
                logger.info("-" * 70)
        return True

    # Handle --pair
    if args.pair:
        logger.info("Pairing with iOS device...")
        success, message = conn.pair_device(args.device_id)
        logger.info("%s %s", '✓' if success else '✗', message)
        return True

    # Handle --wda-status
    if args.wda_status:
        logger.info("Checking WebDriverAgent status at %s...", args.wda_url)
        logger.info("-" * 50)

        if conn.is_wda_ready():
            logger.info("✓ WebDriverAgent is running")

            status = conn.get_wda_status()
            if status:
                logger.info("\nStatus details:")
                value = status.get("value", {})
                logger.info("  Session ID: %s", status.get('sessionId', 'N/A'))
                logger.info("  Build: %s", value.get('build', {}).get('time', 'N/A'))

                current_app = value.get("currentApp", {})
                if current_app:
                    logger.info("\nCurrent App:")
                    logger.info("  Bundle ID: %s", current_app.get('bundleId', 'N/A'))
                    logger.info("  Process ID: %s", current_app.get('pid', 'N/A'))
        else:
            logger.info("✗ WebDriverAgent is not running")
            logger.info("\nPlease start WebDriverAgent on your iOS device:")
            logger.info("  1. Open WebDriverAgent.xcodeproj in Xcode")
            logger.info("  2. Select your device")
            logger.info("  3. Run WebDriverAgentRunner (Product > Test or Cmd+U)")
            logger.info("  4. For USB: Run port forwarding: iproxy 8100 8100")

        return True

    return False


def main():
    """Main entry point."""
    args = parse_args()

    # Handle --list-apps (no system check needed)
    if args.list_apps:
        logger.info("Supported iOS apps:")
        logger.info("\nNote: For iOS apps, Bundle IDs are configured in:")
        logger.info("  phone_agent/config/apps_ios.py")
        logger.info("\nCurrently configured apps:")
        for app in sorted(list_supported_apps()):
            logger.info("  - %s", app)
        logger.info("\nTo add iOS apps, find the Bundle ID and add to APP_PACKAGES_IOS dictionary.")
        return

    # Handle device commands (these may need partial system checks)
    if handle_device_commands(args):
        return

    # Run system requirements check before proceeding
    if not check_system_requirements(wda_url=args.wda_url):
        sys.exit(1)

    # Check model API connectivity and model availability
    # if not check_model_api(args.base_url, args.api_key, args.model):
    #     sys.exit(1)

    # Create configurations
    model_config = ModelConfig(
        base_url=args.base_url,
        model_name=args.model,
        api_key=args.api_key
    )

    agent_config = IOSAgentConfig(
        max_steps=args.max_steps,
        wda_url=args.wda_url,
        device_id=args.device_id,
        verbose=not args.quiet,
        lang=args.lang,
    )

    # Create iOS agent
    agent = IOSPhoneAgent(
        model_config=model_config,
        agent_config=agent_config,
    )

    # Print header
    logger.info("=" * 50)
    logger.info("Phone Agent iOS - AI-powered iOS automation")
    logger.info("=" * 50)
    logger.info("Model: %s", model_config.model_name)
    logger.info("Base URL: %s", model_config.base_url)
    logger.info("WDA URL: %s", args.wda_url)
    logger.info("Max Steps: %d", agent_config.max_steps)
    logger.info("Language: %s", agent_config.lang)

    # Show device info
    devices = list_devices()
    if agent_config.device_id:
        logger.info("Device: %s", agent_config.device_id)
    elif devices:
        device = devices[0]
        logger.info("Device: %s", device.device_name or device.device_id[:16])
        logger.info("        %s, iOS %s", device.model, device.ios_version)

    logger.info("=" * 50)

    # Run with provided task or enter interactive mode
    if args.task:
        logger.info("\nTask: %s\n", args.task)
        result = agent.run(args.task)
        logger.info("\nResult: %s", result)
    else:
        # Interactive mode
        logger.info("\nEntering interactive mode. Type 'quit' to exit.\n")

        while True:
            try:
                task = input("Enter your task: ").strip()

                if task.lower() in ("quit", "exit", "q"):
                    logger.info("Goodbye!")
                    break

                if not task:
                    continue

                logger.info("")
                result = agent.run(task)
                logger.info("\nResult: %s\n", result)
                agent.reset()

            except KeyboardInterrupt:
                logger.info("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                logger.info("\nError: %s\n", e)


if __name__ == "__main__":
    main()
