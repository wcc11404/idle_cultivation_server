import logging
import sys
from datetime import datetime

# 配置日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# 创建logger
logger = logging.getLogger('idle_cultivation_server')
logger.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format, date_format))

# 添加处理器到logger
logger.addHandler(console_handler)

# 确保没有重复的处理器
if len(logger.handlers) > 1:
    for handler in logger.handlers[:-1]:
        logger.removeHandler(handler)

# 导出logger
__all__ = ['logger']