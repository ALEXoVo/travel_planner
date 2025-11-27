# Travel Planner 项目功能与技术实现指南

## 1. 项目概述

Travel Planner 是一个智能旅行规划平台，旨在通过结合**大语言模型 (LLM) 的创意能力**与**地图算法的精确计算能力**，为用户提供可落地的个性化行程。核心差异化在于解决“大景点多出入口导致的回头路”痛点，以及根据“行程临近度”动态调整规划策略。

---

## 2. 核心功能架构

### 2.1 智能行程规划 (Path Planning + Recommendation)

* **功能描述**：
  * 用户输入必去地点（锚点）。
  * 系统调用 LLM 补充推荐周边的餐厅、隐藏打卡点（基于用户偏好）。
  * 算法对所有地点进行路径规划（TSP 变种），生成最优访问顺序。
  * LLM 基于规划结果生成最终的时间安排和导游式文案。
* **技术策略**：**“三明治”架构**
  * **上层 (LLM)**：意图识别 & POI 推荐（输出 JSON）。
  * **中层 (算法)**：地理编码、多出入口计算、路径排序。
  * **下层 (LLM)**：润色最终方案。

### 2.2 动态精细化路由 (Dynamic & Realistic Routing)

* **功能描述**：
  * **时间敏感性**：
    * *远期规划*：主要基于距离权重。
    * *近期规划*：调用天气和未来路况 API，若有雨则降权步行/骑行，若拥堵则推荐地铁。
  * **拒绝“回头路” (Smart Entry/Exit)**：
    * 不将景点视为单一坐标点。
    * 动态获取景点的“门”或“出入口”坐标。
    * 根据前后景点的方位向量，计算“最优进、最优出”组合（如：西门进、南门出）。
  * **多方案推荐**：提供“耗时最少”、“换乘最少”、“距离最短”三种方案。

### 2.3 风格定制 (Style Customization)

* **功能描述**：
  * 支持预设风格：“出片摄影”、“美食体验”、“运动探险”、“文化氛围”或用户自定义输入，选填。
  * 支持游玩天数（必填）预算（必填，提供范围选项）输入
  * 支持自定义 Prompt 输入（选填，如“带父母，少走路”）。
* **技术策略**：
  * **System Prompt 模板化**：根据选择加载不同的 Persona（参考 `tripper` 的 Agent 设计）。
  * **POI 搜索增强**：选择“美食”时，在路径规划间隙主动搜索高分餐厅。

### 2.4 交互式 Chatbox (Chat-to-Action)

* **功能描述**：
  * 侧边展开栏，支持自然语言聊天。
  * **操作锚点**：AI 回复中的地点可一键“添加到行程”，触发主地图更新。

---

## 3. 关键技术实现与参考代码

### 3.1 无库化动态 POI 获取 (No-Database POI Resolution)

**核心逻辑**：不维护本地数据库，利用高德 API 实时获取主地点及其子节点（门）。

* **参考代码 (`amap-mcp-server`)**：
  * `sugarforever/amap-mcp-server/.../server.py`:
    * `maps_text_search(keywords, city)`: 获取地点主坐标。
    * `maps_around_search(location, keywords="门|出入口")`: **关键**，用于获取某个地点周边的所有门。
    * `maps_search_detail(id)`: 获取地点详细类型（判断是否为大景区）。

### 3.2 向量化出入口选择算法 (Vector-based Gate Selection)

**核心逻辑**：实现 `optimize_gates_for_sequence` 函数。
假设路径 $A \rightarrow B \rightarrow C$：

1. 获取 $B$ 的所有门 $\{g_1, g_2, ...\}$。
2. 计算 $A \rightarrow g_i$ 的距离，取最小值确定 $Entry_B$。
3. 计算 $g_j \rightarrow C$ 的距离，取最小值确定 $Exit_B$。
4. 校验 $Entry_B \neq Exit_B$（针对大景区强制穿越），否则允许原路返回。

* **参考代码**：
  * **工具支持**：`amap-mcp-server/.../server.py` 中的 `maps_distance(origins, destination)` 用于计算距离矩阵。
  * **算法思想**：`graphhopper` 中的 `VirtualEdgeIterator` 概念（将 POI 吸附到路网上），此处变为“将 POI 吸附到具体的门坐标上”。

### 3.3 动态权重计算 (Dynamic Weighting)

**核心逻辑**：在 `route_optimizer.py` 中引入 `Cost` 函数。

$$
Cost = Distance \times w_1 + Duration \times w_2 + WeatherPenalty
$$

* **参考代码**：
  * **数据源**：
    * `maps_weather(city)`: 获取天气，用于设定 $WeatherPenalty$。
    * `maps_direction_driving_by_coordinates`: 获取含路况的 $Duration$。
  * **算法参考 (`graphhopper`)**：
    * 参考 `graphhopper/.../weighting/SpeedWeighting.java`: 学习如何根据不同路况/最大速度计算边的权重。
    * 参考 `graphhopper/.../weighting/custom/CustomWeighting.java`: 学习如何注入自定义参数（如天气系数）。

### 3.4 风格化 Prompt 工程

**核心逻辑**：将 Python 后端的数据组装成 Prompt 上下文。

* **参考代码 (`tripper`)**：
  * `embabel/tripper/.../TripperAgent.kt`: 学习其如何定义 `Personas`（角色）和 `Style`。
  * `embabel/tripper/.../agent/domain.kt`: 查看其如何结构化定义旅行偏好（Preferences）。
  * **应用位置**： `backend/services/ai_service.py`。

---

## 4. 后端开发路线图 (Action Plan)

1. **API 集成层 (`backend/services/amap_service.py`)**：

   * [ ] 移植 `amap_mcp_server/server.py` 中的核心函数 (`maps_text_search`, `maps_weather`, `maps_distance` 等) 到您的项目中。
   * [ ] 新增 `get_poi_gates(poi_name)` 函数，封装“搜主点 -> 搜周边门”的逻辑。
2. **核心算法层 (`backend/services/route_optimizer.py`)**：

   * [ ] 实现 `calculate_optimized_route(poi_list, date_proximity)`。
   * [ ] 实现三种最优路径规划的逻辑
3. **业务逻辑层 (`backend/services/itinerary_builder.py`)**：

   * [ ] 整合算法输出。
   * [ ] 构建 Prompt，将 `{"poi": "故宫", "entry": "午门", "exit": "神武门"}` 这样的结构化数据喂给 LLM，让其生成“从午门检票进入...”的准确文案。
4. **数据结构修正**：

   * 修改前端传来的 JSON 结构，支持 `style`、`budget`、`people_count` 字段，以便后端进行风格定制。
