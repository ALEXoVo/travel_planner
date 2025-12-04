# TravelPlanner API 接口规范文档

本文档定义了后端API的接口规范，前端开发者应基于此文档进行开发。后端修改时应同步更新本文档。

**后端Base URL**: `http://localhost:8888`
**前端需配置**: 所有请求需添加 `credentials: 'include'` 以支持Cookie/Session

---

## 一、认证相关 API

### 1.1 用户注册
```
POST /api/auth/register
```

**请求体**:
```json
{
  "username": "string (必需, 3-50字符)",
  "password": "string (必需, 最少6字符)",
  "email": "string (可选)"
}
```

**成功响应** (201):
```json
{
  "message": "Registration successful",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**错误响应**:
- 400: `{ "error": "Username and password are required" }`
- 409: `{ "error": "Username already exists" }`

---

### 1.2 用户登录
```
POST /api/auth/login
```

**请求体**:
```json
{
  "username": "string (必需)",
  "password": "string (必需)"
}
```

**成功响应** (200):
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**错误响应**:
- 400: `{ "error": "Username and password are required" }`
- 401: `{ "error": "Invalid username or password" }`

---

### 1.3 用户登出
```
POST /api/auth/logout
```

**成功响应** (200):
```json
{
  "message": "Logout successful"
}
```

---

### 1.4 获取当前用户信息
```
GET /api/auth/me
```

**需要登录**: 是

**成功响应** (200):
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**错误响应**:
- 401: 未登录（由Flask-Login处理）

---

## 二、行程生成 API

### 2.1 生成行程计划
```
POST /api/itinerary/generate
```

**请求体**:
```json
{
  "destinationCity": "北京 (必需)",
  "originCity": "上海 (可选)",
  "startDate": "2024-12-07 (必需)",
  "endDate": "2024-12-09 (必需)",
  "budget": "3000-5000 | 5000 (必需)",
  "budgetType": "range | fixed (必需)",
  "customBudget": "string (可选, budgetType=custom时使用)",
  "travelers": 2,
  "travelStyles": ["culture", "food"],
  "customPrompt": "自定义偏好描述 (可选)",
  "replanMode": "full | incremental (可选, 重新规划时使用)",
  "previousItinerary": [...] (可选, 重新规划时传入现有行程),
  "userPOIs": [...] (可选, 用户选择的POI列表)
}
```

**成功响应** (200):
```json
{
  "itinerary": [
    {
      "day": 1,
      "date": "2024-12-07",
      "theme": "故宫文化之旅",
      "activities": [
        {
          "time": "09:00-12:00",
          "title": "故宫博物院",
          "description": "游览故宫...",
          "coordinates": { "lng": 116.397, "lat": 39.917 },
          "type": "attraction",
          "tips": "建议提前预约"
        }
      ],
      "transportation": [
        {
          "from": "酒店",
          "to": "故宫",
          "mode": "地铁",
          "duration": "30分钟",
          "polyline": "116.4,39.9;116.41,39.91;..."
        }
      ]
    }
  ],
  "summary": {
    "total_days": 3,
    "destination": "北京",
    "highlights": ["故宫", "长城", "颐和园"]
  },
  "itinerary_id": 123
}
```

---

### 2.2 AI聊天助手
```
POST /api/assistant/chat
```

**请求体**:
```json
{
  "message": "推荐一些北京的美食 (必需)",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "destination_city": "北京 (可选)",
  "travel_date": "2024-12-07 (可选)"
}
```

**成功响应** (200):
```json
{
  "response": "北京有很多美食推荐...",
  "timestamp": "2024-12-05T10:30:00"
}
```

---

### 2.3 获取行程历史列表
```
GET /api/itinerary/history?page=1&per_page=10&destination_city=北京
```

**需要登录**: 是

**Query参数**:
- `page`: 页码 (默认1)
- `per_page`: 每页数量 (默认10)
- `destination_city`: 按目的地筛选 (可选)

**成功响应** (200):
```json
{
  "items": [
    {
      "id": 123,
      "destination_city": "北京",
      "start_date": "2024-12-07",
      "end_date": "2024-12-09",
      "created_at": "2024-12-05T10:00:00"
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 10,
  "pages": 2
}
```

---

### 2.4 获取行程详情
```
GET /api/itinerary/history/<itinerary_id>
```

**需要登录**: 是

**成功响应** (200): 返回完整行程数据（同2.1的响应格式）

**错误响应**:
- 404: `{ "error": "Itinerary not found" }`

---

### 2.5 删除行程
```
DELETE /api/itinerary/history/<itinerary_id>
```

**需要登录**: 是

**成功响应** (200):
```json
{
  "message": "Itinerary deleted successfully"
}
```

---

## 三、POI管理 API

### 3.1 POI搜索自动补全
```
GET /api/poi/autocomplete?keywords=故宫&city=北京&limit=10
```

**Query参数**:
- `keywords` 或 `query`: 搜索关键词 (必需)
- `city`: 城市名 (必需)
- `limit`: 返回数量 (默认10)

**成功响应** (200):
```json
{
  "suggestions": [
    {
      "id": "B000A7BD6C",
      "name": "故宫博物院",
      "address": "北京市东城区景山前街4号",
      "type": "风景名胜;风景名胜相关",
      "location": "116.397026,39.918058"
    }
  ],
  "count": 10
}
```

---

### 3.2 添加POI到用户列表
```
POST /api/user-pois/add
```

**请求体**:
```json
{
  "poi": {
    "id": "B000A7BD6C (必需)",
    "name": "故宫博物院 (必需)",
    "location": "116.397026,39.918058 (必需)",
    "type": "风景名胜 (可选)"
  },
  "city": "北京 (必需)",
  "source": "user | ai (可选, 默认user)",
  "priority": "must_visit | optional (可选, 默认must_visit)",
  "itinerary_id": 123 (可选, 关联到行程)
}
```

**成功响应** (200):
```json
{
  "message": "POI added successfully",
  "total_count": 5
}
```

**错误响应**:
- 400: `{ "error": "poi and city are required" }`
- 409: `{ "error": "POI already in the list" }`

---

### 3.3 获取用户POI列表
```
GET /api/user-pois/list?city=北京
```

**Query参数**:
- `city`: 按城市筛选 (可选)

**成功响应** (200):
```json
{
  "destination_city": "北京",
  "pois": [
    {
      "poi_id": "B000A7BD6C",
      "poi_name": "故宫博物院",
      "id": "B000A7BD6C",
      "name": "故宫博物院",
      "city": "北京",
      "lng": 116.397026,
      "lat": 39.918058,
      "type": "风景名胜",
      "priority": "must_visit",
      "source": "user",
      "added_at": "2024-12-05T10:00:00"
    }
  ],
  "count": 5
}
```

**字段说明**:
- `poi_id` / `id`: POI唯一标识（两个字段值相同，兼容新旧前端）
- `poi_name` / `name`: POI名称（两个字段值相同，兼容新旧前端）

---

### 3.4 删除单个POI
```
DELETE /api/user-pois/remove/<poi_id>
```

**成功响应** (200):
```json
{
  "message": "POI removed successfully",
  "remaining_count": 4
}
```

**错误响应**:
- 404: `{ "error": "POI not found" }`

---

### 3.5 更新POI优先级
```
POST /api/user-pois/update-priority
```

**请求体**:
```json
{
  "poi_id": "B000A7BD6C (必需)",
  "priority": "must_visit | optional (必需)"
}
```

**成功响应** (200):
```json
{
  "message": "Priority updated successfully",
  "poi_id": "B000A7BD6C",
  "priority": "optional"
}
```

---

### 3.6 清空所有POI
```
DELETE /api/user-pois/clear?city=北京
```

**Query参数**:
- `city`: 已登录用户必需

**成功响应** (200):
```json
{
  "message": "All POIs cleared successfully",
  "deleted_count": 5
}
```

---

## 四、自定义活动 API

### 4.1 添加自定义活动
```
POST /api/activities/add
```

**请求体**:
```json
{
  "itinerary_id": 123 (必需),
  "day_index": 1 (必需, 从1开始),
  "activity_text": "去三里屯喝咖啡 (必需)",
  "time_slot": "15:00-16:00 (可选)"
}
```

**成功响应** (200):
```json
{
  "message": "Activity added successfully",
  "activity": {
    "id": "act_123",
    "itinerary_id": 123,
    "day_index": 1,
    "activity_text": "去三里屯喝咖啡",
    "time_slot": "15:00-16:00"
  }
}
```

---

### 4.2 获取活动列表
```
GET /api/activities/list?itinerary_id=123
```

**Query参数**:
- `itinerary_id`: 行程ID (必需)

**成功响应** (200):
```json
{
  "activities": [...],
  "count": 3
}
```

---

### 4.3 删除活动
```
DELETE /api/activities/remove/<activity_id>?itinerary_id=123
```

**Query参数**:
- `itinerary_id`: Session用户需要传此参数

**成功响应** (200):
```json
{
  "message": "Activity removed successfully",
  "remaining_count": 2
}
```

---

## 五、前端localStorage规范

由于Session Cookie跨域问题，前端应同时使用localStorage存储POI数据。

### 存储结构
```javascript
// Key: 'user_selected_pois'
{
  "destination_city": "北京",
  "pois": [
    {
      "id": "B000A7BD6C",
      "name": "故宫博物院",
      "location": "116.397026,39.918058",
      "type": "风景名胜",
      "city": "北京",
      "added_at": "2024-12-05T10:00:00.000Z",
      "priority": "must_visit",
      "source": "user"
    }
  ]
}
```

### 同步规则
1. **添加POI时**: 同时调用API和保存localStorage
2. **读取POI时**: 优先从localStorage读取，无数据时fallback到API
3. **删除POI时**: 同时从API和localStorage删除
4. **切换城市时**: 清空localStorage中的POI列表

---

## 六、后端修改注意事项

当后端API发生以下变更时，必须同步更新本文档并通知前端：

1. **新增/删除API端点**
2. **修改请求参数**（字段名、类型、必需性）
3. **修改响应格式**（字段名、结构）
4. **修改错误码或错误信息**
5. **修改认证要求**

### 版本记录

| 日期 | 版本 | 变更说明 |
|-----|------|---------|
| 2024-12-05 | 1.0 | 初始版本 |

---

## 七、后端未使用但已实现的API

以下API后端已实现但前端尚未调用，可按需集成：

| API | 功能 | 前端可用场景 |
|-----|------|-------------|
| `POST /api/poi/optimize` | OR-Tools路线优化 | POI列表优化排序 |
| `POST /api/itinerary/generate-from-user-pois` | 仅基于用户POI生成行程 | 高级用户自定义行程 |
| `POST /api/route/planning` | 高德路线规划 | 自定义起终点导航 |
| `GET /api/weather/info` | 获取天气信息 | 显示目的地天气 |
