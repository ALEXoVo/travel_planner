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
        应用天气和路况权重调整距离矩阵（动态权重计算）。

        权重策略：
        1. 天气权重：雨天 → 户外POI成本增加1.5倍，步行路线增加1.3倍
        2. 路况权重：近期出行(<7天) → 使用实时路况，堵车路线增加成本
        3. 基础权重：距离 × 0.5 + 时间 × 0.5

        Args:
            distance_matrix: 原始距离矩阵
            pois: POI列表（第0个是起点，其余是POI）
            weather_data: 天气数据（from amap weather API）
            traffic_data: 路况数据

        Returns:
            List[List[float]]: 调整后的距离矩阵
        """
        # 复制矩阵
        weighted_matrix = [row[:] for row in distance_matrix]

        # 1. 天气权重逻辑
        if weather_data:
            try:
                # 解析天气数据
                forecasts = weather_data.get('forecasts', [])
                if forecasts:
                    # 取第一天的天气（当天或出发日）
                    first_day = forecasts[0]
                    casts = first_day.get('casts', [])
                    if casts:
                        day_weather = casts[0].get('dayweather', '')

                        # 判断是否有雨
                        is_rainy = any(keyword in day_weather for keyword in ['雨', '雪', '冰雹'])

                        if is_rainy:
                            logger.info(f"Rainy weather detected: {day_weather}, applying weather penalties")

                            # 遍历矩阵，对户外POI和步行路线增加惩罚
                            for i in range(len(weighted_matrix)):
                                for j in range(len(weighted_matrix[i])):
                                    if i == j:
                                        continue

                                    # 如果目标POI是户外类型（索引j-1，因为第0个是起点）
                                    if j > 0 and j - 1 < len(pois):
                                        poi = pois[j - 1]
                                        poi_type = poi.get('type', '')

                                        # 户外POI类型：风景区、公园、游乐场等
                                        outdoor_types = ['风景名胜', '公园广场', '旅游景点', '文物古迹']
                                        if any(t in poi_type for t in outdoor_types):
                                            # 户外景点在雨天成本增加50%
                                            weighted_matrix[i][j] *= 1.5
                                            logger.debug(f"Applied outdoor penalty for {poi.get('name')}")

                                    # 对短距离（<1000米）路线增加惩罚（假设是步行）
                                    if weighted_matrix[i][j] < 1000:
                                        # 步行路线在雨天成本增加30%
                                        weighted_matrix[i][j] *= 1.3

            except Exception as e:
                logger.error(f"Error applying weather weights: {str(e)}")

        # 2. 路况权重逻辑（仅用于近期出行）
        if traffic_data:
            try:
                # traffic_data 应包含实时路况信息
                # 格式示例: {'congestion': True, 'delay_factor': 1.5}
                is_congested = traffic_data.get('congestion', False)
                delay_factor = traffic_data.get('delay_factor', 1.0)

                if is_congested:
                    logger.info(f"Traffic congestion detected, delay factor: {delay_factor}")

                    # 对长距离路线（>5000米）增加拥堵惩罚
                    for i in range(len(weighted_matrix)):
                        for j in range(len(weighted_matrix[i])):
                            if i != j and weighted_matrix[i][j] > 5000:
                                # 驾车路线在拥堵时成本增加
                                weighted_matrix[i][j] *= delay_factor

            except Exception as e:
                logger.error(f"Error applying traffic weights: {str(e)}")

        # 3. 应用配置的权重系数
        weather_weight = Config.ROUTE_OPTIMIZATION.get('weather_weight', 0.2)
        traffic_weight = Config.ROUTE_OPTIMIZATION.get('traffic_weight', 0.3)
        distance_weight = Config.ROUTE_OPTIMIZATION.get('distance_weight', 0.5)

        # 注意：上面的惩罚已经应用，这里的权重系数可以用于进一步调整
        # 目前直接返回调整后的矩阵

        return weighted_matrix

    def optimize_gates_for_sequence(
        self,
        poi_sequence: List[Dict[str, Any]],
        amap_service=None
    ) -> List[Dict[str, Any]]:
        """
        为POI序列优化出入口选择（向量化算法）。

        这是多出入口优化的核心算法。对于序列 A → B → C：
        - B的入口 = 距离A最近的B的门
        - B的出口 = 距离C最近的B的门
        - 对于大型景点，确保入口≠出口（强制穿越）

        Args:
            poi_sequence: POI序列，每个POI包含name, lng, lat等信息
            amap_service: AmapService实例（用于查询门信息）

        Returns:
            List[Dict]: 优化后的POI序列，每个POI增加了 'entry_gate' 和 'exit_gate' 字段

        Examples:
            >>> sequence = [
            ...     {'name': '故宫', 'lng': 116.397, 'lat': 39.909, 'city': '北京'},
            ...     {'name': '天坛', 'lng': 116.407, 'lat': 39.883, 'city': '北京'}
            ... ]
            >>> optimizer = RouteOptimizer()
            >>> result = optimizer.optimize_gates_for_sequence(sequence, amap_service)
            >>> # result[0] 会有 entry_gate 和 exit_gate 字段
        """
        if not poi_sequence or not amap_service:
            logger.warning("Cannot optimize gates: empty sequence or no amap_service")
            return poi_sequence

        optimized_sequence = []

        for i, poi in enumerate(poi_sequence):
            poi_copy = poi.copy()

            # 获取当前POI的所有门
            gates_data = amap_service.get_poi_gates(
                poi_name=poi.get('name', ''),
                city=poi.get('city', ''),
                search_radius=2000
            )

            gates = gates_data.get('gates', [])
            has_multiple_gates = gates_data.get('has_multiple_gates', False)

            # 如果没有门或只有一个门，直接使用主POI坐标
            if not gates or len(gates) <= 1:
                main_location = poi.get('location', '') or gates[0].get('location', '') if gates else ''
                if main_location:
                    lng, lat = map(float, main_location.split(','))
                    poi_copy['entry_gate'] = {
                        'name': poi.get('name', '') + '(主入口)',
                        'location': main_location,
                        'lng': lng,
                        'lat': lat
                    }
                    poi_copy['exit_gate'] = poi_copy['entry_gate'].copy()
                optimized_sequence.append(poi_copy)
                continue

            # 有多个门时，进行优化选择
            # 1. 确定前一个POI和后一个POI的位置
            prev_location = None
            next_location = None

            if i > 0:
                # 前一个POI的出口位置（如果有的话）
                prev_poi = optimized_sequence[i - 1]
                if 'exit_gate' in prev_poi and prev_poi['exit_gate']:
                    prev_location = (
                        prev_poi['exit_gate']['lng'],
                        prev_poi['exit_gate']['lat']
                    )
                else:
                    prev_location = (prev_poi.get('lng'), prev_poi.get('lat'))

            if i < len(poi_sequence) - 1:
                # 后一个POI的位置
                next_poi = poi_sequence[i + 1]
                next_location = (next_poi.get('lng'), next_poi.get('lat'))

            # 2. 选择最优入口门（距离前一个POI最近）
            entry_gate = None
            if prev_location:
                entry_gate = min(
                    gates,
                    key=lambda g: self._calculate_distance(
                        prev_location,
                        tuple(map(float, g.get('location', '0,0').split(',')))
                    )
                )
            else:
                # 第一个POI，选择第一个门或主入口
                entry_gate = gates[0]

            # 3. 选择最优出口门（距离后一个POI最近）
            exit_gate = None
            if next_location:
                # 计算所有门到下一个POI的距离
                gate_distances = [
                    (g, self._calculate_distance(
                        tuple(map(float, g.get('location', '0,0').split(','))),
                        next_location
                    ))
                    for g in gates
                ]
                gate_distances.sort(key=lambda x: x[1])

                # 选择最近的门
                exit_gate = gate_distances[0][0]

                # 4. 大型景点强制穿越：如果入口==出口且有多个门，选择第二近的门
                if (has_multiple_gates and len(gate_distances) > 1 and
                    entry_gate.get('location') == exit_gate.get('location')):
                    # 检查是否确实是大型景点（门之间距离>500米）
                    max_gate_distance = max(
                        self._calculate_distance(
                            tuple(map(float, g1.get('location', '0,0').split(','))),
                            tuple(map(float, g2.get('location', '0,0').split(',')))
                        )
                        for g1 in gates for g2 in gates if g1 != g2
                    ) if len(gates) > 1 else 0

                    if max_gate_distance > 500:  # 大型景点阈值：500米
                        logger.info(f"Large attraction detected for {poi.get('name')}, forcing traversal")
                        exit_gate = gate_distances[1][0]  # 选择第二近的门
            else:
                # 最后一个POI，出口==入口
                exit_gate = entry_gate

            # 5. 添加门信息到POI
            if entry_gate:
                entry_loc = entry_gate.get('location', '0,0')
                entry_lng, entry_lat = map(float, entry_loc.split(','))
                poi_copy['entry_gate'] = {
                    'name': entry_gate.get('name', ''),
                    'location': entry_loc,
                    'lng': entry_lng,
                    'lat': entry_lat,
                    'address': entry_gate.get('address', '')
                }

            if exit_gate:
                exit_loc = exit_gate.get('location', '0,0')
                exit_lng, exit_lat = map(float, exit_loc.split(','))
                poi_copy['exit_gate'] = {
                    'name': exit_gate.get('name', ''),
                    'location': exit_loc,
                    'lng': exit_lng,
                    'lat': exit_lat,
                    'address': exit_gate.get('address', '')
                }

            logger.info(
                f"Optimized gates for {poi.get('name')}: "
                f"Entry={poi_copy.get('entry_gate', {}).get('name')} "
                f"Exit={poi_copy.get('exit_gate', {}).get('name')}"
            )

            optimized_sequence.append(poi_copy)

        return optimized_sequence

    def optimize_route_multi_strategy(
        self,
        pois: List[Dict[str, Any]],
        start_location: Tuple[float, float],
        weather_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        多策略路径规划：生成3种优化策略的路线。

        策略说明：
        1. fastest: 最快路线（基于时间）
        2. shortest: 最短路线（基于距离）
        3. balanced: 平衡路线（距离+时间+天气权重）

        Args:
            pois: POI列表
            start_location: 起点坐标
            weather_data: 天气数据

        Returns:
            Dict包含3种策略的路线：
            {
                'fastest': {
                    'route': [索引列表],
                    'total_distance': 总距离,
                    'total_duration': 总时间
                },
                'shortest': {...},
                'balanced': {...}
            }
        """
        if not pois:
            return {
                'fastest': {'route': [], 'total_distance': 0, 'total_duration': 0},
                'shortest': {'route': [], 'total_distance': 0, 'total_duration': 0},
                'balanced': {'route': [], 'total_distance': 0, 'total_duration': 0}
            }

        try:
            # 1. 构建基础距离矩阵
            base_distance_matrix = self._build_distance_matrix(pois, start_location)

            # 2. 策略1: 最短距离
            shortest_route = self._solve_with_ortools(
                pois, start_location, base_distance_matrix, None, None
            )
            shortest_stats = self._calculate_route_stats(shortest_route, pois, start_location)

            # 3. 策略2: 最快时间（需要假设速度或使用估算）
            # 简化版：假设距离矩阵已经是时间，或者使用加权矩阵
            fastest_weighted_matrix = [row[:] for row in base_distance_matrix]
            # 对长距离（>5km）应用速度因子（假设驾车更快）
            for i in range(len(fastest_weighted_matrix)):
                for j in range(len(fastest_weighted_matrix[i])):
                    if fastest_weighted_matrix[i][j] > 5000:
                        # 长距离路线成本降低（优先选择）
                        fastest_weighted_matrix[i][j] *= 0.7

            fastest_route = self._solve_with_ortools(
                pois, start_location, fastest_weighted_matrix, None, None
            )
            fastest_stats = self._calculate_route_stats(fastest_route, pois, start_location)

            # 4. 策略3: 平衡路线（考虑天气等因素）
            balanced_route = self._solve_with_ortools(
                pois, start_location, base_distance_matrix, weather_data, None
            )
            balanced_stats = self._calculate_route_stats(balanced_route, pois, start_location)

            logger.info(f"Multi-strategy optimization complete:")
            logger.info(f"  Shortest: {len(shortest_route)} POIs, {shortest_stats['total_distance']/1000:.2f}km")
            logger.info(f"  Fastest: {len(fastest_route)} POIs, {fastest_stats['total_distance']/1000:.2f}km")
            logger.info(f"  Balanced: {len(balanced_route)} POIs, {balanced_stats['total_distance']/1000:.2f}km")

            return {
                'shortest': {
                    'route': shortest_route,
                    'total_distance': shortest_stats['total_distance'],
                    'total_duration': shortest_stats['total_duration'],
                    'ordered_pois': reorder_pois(pois, shortest_route)
                },
                'fastest': {
                    'route': fastest_route,
                    'total_distance': fastest_stats['total_distance'],
                    'total_duration': fastest_stats['total_duration'],
                    'ordered_pois': reorder_pois(pois, fastest_route)
                },
                'balanced': {
                    'route': balanced_route,
                    'total_distance': balanced_stats['total_distance'],
                    'total_duration': balanced_stats['total_duration'],
                    'ordered_pois': reorder_pois(pois, balanced_route)
                }
            }

        except Exception as e:
            logger.error(f"Multi-strategy optimization error: {str(e)}")
            # 回退到单一策略
            fallback_route = self._greedy_nearest_neighbor(pois, start_location)
            fallback_stats = self._calculate_route_stats(fallback_route, pois, start_location)
            return {
                'shortest': {
                    'route': fallback_route,
                    'total_distance': fallback_stats['total_distance'],
                    'total_duration': fallback_stats['total_duration'],
                    'ordered_pois': reorder_pois(pois, fallback_route)
                },
                'fastest': {
                    'route': fallback_route,
                    'total_distance': fallback_stats['total_distance'],
                    'total_duration': fallback_stats['total_duration'],
                    'ordered_pois': reorder_pois(pois, fallback_route)
                },
                'balanced': {
                    'route': fallback_route,
                    'total_distance': fallback_stats['total_distance'],
                    'total_duration': fallback_stats['total_duration'],
                    'ordered_pois': reorder_pois(pois, fallback_route)
                }
            }

    def _calculate_route_stats(
        self,
        route: List[int],
        pois: List[Dict[str, Any]],
        start_location: Tuple[float, float]
    ) -> Dict[str, float]:
        """
        计算路线统计信息（总距离、总时间）。

        Args:
            route: POI访问顺序
            pois: POI列表
            start_location: 起点坐标

        Returns:
            Dict: {'total_distance': float, 'total_duration': float}
        """
        total_distance = 0.0
        total_duration = 0.0  # 估算时间（秒）

        current_loc = start_location

        for poi_idx in route:
            if poi_idx < len(pois):
                poi = pois[poi_idx]
                next_loc = (poi.get('lng'), poi.get('lat'))

                distance = self._calculate_distance(current_loc, next_loc)
                total_distance += distance

                # 估算时间：步行速度5km/h，驾车速度40km/h
                if distance < 1000:
                    # 步行
                    total_duration += (distance / 1000) / 5 * 3600  # 秒
                elif distance < 5000:
                    # 公交/地铁
                    total_duration += (distance / 1000) / 20 * 3600
                else:
                    # 驾车
                    total_duration += (distance / 1000) / 40 * 3600

                current_loc = next_loc

        return {
            'total_distance': total_distance,
            'total_duration': total_duration
        }


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
