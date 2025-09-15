"""
参数管理系统 Python 客户端
支持类似pandas DataFrame的点号访问方式
"""

from .client import ParameterClient, create_client
from .exceptions import ParameterClientError, ParameterNotFoundError, CategoryNotFoundError

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "ParameterClient",
    "create_client", 
    "ParameterClientError",
    "ParameterNotFoundError",
    "CategoryNotFoundError"
]
