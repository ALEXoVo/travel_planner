"""
用户自定义POI行程构建器

基于用户选择的POI列表，生成优化的旅行行程。
支持多策略路径规划、多出入口优化、AI补充等功能。
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from services.amap_service import AmapService
from services.ai_service import AIService
from services.route_optimizer import RouteOptimizer
from utils.prompts import build_itinerary_generation_prompt
from config import Config

logger = logging.getLogger(__name__)


class UserPoiItineraryBuilder:
    """用户POI行程构建器"""

    def __init__(
        self,
        amap_service: AmapService = None,
        ai_service: AIService = None,
        route_optimizer: RouteOptimizer = None
    ):
        self.amap_service = amap_service or AmapService()
        self.ai_service = ai_service or AIService()
        self.route_optimizer = route_optimizer or RouteOptimizer()

    def build_itinerary_from_user_pois(
        self,
        user_pois: List[Dict],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        基于用户选择的POI生成行程

        Args:
            user_pois: 用户选择的POI列表
            preferences: 用户偏好设置
                - start_date: 开始日期
                - end_date: 结束日期
                - destination_city: 目的地城市
                - user_pois_only: bool, 是否仅规划用户POI
                - optimization_strategy: 'all' | 'shortest' | 'fastest' | 'balanced'
                - travelers: 人数
                - budget: 预算

        Returns:
            完整行程数据 + 多策略对比
        """
        try:
            # 1. 提取参数
            start_date = preferences['start_date']
            end_date = preferences['end_date']
            destination_city = preferences['destination_city']
            user_pois_only = preferences.get('user_pois_only', False)
            strategy = preferences.get('optimization_strategy', 'balanced')

            # 2. 计算天数
            days = self._calculate_days(start_date, end_date)
            logger.info(f"Building itinerary for {days} days with {len(user_pois)} user POIs")

            # 3. 获取天气数据
            weather_data = self._fetch_weather_data(destination_city)

            # 4. 多策略路径优化
            start_location = (user_pois[0]['lng'], user_pois[0]['lat'])

            if strategy == 'all':
                # 返回所有策略
                route_strategies = self.route_optimizer.optimize_route_multi_strategy(
                    pois=user_pois,
                    start_location=start_location,
                    weather_data=weather_data
                )
                selected_strategy = 'balanced'
                optimized_pois = route_strategies['balanced']['ordered_pois']
            else:
                # 单一策略
                route_order = self.route_optimizer.optimize_route(
                    pois=user_pois,
                    start_location=start_location,
                    weather_data=weather_data
                )
                optimized_pois = [user_pois[i] for i in route_order]
                route_strategies = None
                selected_strategy = strategy

            # 5. 分配POI到每一天
            daily_pois = self._distribute_pois_to_days(optimized_pois, days)

            # 6. 如果允许AI补充，添加餐厅、酒店
            if not user_pois_only:
                daily_pois = self._supplement_with_meals_and_hotels(
                    daily_pois,
                    destination_city,
                    days
                )

            # 7. 为每天优化出入口（如果POI有多门）
            enriched_days = []
            for day_idx, day_pois in enumerate(daily_pois):
                # 优化出入口
                optimized_sequence = self.route_optimizer.optimize_gates_for_sequence(
                    poi_sequence=day_pois,
                    amap_service=self.amap_service
                )

                # 计算交通信息
                activities = self._build_activities_with_transportation(
                    optimized_sequence,
                    day_idx,
                    start_date,
                    destination_city,
                    weather_data=weather_data  # 🆕 传入天气数据
                )

                enriched_days.append({
                    'day': day_idx + 1,
                    'date': (datetime.strptime(start_date, '%Y-%m-%d') +
                            timedelta(days=day_idx)).strftime('%Y-%m-%d'),
                    'activities': activities
                })

            # 8. 构建返回结果
            result = {
                'itinerary': {
                    'days': enriched_days,
                    'destination': destination_city,
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_days': days,
                    'total_pois': len(user_pois),
                    'user_pois_only': user_pois_only,
                    'selected_strategy': selected_strategy
                }
            }

            # 9. 如果是多策略，添加对比数据
            if route_strategies:
                result['route_strategies'] = route_strategies

            return result

        except Exception as e:
            logger.error(f"Build itinerary from user POIs error: {str(e)}")
            raise

    def _calculate_days(self, start_date: str, end_date: str) -> int:
        """计算天数"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return (end - start).days + 1

    def _fetch_weather_data(self, city: str) -> Optional[Dict]:
        """获取天气数据"""
        try:
            return self.amap_service.get_weather(city)
        except Exception as e:
            logger.warning(f"Failed to fetch weather: {str(e)}")
            return None

    def _distribute_pois_to_days(
        self,
        pois: List[Dict],
        days: int
    ) -> List[List[Dict]]:
        """
        将POI均匀分配到每一天

        算法:
            - 基础每天: total // days
            - 前 (total % days) 天多分配1个

        示例:
            7个POI, 3天 -> Day1(3), Day2(2), Day3(2)
        """
        total = len(pois)
        base = total // days
        remainder = total % days

        result = []
        start_idx = 0

        for day in range(days):
            # 前remainder天多分配1个
            count = base + (1 if day < remainder else 0)
            end_idx = start_idx + count

            result.append(pois[start_idx:end_idx])
            start_idx = end_idx

        return result

    def _supplement_with_meals_and_hotels(
        self,
        daily_pois: List[List[Dict]],
        city: str,
        days: int
    ) -> List[List[Dict]]:
        """
        为每天补充餐厅和酒店

        策略:
            - 每天添加: 早餐、午餐、晚餐
            - 非最后一天添加: 酒店
        """
        try:
            for day_idx, day_pois in enumerate(daily_pois):
                # 在第一个景点前添加早餐
                breakfast = self._find_nearby_restaurant(
                    day_pois[0] if day_pois else None,
                    city,
                    meal_type='早餐'
                )
                if breakfast:
                    day_pois.insert(0, breakfast)

                # 在中间添加午餐
                if len(day_pois) >= 2:
                    mid_idx = len(day_pois) // 2
                    lunch = self._find_nearby_restaurant(
                        day_pois[mid_idx],
                        city,
                        meal_type='午餐'
                    )
                    if lunch:
                        day_pois.insert(mid_idx, lunch)

                # 在最后添加晚餐
                dinner = self._find_nearby_restaurant(
                    day_pois[-1] if day_pois else None,
                    city,
                    meal_type='晚餐'
                )
                if dinner:
                    day_pois.append(dinner)

                # 非最后一天添加酒店
                if day_idx < days - 1:
                    hotel = self._find_nearby_hotel(
                        day_pois[-1] if day_pois else None,
                        city
                    )
                    if hotel:
                        day_pois.append(hotel)

        except Exception as e:
            logger.warning(f"Supplement meals/hotels error: {str(e)}")

        return daily_pois

    def _find_nearby_restaurant(
        self,
        reference_poi: Optional[Dict],
        city: str,
        meal_type: str
    ) -> Optional[Dict]:
        """在指定POI附近搜索餐厅"""
        try:
            if not reference_poi:
                # 无参考POI，搜索城市热门餐厅
                restaurants = self.amap_service.search_food(city)
            else:
                # 在参考POI周围搜索
                location = f"{reference_poi['lng']},{reference_poi['lat']}"
                restaurants = self.amap_service.search_around(
                    location=location,
                    keywords='餐厅',
                    radius=2000
                )

            if restaurants:
                # 返回第一个餐厅，添加meal_type标记
                restaurant = restaurants[0].copy()
                restaurant['meal_type'] = meal_type
                restaurant['type'] = 'meal'
                return restaurant

        except Exception as e:
            logger.warning(f"Find restaurant error: {str(e)}")

        return None

    def _find_nearby_hotel(
        self,
        reference_poi: Optional[Dict],
        city: str
    ) -> Optional[Dict]:
        """在指定POI附近搜索酒店"""
        try:
            if not reference_poi:
                hotels = self.amap_service.search_hotels(city)
            else:
                location = f"{reference_poi['lng']},{reference_poi['lat']}"
                hotels = self.amap_service.search_around(
                    location=location,
                    keywords='酒店',
                    radius=3000
                )

            if hotels:
                hotel = hotels[0].copy()
                hotel['type'] = 'hotel'
                return hotel

        except Exception as e:
            logger.warning(f"Find hotel error: {str(e)}")

        return None

    def _build_activities_with_transportation(
        self,
        optimized_sequence: List[Dict],
        day_idx: int,
        start_date: str,
        city: str,
        weather_data: Optional[Dict] = None
    ) -> List[Dict]:
        """
        构建带交通信息的活动列表

        Args:
            optimized_sequence: 优化后的POI序列
            day_idx: 天数索引
            start_date: 开始日期
            city: 城市名称
            weather_data: 天气数据（用于生成交通提示）
        """
        activities = []

        for i, poi in enumerate(optimized_sequence):
            activity = {
                'name': poi.get('name'),
                'type': poi.get('type', 'attraction'),
                'address': poi.get('address', ''),
                'coordinates': {
                    'lng': poi.get('exit_gate', {}).get('lng') or poi.get('lng'),
                    'lat': poi.get('exit_gate', {}).get('lat') or poi.get('lat')
                }
            }

            # 第一个活动无交通信息
            if i == 0:
                activity['transportation_options'] = []  # 🔧 修正字段名
            else:
                # 计算交通信息
                prev_poi = optimized_sequence[i - 1]
                prev_location = (
                    prev_poi.get('exit_gate', {}).get('lng') or prev_poi.get('lng'),
                    prev_poi.get('exit_gate', {}).get('lat') or prev_poi.get('lat')
                )
                curr_location = (
                    poi.get('entry_gate', {}).get('lng') or poi.get('lng'),
                    poi.get('entry_gate', {}).get('lat') or poi.get('lat')
                )

                # 估算当前活动时间
                estimated_hour = 9 + day_idx + (i * 2)
                current_time = f"{estimated_hour % 24:02d}:00"

                transportation_options = self._calculate_transportation(
                    prev_location,
                    curr_location,
                    city,
                    weather_data=weather_data,  # 🆕 传入天气数据
                    current_time=current_time   # 🆕 传入当前时间
                )
                activity['transportation_options'] = transportation_options  # 🔧 修正字段名

            activities.append(activity)

        return activities

    def _calculate_transportation(
        self,
        origin: tuple,
        destination: tuple,
        city: str,
        weather_data: Optional[Dict] = None,
        current_time: str = "09:00"
    ) -> List[Dict]:
        """
        计算多方案交通信息

        Args:
            origin: 起点坐标 (lng, lat)
            destination: 终点坐标 (lng, lat)
            city: 城市名称
            weather_data: 天气数据（用于生成提示）
            current_time: 当前时间（用于判断高峰期）

        Returns:
            多个交通方案列表
        """
        try:
            origin_str = f"{origin[0]},{origin[1]}"
            dest_str = f"{destination[0]},{destination[1]}"

            # 获取距离
            distance_data = self.amap_service.get_distance(origin_str, dest_str)
            if not distance_data or not distance_data.get('results'):
                return []

            distance = int(distance_data['results'][0].get('distance', 0))
            if distance == 0:
                return []

            options = []

            # 1. 驾车方案（永远添加）
            driving = self.amap_service.get_driving_route(origin_str, dest_str)
            if driving[0] > 0:
                options.append({
                    'mode': Config.TRANSPORT_MODES['driving'],
                    'mode_key': 'driving',
                    'distance': driving[0],
                    'duration': driving[1],
                    'distance_text': f"{driving[0] / 1000:.1f}公里",
                    'duration_text': f"{driving[1] // 60}分钟" if driving[1] >= 60 else f"{driving[1]}秒",
                    'polyline': driving[2],
                    'tips': self._generate_tips('driving', weather_data, current_time, driving[0])
                })

            # 2. 公交方案（距离 > 1km）
            if distance > 1000:
                transit = self.amap_service.get_transit_route(origin_str, dest_str, city)
                if transit[0] > 0:
                    options.append({
                        'mode': Config.TRANSPORT_MODES['transit'],
                        'mode_key': 'transit',
                        'distance': transit[0],
                        'duration': transit[1],
                        'distance_text': f"{transit[0] / 1000:.1f}公里",
                        'duration_text': f"{transit[1] // 60}分钟" if transit[1] >= 60 else f"{transit[1]}秒",
                        'polyline': transit[2],
                        'tips': self._generate_tips('transit', weather_data, current_time, transit[0])
                    })

            # 3. 步行方案（距离 < 2km）
            if distance < 2000:
                walking = self.amap_service.get_walking_route(origin_str, dest_str)
                if walking[0] > 0:
                    options.append({
                        'mode': Config.TRANSPORT_MODES['walking'],
                        'mode_key': 'walking',
                        'distance': walking[0],
                        'duration': walking[1],
                        'distance_text': f"{walking[0] / 1000:.1f}公里",
                        'duration_text': f"{walking[1] // 60}分钟" if walking[1] >= 60 else f"{walking[1]}秒",
                        'polyline': walking[2],
                        'tips': self._generate_tips('walking', weather_data, current_time, walking[0])
                    })

            # 4. 骑行方案（距离 < 5km）
            if distance < 5000:
                cycling = self.amap_service.get_cycling_route(origin_str, dest_str)
                if cycling[0] > 0:
                    options.append({
                        'mode': Config.TRANSPORT_MODES['cycling'],
                        'mode_key': 'cycling',
                        'distance': cycling[0],
                        'duration': cycling[1],
                        'distance_text': f"{cycling[0] / 1000:.1f}公里",
                        'duration_text': f"{cycling[1] // 60}分钟" if cycling[1] >= 60 else f"{cycling[1]}秒",
                        'polyline': cycling[2],
                        'tips': self._generate_tips('cycling', weather_data, current_time, cycling[0])
                    })

            return options

        except Exception as e:
            logger.error(f"Calculate multi transportation error: {str(e)}")
            return []

    def _generate_tips(
        self,
        mode_key: str,
        weather_data: Optional[Dict],
        current_time: str,
        distance: int
    ) -> List[str]:
        """生成交通提示（与itinerary_builder中的逻辑相同）"""
        tips = []

        # 天气提示
        if weather_data and weather_data.get('forecasts'):
            dayweather = weather_data['forecasts'][0].get('casts', [{}])[0].get('dayweather', '')
            has_bad_weather = any(kw in dayweather for kw in ['雨', '雪', '雾'])

            if has_bad_weather:
                if mode_key == 'walking':
                    tips.append(f"今日{dayweather}，建议携带雨具")
                elif mode_key == 'cycling':
                    tips.append(f"今日{dayweather}，骑行路滑注意安全，建议选择其他方式")
                elif mode_key == 'transit':
                    tips.append(f"今日{dayweather}，公共交通较为舒适")
                elif mode_key == 'driving':
                    tips.append(f"今日{dayweather}，驾车请减速慢行")

        # 高峰期提示
        try:
            hour = int(current_time.split(':')[0])
            if (7 <= hour < 9 or 17 <= hour < 19):
                if mode_key == 'driving':
                    tips.append("当前时段可能拥堵，建议预留充足时间或选择公共交通")
                elif mode_key == 'transit':
                    tips.append("高峰期公交可能较为拥挤")
        except Exception:
            pass

        # 距离提示
        if mode_key == 'walking' and distance > 1500:
            tips.append(f"步行距离较远（{distance/1000:.1f}km），请根据体力选择")

        if mode_key == 'cycling' and distance > 4000:
            tips.append(f"骑行距离较远（{distance/1000:.1f}km），请注意安全")

        return tips
