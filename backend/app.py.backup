from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import logging
from datetime import datetime, timedelta
import json
import re
from openai import OpenAI
import httpx
from json import JSONDecodeError


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})  # 允许跨域请求

# 高德API配置
AMAP_API_KEY = os.environ.get('AMAP_API_KEY', '195725c002640ec2e5a80b4775dd2189')
if AMAP_API_KEY == '':
    logger.warning("AMAP_API_KEY not set. Please set the AMAP_API_KEY environment variable for full functionality.")

# DeepSeek API配置
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-d5826bdc14774b718b056a376bf894e0')
if DEEPSEEK_API_KEY == '' or DEEPSEEK_API_KEY == 'sk-d5826bdc14774b718b056a376bf894e0':
    logger.warning("DEEPSEEK_API_KEY not set or using default key. AI features will be disabled.")

def fix_incomplete_json(json_str):
    """
    修复不完整的JSON字符串。
    1. 修复缺失的逗号。
    2. 尝试闭合未闭合的字符串（添加引号）。
    3. 尝试平衡所有括号。
    4. 如果仍失败，尝试智能截断不完整的最后一行/字段。
    """
    # 移除可能的代码块标记
    json_str = json_str.replace('```json', '').replace('```', '').strip()
    
    # 核心修复循环
    while True:
        original_json_str = json_str
        
        # 1. 修复缺失的逗号 (在 }{、][、}[、]{ 之间)
        json_str = re.sub(r'(\})\s*(\{)', r'\1,\2', json_str)
        json_str = re.sub(r'(\])\s*(\[)', r'\1,\2', json_str)
        json_str = re.sub(r'(\})\s*(\[)', r'\1,\2', json_str)
        json_str = re.sub(r'(\])\s*(\{)', r'\1,\2', json_str)

        # 2. 移除末尾多余的逗号
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str.strip())
        
        # 3. 尝试闭合未闭合的字符串 (引号修复)
        quote_count = json_str.count('"')
        if quote_count % 2 != 0 and json_str.endswith('"') is False:
            # 如果引号数量是奇数且字符串末尾没有引号，尝试在末尾添加引号
            json_str += '"'
            
        # 4. 补充缺失的括号
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        temp_json_str = json_str
        temp_json_str += '}' * max(0, open_braces - close_braces)
        temp_json_str += ']' * max(0, open_brackets - close_brackets)

        # 5. 尝试解析
        try:
            json.loads(temp_json_str)
            return temp_json_str # 成功，返回
        except json.JSONDecodeError as e:
            # 6. 智能截断：找到最后一个有效分隔符，截断其后的内容。
            last_comma_pos = json_str.rfind(',')
            last_valid_pos = max(json_str.rfind('}'), json_str.rfind(']'))
            
            if last_comma_pos != -1 and (last_comma_pos > last_valid_pos or last_valid_pos == -1):
                # 如果找到逗号，且它在最后一个闭合符之后（或没有闭合符），截断到逗号之前。
                json_str = json_str[:last_comma_pos]
            elif last_valid_pos != -1:
                # 否则，如果有一个闭合符，截断到该闭合符之后，以清除后续的垃圾字符。
                json_str = json_str[:last_valid_pos + 1]
            else:
                # 没有任何有效分隔符，无法修复
                break

            # 7. 检查修复是否产生了变化
            if json_str == original_json_str:
                break
            
            # 修复导致字符串变化，继续循环
            continue
            
        except Exception:
            # 捕获其他异常，防止无限循环
            break
            
    return original_json_str


@app.route('/')
def home():
    return jsonify({"message": "Travel Planner Backend API"})

def _get_estimated_distance_and_duration(origin: str, destination: str) -> tuple[int, int]:
    """
    使用距离测量API获取粗略距离（用于模式选择）和时间。
    返回: (distance_meters, duration_seconds)
    """
    try:
        distance_params = {'key': AMAP_API_KEY, 'origins': origin, 'destination': destination, 'type': '1'}
        distance_response = requests.get("https://restapi.amap.com/v3/distance", params=distance_params, timeout=10)
        distance_data = distance_response.json()
        if distance_data.get('status') == '1' and distance_data.get('results'):
            return int(distance_data['results'][0].get('distance', 0)), int(distance_data['results'][0].get('duration', 0))
        return 0, 0
    except Exception as e:
        logger.error(f"Error calculating estimated distance: {str(e)}")
        return 0, 0


def _get_route_data(origin: str, destination: str, mode: str, city: str) -> tuple[int, int, str, str]: # <<< 修正 1: 更新返回类型
    """
    调用精确路径规划API并提取距离、时间、和 Polyline。
    逻辑对应于 maps_direction_*_by_coordinates 系列工具。
    返回: (distance_meters, duration_seconds, final_mode_name, polyline_string) # <<< 修正 2: 更新文档
    """
    route_url = ""
    route_params = {'key': AMAP_API_KEY, 'origin': origin, 'destination': destination}
    
    # <<< 修正 3: 确保所有变量在所有路径中都已初始化，避免 'unbound local error' >>>
    distance = 0
    duration = 0
    polyline = ""
    
    # 1. 选择 URL 和参数
    if mode == "步行":
        route_url = "https://restapi.amap.com/v3/direction/walking"
    elif mode == "公交/地铁":
        # maps_direction_transit_integrated_by_coordinates(origin, destination, city, cityd)
        route_url = "https://restapi.amap.com/v3/direction/transit/integrated"
        route_params['city'] = city
        route_params['extensions'] = 'base'
    elif mode == "驾车/打车":
        # maps_direction_driving_by_coordinates(origin, destination)
        route_url = "https://restapi.amap.com/v3/direction/driving"
    else:
        # 如果模式不支持，返回初始化的默认值
        return distance, duration, mode, polyline # <<< 修正 4: 确保返回 4 个值

    try:
        route_response = requests.get(route_url, params=route_params, timeout=10)
        route_result = route_response.json()
        
        if route_result.get('status') == '1' and route_result.get('route'):
            route_data = route_result['route']
            # distance 和 duration 已在上方初始化，此处将在路径内重新赋值
            
            all_polylines = []
            
            # --- 模式 1: 驾车/步行 (Path-based) ---
            if route_data.get('paths'):
                path = route_data['paths'][0]
                distance = int(path.get('distance', 0))
                duration = int(path.get('duration', 0))

                # 提取 Polyline
                steps = path.get('steps', [])
                all_polylines = [step.get('polyline') for step in steps if step.get('polyline')]
                
            # --- 2: 公交/地铁 (Transits-based) ---
            elif mode == "公交/地铁" and route_data.get('transits'):
                # 提取第一条最优路线的 Polyline
                transit = route_data['transits'][0]
                segments = transit.get('segments', [])
                
                for segment in segments:
                    # 提取步行 Polyline
                    walk_steps = segment.get('walking', {}).get('steps', [])
                    walk_polylines = [step.get('polyline') for step in walk_steps if step.get('polyline')]
                    all_polylines.extend(walk_polylines)
                    
                    # 提取公交/地铁 Polyline
                    if segment.get('bus'):
                        bus_steps = segment['bus'].get('buslines', [])
                        if bus_steps:
                            # 公交/地铁路线本身也是 Polyline
                            bus_line_polyline = bus_steps[0].get('polyline')
                            if bus_line_polyline:
                                all_polylines.append(bus_line_polyline)

                distance = int(transit.get('distance', 0))
                duration = int(transit.get('duration', 0))

            # 将所有 Polyline 片段合并成一个以分号分隔的字符串，供前端解码
            polyline = ";".join(all_polylines)
            
            # 返回结果增加 Polyline
            return distance, duration, mode, polyline
        else:
             logger.warning(f"路径规划 API 失败: {mode} ({route_result.get('infocode', 'N/A')})")
             # API 调用成功但无路线结果，返回初始化的默认值
             return distance, duration, mode, polyline # <<< 修正 5: 确保返回 4 个值
    except Exception as e:
        logger.error(f"调用 {mode} 路径规划 API 失败: {str(e)}")
        # API 调用失败，返回初始化的默认值
        return distance, duration, mode, polyline # <<< 修正 6: 确保返回 4 个值
    
def _get_poi_coordinates(name: str, address: str, city: str, amap_key: str):
    """
    尝试通过地理编码或 POI 搜索获取名称和地址的精确坐标。
    返回: (lng, lat) 或 (None, None)
    """
    # 优先使用地理编码，将名称和地址合并，提高准确率
    full_address = f"{name}, {address}" if address else name
    
    try:
        # 1. 标准地理编码
        geo_params = {
            'key': amap_key,
            'address': full_address,
            'city': city
        }
        geo_response = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params=geo_params,
            timeout=5
        )
        geo_data = geo_response.json()
        
        if geo_data.get('status') == '1' and geo_data.get('geocodes'):
            location_str = geo_data['geocodes'][0]['location']
            if location_str:
                lng, lat = map(float, location_str.split(','))
                return lng, lat
            
    except Exception as e:
        logger.warning(f"Geocode 失败 for {name}: {str(e)}")
        
    # 2. Fallback: POI 文本搜索 (使用名称)
    try:
        text_search_params = {
            "key": amap_key,
            "keywords": name,
            "city": city,
            "citylimit": "true",
            "offset": 1
        }
        text_search_response = requests.get(
            "https://restapi.amap.com/v3/place/text",
            params=text_search_params,
            timeout=5
        )
        text_search_data = text_search_response.json()
        
        if text_search_data.get('status') == '1' and text_search_data.get('pois'):
            poi_location_str = text_search_data['pois'][0].get('location')
            if poi_location_str:
                lng, lat = map(float, poi_location_str.split(','))
                return lng, lat
            
    except Exception as e:
        logger.warning(f"POI Search 失败 for {name}: {str(e)}")
    
    return None, None
    
def _add_coordinates_to_pois(poi_list: list, city: str, amap_key: str):
    """
    批量为 POI 列表中的每个 POI 添加 'lng' 和 'lat' 坐标字段。
    """
    for poi in poi_list:
        if 'location' in poi and poi['location']:
            try:
                # 如果 POI 数据自带 location (lng,lat 格式)
                lng, lat = map(float, poi['location'].split(','))
                poi['lng'] = lng
                poi['lat'] = lat
            except Exception:
                # 如果 location 格式不正确，尝试通过名称和地址获取
                name = poi.get('name', '')
                address = poi.get('address', '')
                lng, lat = _get_poi_coordinates(name, address, city, amap_key)
                poi['lng'] = lng
                poi['lat'] = lat
        else:
            # 如果没有 location 字段，尝试通过名称和地址获取
            name = poi.get('name', '')
            address = poi.get('address', '')
            lng, lat = _get_poi_coordinates(name, address, city, amap_key)
            poi['lng'] = lng
            poi['lat'] = lat

@app.route('/api/itinerary/generate', methods=['POST'])
def generate_itinerary():
    """
    生成旅游行程计划。
    集成了健壮的地址坐标获取逻辑，并在JSON解析失败时，记录原始AI响应。
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        destination_city = data.get('destinationCity')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        budget = data.get('budget')
        travelers = data.get('travelers')
        travel_styles = data.get('travelStyles', [])
        origin_city = data.get('originCity')
        budget_type = data.get('budgetType')
        custom_budget = data.get('customBudget')
        
        if not destination_city or not start_date or not end_date:
            return jsonify({"error": "Missing required parameters"}), 400
        
        # 获取目的地城市POI信息
        destination_pois = []
        food_pois = []
        hotel_pois = []
        cultural_pois = []
        shopping_pois = []
        parent_child_pois = []
        
        try:
            # 获取目的地POI信息
            destination_params = {
                'key': AMAP_API_KEY,
                'keywords': destination_city,
                'types': '风景名胜',
                'city': destination_city,
                'citylimit': 'true',
                'offset': 100,
                'page': 1,
                'extensions': 'all'
            }
            
            destination_response = requests.get(
                "https://restapi.amap.com/v3/place/text",
                params=destination_params,
                timeout=30
            )
            destination_response.raise_for_status()
            destination_data = destination_response.json()
            destination_pois = destination_data.get('pois', [])
            
            # 获取美食POI信息
            food_params = {
                'key': AMAP_API_KEY,
                'keywords': '美食',
                'types': '餐饮服务',
                'city': destination_city,
                'citylimit': 'true',
                'offset': 100,
                'page': 1,
                'extensions': 'all'
            }
            
            food_response = requests.get(
                "https://restapi.amap.com/v3/place/text",
                params=food_params,
                timeout=30
            )
            food_response.raise_for_status()
            food_data = food_response.json()
            food_pois = food_data.get('pois', [])
            
            # 获取酒店POI信息
            hotel_params = {
                'key': AMAP_API_KEY,
                'keywords': '酒店',
                'types': '住宿服务',
                'city': destination_city,
                'citylimit': 'true',
                'offset': 100,
                'page': 1,
                'extensions': 'all'
            }
            
            hotel_response = requests.get(
                "https://restapi.amap.com/v3/place/text",
                params=hotel_params,
                timeout=30
            )
            hotel_response.raise_for_status()
            hotel_data = hotel_response.json()
            hotel_pois = hotel_data.get('pois', [])
            
        except Exception as e:
            logger.error(f"Error fetching base POI data: {str(e)}")
        
        # 获取文化场所POI信息（博物馆、美术馆等）
        try:
            cultural_params = {
                'key': AMAP_API_KEY,
                'keywords': '博物馆|美术馆|文化中心|展览馆',
                'types': '科教文化服务',
                'city': destination_city,
                'citylimit': 'true',
                'offset': 100,
                'page': 1,
                'extensions': 'all'
            }
            
            cultural_response = requests.get(
                "https://restapi.amap.com/v3/place/text",
                params=cultural_params,
                timeout=30
            )
            cultural_response.raise_for_status()
            cultural_data = cultural_response.json()
            cultural_pois = cultural_data.get('pois', [])
            logger.info(f"Fetched {len(cultural_pois)} cultural POIs")
            
        except Exception as e:
            logger.error(f"Error fetching cultural POI data: {str(e)}")
            
            
        try:
            shopping_params = {
                'key': AMAP_API_KEY,
                'keywords': '购物中心|商场|百货',
                'types': '购物服务',
                'city': destination_city,
                'citylimit': 'true',
                'offset': 100,
                'page': 1,
                'extensions': 'all'
            }
            
            shopping_response = requests.get(
                "https://restapi.amap.com/v3/place/text",
                params=shopping_params,
                timeout=30
            )
            shopping_response.raise_for_status()
            shopping_data = shopping_response.json()
            shopping_pois = shopping_data.get('pois', [])
            logger.info(f"Fetched {len(shopping_pois)} shopping POIs")
        except Exception as e:
            logger.error(f"Error fetching shopping POI data: {str(e)}")

        # --- 新增：获取亲子场所POI信息 ---
        try:
            parent_child_params = {
                'key': AMAP_API_KEY,
                'keywords': '亲子乐园|儿童乐园|动物园|水族馆|科技馆',
                'types': '休闲娱乐服务|科教文化服务|生活服务',
                'city': destination_city,
                'citylimit': 'true',
                'offset': 100,
                'page': 1,
                'extensions': 'all'
            }
            
            parent_child_response = requests.get(
                "https://restapi.amap.com/v3/place/text",
                params=parent_child_params,
                timeout=30
            )
            parent_child_response.raise_for_status()
            parent_child_data = parent_child_response.json()
            parent_child_pois = parent_child_data.get('pois', [])
            logger.info(f"Fetched {len(parent_child_pois)} parent-child POIs")
        except Exception as e:
            logger.error(f"Error fetching parent-child POI data: {str(e)}")            

        # --- 新增逻辑: 批量获取 POI 坐标 ---
        all_pois = {
            'destination': destination_pois,
            'food': food_pois,
            'hotel': hotel_pois,
            'cultural': cultural_pois,
            'shopping': shopping_pois,
            'parent_child': parent_child_pois
        }
        
        for category, pois in all_pois.items():
            _add_coordinates_to_pois(pois, destination_city, AMAP_API_KEY)
            logger.info(f"Processed coordinates for {len(pois)} {category} POIs.")
        # --- 结束新增逻辑 ---
        
        # 获取天气信息
        weather_data = None
        try:
            weather_params = {
                'key': AMAP_API_KEY,
                'city': destination_city,
                'extensions': 'all',
                'output': 'json'
            }
            
            weather_response = requests.get(
                "https://restapi.amap.com/v3/weather/weatherInfo",
                params=weather_params,
                timeout=15
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
        
        # 计算天数以调整max_tokens
        from datetime import datetime
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        
        # 根据天数动态调整max_tokens，每天约需要800 tokens
        estimated_tokens = min(days * 800 + 500, 4000)
        
        # --- 修正后的 Prompt 合成 ---
        def poi_to_prompt_line(poi):
            lng_lat = f"({poi.get('lng', '无')},{poi.get('lat', '无')})"
            rating = poi.get('biz_ext', {}).get('rating', '无评分')
            cost = poi.get('biz_ext', {}).get('cost', '未知')
            
            base_info = f"- {poi.get('name', '未知地点')}: {poi.get('address', '地址未知')} 坐标:{lng_lat}, 评分: {rating}"
            
            if cost != '未知':
                return f"{base_info}, 价格/人均: {cost}元"
            return base_info

        prompt = f"""
        请为用户规划一个从{origin_city if origin_city else '出发地'}到{destination_city}的旅游行程。
        出行日期: {start_date} 至 {end_date}
        预算: {budget if budget_type == 'preset' else f'自定义 {custom_budget}'} 
        出行人数: {travelers}人
        旅游风格: {', '.join(travel_styles) if travel_styles else '无特定偏好'}
        
        以下是通过高德地图API获取的{destination_city}相关信息，请结合这些真实数据规划行程。
        请特别注意POI后的**坐标信息 (lng,lat)**，这是您进行合理路线规划的关键输入：
        
        推荐景点（附坐标）：
        {chr(10).join([poi_to_prompt_line(poi) for poi in destination_pois[:15]]) if destination_pois else "暂无数据"}
        
        推荐餐厅（附坐标）：
        {chr(10).join([poi_to_prompt_line(poi) for poi in food_pois[:15]]) if food_pois else "暂无数据"}
        
        推荐酒店（附坐标）：
        {chr(10).join([poi_to_prompt_line(poi) for poi in hotel_pois[:15]]) if hotel_pois else "暂无数据"}
        
        文化场所（博物馆、美术馆等, 附坐标）：
        {chr(10).join([poi_to_prompt_line(poi) for poi in cultural_pois[:10]]) if cultural_pois else "暂无数据"}
        
        购物场所（附坐标）：
        {chr(10).join([poi_to_prompt_line(poi) for poi in shopping_pois[:25]]) if shopping_pois else "暂无数据"}

        亲子/家庭场所（附坐标）：
        {chr(10).join([poi_to_prompt_line(poi) for poi in parent_child_pois[:25]]) if parent_child_pois else "暂无数据"}
        
        天气信息：
        {chr(10).join([f"- 日期: {forecast.get('date', '未知')}, 天气: {forecast.get('dayweather', '未知')}/{forecast.get('nightweather', '未知')}, 温度: {forecast.get('nighttemp', '未知')}-{forecast.get('daytemp', '未知')}°C" for forecast in weather_data.get('forecasts', [])[0].get('casts', [])]) if weather_data and weather_data.get('forecasts') and weather_data.get('forecasts')[0].get('casts') else "暂无数据"}
        ... (中间 POI 和天气信息省略) ...
        
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
        # --- 结束修正后的 Prompt 合成 ---

        deepseek_api_key = DEEPSEEK_API_KEY
        # 检查API密钥
        if not deepseek_api_key or deepseek_api_key == 'your_deepseek_api_key_here':
            logger.warning("DeepSeek API key not configured or using default key")
            return jsonify({"error": "无法生成行程计划，请稍后重试"}), 500
        
        # 初始化DeepSeek客户端
        client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        
        messages = [
            {"role": "system", "content": "你是一个专业的旅游规划助手，帮助用户制定最佳的旅游路线和行程安排。请以友好、专业的语气回答问题，并根据用户的兴趣、时间和预算提供建议。必须严格按照指定的JSON格式返回结果。**关键：必须确保返回完整的JSON结构，所有括号和引号都必须正确闭合。**"},
            {"role": "user", "content": prompt}
        ]
        
        # 设置AI调用的超时时间
        http_client = httpx.Client(timeout=60.0)
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False,
            temperature=0.7,
            max_tokens=estimated_tokens
        )
        
        ai_response = response.choices[0].message.content
        logger.info(f"AI response received, length: {len(ai_response)}")
        
        # 尝试提取JSON部分
        json_match = re.search(r'\{.*\}|\[.*\]', ai_response, re.DOTALL) 
        itinerary_data = None
        
        if json_match:
            json_str = json_match.group()
            
            # 尝试解析JSON
            try:
                itinerary_data = json.loads(json_str)
                logger.info("JSON parsing successful on first attempt")
            except JSONDecodeError as je:
                logger.error(f"JSON Decode Error (Attempt 1): {str(je)}")
                logger.error(f"Error at position: {je.pos}, line: {je.lineno}, column: {je.colno}")
                
                # 尝试修复
                try:
                    fixed_json = fix_incomplete_json(json_str)
                    itinerary_data = json.loads(fixed_json)
                    logger.info("JSON parsing successful after fix.")
                except Exception as fix_error:
                    logger.error(f"JSON Fix Failed: {str(fix_error)}")
                    # 记录详细信息用于调试
                    logger.error(f"JSON string length: {len(json_str)}")
                    logger.error(f"Last 500 chars: {json_str[-500:]}")
                    
                    # 如果修复失败，返回错误信息
                    return jsonify({
                        "error": "AI返回的JSON结构不完整，可能是因为行程天数较多导致响应被截断。建议缩短行程天数或稍后重试。",
                        "details": f"JSON解析错误位置: 第{je.lineno}行，第{je.colno}列"
                    }), 500
        else:
            logger.error("No valid JSON structure found in AI response")
            logger.error(f"Response length: {len(ai_response)}")
            logger.error(f"Response preview: {ai_response[:500]}...")
            
            return jsonify({"error": "无法生成行程计划，AI返回内容格式错误"}), 500

        # 后续处理逻辑（地理编码和交通计算）
        if itinerary_data and 'itinerary' in itinerary_data:
            logger.info(f"Processing itinerary with {len(itinerary_data['itinerary'])} days")
            
            default_lng, default_lat = 116.397428, 39.90923
            
            # 尝试获取出发地坐标
            origin_coords = None
            if origin_city:
                try:
                    geo_params = {'key': AMAP_API_KEY, 'address': origin_city, 'city': origin_city}
                    geo_response = requests.get("https://restapi.amap.com/v3/geocode/geo", params=geo_params, timeout=10)
                    if geo_response.status_code == 200 and geo_response.json().get('status') == '1' and geo_response.json().get('geocodes'):
                        location_str = geo_response.json()['geocodes'][0]['location']
                        origin_coords = tuple(map(float, location_str.split(',')))
                except Exception as e:
                    logger.warning(f"无法获取出发地 {origin_city} 坐标: {str(e)}")            
            
            # 处理天气信息
            for day in itinerary_data['itinerary']:
                if 'weather' not in day or day['weather'] is None:
                    if weather_data and weather_data.get('forecasts'):
                        forecasts = weather_data['forecasts'][0].get('casts', []) if weather_data['forecasts'] else []
                        if 'date' in day and forecasts:
                            day_index = 0
                            try:
                                day_index = (int(day['day']) - 1) % len(forecasts)
                            except:
                                pass
                            day['weather'] = forecasts[day_index] if day_index < len(forecasts) else forecasts[0]
                        else:
                            day['weather'] = forecasts[0] if forecasts else None
            
            # 处理活动地点坐标和交通方式建议
            for day_index, day in enumerate(itinerary_data['itinerary']):
                if 'activities' in day:
                    activities = day['activities']
                    current_day_number = day.get('day', day_index + 1)
                    
                    previous_activities = []
                    if day_index > 0:
                        previous_activities = itinerary_data['itinerary'][day_index - 1].get('activities', [])

                    for i, activity in enumerate(activities):
                        address = activity['location']['address']
                        title = activity.get('title', address)
                        
                        default_lng, default_lat = 116.397428, 39.90923
                        location_found = False
                        
                        # 如果 AI 已经提供了 lng/lat (因为 AI 已经有 POI 坐标作为输入)，则跳过重新编码
                        if activity['location'].get('lng') is not None and activity['location'].get('lat') is not None:
                            try:
                                # 尝试将字符串坐标转换为浮点数
                                activity['location']['lng'] = float(activity['location']['lng'])
                                activity['location']['lat'] = float(activity['location']['lat'])
                                location_found = True
                            except ValueError:
                                # 如果转换失败，重新获取坐标
                                logger.warning(f"AI提供的坐标格式错误，重新获取: {title}")
                                activity['location']['lng'] = None
                                activity['location']['lat'] = None


                        if not location_found and address and address != '详细地址':
                            # 1. 标准地理编码
                            try:
                                geo_params = {
                                    'key': AMAP_API_KEY,
                                    'address': address,
                                    'city': destination_city
                                }
                                geo_response = requests.get(
                                    "https://restapi.amap.com/v3/geocode/geo",
                                    params=geo_params,
                                    timeout=15
                                )
                                geo_response.raise_for_status()
                                geo_data = geo_response.json()
                                
                                if geo_data.get('status') == '1' and geo_data.get('geocodes'):
                                    location_str = geo_data['geocodes'][0]['location']
                                    lng, lat = map(float, location_str.split(','))
                                    activity['location']['lng'] = lng
                                    activity['location']['lat'] = lat
                                    location_found = True
                                    logger.info(f"成功获取坐标 (Geocode): {title} ({address}) -> {lng}, {lat}")
                                else:
                                    logger.warning(f"Geocode 失败 ({address}), 尝试 Fallback (POI Text Search)")
                            except Exception as e:
                                logger.error(f"Error getting Geocode for {address}: {str(e)}")
                        
                            # 2. Fallback: POI搜索
                            if not location_found and title:
                                try:
                                    # 由于在最开始已经对所有 POI 进行了坐标提取，如果 AI 使用了真实的 POI 名称，
                                    # 此时的 Fallback 搜索能很快命中。
                                    text_search_params = {
                                        "key": AMAP_API_KEY,
                                        "keywords": title,
                                        "city": destination_city,
                                        "citylimit": "true",
                                        "offset": 1
                                    }
                                    text_search_response = requests.get(
                                        "https://restapi.amap.com/v3/place/text",
                                        params=text_search_params,
                                        timeout=15
                                    )
                                    text_search_response.raise_for_status()
                                    text_search_data = text_search_response.json()
                                    
                                    if text_search_data.get('status') == '1' and text_search_data.get('pois'):
                                        poi_data = text_search_data['pois'][0]
                                        poi_location_str = poi_data.get('location')
                                        if poi_location_str:
                                            lng, lat = map(float, poi_location_str.split(','))
                                            activity['location']['lng'] = lng
                                            activity['location']['lat'] = lat
                                            location_found = True
                                            # 更新地址为更精确的 POI 地址
                                            activity['location']['address'] = poi_data.get('address', address) 
                                            logger.info(f"成功获取坐标 (POI Search): {title} -> {lng}, {lat}")
                                    
                                    if not location_found:
                                        logger.warning(f"POI Search 失败 ({title}), 无法获取坐标。")

                                except Exception as e:
                                    logger.error(f"Error getting POI Search for {title}: {str(e)}")

                        # 3. 使用默认值
                        if not location_found:
                            logger.warning(f"最终无法获取坐标，使用默认值 {default_lng}, {default_lat}: {title}")
                            activity['location']['lng'] = default_lng
                            activity['location']['lat'] = default_lat
                        
                        
                        # 4. 计算交通信息
                        origin_lng, origin_lat = None, None
                        origin_name = ""
                        is_arrival_trip = False

                        if i == 0:
                            # --- FIX: 当天第一个活动 (作为启点值，跳过交通计算) ---
                            
                            # 确定起点坐标 (不计算交通，但为了下一个活动作准备)
                            if day_index == 0 and origin_coords:
                                # Day 1, Activity 1: 使用行程起点
                                ...
                            elif day_index > 0 and previous_activities:
                                # Day N (N>1), Activity 1: 使用前一天最后一个活动
                                prev_activity = previous_activities[-1]
                                # 由于 Prompt 已要求 AI 将住宿作为前一天的最后一个活动，
                                # 这里的 prev_activity 就会是前一天的酒店，作为今天的起点。
                                if (prev_activity.get('location') and 
                                    prev_activity['location'].get('lng') is not None and
                                    prev_activity['location'].get('lat') is not None):
                                    origin_lng = prev_activity['location']['lng']
                                    origin_lat = prev_activity['location']['lat']
                                    origin_name = prev_activity.get('title')

                            # 关键：跳过本次活动的交通计算
                            activity['transportation'] = [] # 确保 transportation 字段为空列表
                            continue
                            # ----------------------------------------------------

                        # 当天非第一个活动 (i > 0)
                        else:
                            previous_activity = activities[i - 1]
                            if (previous_activity.get('location') and 
                                previous_activity['location'].get('lng') is not None and
                                previous_activity['location'].get('lat') is not None):
                                origin_lng = previous_activity['location']['lng']
                                origin_lat = previous_activity['location']['lat']
                                origin_name = previous_activity['title']

                        if origin_lng is not None and origin_lat is not None:
                            origin_coords_str = f"{origin_lng},{origin_lat}"
                            dest_coords_str = f"{activity['location']['lng']},{activity['location']['lat']}"
                        
                            distance = 0
                            duration_minutes = 0
                            transport_mode = "未知"
                            polyline = ""
                            estimated_distance, estimated_duration_s = _get_estimated_distance_and_duration(origin_coords_str, dest_coords_str)
                        
                            # 原本用于 Day 1, Activity 1的逻辑块，现在 i > 0，is_arrival_trip = False，故跳过
                            # if is_arrival_trip:
                            #    ...
                        
                            if estimated_distance > 0:
                                # 模式选择逻辑
                                if estimated_distance < 1000: 
                                    mode_for_routing = "步行"
                                elif estimated_distance < 5000: 
                                    mode_for_routing = "公交/地铁"
                                else:
                                    mode_for_routing = "驾车/打车"

                                # --- FIX: 修正 _get_route_data 的参数 ---
                                distance, duration_seconds, transport_mode, polyline = _get_route_data( 
                                    origin=origin_coords_str, # 使用已定义的起点坐标字符串
                                    destination=dest_coords_str, # 使用已定义的目的地坐标字符串
                                    mode=mode_for_routing, 
                                    city=destination_city
                                )
                                duration_minutes = duration_seconds // 60

                            if distance > 0:
                                if 'transportation' not in activity:
                                    activity['transportation'] = []
                                
                                activity['transportation'].append({
                                    "from_location": origin_name,
                                    "mode": transport_mode,
                                    "distance": f"{distance / 1000:.1f}公里",
                                    "duration": f"{duration_minutes}分钟",
                                    "polyline": polyline
                                })
                            elif not is_arrival_trip:
                                logger.warning(f"跳过交通信息添加: {origin_name} -> {activity.get('title')} 距离为0或规划失败。")

            logger.info("Itinerary generated successfully with robust geocoding and accurate transportation info.")
            return jsonify(itinerary_data)
    
        return jsonify({"error": "AI返回的行程数据结构不完整，请重试"}), 500
        
    except requests.exceptions.Timeout:
        logger.error("API request timeout")
        return jsonify({"error": "Request timeout"}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        return jsonify({"error": f"Request error: {str(e)}"}), 502
    except ValueError as e:
        logger.error(f"JSON decode error (request body or API response): {str(e)}")
        return jsonify({"error": "Invalid data format or API response"}), 502
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500




@app.route('/api/route/planning', methods=['POST'])
def route_planning():
    """
    路径规划
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        origin = data.get('origin')
        destination = data.get('destination')
        waypoints = data.get('waypoints', [])
        strategy = data.get('strategy', 0)  # 0: 最快速度, 1: 最短距离, etc.
        
        if not origin or not destination:
            return jsonify({"error": "Missing origin or destination"}), 400
        
        url = "https://restapi.amap.com/v3/direction/driving"
        params = {
            'key': AMAP_API_KEY,
            'origin': origin,
            'destination': destination,
            'waypoints': '|'.join(waypoints) if waypoints else '',
            'strategy': strategy
        }
        
        logger.info(f"Planning route from {origin} to {destination}")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        logger.info("Route planning successful")
        return jsonify(data)
    except requests.exceptions.Timeout:
        logger.error("AMAP API request timeout")
        return jsonify({"error": "Request timeout"}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"AMAP API request error: {str(e)}")
        return jsonify({"error": f"Request error: {str(e)}"}), 502
    except ValueError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({"error": "Invalid response from AMap API"}), 502
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/weather/info', methods=['GET'])
def weather_info():
    """
    获取天气信息
    """
    try:
        city = request.args.get('city')
        
        if not city:
            return jsonify({"error": "Missing city parameter"}), 400
        
        url = "https://restapi.amap.com/v3/weather/weatherInfo"
        params = {
            'key': AMAP_API_KEY,
            'city': city,
            'extensions': 'all',
            'output': 'json'
        }
        
        logger.info(f"Fetching weather info for city: {city}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info("Weather info fetched successfully")
        return jsonify(data)
    except requests.exceptions.Timeout:
        logger.error("AMAP API request timeout")
        return jsonify({"error": "Request timeout"}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"AMAP API request error: {str(e)}")
        return jsonify({"error": f"Request error: {str(e)}"}), 502
    except ValueError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return jsonify({"error": "Invalid response from AMap API"}), 502
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/assistant/chat', methods=['POST'])
def ai_assistant_chat():
    """
    AI助手对话接口
    """
    try:
        data = request.get_json(force=True)
        message = data.get('message')
        conversation_history = data.get('history', [])
        destination_city = data.get('destination_city', '')
        travel_date = data.get('travel_date', '')
        
        # 获取DeepSeek API密钥
        deepseek_api_key = DEEPSEEK_API_KEY

        # 构建消息历史
        messages = [
            {"role": "system", "content": "你是一个专业的旅游规划助手，帮助用户制定最佳的旅游路线和行程安排。请以友好、专业的语气回答问题，并根据用户的兴趣、时间和预算提供建议。"}
        ]
        
        # 添加历史对话（如果有）
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": message})
        
        # 如果有目的地和日期信息，获取天气信息
        weather_info = None
        if destination_city and travel_date:
            try:
                weather_params = {
                    'key': AMAP_API_KEY,
                    'city': destination_city,
                    'extensions': 'all',
                    'output': 'json'
                }
                
                weather_response = requests.get(
                    "https://restapi.amap.com/v3/weather/weatherInfo",
                    params=weather_params,
                    timeout=10
                )
                weather_response.raise_for_status()
                weather_data = weather_response.json()
                
                # 提取天气信息
                if 'forecasts' in weather_data and weather_data['forecasts']:
                    forecasts = weather_data['forecasts']
                    for forecast in forecasts:
                        if forecast.get('date') == travel_date or travel_date in forecast.get('date', ''):
                            weather_info = forecast
                            break
                    
                    # 如果没有找到特定日期的天气，使用第一天的天气
                    if not weather_info and forecasts:
                        weather_info = forecasts[0]
                        
            except Exception as e:
                logger.error(f"Failed to get weather info: {str(e)}")
        
        # 如果获取到天气信息，添加到系统提示中
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
            messages[0]["content"] += "\n\n" + weather_prompt

        # 检查API密钥
        if not deepseek_api_key or deepseek_api_key == 'your_deepseek_api_key_here':
            return jsonify({
                "response": "抱歉，AI助手当前不可用，因为未配置API密钥。请在后端设置DEEPSEEK_API_KEY环境变量。"
            })
        
        # 初始化DeepSeek客户端
        from openai import OpenAI
        client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        
        # 发送请求到DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False,
            temperature=0.7,
            max_tokens=10000
        )
        
        # 提取回复内容
        ai_response = response.choices[0].message.content
        
        return jsonify({
            "response": ai_response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        logger.error(f"AI assistant error: {str(e)}")
        return jsonify({
            "response": "抱歉，AI助手当前不可用。请稍后再试。"
        }), 500


def get_location_info(poi):
    """
    获取POI的位置信息
    
    >>> 注意: 此函数在 generate_itinerary 中已被 _get_poi_coordinates 逻辑取代，
    >>> 并且在 generate_itinerary 后处理逻辑中，为了获取更准确的地址，
    >>> 使用了标准的 Geocode/POI Search + Detail 流程。
    >>> 此处保留原函数结构，但其功能已被优化后的逻辑覆盖。
    """
    location = None
    if poi and 'location' in poi:
        try:
            lng, lat = poi['location'].split(',')
            # 使用高德API获取精确地址信息
            regeo_params = {
                'key': AMAP_API_KEY,
                'location': f"{lng},{lat}"
            }
            
            regeo_response = requests.get(
                "https://restapi.amap.com/v3/geocode/regeo",
                params=regeo_params,
                timeout=10
            )
            regeo_response.raise_for_status()
            regeo_data = regeo_response.json()
            
            if regeo_data.get("status") == "1":
                address_component = regeo_data["regeocode"]["addressComponent"]
                address = f"{address_component.get('province', '')}{address_component.get('city', '')}{address_component.get('district', '')}"
                location = {
                    "address": address,
                    "lng": float(lng),
                    "lat": float(lat)
                }
            else:
                location = {
                    "address": poi.get('address', ''),
                    "lng": float(lng),
                    "lat": float(lat)
                }
        except Exception as e:
            logger.error(f"Error getting regeo for {poi.get('location', '')}: {str(e)}")
            if 'location' in poi:
                lng, lat = poi['location'].split(',')
                location = {
                    "address": poi.get('address', ''),
                    "lng": float(lng),
                    "lat": float(lat)
                }
    return location


def generate_simple_sample_itinerary(destination_city, start_date, end_date, weather_data=None):
    """
    生成简单的示例行程序作为备选方案
    """
    try:
        # 解析日期
        from datetime import datetime, timedelta
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        
        itinerary = []
        
        # 获取天气预报（如果有的话）
        forecasts = []
        if weather_data and weather_data.get('forecasts'):
            forecasts = weather_data['forecasts'][0].get('casts', []) if weather_data['forecasts'] else []
        
        for i in range(days):
            current_date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            
            # 获取当天的天气信息
            day_weather = None
            if forecasts:
                # 循环使用天气预报数据，确保每一天都有天气信息
                forecast_index = i % len(forecasts)
                day_weather = forecasts[forecast_index]
            
            day_plan = {
                "day": i + 1,
                "date": current_date,
                "weather": day_weather,
                "activities": []
            }
            
            # 根据天数生成活动
            if i == 0:  # 第一天
                activities = [
                    {
                        "time": "09:00",
                        "title": f"抵达{destination_city}",
                        "description": "抵达目的地，办理入住手续",
                        "duration": "2小时",
                        "location": {
                            "address": f"{destination_city}市中心",
                            "lng": 116.397428,
                            "lat": 39.90923
                        }
                    },
                    {
                        "time": "12:00",
                        "title": "午餐",
                        "description": "在当地特色餐厅享用午餐",
                        "duration": "1.5小时",
                        "location": {
                            "address": f"{destination_city}某餐厅",
                            "lng": 116.398,
                            "lat": 39.910
                        }
                    },
                    {
                        "time": "14:30",
                        "title": f"{destination_city}市区游览",
                        "description": "参观市区主要景点",
                        "duration": "3小时",
                        "location": {
                            "address": f"{destination_city}著名景点",
                            "lng": 116.399,
                            "lat": 39.911
                        }
                    },
                    {
                        "time": "19:00",
                        "title": "晚餐",
                        "description": "品尝当地特色美食",
                        "duration": "2小时",
                        "location": {
                            "address": f"{destination_city}特色餐厅",
                            "lng": 116.400,
                            "lat": 39.912
                        }
                    }
                ]
            elif i == days - 1:  # 最后一天
                activities = [
                    {
                        "time": "09:00",
                        "title": "早餐",
                        "description": "在酒店享用早餐",
                        "duration": "1小时",
                        "location": {
                            "address": f"{destination_city}某酒店",
                            "lng": 116.397,
                            "lat": 39.908
                        }
                    },
                    {
                        "time": "10:30",
                        "title": "购物和休闲",
                        "description": "购买纪念品，休闲放松",
                        "duration": "2小时",
                        "location": {
                            "address": f"{destination_city}购物中心",
                            "lng": 116.398,
                            "lat": 39.909
                        }
                    },
                    {
                        "time": "14:00",
                        "title": "午餐",
                        "description": "享用午餐",
                        "duration": "1.5小时",
                        "location": {
                            "address": f"{destination_city}某餐厅",
                            "lng": 116.399,
                            "lat": 39.910
                        }
                    },
                    {
                        "time": "16:00",
                        "title": "前往机场/车站",
                        "description": "准备返程",
                        "duration": "2小时",
                        "location": {
                            "address": f"{destination_city}机场/车站",
                            "lng": 116.400,
                            "lat": 39.911
                        }
                    }
                ]
            else:  # 中间天数
                activities = [
                    {
                        "time": "08:00",
                        "title": "早餐",
                        "description": "在酒店享用早餐",
                        "duration": "1小时",
                        "location": {
                            "address": f"{destination_city}某酒店",
                            "lng": 116.397,
                            "lat": 39.908
                        }
                    },
                    {
                        "time": "09:30",
                        "title": f"{destination_city}著名景点游览",
                        "description": "参观主要景点",
                        "duration": "3小时",
                        "location": {
                            "address": f"{destination_city}著名景点",
                            "lng": 116.398,
                            "lat": 39.909
                        }
                    },
                    {
                        "time": "13:00",
                        "title": "午餐",
                        "description": "在当地特色餐厅用餐",
                        "duration": "1.5小时",
                        "location": {
                            "address": f"{destination_city}某餐厅",
                            "lng": 116.399,
                            "lat": 39.910
                        }
                    },
                    {
                        "time": "15:00",
                        "title": "文化体验活动",
                        "description": "参观博物馆或体验当地文化",
                        "duration": "2小时",
                        "location": {
                            "address": f"{destination_city}博物馆",
                            "lng": 116.400,
                            "lat": 39.911
                        }
                    },
                    {
                        "time": "18:00",
                        "title": "晚餐",
                        "description": "享用晚餐并欣赏夜景",
                        "duration": "2小时",
                        "location": {
                            "address": f"{destination_city}特色餐厅",
                            "lng": 116.401,
                            "lat": 39.912
                        }
                    }
                ]
            
            day_plan["activities"] = activities
            itinerary.append(day_plan)
        
        return itinerary
    except Exception as e:
        logger.error(f"Error generating simple sample itinerary: {str(e)}")
        # 返回一个基本的示例行程序
        return [
            {
                "day": 1,
                "date": start_date,
                "weather": forecasts[0] if forecasts and len(forecasts) > 0 else None,
                "activities": [
                    {
                        "time": "09:00",
                        "title": f"抵达{destination_city}",
                        "description": "开始愉快的旅程",
                        "duration": "2小时",
                        "location": {
                            "address": f"{destination_city}市中心",
                            "lng": 116.397428,
                            "lat": 39.90923
                        }
                    }
                ]
            }
        ]

# 全局错误处理
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    logger.error(f"Endpoint not found: {str(error)}")
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    logger.error(f"Method not allowed: {str(error)}")
    return jsonify({"error": "Method not allowed for the requested URL"}), 405

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)