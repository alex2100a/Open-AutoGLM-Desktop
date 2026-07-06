#!/usr/bin/env python3
"""日志系统使用示例

演示如何使用统一的日志系统替代print语句。

运行方式：
    # 默认INFO级别
    python examples/logging_demo.py

    # DEBUG级别（显示所有日志）
    PHONE_AGENT_LOG_LEVEL=DEBUG python examples/logging_demo.py

    # 输出到文件
    PHONE_AGENT_LOG_FILE=demo.log python examples/logging_demo.py

    # 禁用颜色
    NO_COLOR=1 python examples/logging_demo.py
"""

import time
from phone_agent.utils import get_logger, setup_logging

# 获取logger实例
logger = get_logger(__name__)


def demo_basic_logging():
    """演示基本的日志记录"""
    logger.info("=" * 50)
    logger.info("示例 1: 基本日志记录")
    logger.info("=" * 50)

    logger.debug("这是DEBUG级别的日志（默认不显示）")
    logger.info("这是INFO级别的日志")
    logger.warning("这是WARNING级别的日志")
    logger.error("这是ERROR级别的日志")
    logger.critical("这是CRITICAL级别的日志")

    logger.info("")


def demo_formatted_logging():
    """演示格式化日志"""
    logger.info("=" * 50)
    logger.info("示例 2: 格式化日志")
    logger.info("=" * 50)

    user = "张三"
    age = 25
    score = 95.5

    # 推荐：使用 % 格式化（延迟格式化）
    logger.info("用户: %s, 年龄: %d, 分数: %.2f", user, age, score)

    # 也可以使用 f-string（但不推荐，性能较差）
    logger.info(f"用户: {user}, 年龄: {age}, 分数: {score}")

    logger.info("")


def demo_performance_logging():
    """演示性能指标记录"""
    logger.info("=" * 50)
    logger.info("示例 3: 性能指标记录")
    logger.info("=" * 50)

    start_time = time.time()

    # 模拟耗时操作
    logger.info("开始执行任务...")
    time.sleep(0.5)

    elapsed = time.time() - start_time
    logger.info("任务完成，耗时: %.3f秒", elapsed)

    logger.info("")


def demo_exception_logging():
    """演示异常日志记录"""
    logger.info("=" * 50)
    logger.info("示例 4: 异常日志记录")
    logger.info("=" * 50)

    try:
        # 模拟异常
        result = 10 / 0
    except ZeroDivisionError as e:
        # 使用 exc_info=True 记录完整堆栈
        logger.error("发生除零错误: %s", e, exc_info=True)

    try:
        # 模拟另一个异常
        data = {"name": "test"}
        value = data["age"]
    except KeyError as e:
        logger.warning("键不存在: %s", e)

    logger.info("")


def demo_conditional_logging():
    """演示条件日志"""
    logger.info("=" * 50)
    logger.info("示例 5: 条件日志")
    logger.info("=" * 50)

    verbose = True

    for i in range(5):
        # 详细日志（仅在DEBUG级别显示）
        logger.debug("处理第 %d 项", i)

        # 根据条件决定日志级别
        if verbose:
            logger.info("完成第 %d 项", i)

    logger.info("")


def demo_structured_logging():
    """演示结构化日志"""
    logger.info("=" * 50)
    logger.info("示例 6: 结构化日志")
    logger.info("=" * 50)

    # 模拟任务执行
    task_id = "task_001"
    logger.info("任务开始: %s", task_id)

    steps = ["初始化", "数据加载", "处理", "保存结果"]

    for step in steps:
        logger.info("  - %s", step)
        time.sleep(0.1)

    logger.info("任务完成: %s", task_id)

    logger.info("")


def demo_comparison():
    """对比print和logger的区别"""
    logger.info("=" * 50)
    logger.info("示例 7: print vs logger 对比")
    logger.info("=" * 50)

    # 旧方式：使用print
    logger.info("这是使用print输出的信息")
    logger.info(f"当前时间: {time.time()}")

    # 新方式：使用logger
    logger.info("这是使用logger输出的信息")
    logger.info("当前时间: %.3f", time.time())

    logger.info("")
    logger.info("logger的优势:")
    logger.info("  ✓ 可以控制日志级别")
    logger.info("  ✓ 统一的格式（包含时间戳、模块名等）")
    logger.info("  ✓ 可以输出到文件")
    logger.info("  ✓ 支持彩色输出")
    logger.info("  ✓ 延迟格式化，性能更好")

    logger.info("")


def main():
    """主函数"""
    # 配置日志系统（可选，如果不配置会使用默认设置）
    # setup_logging(level="DEBUG", use_colors=True)

    logger.info("\n" + "=" * 50)
    logger.info("🎯 日志系统使用示例")
    logger.info("=" * 50)
    logger.info("")

    # 运行各个示例
    demo_basic_logging()
    demo_formatted_logging()
    demo_performance_logging()
    demo_exception_logging()
    demo_conditional_logging()
    demo_structured_logging()
    demo_comparison()

    logger.info("=" * 50)
    logger.info("✅ 所有示例运行完成")
    logger.info("=" * 50)
    logger.info("")

    # 提示如何使用不同配置
    logger.info("💡 提示:")
    logger.info("  - 查看DEBUG日志: PHONE_AGENT_LOG_LEVEL=DEBUG python %s", __file__)
    logger.info("  - 输出到文件: PHONE_AGENT_LOG_FILE=demo.log python %s", __file__)
    logger.info("  - 禁用颜色: NO_COLOR=1 python %s", __file__)


if __name__ == "__main__":
    main()
