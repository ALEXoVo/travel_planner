"""
行程构建服务模块

整合AI服务、地图服务、路径优化等功能，
负责完整的行程生成流程。
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

from services.amap_service import AmapService
from services.ai_service import AIService
from utils.geo_utils import add_coordinates_to_pois
from utils.json_fixer import extract_json_from_text, fix_incomplete_json
from utils.prompts import build_itinerary_generation_prompt
from config import Config

logger = logging.getLogger(__name__)


class ItineraryBuilder:
    """行程构建器类"""

    def __init__(
        self,
        amap_service: AmapService = None,
        ai_service: AIService = None
    ):
        """
        初始化行程构建器。

        Args:
            amap_service: 高德地图服务实例
            ai_service: AI服务实例
        """
        self.amap_service = amap_service or AmapService()
        self.ai_service = ai_service or AIService()

    def build_itinerary(
        self,
        user_preferences: Dict[str, Any],
        replan_mode: str = None,
        previous_itinerary: Dict[str, Any] = None,
        user_pois: list = None
    ) -> Dict[str, Any]:
        """
        构建完整的旅游行程（支持重新规划）。

        Args:
            user_preferences: 用户偏好设置，包含：
                - destinationCity: 目的地城市
                - originCity: 出发城市（可选）
                - startDate: 开始日期
                - endDate: 结束日期
                - budget: 预算
                - budgetType: 预算类型
                - customBudget: 自定义预算（可选）
                - travelers: 出行人数
                - travelStyles: 旅游风格列表
            replan_mode: 重新规划模式
                - None: 首次规划
                - 'incremental': 增量规划（保留所有原有景点）
                - 'complete': 完全重新规划（只保留必去景点）
            previous_itinerary: 上次生成的行程数据（用于增量规划）
            user_pois: 用户添加的POI列表

        Returns:
            Dict[str, Any]: 完整的行程数据

        Raises:
            ValueError: 参数验证失败
            Exception: 行程生成失败
        """
        # 1. 验证必需参数
        self._validate_preferences(user_preferences)

        # 2. 提取参数
        destination_city = user_preferences['destinationCity']
        origin_city = user_preferences.get('originCity')
        start_date = user_preferences['startDate']
        end_date = user_preferences['endDate']
        budget = user_preferences.get('budget')
        budget_type = user_preferences.get('budgetType')
        custom_budget = user_preferences.get('customBudget')
        travelers = user_preferences.get('travelers', 1)
        travel_styles = user_preferences.get('travelStyles', [])
        custom_prompt = user_preferences.get('customPrompt', '')  # 自定义需求
        accommodation = user_preferences.get('accommodation', '')  # 住宿信息

        # 3. 处理用户POI（如果提供）
        if user_pois is None:
            user_pois = []

        logger.info(f"Building itinerary with {len(user_pois)} user POIs, replan_mode={replan_mode}")

        # 3. 计算天数
        days = self._calculate_days(start_date, end_date)
        logger.info(f"Building itinerary for {days} days in {destination_city}")

        # 4. 获取POI数据
        poi_data = self._fetch_poi_data(destination_city)

        # 5. 获取天气数据
        weather_data = self._fetch_weather_data(destination_city)

        # 6. 生成AI行程（支持重新规划）
        itinerary_data = self._generate_ai_itinerary(
            destination_city=destination_city,
            origin_city=origin_city,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            budget_type=budget_type,
            custom_budget=custom_budget,
            travelers=travelers,
            travel_styles=travel_styles,
            custom_prompt=custom_prompt,
            accommodation=accommodation,
            poi_data=poi_data,
            weather_data=weather_data,
            days=days,
            user_pois=user_pois,
            replan_mode=replan_mode
        )

        # 7. 增强行程（坐标、交通）
        enriched_itinerary = self._enrich_itinerary(
            itinerary_data=itinerary_data,
            destination_city=destination_city,
            origin_city=origin_city,
            weather_data=weather_data
        )

        logger.info("Itinerary building completed successfully")
        return enriched_itinerary

    def _validate_preferences(self, preferences: Dict[str, Any]) -> None:
        """验证用户偏好参数"""
        required_fields = ['destinationCity', 'startDate', 'endDate']
        missing_fields = [f for f in required_fields if not preferences.get(f)]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    def _calculate_days(self, start_date: str, end_date: str) -> int:
        """计算行程天数"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days + 1

    def _fetch_poi_data(self, city: str) -> Dict[str, List[Dict]]:
        """
        获取所有类别的POI数据。

        Args:
            city: 城市名称

        Returns:
            Dict[str, List[Dict]]: 各类别POI数据
        """
        logger.info(f"Fetching POI data for {city}")

        poi_data = {
            'destination': [],
            'food': [],
            'hotel': [],
            'cultural': [],
            'shopping': [],
            'parent_child': []
        }

        try:
            poi_data['destination'] = self.amap_service.search_scenic_spots(city)
            logger.info(f"Fetched {len(poi_data['destination'])} scenic spots")
        except Exception as e:
            logger.error(f"Error fetching scenic spots: {str(e)}")

        try:
            poi_data['food'] = self.amap_service.search_food(city)
            logger.info(f"Fetched {len(poi_data['food'])} food POIs")
        except Exception as e:
            logger.error(f"Error fetching food POIs: {str(e)}")

        try:
            poi_data['hotel'] = self.amap_service.search_hotels(city)
            logger.info(f"Fetched {len(poi_data['hotel'])} hotels")
        except Exception as e:
            logger.error(f"Error fetching hotels: {str(e)}")

        try:
            poi_data['cultural'] = self.amap_service.search_cultural(city)
            logger.info(f"Fetched {len(poi_data['cultural'])} cultural POIs")
        except Exception as e:
            logger.error(f"Error fetching cultural POIs: {str(e)}")

        try:
            poi_data['shopping'] = self.amap_service.search_shopping(city)
            logger.info(f"Fetched {len(poi_data['shopping'])} shopping POIs")
        except Exception as e:
            logger.error(f"Error fetching shopping POIs: {str(e)}")

        try:
            poi_data['parent_child'] = self.amap_service.search_parent_child(city)
            logger.info(f"Fetched {len(poi_data['parent_child'])} parent-child POIs")
        except Exception as e:
            logger.error(f"Error fetching parent-child POIs: {str(e)}")

        # 批量添加坐标
        for category, pois in poi_data.items():
            add_coordinates_to_pois(pois, city, self.amap_service.api_key)
            logger.info(f"Processed coordinates for {len(pois)} {category} POIs")

        return poi_data

    def _fetch_weather_data(self, city: str) -> Optional[Dict[str, Any]]:
        """获取天气数据"""
        try:
            weather_data = self.amap_service.get_weather(city)
            logger.info("Weather data fetched successfully")
            return weather_data
        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            return None

    def _generate_ai_itinerary(
        self,
        destination_city: str,
        origin_city: str,
        start_date: str,
        end_date: str,
        budget: str,
        budget_type: str,
        custom_budget: str,
        travelers: int,
        travel_styles: List[str],
        custom_prompt: str,
        accommodation: str,
        poi_data: Dict[str, List],
        weather_data: Dict[str, Any],
        days: int,
        user_pois: list = None,
        replan_mode: str = None
    ) -> Dict[str, Any]:
        """
        调用AI生成行程。

        Args:
            user_pois: 用户选择的POI列表（可选）
            replan_mode: 重新规划模式（'incremental'/'complete'/None，可选）

        Returns:
            Dict[str, Any]: AI生成的行程数据
        """
        # 构建提示词
        prompt = build_itinerary_generation_prompt(
            destination_city=destination_city,
            origin_city=origin_city,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            budget_type=budget_type,
            custom_budget=custom_budget,
            travelers=travelers,
            travel_styles=travel_styles,
            custom_prompt=custom_prompt,
            accommodation=accommodation,
            destination_pois=poi_data['destination'],
            food_pois=poi_data['food'],
            hotel_pois=poi_data['hotel'],
            cultural_pois=poi_data['cultural'],
            shopping_pois=poi_data['shopping'],
            parent_child_pois=poi_data['parent_child'],
            weather_data=weather_data,
            days=days,
            user_pois=user_pois,
            replan_mode=replan_mode
        )

        # 调用AI
        ai_response = self.ai_service.generate_itinerary(prompt, days)

        # 解析JSON
        itinerary_data = self._parse_ai_response(ai_response)

        return itinerary_data

    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        解析AI响应，提取并修复JSON。

        Args:
            ai_response: AI返回的原始响应

        Returns:
            Dict[str, Any]: 解析后的行程数据

        Raises:
            ValueError: JSON解析失败
        """
        import re

        # 尝试提取JSON
        json_match = re.search(r'\{.*\}|\[.*\]', ai_response, re.DOTALL)
        if not json_match:
            logger.error("No JSON structure found in AI response")
            raise ValueError("AI返回内容格式错误：未找到JSON结构")

        json_str = json_match.group()

        # 尝试解析
        try:
            itinerary_data = json.loads(json_str)
            logger.info("JSON parsing successful on first attempt")
            return itinerary_data
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed, attempting to fix: {str(e)}")

            # 尝试修复
            try:
                fixed_json = fix_incomplete_json(json_str)
                itinerary_data = json.loads(fixed_json)
                logger.info("JSON parsing successful after fix")
                return itinerary_data
            except Exception as fix_error:
                logger.error(f"JSON fix failed: {str(fix_error)}")
                logger.error(f"JSON string length: {len(json_str)}")
                logger.error(f"Last 500 chars: {json_str[-500:]}")

                raise ValueError(
                    "AI返回的JSON结构不完整，可能是因为行程天数较多导致响应被截断。"
                    "建议缩短行程天数或稍后重试。"
                )

    def _enrich_itinerary(
        self,
        itinerary_data: Dict[str, Any],
        destination_city: str,
        origin_city: str,
        weather_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        增强行程数据：添加坐标、交通信息等。

        Args:
            itinerary_data: AI生成的原始行程数据
            destination_city: 目的地城市
            origin_city: 出发城市
            weather_data: 天气数据

        Returns:
            Dict[str, Any]: 增强后的行程数据
        """
        if 'itinerary' not in itinerary_data:
            logger.warning("No itinerary found in data")
            return itinerary_data

        logger.info(f"Enriching itinerary with {len(itinerary_data['itinerary'])} days")

        # 获取出发地坐标
        origin_coords = None
        if origin_city:
            origin_coords = self.amap_service.geocode(origin_city, origin_city)

        # 处理每一天的行程
        for day_index, day in enumerate(itinerary_data['itinerary']):
            # 填充天气信息
            self._fill_weather_info(day, day_index, weather_data)

            # 处理活动
            if 'activities' in day:
                self._enrich_activities(
                    day=day,
                    day_index=day_index,
                    all_days=itinerary_data['itinerary'],
                    destination_city=destination_city,
                    origin_coords=origin_coords,
                    weather_data=weather_data  #  传入天气数据
                )

        return itinerary_data

    def _fill_weather_info(
        self,
        day: Dict[str, Any],
        day_index: int,
        weather_data: Dict[str, Any]
    ) -> None:
        """填充天气信息"""
        if 'weather' in day and day['weather']:
            return  # 已有天气信息

        if not weather_data or not weather_data.get('forecasts'):
            return

        forecasts = weather_data['forecasts'][0].get('casts', [])
        if not forecasts:
            return

        # 根据天数索引获取天气
        forecast_index = day_index % len(forecasts)
        day['weather'] = forecasts[forecast_index]

    def _enrich_activities(
        self,
        day: Dict[str, Any],
        day_index: int,
        all_days: List[Dict],
        destination_city: str,
        origin_coords: Optional[tuple],
        weather_data: Optional[Dict] = None
    ) -> None:
        """
        增强活动信息：坐标、交通。

        Args:
            day: 当天行程数据
            day_index: 天数索引
            all_days: 所有天的行程
            destination_city: 目的地城市
            origin_coords: 出发地坐标
            weather_data: 天气数据（用于生成交通提示）
        """
        activities = day.get('activities', [])
        previous_day_activities = []

        if day_index > 0:
            previous_day_activities = all_days[day_index - 1].get('activities', [])

        # 第一遍：解析所有活动的坐标
        for i, activity in enumerate(activities):
            self._resolve_activity_coordinates(activity, destination_city)

        # 第二遍：优化出入口选择（多出入口优化）
        if len(activities) > 0:
            try:
                # 准备POI序列供优化
                poi_sequence = []
                for activity in activities:
                    loc = activity.get('location', {})
                    poi_sequence.append({
                        'name': activity.get('title', ''),
                        'lng': loc.get('lng'),
                        'lat': loc.get('lat'),
                        'city': destination_city,
                        'location': f"{loc.get('lng', 0)},{loc.get('lat', 0)}"
                    })

                # 调用门优化算法
                optimized_pois = self.route_optimizer.optimize_gates_for_sequence(
                    poi_sequence,
                    self.amap_service
                )

                # 将优化后的门信息写回activities
                for i, activity in enumerate(activities):
                    if i < len(optimized_pois):
                        optimized = optimized_pois[i]
                        if 'entry_gate' in optimized:
                            activity['entry_gate'] = optimized['entry_gate']
                        if 'exit_gate' in optimized:
                            activity['exit_gate'] = optimized['exit_gate']

                logger.info(f"Gate optimization complete for day {day_index + 1}, {len(activities)} activities")

            except Exception as e:
                logger.warning(f"Gate optimization failed for day {day_index + 1}: {str(e)}")
                # 优化失败不影响主流程，继续执行

        # 第三遍：计算交通信息
        for i, activity in enumerate(activities):
            # 计算交通信息（跳过第一天的第一个活动）
            if not (day_index == 0 and i == 0):
                # 估算当前活动时间（假设第一天9点开始，每个活动间隔2小时）
                estimated_hour = 9 + day_index + (i * 2)
                current_time = f"{estimated_hour % 24:02d}:00"

                self._calculate_transportation(
                    activity=activity,
                    activity_index=i,
                    activities=activities,
                    previous_day_activities=previous_day_activities,
                    is_first_of_day=(i == 0),
                    destination_city=destination_city,
                    origin_coords=origin_coords,
                    is_first_day=(day_index == 0),
                    weather_data=weather_data,  #  传入天气数据
                    current_time=current_time   #  传入当前时间
                )
            else:
                activity['transportation_options'] = []  #  修正字段名

    def _resolve_activity_coordinates(
        self,
        activity: Dict[str, Any],
        city: str
    ) -> None:
        """解析活动坐标"""
        location = activity.get('location', {})

        # 如果AI已提供坐标，验证并转换
        if location.get('lng') is not None and location.get('lat') is not None:
            try:
                location['lng'] = float(location['lng'])
                location['lat'] = float(location['lat'])
                return  # 坐标有效，直接返回
            except ValueError:
                logger.warning(f"Invalid coordinates from AI: {location}")

        # 尝试地理编码
        address = location.get('address')
        title = activity.get('title')

        if address and address != '详细地址':
            coords = self.amap_service.geocode(address, city)
            if coords:
                location['lng'], location['lat'] = coords
                logger.info(f"Geocoded: {title} -> {coords}")
                return

        # 尝试POI搜索
        if title:
            from utils.geo_utils import get_poi_coordinates
            lng, lat = get_poi_coordinates(title, address or '', city, self.amap_service.api_key)
            if lng and lat:
                location['lng'] = lng
                location['lat'] = lat
                logger.info(f"POI search: {title} -> ({lng}, {lat})")
                return

        # 使用默认坐标
        logger.warning(f"Using default coordinates for: {title}")
        location['lng'] = Config.DEFAULT_LNG
        location['lat'] = Config.DEFAULT_LAT

    def _calculate_transportation(
        self,
        activity: Dict[str, Any],
        activity_index: int,
        activities: List[Dict],
        previous_day_activities: List[Dict],
        is_first_of_day: bool,
        destination_city: str,
        origin_coords: Optional[tuple],
        is_first_day: bool,
        weather_data: Optional[Dict] = None,
        current_time: str = "09:00"
    ) -> None:
        """
        计算多方案交通信息（支持多出入口优化）

        新增参数：
            weather_data: 天气数据（用于生成提示）
            current_time: 当前时间（用于判断高峰期）
        """
        # === 1. 确定起点（保持原逻辑，优先使用前一个活动的出口门）===
        if is_first_of_day and previous_day_activities:
            prev_activity = previous_day_activities[-1]
            if 'exit_gate' in prev_activity and prev_activity['exit_gate']:
                origin_lng = prev_activity['exit_gate'].get('lng')
                origin_lat = prev_activity['exit_gate'].get('lat')
                origin_name = prev_activity.get('title', '') + f"({prev_activity['exit_gate'].get('name', '出口')})"
            else:
                origin_lng = prev_activity['location'].get('lng')
                origin_lat = prev_activity['location'].get('lat')
                origin_name = prev_activity.get('title', '')
        elif not is_first_of_day:
            prev_activity = activities[activity_index - 1]
            if 'exit_gate' in prev_activity and prev_activity['exit_gate']:
                origin_lng = prev_activity['exit_gate'].get('lng')
                origin_lat = prev_activity['exit_gate'].get('lat')
                origin_name = prev_activity.get('title', '') + f"({prev_activity['exit_gate'].get('name', '出口')})"
            else:
                origin_lng = prev_activity['location'].get('lng')
                origin_lat = prev_activity['location'].get('lat')
                origin_name = prev_activity.get('title', '')
        else:
            activity['transportation_options'] = []
            return

        # === 2. 确定终点（优先使用当前活动的入口门）===
        if 'entry_gate' in activity and activity['entry_gate']:
            dest_lng = activity['entry_gate'].get('lng')
            dest_lat = activity['entry_gate'].get('lat')
        else:
            dest_lng = activity['location'].get('lng')
            dest_lat = activity['location'].get('lat')

        if origin_lng is None or origin_lat is None or dest_lng is None or dest_lat is None:
            activity['transportation_options'] = []
            return

        origin_str = f"{origin_lng},{origin_lat}"
        dest_str = f"{dest_lng},{dest_lat}"

        # === 3. 获取估算距离 ===
        distance, _ = self.amap_service.get_distance(origin_str, dest_str)

        if distance == 0:
            activity['transportation_options'] = []
            return

        # === 4. 生成多个交通方案 ===
        options = []

        # 4.1 驾车方案（永远添加）
        driving_dist, driving_dur, driving_poly = self.amap_service.get_driving_route(origin_str, dest_str)
        if driving_dist > 0:
            options.append({
                'mode': Config.TRANSPORT_MODES['driving'],
                'mode_key': 'driving',
                'distance': driving_dist,
                'duration': driving_dur,
                'distance_text': f"{driving_dist / 1000:.1f}公里",
                'duration_text': f"{driving_dur // 60}分钟" if driving_dur >= 60 else f"{driving_dur}秒",
                'polyline': driving_poly,
                'tips': []
            })

        # 4.2 公交方案（距离 > 1km）
        if distance > Config.TRANSPORT_OPTIONS_RULES['transit']['threshold']:
            transit_dist, transit_dur, transit_poly = self.amap_service.get_transit_route(
                origin_str, dest_str, destination_city
            )
            if transit_dist > 0:
                options.append({
                    'mode': Config.TRANSPORT_MODES['transit'],
                    'mode_key': 'transit',
                    'distance': transit_dist,
                    'duration': transit_dur,
                    'distance_text': f"{transit_dist / 1000:.1f}公里",
                    'duration_text': f"{transit_dur // 60}分钟" if transit_dur >= 60 else f"{transit_dur}秒",
                    'polyline': transit_poly,
                    'tips': []
                })

        # 4.3 步行方案（距离 < 2km）
        if distance < Config.TRANSPORT_OPTIONS_RULES['walking']['threshold']:
            walking_dist, walking_dur, walking_poly = self.amap_service.get_walking_route(origin_str, dest_str)
            if walking_dist > 0:
                options.append({
                    'mode': Config.TRANSPORT_MODES['walking'],
                    'mode_key': 'walking',
                    'distance': walking_dist,
                    'duration': walking_dur,
                    'distance_text': f"{walking_dist / 1000:.1f}公里",
                    'duration_text': f"{walking_dur // 60}分钟" if walking_dur >= 60 else f"{walking_dur}秒",
                    'polyline': walking_poly,
                    'tips': []
                })

        # 4.4 骑行方案（距离 < 5km）
        if distance < Config.TRANSPORT_OPTIONS_RULES['cycling']['threshold']:
            cycling_dist, cycling_dur, cycling_poly = self.amap_service.get_cycling_route(origin_str, dest_str)
            if cycling_dist > 0:
                options.append({
                    'mode': Config.TRANSPORT_MODES['cycling'],
                    'mode_key': 'cycling',
                    'distance': cycling_dist,
                    'duration': cycling_dur,
                    'distance_text': f"{cycling_dist / 1000:.1f}公里",
                    'duration_text': f"{cycling_dur // 60}分钟" if cycling_dur >= 60 else f"{cycling_dur}秒",
                    'polyline': cycling_poly,
                    'tips': []
                })

        # === 5. 为每个方案生成智能提示 ===
        for option in options:
            option['tips'] = self._generate_transport_tips(
                mode_key=option['mode_key'],
                weather_data=weather_data,
                current_time=current_time,
                distance=option['distance']
            )

        # === 6. 保存到activity ===
        activity['transportation_options'] = options
        activity['from_location'] = origin_name  # 保留起点信息（用于前端显示）

    def _select_transport_mode(self, distance: int) -> str:
        """根据距离选择交通方式（已弃用，保留向后兼容）"""
        if distance < Config.TRANSPORT_THRESHOLD['walking']:
            return Config.TRANSPORT_MODES['walking']
        elif distance < Config.TRANSPORT_THRESHOLD['transit']:
            return Config.TRANSPORT_MODES['transit']
        else:
            return Config.TRANSPORT_MODES['driving']

    def _generate_transport_tips(
        self,
        mode_key: str,
        weather_data: Optional[Dict],
        current_time: str,
        distance: int
    ) -> List[str]:
        """
        生成交通方式智能提示

        Args:
            mode_key: 'driving' | 'transit' | 'walking' | 'cycling'
            weather_data: 天气数据 {'forecasts': [...]}
            current_time: "HH:MM"
            distance: 距离（米）

        Returns:
            提示列表 ["今日有雨，建议携带雨具", ...]
        """
        tips = []

        # 1. 天气提示
        if weather_data and weather_data.get('forecasts'):
            today_weather = weather_data['forecasts'][0]
            casts = today_weather.get('casts', [{}])
            dayweather = casts[0].get('dayweather', '') if casts else ''

            # 检查是否有雨雪雾
            has_bad_weather = any(
                keyword in dayweather
                for keyword in Config.TRANSPORT_TIPS_CONFIG['rain_keywords']
            )

            if has_bad_weather:
                if mode_key == 'walking':
                    tips.append(f"今日{dayweather}，建议携带雨具")
                elif mode_key == 'cycling':
                    tips.append(f"今日{dayweather}，骑行路滑注意安全，建议选择其他方式")
                elif mode_key == 'transit':
                    tips.append(f"今日{dayweather}，公共交通较为舒适")
                elif mode_key == 'driving':
                    tips.append(f"今日{dayweather}，驾车请减速慢行")

        # 2. 高峰期提示（仅驾车和公交）
        try:
            hour = int(current_time.split(':')[0])
            is_rush_hour = any(
                start <= hour < end
                for start, end in Config.TRANSPORT_TIPS_CONFIG['rush_hours']
            )

            if is_rush_hour:
                if mode_key == 'driving':
                    tips.append("当前时段可能拥堵，建议预留充足时间或选择公共交通")
                elif mode_key == 'transit':
                    tips.append("高峰期公交可能较为拥挤")
        except Exception:
            pass

        # 3. 距离适宜性提示
        if mode_key == 'walking' and distance > 1500:
            tips.append(f"步行距离较远（{distance/1000:.1f}km），请根据体力选择")

        if mode_key == 'cycling' and distance > 4000:
            tips.append(f"骑行距离较远（{distance/1000:.1f}km），请注意安全")

        return tips

    def _get_route_by_mode(
        self,
        origin: str,
        destination: str,
        mode: str,
        city: str
    ) -> tuple[int, int, str]:
        """根据交通方式获取路线"""
        if mode == Config.TRANSPORT_MODES['walking']:
            return self.amap_service.get_walking_route(origin, destination)
        elif mode == Config.TRANSPORT_MODES['transit']:
            return self.amap_service.get_transit_route(origin, destination, city)
        else:  # driving
            return self.amap_service.get_driving_route(origin, destination)
