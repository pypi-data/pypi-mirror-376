"""
amap_route_planner - 一个基于高德API的MCP路线规划服务器。
"""
from .mcpmap import run

__all__ = ['run']
__version__ = "1.1.2"
# 不再暴露 draw_route，也无需 __all__
