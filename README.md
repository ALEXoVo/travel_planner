# TravelWorld - 智能旅游行程规划助手

这是一个基于高德API和DeepSeek AI的旅游行程规划平台，具有AI对话生成路线框架、目的地管理、活动编辑、自动路线规划等功能。

![Figma Design](https://www.figma.com/design/LMzgGp8KiNLGMAjhLonAln/TravelWorld---Travel-Planning---Booking-Website--Community-?node-id=0-1)

## 功能特性

1. AI对话生成路线框架（浮窗）
2. 用户可添加目的地（使用高德搜索API、坐标转换API、地图API等）
3. 用户可编辑活动及预计停留时间
4. 基于高德路径规划API，结合用户需求自动规划路线
5. 调用高德天气和交通API，实时提供新路线供用户选择
6. 根据用户偏好（目的地城市、旅游时间、预算、人数、旅游风格）生成个性化行程

## 技术架构

- 前端：HTML + CSS + JavaScript + 高德地图JavaScript API
- 后端：Python Flask + 高德Web服务API + DeepSeek AI API

## 快速开始

### 前端设置

1. 获取高德地图API Key:
   - 访问 https://console.amap.com/
   - 创建应用并获取API Key

2. 替换API Key:
   - 打开 `frontend/index.html`
   - 将 `YOUR_AMAP_API_KEY` 替换为你的实际API Key

3. 在浏览器中打开 `frontend/index.html` 即可使用

### 后端设置

1. 安装依赖:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. 设置环境变量:
   ```bash
   export AMAP_API_KEY=your_amap_api_key_here
   export DEEPSEEK_API_KEY=your_deepseek_api_key_here
   ```

3. 运行服务器:
   ```bash
   python app.py
   ```

   服务器将在 `http://localhost:5000` 上运行

## API 接口

### 生成行程计划
```
POST /api/itinerary/generate
{
  "destinationCity": "北京",
  "startDate": "2023-10-01",
  "endDate": "2023-10-03",
  "budget": "medium",
  "travelers": 2,
  "travelStyles": ["culture", "food"]
}
```

### 搜索地点
```
GET /api/search/place?keyword=地点名称&city=城市名
```

### 地理编码（地址转坐标）
```
GET /api/geo/geocode?address=详细地址
```

### 路径规划
```
POST /api/route/planning
{
  "origin": "起点坐标",
  "destination": "终点坐标",
  "waypoints": ["途经点坐标1", "途经点坐标2"],
  "strategy": 0
}
```

### 天气信息
```
GET /api/weather/info?city=城市名
```

### AI助手对话 (使用DeepSeek API)
```
POST /api/assistant/chat
{
  "message": "用户问题",
  "history": [
    {"role": "user", "content": "之前的用户消息"},
    {"role": "assistant", "content": "之前的AI回复"}
  ]
}
```

## 设计参考

本项目UI设计参考了[Figma上的TravelWorld设计](https://www.figma.com/design/LMzgGp8KiNLGMAjhLonAln/TravelWorld---Travel-Planning---Booking-Website--Community-?node-id=0-1)

## AI集成

本项目集成了DeepSeek AI API，用于提供更智能的旅游规划建议：

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.choices[0].message.content)
```

## 开发计划

- [x] 集成真实的AI大模型API（已完成DeepSeek集成）
- [x] 实现基础的行程生成功能
- [ ] 实现完整的路线优化算法
- [ ] 添加用户认证系统
- [ ] 支持离线地图功能
- [ ] 移动端适配优化
- [ ] 社区分享功能