"""
AI提示词模板模块

管理所有与AI交互相关的提示词模板。
"""
from typing import List, Dict, Any


def poi_to_prompt_line(poi: Dict[str, Any]) -> str:
    """
    将POI信息格式化为提示词中的一行。

    Args:
        poi: POI信息字典

    Returns:
        str: 格式化后的POI描述行

    Examples:
        >>> poi = {'name': '天安门', 'address': '东城区', 'lng': 116.39, 'lat': 39.90}
        >>> poi_to_prompt_line(poi)
        '- 天安门: 东城区 坐标:(116.39,39.90), 评分: 无评分'
    """
    lng_lat = f"({poi.get('lng', '无')},{poi.get('lat', '无')})"
    rating = poi.get('biz_ext', {}).get('rating', '无评分')
    cost = poi.get('biz_ext', {}).get('cost', '未知')

    base_info = f"- {poi.get('name', '未知地点')}: {poi.get('address', '地址未知')} 坐标:{lng_lat}, 评分: {rating}"

    if cost != '未知':
        return f"{base_info}, 价格/人均: {cost}元"
    return base_info


def build_itinerary_generation_prompt(
    destination_city: str,
    origin_city: str,
    start_date: str,
    end_date: str,
    budget: str,
    budget_type: str,
    custom_budget: str,
    travelers: int,
    travel_styles: List[str],
    destination_pois: List[Dict],
    food_pois: List[Dict],
    hotel_pois: List[Dict],
    cultural_pois: List[Dict],
    shopping_pois: List[Dict],
    parent_child_pois: List[Dict],
    weather_data: Dict[str, Any],
    days: int
) -> str:
    """
    构建行程生成的AI提示词。

    Args:
        destination_city: 目的地城市
        origin_city: 出发城市
        start_date: 开始日期
        end_date: 结束日期
        budget: 预算
        budget_type: 预算类型（preset/custom）
        custom_budget: 自定义预算
        travelers: 出行人数
        travel_styles: 旅游风格列表
        destination_pois: 景点POI列表
        food_pois: 美食POI列表
        hotel_pois: 酒店POI列表
        cultural_pois: 文化场所POI列表
        shopping_pois: 购物场所POI列表
        parent_child_pois: 亲子场所POI列表
        weather_data: 天气数据
        days: 行程天数

    Returns:
        str: 完整的提示词
    """
    # 格式化POI列表
    destination_pois_str = '\n'.join([poi_to_prompt_line(poi) for poi in destination_pois[:15]]) if destination_pois else "暂无数据"
    food_pois_str = '\n'.join([poi_to_prompt_line(poi) for poi in food_pois[:15]]) if food_pois else "暂无数据"
    hotel_pois_str = '\n'.join([poi_to_prompt_line(poi) for poi in hotel_pois[:15]]) if hotel_pois else "暂无数据"
    cultural_pois_str = '\n'.join([poi_to_prompt_line(poi) for poi in cultural_pois[:10]]) if cultural_pois else "暂无数据"
    shopping_pois_str = '\n'.join([poi_to_prompt_line(poi) for poi in shopping_pois[:25]]) if shopping_pois else "暂无数据"
    parent_child_pois_str = '\n'.join([poi_to_prompt_line(poi) for poi in parent_child_pois[:25]]) if parent_child_pois else "暂无数据"

    # 格式化天气信息
    weather_str = "暂无数据"
    if weather_data and weather_data.get('forecasts'):
        forecasts = weather_data['forecasts'][0].get('casts', []) if weather_data['forecasts'] else []
        if forecasts:
            weather_lines = []
            for forecast in forecasts:
                line = f"- 日期: {forecast.get('date', '未知')}, 天气: {forecast.get('dayweather', '未知')}/{forecast.get('nightweather', '未知')}, 温度: {forecast.get('nighttemp', '未知')}-{forecast.get('daytemp', '未知')}°C"
                weather_lines.append(line)
            weather_str = '\n'.join(weather_lines)

    prompt = f"""
请为用户规划一个从{origin_city if origin_city else '出发地'}到{destination_city}的旅游行程。
出行日期: {start_date} 至 {end_date}
预算: {budget if budget_type == 'preset' else f'自定义 {custom_budget}'}
出行人数: {travelers}人
旅游风格: {', '.join(travel_styles) if travel_styles else '无特定偏好'}

以下是通过高德地图API获取的{destination_city}相关信息，请结合这些真实数据规划行程。
请特别注意POI后的**坐标信息 (lng,lat)**，这是您进行合理路线规划的关键输入：

推荐景点（附坐标）：
{destination_pois_str}

推荐餐厅（附坐标）：
{food_pois_str}

推荐酒店（附坐标）：
{hotel_pois_str}

文化场所（博物馆、美术馆等, 附坐标）：
{cultural_pois_str}

购物场所（附坐标）：
{shopping_pois_str}

亲子/家庭场所（附坐标）：
{parent_child_pois_str}

天气信息：
{weather_str}

请结合高德地图的数据，提供详细的每日行程安排，包括：
1. 每天的具体活动安排（时间、地点、活动内容、预计停留时间）
2. 推荐的交通方式和路线规划
3. **必须根据预算和行程，从提供的酒店列表中动态推荐住宿地点，
并将其作为当天行程的最后一个活动（例如：20:00 办理入住/休息）。同时酒店的选择综合考虑行程和预算，并且尽量不要更换酒店。**
4. 当地特色美食推荐
5. 景点门票信息和开放时间
6. 根据天气情况提供出行建议

对于每个活动地点，请提供准确的地址信息，以便后续获取精确的地理坐标。
每天至少安排3-5个景点，合理安排时间，确保行程充实但不紧张。
为每个景点或活动提供预计停留时间（例如：2小时、半天等）。
活动时间应该合理安排，考虑交通时间和地点间的距离。
行程应充分考虑用户的偏好、预算和时间安排，提供实用且个性化的建议。

**重要**：由于响应长度限制，请确保完整输出所有{days}天的行程。如果内容较长，请精简描述但保持JSON结构完整。

请严格按照以下JSON格式返回结果，注意：地点名称要使用上面提供的真实地点名称，并且每一天都必须包含天气信息，**必须确保JSON结构完整，所有括号和引号都正确闭合**：
{{
    "itinerary": [
        {{
            "day": 1,
            "date": "{start_date}",
            "weather": {{
                "date": "...",
                "dayweather": "...",
                "nightweather": "...",
                "daytemp": "...",
                "nighttemp": "..."
            }},
            "activities": [
                {{
                    "time": "09:00",
                    "title": "活动标题（必须使用上面提供的真实地点名称）",
                    "description": "活动详细描述",
                    "duration": "预计停留时间（如2小时、半天等）",
                    "location": {{
                        "address": "详细地址",
                        "lng": "经度",
                        "lat": "纬度"
                    }}
                }},
                // ... 其他活动
                {{
                    "time": "20:00",
                    "title": "酒店入住/休息（使用推荐酒店名称）",
                    "description": "办理入住手续，享受酒店设施",
                    "duration": "过夜",
                    "location": {{
                        "address": "推荐酒店的地址",
                        "lng": "经度",
                        "lat": "纬度"
                    }}
                }}
            ]
        }}
    ]
}}
"""
    return prompt


def build_chat_system_prompt(weather_info: Dict[str, Any] = None) -> str:
    """
    构建AI聊天助手的系统提示词。

    Args:
        weather_info: 可选的天气信息

    Returns:
        str: 系统提示词
    """
    base_prompt = "你是一个专业的旅游规划助手，帮助用户制定最佳的旅游路线和行程安排。请以友好、专业的语气回答问题，并根据用户的兴趣、时间和预算提供建议。"

    if weather_info:
        weather_prompt = f"""

目的地天气信息（{weather_info.get('date', '未知日期')}）:
- 白天天气: {weather_info.get('dayweather', '未知')}
- 夜间天气: {weather_info.get('nightweather', '未知')}
- 最高温度: {weather_info.get('daytemp', '未知')}°C
- 最低温度: {weather_info.get('nighttemp', '未知')}°C
- 风向: {weather_info.get('daywind', '未知')}
- 风力: {weather_info.get('daypower', '未知')}

请根据天气情况为用户提供出行建议。
"""
        return base_prompt + weather_prompt

    return base_prompt
