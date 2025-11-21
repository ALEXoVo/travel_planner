"""
路径优化服务模块

基于Google OR-Tools实现的智能路径优化功能，
支持多约束条件的旅行商问题（TSP）求解。

功能特性：
- 最优访问顺序计算
- 时间窗口约束（景点开放时间）
- 多因素权重（距离、天气、路况）
- 实时调整能力
"""
from typing import List, Dict, Tuple, Optional, Any
import logging
import numpy as np

# OR-Tools导入（需要在requirements.txt中添加ortools）
try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    logging.warning("OR-Tools not installed. Route optimization features will be limited.")

from config import Config

logger = logging.getLogger(__name__)


class RouteOptimizer:
    """路径优化器类"""

    def __init__(self):
        """初始化路径优化器"""
        if not ORTOOLS_AVAILABLE:
            logger.warning("OR-Tools not available. Using fallback greedy algorithm.")

    def optimize_route(
        self,
        pois: List[Dict[str, Any]],
        start_location: Tuple[float, float],
        distance_matrix: List[List[float]] = None,
        weather_data: Dict[str, Any] = None,
        traffic_data: Dict[str, Any] = None
    ) -> List[int]:
        """
        优化POI访问顺序。

        Args:
            pois: POI列表，每个POI包含坐标、开放时间等信息
            start_location: 起点坐标 (lng, lat)
            distance_matrix: 距离矩阵（可选，如果提供则使用，否则自动计算）
            weather_data: 天气数据（用于调整权重）
            traffic_data: 实时路况数据（用于调整权重）

        Returns:
            List[int]: 优化后的POI访问顺序（索引列表）

        Examples:
            >>> pois = [{'name': 'A', 'lng': 116.4, 'lat': 39.9}, ...]
            >>> optimizer = RouteOptimizer()
            >>> route = optimizer.optimize_route(pois, (116.3, 39.8))
            >>> print(route)  # [0, 2, 1, 3]  表示访问顺序
        """
        if not pois:
            return []

        # 如果OR-Tools可用，使用专业求解器
        if ORTOOLS_AVAILABLE and len(pois) > 2:
            return self._solve_with_ortools(
                pois, start_location, distance_matrix, weather_data, traffic_data
            )
        else:
            # 回退到贪心算法
            return self._greedy_nearest_neighbor(pois, start_location)

    def _solve_with_ortools(
        self,
        pois: List[Dict[str, Any]],
        start_location: Tuple[float, float],
        distance_matrix: List[List[float]] = None,
        weather_data: Dict[str, Any] = None,
        traffic_data: Dict[str, Any] = None
    ) -> List[int]:
        """
        使用OR-Tools求解TSP问题。

        这是一个基础示例，展示如何使用OR-Tools。
        后续可以扩展支持时间窗口、容量约束等复杂场景。
        """
        try:
            # 1. 构建距离矩阵（如果未提供）
            if distance_matrix is None:
                distance_matrix = self._build_distance_matrix(pois, start_location)

            # 2. 应用权重调整（天气、路况）
            weighted_matrix = self._apply_weights(
                distance_matrix, pois, weather_data, traffic_data
            )

            # 3. 转换为整数矩阵（OR-Tools要求）
            int_matrix = (np.array(weighted_matrix) * 1000).astype(int).tolist()

            # 4. 创建路由模型
            manager = pywrapcp.RoutingIndexManager(
                len(int_matrix),  # 节点数量
                1,  # 车辆数量（单个旅行者）
                0   # 起点索引（添加了起点作为第0个节点）
            )
            routing = pywrapcp.RoutingModel(manager)

            # 5. 定义距离回调函数
            def distance_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return int_matrix[from_node][to_node]

            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

            # 6. 设置搜索参数
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.seconds = 5  # 5秒超时

            # 7. 求解
            solution = routing.SolveWithParameters(search_parameters)

            # 8. 提取路径
            if solution:
                route = []
                index = routing.Start(0)
                while not routing.IsEnd(index):
                    node = manager.IndexToNode(index)
                    if node > 0:  # 跳过起点（第0个节点）
                        route.append(node - 1)  # 调整索引（因为起点占用了索引0）
                    index = solution.Value(routing.NextVar(index))

                logger.info(f"OR-Tools optimized route: {route}")
                return route
            else:
                logger.warning("OR-Tools failed to find solution, using greedy fallback")
                return self._greedy_nearest_neighbor(pois, start_location)

        except Exception as e:
            logger.error(f"OR-Tools optimization error: {str(e)}")
            return self._greedy_nearest_neighbor(pois, start_location)

    def _greedy_nearest_neighbor(
        self,
        pois: List[Dict[str, Any]],
        start_location: Tuple[float, float]
    ) -> List[int]:
        """
        贪心最近邻算法（简单快速的回退方案）。

        从起点开始，每次选择最近的未访问POI。

        Args:
            pois: POI列表
            start_location: 起点坐标

        Returns:
            List[int]: 访问顺序
        """
        if not pois:
            return []

        unvisited = set(range(len(pois)))
        route = []
        current_location = start_location

        while unvisited:
            # 找到最近的未访问POI
            nearest_idx = min(
                unvisited,
                key=lambda idx: self._calculate_distance(
                    current_location,
                    (pois[idx].get('lng'), pois[idx].get('lat'))
                )
            )

            route.append(nearest_idx)
            unvisited.remove(nearest_idx)
            current_location = (pois[nearest_idx].get('lng'), pois[nearest_idx].get('lat'))

        logger.info(f"Greedy route: {route}")
        return route

    def _build_distance_matrix(
        self,
        pois: List[Dict[str, Any]],
        start_location: Tuple[float, float]
    ) -> List[List[float]]:
        """
        构建距离矩阵。

        矩阵第0行/列为起点，后续为各个POI。

        Args:
            pois: POI列表
            start_location: 起点坐标

        Returns:
            List[List[float]]: 距离矩阵（米）
        """
        # 所有位置 = 起点 + 所有POI
        locations = [start_location] + [(p.get('lng'), p.get('lat')) for p in pois]
        n = len(locations)

        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = self._calculate_distance(locations[i], locations[j])

        return matrix

    def _calculate_distance(
        self,
        loc1: Tuple[float, float],
        loc2: Tuple[float, float]
    ) -> float:
        """
        计算两点间的距离（Haversine公式）。

        Args:
            loc1: 位置1 (lng, lat)
            loc2: 位置2 (lng, lat)

        Returns:
            float: 距离（米）
        """
        from math import radians, sin, cos, sqrt, atan2

        lng1, lat1 = loc1
        lng2, lat2 = loc2

        R = 6371000  # 地球半径（米）

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lng = radians(lng2 - lng1)

        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def _apply_weights(
        self,
        distance_matrix: List[List[float]],
        pois: List[Dict[str, Any]],
        weather_data: Dict[str, Any] = None,
        traffic_data: Dict[str, Any] = None
    ) -> List[List[float]]:
        """
        应用天气和路况权重调整距离矩阵。

        这是一个扩展点，可以根据实际需求实现复杂的权重逻辑。

        Args:
            distance_matrix: 原始距离矩阵
            pois: POI列表
            weather_data: 天气数据
            traffic_data: 路况数据

        Returns:
            List[List[float]]: 调整后的距离矩阵
        """
        # 复制矩阵
        weighted_matrix = [row[:] for row in distance_matrix]

        # TODO: 实现天气权重
        # 示例：如果下雨，户外景点的"距离"增加（降低优先级）
        if weather_data:
            weather_weight = Config.ROUTE_OPTIMIZATION['weather_weight']
            # 这里可以添加天气权重逻辑

        # TODO: 实现路况权重
        # 示例：根据实时路况调整权重
        if traffic_data:
            traffic_weight = Config.ROUTE_OPTIMIZATION['traffic_weight']
            # 这里可以添加路况权重逻辑

        return weighted_matrix


# 辅助函数：基于优化结果重新排序POI列表
def reorder_pois(pois: List[Dict], route: List[int]) -> List[Dict]:
    """
    根据优化路径重新排序POI列表。

    Args:
        pois: 原始POI列表
        route: 优化后的访问顺序

    Returns:
        List[Dict]: 重新排序后的POI列表

    Examples:
        >>> pois = [{'name': 'A'}, {'name': 'B'}, {'name': 'C'}]
        >>> route = [1, 0, 2]
        >>> reorder_pois(pois, route)
        [{'name': 'B'}, {'name': 'A'}, {'name': 'C'}]
    """
    return [pois[i] for i in route]
