// 初始化默认地图
function initDefaultMap() {
    const mapContainer = document.getElementById('day1-map');
    if (mapContainer && typeof AMap !== 'undefined') {
        // 清空容器内容
        mapContainer.innerHTML = '';
        
        // 创建地图实例
        const map = new AMap.Map('day1-map', {
            zoom: 10,
            center: [116.397428, 39.90923] // 默认北京中心坐标
        });
        
        // 添加一个默认标记
        new AMap.Marker({
            position: [116.397428, 39.90923],
            title: '默认位置',
            map: map
        });
    }
}

// 存储用户偏好和行程
let userPreferences = {
    originCity: '',
    destinationCity: '',
    startDate: '',
    endDate: '',
    budget: '',
    budgetType: 'preset',
    customBudget: '',
    travelers: 1,
    groupType: [],
    travelStyles: []
};

let itinerary = [];
let chatHistory = [];

// DOM 元素
let toggleChatBtn;
let chatPanel;
let chatInput;
let sendChatBtn;
let chatHistoryEl;
let newJourneyBtn;
let historyJourneyBtn;
let welcomeScreen;
let settingsScreen;
let itineraryScreen;
let backToWelcomeBtn;
let backToSettingsBtn;
let aiGenerateBtn;
let originCityInput;
let destinationCityInput;
let startDateInput;
let endDateInput;
let budgetTypeSelect;
let presetBudgetDiv;
let customBudgetDiv;
let budgetSelect;
let customBudgetInput;
let travelersSelect;
let groupTypeButtons;
let styleButtons;
// 消息模态框元素
let messageModal;
let messageTitle;
let messageContent;
let closeModalBtn;
let confirmModalBtn;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化DOM元素引用
    initializeDOMElements();
    
    // 绑定事件监听器
    bindEventListeners();
    
    // 初始化默认地图
    initDefaultMap();
});

// 初始化所有可折叠部分
function initializeCollapsibleSections() {
    const collapsibleHeaders = document.querySelectorAll('.collapsible');
    collapsibleHeaders.forEach(header => {
        // 避免重复添加事件监听器
        if (!header.classList.contains('initialized')) {
            header.classList.add('initialized');
            header.addEventListener('click', () => {
                const section = header.parentElement;
                section.classList.toggle('expanded');
                
                const icon = header.querySelector('i');
                if (section.classList.contains('expanded')) {
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                } else {
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            });
        }
    });
}

// 初始化DOM元素引用
function initializeDOMElements() {
    // 聊天面板元素
    toggleChatBtn = document.getElementById('toggle-chat');
    chatPanel = document.querySelector('.chat-panel');
    chatInput = document.getElementById('chat-input');
    sendChatBtn = document.getElementById('send-chat-btn');
    chatHistoryEl = document.getElementById('chat-history');

    // 主要界面元素
    newJourneyBtn = document.getElementById('new-journey-btn');
    historyJourneyBtn = document.getElementById('history-journey-btn');
    welcomeScreen = document.getElementById('welcome-screen');
    settingsScreen = document.getElementById('settings-screen');
    itineraryScreen = document.getElementById('itinerary-screen');
    backToWelcomeBtn = document.getElementById('back-to-welcome');
    backToSettingsBtn = document.getElementById('back-to-settings');
    aiGenerateBtn = document.getElementById('ai-generate-itinerary');

    // 表单元素
    originCityInput = document.getElementById('origin-city');
    destinationCityInput = document.getElementById('destination-city');
    startDateInput = document.getElementById('start-date');
    endDateInput = document.getElementById('end-date');
    budgetTypeSelect = document.getElementById('budget-type');
    presetBudgetDiv = document.getElementById('preset-budget');
    customBudgetDiv = document.getElementById('custom-budget');
    budgetSelect = document.getElementById('budget');
    customBudgetInput = document.getElementById('custom-budget-amount');
    travelersSelect = document.getElementById('travelers');
    groupTypeButtons = document.querySelectorAll('#group-type .style-btn');
    styleButtons = document.querySelectorAll('#travel-style .style-btn');

    // 消息模态框元素
    messageModal = document.getElementById('message-modal');
    messageTitle = document.getElementById('message-title');
    messageContent = document.getElementById('message-content');
    closeModalBtn = document.getElementById('close-modal');
    confirmModalBtn = document.getElementById('confirm-modal');

    console.log('DOM Elements initialized:', {
        newJourneyBtn,
        historyJourneyBtn,
        aiGenerateBtn,
        originCityInput,
        destinationCityInput
    });
}

function planAllRoutes() {
    console.log('开始规划所有路线...');
    showMessage('正在规划', '正在为您规划所有活动间的路线...');
    
    // 遍历存储的行程数据
    // 这里的 itinerary 变量必须在 generateItineraryWithAI 中正确设置
    if (itinerary && Array.isArray(itinerary)) { 
        itinerary.forEach((day) => {
            // initDayMap 函数内部会调用 drawRouteOnMap 来绘制路线
            // 确保 initDayMap 能够正确地从 day.activities 中获取到地点坐标和交通信息
            initDayMap(day.day, day.activities); 
        });
        
        messageModal.style.display = 'none';
        showMessage('规划完成', '所有路线已成功在地图上显示！');
        
    } else {
        messageModal.style.display = 'none';
        showMessage('错误', '没有找到行程数据，请先生成行程。');
    }
}


// 绑定事件监听器
function bindEventListeners() {
    console.log('Binding event listeners...');
    
    // 聊天面板折叠功能
    if (toggleChatBtn) {
        toggleChatBtn.addEventListener('click', () => {
            chatPanel.classList.toggle('collapsed');
        });
    }

    // 事件监听器
    if (newJourneyBtn) {
        newJourneyBtn.addEventListener('click', () => {
            console.log('New journey button clicked');
            welcomeScreen.style.display = 'none';
            settingsScreen.style.display = 'block';
        });
    }

    if (historyJourneyBtn) {
        historyJourneyBtn.addEventListener('click', () => {
            showMessage('功能待实现', '历史旅程功能还在开发中，敬请期待！');
        });
    }

    if (backToWelcomeBtn) {
        backToWelcomeBtn.addEventListener('click', () => {
            settingsScreen.style.display = 'none';
            welcomeScreen.style.display = 'flex';
        });
    }

    if (backToSettingsBtn) {
        backToSettingsBtn.addEventListener('click', () => {
            itineraryScreen.style.display = 'none';
            settingsScreen.style.display = 'block';
        });
    }

    if (aiGenerateBtn) {
        aiGenerateBtn.addEventListener('click', () => {
            console.log('AI Generate button clicked');
            generateItineraryWithAI();
        });
    }

    // 路线规划按钮
    const planAllRoutesBtn = document.getElementById('plan-all-routes-btn');
    if (planAllRoutesBtn) {
        planAllRoutesBtn.addEventListener('click', () => {
            planAllRoutes();
        });
    }

    // 消息模态框事件监听器
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => {
            messageModal.style.display = 'none';
        });
    }

    if (confirmModalBtn) {
        confirmModalBtn.addEventListener('click', () => {
            messageModal.style.display = 'none';
        });
    }

    // 点击模态框外部关闭
    window.addEventListener('click', (e) => {
        if (e.target === messageModal) {
            messageModal.style.display = 'none';
        }
    });

    // 预算类型切换
    if (budgetTypeSelect) {
        budgetTypeSelect.addEventListener('change', () => {
            userPreferences.budgetType = budgetTypeSelect.value;
            
            if (userPreferences.budgetType === 'preset') {
                presetBudgetDiv.style.display = 'block';
                customBudgetDiv.style.display = 'none';
            } else {
                presetBudgetDiv.style.display = 'none';
                customBudgetDiv.style.display = 'block';
            }
        });
    }

    // 人群类型按钮点击事件
    if (groupTypeButtons && groupTypeButtons.length > 0) {
        groupTypeButtons.forEach(button => {
            button.addEventListener('click', () => {
                // 清除其他按钮的选中状态（单选）
                groupTypeButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                userPreferences.groupType = [button.dataset.type];
            });
        });
    }

    // 旅游风格按钮点击事件
    if (styleButtons && styleButtons.length > 0) {
        styleButtons.forEach(button => {
            button.addEventListener('click', () => {
                button.classList.toggle('active');
                updateSelectedStyles();
            });
        });
    }

    // 聊天功能
    if (sendChatBtn) {
        sendChatBtn.addEventListener('click', sendChatMessage);
    }
    
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }

    // 日期变化监听
    if (startDateInput) {
        startDateInput.addEventListener('change', () => {
            userPreferences.startDate = startDateInput.value;
        });
    }

    // 出发城市变化监听
    if (originCityInput) {
        originCityInput.addEventListener('change', () => {
            userPreferences.originCity = originCityInput.value;
        });
    }

    // 目的地城市变化监听
    if (destinationCityInput) {
        destinationCityInput.addEventListener('change', () => {
            userPreferences.destinationCity = destinationCityInput.value;
        });
    }

    // 预算变化监听
    if (budgetSelect) {
        budgetSelect.addEventListener('change', () => {
            userPreferences.budget = budgetSelect.value;
        });
    }

    // 自定义预算变化监听
    if (customBudgetInput) {
        customBudgetInput.addEventListener('change', () => {
            userPreferences.customBudget = customBudgetInput.value;
        });
    }

    // 出行人数变化监听
    if (travelersSelect) {
        travelersSelect.addEventListener('change', () => {
            userPreferences.travelers = travelersSelect.value;
        });
    }
    
    console.log('Event listeners bound successfully');
}

// 更新选中的旅游风格
function updateSelectedStyles() {
    const activeButtons = document.querySelectorAll('#travel-style .style-btn.active');
    userPreferences.travelStyles = Array.from(activeButtons).map(btn => btn.dataset.style);
}

// 显示自定义消息模态框
function showMessage(title, content) {
    messageTitle.textContent = title;
    messageContent.textContent = content;
    messageModal.style.display = 'flex';
}

// 生成行程计划
async function generateItineraryWithAI() {
    console.log('Generating itinerary with AI...');
    
    // 收集用户偏好
    userPreferences.originCity = originCityInput.value.trim();
    userPreferences.destinationCity = destinationCityInput.value.trim();
    userPreferences.startDate = startDateInput.value;
    userPreferences.endDate = endDateInput.value;
    userPreferences.budget = budgetSelect.value;
    userPreferences.budgetType = budgetTypeSelect.value;
    userPreferences.customBudget = customBudgetInput.value;
    userPreferences.travelers = travelersSelect.value;
    
    console.log('User preferences:', userPreferences);
    
    // 验证必填字段
    if (!userPreferences.originCity) {
        showMessage('输入错误', '请输入出发城市');
        return;
    }
    
    if (!userPreferences.destinationCity) {
        showMessage('输入错误', '请输入目的地城市');
        return;
    }
    
    if (!userPreferences.startDate || !userPreferences.endDate) {
        showMessage('输入错误', '请选择出行日期');
        return;
    }
    
    if (userPreferences.budgetType === 'custom' && !userPreferences.customBudget) {
        showMessage('输入错误', '请输入自定义预算金额');
        return;
    }
    
    try {
        // 构建发送给AI的prompt
        const prompt = buildAIPrompt(userPreferences);
        
        // 显示正在生成提示
        showMessage('正在生成', '正在为您生成个性化行程，请稍候...');
        
        // 使用AbortController设置请求超时
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5分钟超时
        
        console.log('Sending request to backend...');
        const response = await fetch('http://localhost:8888/api/itinerary/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                originCity: userPreferences.originCity,
                destinationCity: userPreferences.destinationCity,
                startDate: userPreferences.startDate,
                endDate: userPreferences.endDate,
                budgetType: userPreferences.budgetType,
                budget: userPreferences.budget,
                customBudget: userPreferences.customBudget,
                travelers: userPreferences.travelers,
                travelStyles: userPreferences.travelStyles
            }),
            signal: controller.signal
        });
        
        console.log('Received response from backend:', response);
        
        // 清除超时定时器
        clearTimeout(timeoutId);
        
        // 关闭消息模态框
        messageModal.style.display = 'none';
        
        // 检查响应状态
        if (!response.ok) {
            let errorMessage = `HTTP错误 ${response.status}: ${response.statusText}`;
            
            // 尝试获取详细的错误信息
            try {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } else {
                    const errorText = await response.text();
                    if (errorText) {
                        errorMessage = errorText;
                    }
                }
            } catch (parseError) {
                // 如果解析错误信息也失败，使用默认消息
                console.error('Error parsing error response:', parseError);
            }
            
            throw new Error(errorMessage);
        }
        
        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // 如果不是JSON响应，可能是服务器错误
            const errorText = await response.text();
            throw new Error(`服务器返回了非JSON响应 (状态码: ${response.status})`);
        }
        
        const data = await response.json();
        console.log('Received itinerary data:', data);
        
        // === 关键修复：将返回的行程数据存储到全局变量中 ===
        itinerary = data.itinerary; 
        // ===============================================
        
        // 显示行程编辑界面
        settingsScreen.style.display = 'none';
        itineraryScreen.style.display = 'block';
        
        // 更新行程编辑界面中的信息
        document.getElementById('edit-origin-city').value = userPreferences.originCity;
        document.getElementById('edit-destination-city').value = userPreferences.destinationCity;
        document.getElementById('edit-start-date').value = userPreferences.startDate;
        document.getElementById('edit-end-date').value = userPreferences.endDate;
        document.getElementById('edit-travelers').value = userPreferences.travelers;
        
        // 生成每日行程session
        generateDailySessions(data.itinerary);
        
        // 重新初始化折叠功能
        setTimeout(initializeCollapsibleSections, 100);
        
    } catch (error) {
        console.error('Error generating itinerary:', error);
        messageModal.style.display = 'none';
        
        if (error.name === 'AbortError') {
            showMessage('请求超时', '生成行程请求超时，请检查网络连接或稍后重试');
        } else {
            showMessage('生成失败', `生成行程时出错: ${error.message}`);
        }
    }
}

// 构建发送给AI的prompt
function buildAIPrompt(preferences) {
    let budgetInfo = '';
    if (preferences.budgetType === 'preset') {
        const budgetLabels = {
            'low': '经济型(100-300元/天)',
            'medium': '舒适型(300-800元/天)', 
            'high': '豪华型(800元以上/天)'
        };
        budgetInfo = budgetLabels[preferences.budget] || '未指定';
    } else {
        budgetInfo = `自定义预算: ${preferences.customBudget}元`;
    }
    
    const groupTypeLabels = {
        'family': '家庭出游',
        'couple': '情侣度假',
        'friends': '朋友聚会',
        'solo': '独自旅行',
        'business': '商务出行'
    };
    
    const styleLabels = {
        'scenery': '自然风光',
        'culture': '文化历史',
        'food': '美食体验',
        'shopping': '购物娱乐',
        'adventure': '探险户外',
        'relax': '休闲度假'
    };
    
    const travelStyles = preferences.travelStyles.map(style => styleLabels[style] || style).join(', ');
    const groupType = preferences.groupType.map(type => groupTypeLabels[type] || type).join(', ');
    
    return `请为我规划一个旅游行程:
    出发城市: ${preferences.originCity}
    目的地城市: ${preferences.destinationCity}
    出行日期: ${preferences.startDate} 至 ${preferences.endDate}
    预算: ${budgetInfo}
    出行人数: ${preferences.travelers}人
    人群类型: ${groupType}
    旅游风格: ${travelStyles || '无特定偏好'}
    
    请结合高德地图API提供的信息，为我规划详细的每日行程，包括:
    1. 交通信息（航班/火车等）
    2. 酒店信息
    3. 每日活动安排
    4. 景点推荐
    5. 餐厅推荐
    6. 预计停留时间
    `;
}

// 生成每日行程session
function generateDailySessions(itineraryData) {
    console.log('Generating daily sessions with data:', itineraryData);
    
    // 查找已存在的每日行程section（除了前几个固定section）
    const itinerarySections = document.querySelectorAll('.itinerary-section');
    // 从索引2开始删除（跳过交通、酒店section）
    for (let i = itinerarySections.length - 1; i >= 2; i--) {
        itinerarySections[i].remove();
    }
    
    // 生成新的每日行程section
    const itineraryContainer = document.getElementById('itinerary-screen');
    
    // 根据后端返回的数据生成行程
    if (itineraryData && Array.isArray(itineraryData)) {
        itineraryData.forEach((day, index) => {
            const daySection = document.createElement('div');
            daySection.className = 'itinerary-section';
            
            // 日期格式化
            const dateObj = new Date(day.date);
            const formattedDate = dateObj.toLocaleDateString('zh-CN', {
                month: 'long',
                day: 'numeric'
            });
            
            // 构建天气信息HTML（如果存在）
            let weatherHtml = '';
            if (day.weather) {
                weatherHtml = `
                    <div class="weather-info">
                        <h4><i class="fas fa-cloud-sun"></i> 天气信息</h4>
                        <div class="weather-details">
                            <div class="weather-item">
                                <span class="weather-label">天气状况:</span>
                                <span class="weather-value">${day.weather.dayweather || '未知'} / ${day.weather.nightweather || '未知'}</span>
                            </div>
                            <div class="weather-item">
                                <span class="weather-label">温度范围:</span>
                                <span class="weather-value">${day.weather.nighttemp || '未知'}°C - ${day.weather.daytemp || '未知'}°C</span>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            daySection.innerHTML = `
                <div class="section-header collapsible">
                    <h3><i class="fas fa-calendar-day"></i> 第${day.day}天 (${formattedDate})</h3>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="section-content">
                    <div class="day-content">
                        <div class="map-container">
                            <div id="day${day.day}-map" style="width: 100%; height: 300px;"></div>
                        </div>
                        
                        ${weatherHtml}
                        
                        <div class="activities">
                            <h4><i class="fas fa-tasks"></i> 活动安排</h4>
                            ${day.activities && Array.isArray(day.activities) ? day.activities.map(activity => `
                                <div class="activity-item">
                                    <div class="activity-header">
                                        <input type="text" value="${activity.title}" class="activity-title">
                                        <button class="btn-icon remove-activity"><i class="fas fa-trash"></i></button>
                                    </div>
                                    <div class="activity-details">
                                        <label>时间</label>
                                        <input type="text" value="${activity.time}" class="activity-time">
                                        <label>预计停留时间</label>
                                        <input type="text" value="${activity.duration || ''}" class="activity-duration">
                                        <label>描述</label>
                                        <textarea class="activity-description">${activity.description || ''}</textarea>
                                        ${activity.location ? `
                                            <div class="activity-location">
                                                地址: ${activity.location.address || '未提供'}
                                                <br>坐标: ${activity.location.lng || '未知'}, ${activity.location.lat || '未知'}
                                            </div>
                                        ` : ''}
                                        ${activity.transportation && activity.transportation.length > 0 ? `
                                            <div class="activity-transportation">
                                                <h5><i class="fas fa-route"></i> 交通信息</h5>
                                                ${activity.transportation.map(trans => `
                                                    <div class="transport-item">
                                                        <span class="transport-mode ${trans.mode}">${trans.mode}</span>
                                                        <span class="transport-details">
                                                            ${trans.mode}: ${trans.distance}, 约${trans.duration}
                                                        </span>
                                                    </div>
                                                `).join('')}
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            `).join('') : ''}
                            
                            <button class="btn btn-outline add-activity">
                                <i class="fas fa-plus"></i> 添加活动
                            </button>
                        </div>
                    </div>
                </div>
            `;
            itineraryContainer.appendChild(daySection);
            
            // 初始化地图
            setTimeout(() => {
                initDayMap(day.day, day.activities);
            }, 100);
        });
    }
    
    // 为新添加的section添加折叠功能
    setTimeout(initializeCollapsibleSections, 100);
}

/**
 * 修复函数: 手动解析后端返回的未压缩 Polyline 坐标串
 * 格式: "lng1,lat1;lng2,lat2;..."
 * @param {string} polylineStr 后端返回的坐标字符串
 * @returns {Array<Array<number>>} AMap 路径数组 [[lng1, lat1], [lng2, lat2], ...]
 */
function parseUncompressedPolyline(polylineStr) {
    if (!polylineStr) return [];
    
    // Split the string by ';' to get individual coordinate strings
    const segments = polylineStr.split(';');
    const path = [];

    segments.forEach(segment => {
        // Split each segment by ',' to get lng and lat
        const parts = segment.split(',');
        if (parts.length === 2) {
            const lng = parseFloat(parts[0]);
            const lat = parseFloat(parts[1]);
            // Check for valid numbers
            if (!isNaN(lng) && !isNaN(lat)) {
                path.push([lng, lat]);
            }
        }
    });
    return path;
}


// 初始化每天的地图
function initDayMap(dayNumber, activities) {
    console.log(`初始化第${dayNumber}天的地图，活动:`, activities);
    
    const mapContainerId = `day${dayNumber}-map`;
    const mapContainer = document.getElementById(mapContainerId);
    
    // 确保地图容器存在
    if (mapContainer) {
        // 清空容器内容
        mapContainer.innerHTML = '';
        
        // 确保高德地图API已加载
        if (typeof AMap !== 'undefined') {
            // 创建地图实例
            const map = new AMap.Map(mapContainerId, {
                zoom: 12,
                center: [116.397428, 39.90923] // 默认北京中心坐标
            });
            
            console.log('地图实例创建成功');
            
            // 添加标记点
            let hasLocations = false;
            const markers = [];
            const positions = [];
            const locationsWithDetails = [];
            
            if (activities && Array.isArray(activities)) {
                activities.forEach((activity, index) => {
                    if (activity.location && activity.location.lng && activity.location.lat) {
                        hasLocations = true;
                        const position = [parseFloat(activity.location.lng), parseFloat(activity.location.lat)];
                        positions.push(position);
                        locationsWithDetails.push({
                            position: position,
                            title: activity.title,
                            address: activity.location.address || ''
                        });
                        
                        const marker = new AMap.Marker({
                            position: position,
                            title: activity.title,
                            map: map
                        });
                        markers.push(marker);
                        console.log(`添加标记点: ${activity.title}`, position);
                    }
                });
            }
            
            console.log('所有位置点:', positions);
            
            // 如果有地点，调整地图视野以包含所有标记并绘制路线
            if (hasLocations && markers.length >= 1) {
                console.log(`第${dayNumber}天有${markers.length}个位置点，开始绘制路线`);
                map.setFitView(markers);
                // 绘制路线
                drawRouteOnMap(map, activities);
            } else if (!hasLocations) {
                // 如果没有任何地点坐标信息，仍然保留地图显示
                console.log(`第${dayNumber}天没有位置数据，显示默认地图`);
            }
        } else {
            // 高德地图API未加载，显示提示信息
            mapContainer.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #666;">地图服务未加载</div>';
            console.error('高德地图API未加载');
        }
    } else {
        console.error(`找不到地图容器: ${mapContainerId}`);
    }
}

// 在地图上绘制路线 (只渲染后端提供的 Polyline)
function drawRouteOnMap(map, activities) {
    console.log('开始渲染活动间路线 (使用后端 Polyline)...');
    
    if (!activities || activities.length < 2) {
        console.log('活动点少于2个，无法绘制路线');
        return;
    }
    
    // 遍历活动，渲染每个活动段的路线
    for (let i = 0; i < activities.length - 1; i++) {
        const currentActivity = activities[i];
        const nextActivity = activities[i + 1];

        // 检查下一个活动是否有交通信息
        const transportationInfo = nextActivity.transportation && nextActivity.transportation.length > 0 ? nextActivity.transportation[0] : null;

        // 确保起点和终点都有坐标
        if (!currentActivity.location || !currentActivity.location.lng || !currentActivity.location.lat ||
            !nextActivity.location || !nextActivity.location.lng || !nextActivity.location.lat) {
            console.warn(`活动 ${currentActivity.title} 或 ${nextActivity.title} 缺少坐标信息，跳过路线绘制。`);
            continue;
        }
        
        const originPos = [parseFloat(currentActivity.location.lng), parseFloat(currentActivity.location.lat)];
        const destinationPos = [parseFloat(nextActivity.location.lng), parseFloat(nextActivity.location.lat)];

        if (!transportationInfo || !transportationInfo.polyline) {
            console.log(`活动 ${currentActivity.title} 到 ${nextActivity.title} 之间没有 Polyline 数据或交通信息，绘制直线。`);
            drawSimpleLine(map, [originPos, destinationPos], '#6c757d', 3); // 备选直线，使用较浅颜色和较细的线
            continue;
        }

        const mode = transportationInfo.mode;
        const polylineStr = transportationInfo.polyline;
        
        // --- 关键调试日志：查看 Polyline 字符串 ---
        console.log(`[DEBUG] Polyline String (${mode}):`, polylineStr.substring(0, 100) + (polylineStr.length > 100 ? '...' : ''));
        // ---------------------------------------------

        // 根据交通模式设置颜色
        const strokeColor = mode.includes('步行') ? "#29b380" : 
                            (mode.includes('驾车') || mode.includes('打车') ? "#4361ee" : "#fa7070");
        
        try {
            // === 修复点: 调用自定义解析函数，而非 AMap.Util.decodePath ===
            const path = parseUncompressedPolyline(polylineStr);
            // =========================================================

            // --- 关键调试日志：查看解码结果 ---
            console.log(`[DEBUG] Decoded Path Length: ${path.length}`);
            // ------------------------------------

            if (path && path.length > 0) {
                console.log(`${mode}路线 Polyline 解码成功，开始渲染: ${currentActivity.title} -> ${nextActivity.title}`);

                const polyline = new AMap.Polyline({
                    path: path,
                    strokeColor: strokeColor,
                    strokeWeight: 5,
                    strokeOpacity: 0.8,
                    strokeStyle: "solid",
                    zIndex: 50
                });
                map.add(polyline);
            } else {
                console.warn(`Polyline 解析失败或为空 (${mode})，绘制简单直线: ${currentActivity.title} -> ${nextActivity.title}`);
                drawSimpleLine(map, [originPos, destinationPos], strokeColor, 3);
            }
        } catch (e) {
            console.error('Polyline 解析时发生错误:', e);
            drawSimpleLine(map, [originPos, destinationPos], strokeColor, 3);
        }
    }
    
    // 自动调整地图视野
    map.setFitView();
}

// 绘制简单直线连接点（作为备选方案）
function drawSimpleLine(map, positions, color = "#4361ee", weight = 5) {
    console.log('绘制简单直线，位置点:', positions);
    
    if (positions.length < 2) {
        console.log('位置点少于2个，无法绘制直线');
        return;
    }
    
    const polyline = new AMap.Polyline({
        path: positions.map(pos => new AMap.LngLat(pos[0], pos[1])),
        strokeColor: color,
        strokeWeight: weight,
        strokeOpacity: 0.6, // 略微降低透明度以示区分
        strokeStyle: "dashed" // 使用虚线以示区分
    });
    map.add(polyline);
    console.log('简单直线绘制完成');
}

async function sendChatMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // 添加用户消息到聊天历史
    addMessageToChat(message, 'user');
    chatInput.value = '';

    // 添加用户消息到本地历史记录
    chatHistory.push({ role: 'user', content: message });

    try {
        // 显示"AI正在输入"状态
        const aiThinkingMsg = addMessageToChat('AI正在思考...', 'ai', true);

        // 获取当前设置的目的地和日期信息
        const destinationCity = userPreferences.destinationCity || '';
        const travelDate = userPreferences.startDate || '';

        // 调用后端AI助手API (使用正确的端口8888)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时
        
        const response = await fetch('http://localhost:8888/api/assistant/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                history: chatHistory,
                destination_city: destinationCity,
                travel_date: travelDate
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        const data = await response.json();

        // 移除"AI正在输入"消息
        aiThinkingMsg.remove();

        if (data.response) {
            // 添加AI回复到聊天历史
            addMessageToChat(data.response, 'ai');
            
            // 添加AI回复到本地历史记录
            chatHistory.push({ role: 'assistant', content: data.response });
        } else {
            addMessageToChat('抱歉，我无法处理您的请求。请稍后再试。', 'ai');
        }
    } catch (error) {
        console.error('Error:', error);
        // 移除"AI正在输入"消息
        if (typeof aiThinkingMsg !== 'undefined') {
            aiThinkingMsg.remove();
        }
        
        if (error.name === 'AbortError') {
            addMessageToChat('请求超时，请稍后重试。', 'ai');
        } else {
            addMessageToChat('抱歉，网络错误。请检查您的连接后重试。', 'ai');
        }
    }
}

function addMessageToChat(message, sender, isTemporary = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message');
    messageDiv.classList.add(sender + '-message');
    
    if (isTemporary) {
        messageDiv.id = 'ai-thinking-msg';
    }

    messageDiv.innerHTML = `
        <div class="avatar">
            <i class="fas ${sender === 'user' ? 'fa-user' : 'fa-robot'}"></i>
        </div>
        <div class="message-content">${message}</div>
    `;

    chatHistoryEl.appendChild(messageDiv);
    chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
    
    return messageDiv;
}

// 添加活动功能
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('add-activity')) {
        const activitiesContainer = e.target.closest('.activities');
        const newActivity = document.createElement('div');
        newActivity.className = 'activity-item';
        newActivity.innerHTML = `
            <div class="activity-header">\n
                <input type="text" class="activity-title" placeholder="输入活动名称">\n
                <button class="btn-icon remove-activity"><i class="fas fa-trash"></i></button>\n
            </div>\n
            <div class="activity-details">\n
                <label>时间</label>\n
                <input type="text" class="activity-time" value="09:00">\n
                <label>预计停留时间</label>\n
                <input type="text" class="activity-duration">\n
                <label>描述</label>\n
                <textarea class="activity-description"></textarea>\n
            </div>\n
        `;
        activitiesContainer.insertBefore(newActivity, e.target);
    }
    
    // 删除活动功能
    if (e.target.classList.contains('remove-activity')) {
        const activityItem = e.target.closest('.activity-item');
        if (activityItem) {
            activityItem.remove();
        }
    }
});