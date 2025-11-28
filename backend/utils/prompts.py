"""
AI提示词模板模块

管理所有与AI交互相关的提示词模板。
"""
from typing import List, Dict, Any


# 旅行风格Persona定义
STYLE_PERSONAS = {
    "photography": """
你是一位专业旅行摄影师。在规划行程时，请特别注意：
- 优先推荐摄影热门地点和最佳拍摄时间（例如：日出、日落、黄金时刻）
- 标注每个景点的最佳拍摄角度和机位
- 考虑光线条件：避免正午强光，选择早晚柔和光线
- 推荐适合拍照的咖啡厅、观景台等场所
- 提醒天气对摄影的影响（阴天、雨天的拍摄建议）
""",
    "foodie": """
你是一位美食评论家和旅行家。在规划行程时，请特别注意：
- 优先推荐当地特色美食和米其林/高评分餐厅
- 标注每家餐厅的招牌菜、人均消费、营业时间
- 合理安排用餐时间：避开用餐高峰期，预留品尝时间
- 推荐地道小吃、街边美食、夜市等体验
- 考虑食物的季节性和地域特色
- 为美食活动预留充足时间（至少1.5-2小时）
""",
    "adventure": """
你是一位户外探险爱好者。在规划行程时，请特别注意：
- 优先推荐徒步路线、登山、骑行、水上活动等户外体验
- 标注每个活动的难度等级、所需装备、体力要求
- 评估天气对户外活动的影响（雨天取消、高温调整）
- 预留充足的活动时间和休息时间
- 提醒安全注意事项和应急准备
- 推荐沿途补给点和休息区
""",
    "culture": """
你是一位文化历史学者。在规划行程时，请特别注意：
- 优先推荐博物馆、古迹、历史遗址、艺术展览
- 提供每个文化场所的历史背景和参观亮点
- 标注讲解服务、导览时间、特展信息
- 为深度参观预留充足时间（大型博物馆至少3-4小时）
- 推荐相关的文化体验活动（传统手工艺、文化讲座等）
- 考虑开放时间和周一闭馆等限制
""",
    "relaxation": """
你是一位休闲度假专家。在规划行程时，请特别注意：
- 优先推荐舒适悠闲的活动：温泉、SPA、公园漫步、茶馆
- 避免过度紧凑的行程，确保充足的休息时间
- 推荐景色优美、适合放松的场所
- 选择舒适度高的酒店和餐厅
- 每天安排不超过3-4个活动，留出自由活动时间
- 推荐适合冥想、瑜伽、阅读的安静场所
""",
    "family": """
你是一位亲子旅行专家。在规划行程时，请特别注意：
- 优先推荐适合全家的场所：动物园、水族馆、主题乐园、科技馆
- 考虑儿童的年龄和体力：避免过长步行，安排中午休息
- 推荐设施完善的场所（母婴室、无障碍设施）
- 选择亲子友好的餐厅和酒店
- 标注每个场所的儿童票价和适合年龄
- 预留应急时间（孩子需要休息、换尿布等）
- 避免危险性高或需要长时间安静的活动
"""
}


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
    custom_prompt: str,
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
        custom_prompt: 自定义需求
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

    # 格式化天气信息和天气建议
    weather_str = "暂无数据"
    weather_guidance = ""
    if weather_data and weather_data.get('forecasts'):
        forecasts = weather_data['forecasts'][0].get('casts', []) if weather_data['forecasts'] else []
        if forecasts:
            weather_lines = []
            has_rain = False
            for forecast in forecasts:
                day_weather = forecast.get('dayweather', '未知')
                line = f"- 日期: {forecast.get('date', '未知')}, 天气: {day_weather}/{forecast.get('nightweather', '未知')}, 温度: {forecast.get('nighttemp', '未知')}-{forecast.get('daytemp', '未知')}°C"
                weather_lines.append(line)
                if any(keyword in day_weather for keyword in ['雨', '雪', '冰雹']):
                    has_rain = True
            weather_str = '\n'.join(weather_lines)

            # 添加天气建议
            if has_rain:
                weather_guidance = """
**天气建议**：
- 预报有降雨天气，请优先安排室内活动（博物馆、美术馆、购物中心、室内游乐场等）
- 户外景点建议安排在天气较好的日子
- 雨天出行请携带雨具，注意路面湿滑
- 可以将雨天作为体验当地咖啡馆、茶馆、特色餐厅的好时机
"""

    # 获取旅行风格Persona
    persona_prompt = ""
    if travel_styles and len(travel_styles) > 0:
        primary_style = travel_styles[0]  # 使用第一个风格作为主要Persona
        if primary_style in STYLE_PERSONAS:
            persona_prompt = f"""
**旅行风格定位**：
{STYLE_PERSONAS[primary_style]}
"""

    # 处理自定义需求
    custom_requirements = ""
    if custom_prompt and custom_prompt.strip():
        custom_requirements = f"""
**用户自定义需求**：
{custom_prompt}

请务必在规划行程时充分考虑上述自定义需求，并在行程安排中体现。
"""

    prompt = f"""
{persona_prompt}
请为用户规划一个从{origin_city if origin_city else '出发地'}到{destination_city}的旅游行程。
出行日期: {start_date} 至 {end_date}
预算: {budget if budget_type == 'preset' else f'自定义 {custom_budget}'}
出行人数: {travelers}人
旅游风格: {', '.join(travel_styles) if travel_styles else '无特定偏好'}

{custom_requirements}

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

{weather_guidance}

**多出入口景点优化提示**：
对于大型景点（如故宫、颐和园、天坛等），系统会自动为您选择最优的出入口，以减少回头路和步行距离。
在描述活动时，如果您知道推荐的入口/出口（如"故宫午门"、"颐和园东宫门"），可以标注出来，但这不是强制要求。

请结合高德地图的数据和天气情况，提供详细的每日行程安排，包括：
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
