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
    travelStyles: [],
    customPrompt: ''
};

let itinerary = [];
let chatHistory = [];
let currentUser = null; // 全局用户状态

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

    // 认证相关元素
    window.loginBtn = document.getElementById('login-btn');
    window.registerBtn = document.getElementById('register-btn');
    window.logoutBtn = document.getElementById('logout-btn');
    window.authButtons = document.getElementById('auth-buttons');
    window.userInfo = document.getElementById('user-info');
    window.usernameDisplay = document.getElementById('username-display');
    window.loginModal = document.getElementById('login-modal');
    window.registerModal = document.getElementById('register-modal');
    window.loginForm = document.getElementById('login-form');
    window.registerForm = document.getElementById('register-form');

    // POI管理相关元素
    window.poiSearchInput = document.getElementById('poi-search-input');
    window.searchPoiBtn = document.getElementById('search-poi-btn');
    window.poiSearchResults = document.getElementById('poi-search-results');
    window.userPoiList = document.getElementById('user-poi-list');

    console.log('DOM Elements initialized:', {
        newJourneyBtn,
        historyJourneyBtn,
        aiGenerateBtn,
        originCityInput,
        destinationCityInput
    });
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
            showHistoryPage();
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

    // 认证相关事件监听器
    if (window.loginBtn) {
        window.loginBtn.addEventListener('click', () => showLoginModal());
    }

    if (window.registerBtn) {
        window.registerBtn.addEventListener('click', () => showRegisterModal());
    }

    if (window.logoutBtn) {
        window.logoutBtn.addEventListener('click', () => logout());
    }

    if (window.loginForm) {
        window.loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleLogin();
        });
    }

    if (window.registerForm) {
        window.registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleRegister();
        });
    }

    // POI管理相关事件监听器
    if (window.searchPoiBtn) {
        window.searchPoiBtn.addEventListener('click', () => searchPOI());
    }

    if (window.poiSearchInput) {
        window.poiSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchPOI();
            }
        });
    }

    // 目的地城市变化时，加载该城市的POI列表
    if (destinationCityInput) {
        destinationCityInput.addEventListener('change', () => {
            const city = destinationCityInput.value.trim();
            if (city) {
                loadUserPOIs(city);
            }
        });
    }

    // 检查登录状态
    checkLoginStatus();

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
    userPreferences.customPrompt = document.getElementById('custom-prompt').value.trim();

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
                travelStyles: userPreferences.travelStyles,
                customPrompt: userPreferences.customPrompt
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
                            ${day.activities && Array.isArray(day.activities) ? day.activities
                                // 过滤掉酒店和交通相关活动
                                .filter(activity => {
                                    const title = activity.title || '';
                                    const desc = activity.description || '';
                                    const excludeKeywords = [
                                        '酒店', '入住', '办理入住', '休息', '住宿', 'hotel',
                                        '机场', '航班', '机票', '接机', '送机', '机场大巴',
                                        '火车站', '高铁站', '火车', '高铁', '动车',
                                        '返回住宿', '回酒店', '前往机场', '前往火车站'
                                    ];
                                    const text = (title + ' ' + desc).toLowerCase();
                                    return !excludeKeywords.some(keyword =>
                                        text.includes(keyword.toLowerCase())
                                    );
                                })
                                .map(activity => `
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

// ==================== 认证相关函数 ====================

// 显示登录模态框
function showLoginModal() {
    window.loginModal.style.display = 'flex';
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
    const errorDiv = document.getElementById('login-error');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// 显示注册模态框
function showRegisterModal() {
    window.registerModal.style.display = 'flex';
    document.getElementById('register-username').value = '';
    document.getElementById('register-password').value = '';
    document.getElementById('register-password-confirm').value = '';
    document.getElementById('register-email').value = '';
    const errorDiv = document.getElementById('register-error');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// 关闭认证模态框
function closeAuthModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// 处理登录
async function handleLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error');
    const submitBtn = document.getElementById('login-submit-btn');

    if (!username || !password) {
        errorDiv.textContent = '请填写用户名和密码';
        errorDiv.style.display = 'block';
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = '登录中...';

    try {
        const response = await fetch('http://localhost:8888/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            closeAuthModal('login-modal');
            showMessage('登录成功', `欢迎回来，${data.user.username}！`);
            updateAuthUI(data.user);
        } else {
            errorDiv.textContent = data.error || '登录失败';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = '网络错误，请稍后重试';
        errorDiv.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '登录';
    }
}

// 处理注册
async function handleRegister() {
    const username = document.getElementById('register-username').value.trim();
    const password = document.getElementById('register-password').value;
    const passwordConfirm = document.getElementById('register-password-confirm').value;
    const email = document.getElementById('register-email').value.trim();
    const errorDiv = document.getElementById('register-error');
    const submitBtn = document.getElementById('register-submit-btn');

    // 验证
    if (!username || !password) {
        errorDiv.textContent = '请填写用户名和密码';
        errorDiv.style.display = 'block';
        return;
    }

    if (username.length < 3 || username.length > 50) {
        errorDiv.textContent = '用户名长度必须在3-50个字符之间';
        errorDiv.style.display = 'block';
        return;
    }

    if (password.length < 6) {
        errorDiv.textContent = '密码长度至少6个字符';
        errorDiv.style.display = 'block';
        return;
    }

    if (password !== passwordConfirm) {
        errorDiv.textContent = '两次输入的密码不一致';
        errorDiv.style.display = 'block';
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = '注册中...';

    try {
        const response = await fetch('http://localhost:8888/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ username, password, email: email || undefined })
        });

        const data = await response.json();

        if (response.ok) {
            closeAuthModal('register-modal');
            showMessage('注册成功', '注册成功！已自动登录');
            updateAuthUI(data.user);
        } else {
            errorDiv.textContent = data.error || '注册失败';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Register error:', error);
        errorDiv.textContent = '网络错误，请稍后重试';
        errorDiv.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = '注册';
    }
}

// 处理登出
async function logout() {
    try {
        const response = await fetch('http://localhost:8888/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });

        if (response.ok) {
            updateAuthUI(null);

            // 返回欢迎页面
            const screens = document.querySelectorAll('.screen');
            screens.forEach(screen => screen.style.display = 'none');
            if (welcomeScreen) {
                welcomeScreen.style.display = 'flex';
            }

            showMessage('登出成功', '您已成功登出');
        }
    } catch (error) {
        console.error('Logout error:', error);
        showMessage('错误', '登出失败，请稍后重试');
    }
}

// 检查登录状态
async function checkLoginStatus() {
    try {
        const response = await fetch('http://localhost:8888/api/auth/me', {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            updateAuthUI(data.user);
        } else {
            updateAuthUI(null);
        }
    } catch (error) {
        console.error('Check login status error:', error);
        updateAuthUI(null);
    }
}

// 更新认证UI
function updateAuthUI(user) {
    // 保存到全局状态
    currentUser = user;

    if (user) {
        window.authButtons.style.display = 'none';
        window.userInfo.style.display = 'flex';
        window.usernameDisplay.textContent = user.username;
    } else {
        window.authButtons.style.display = 'flex';
        window.userInfo.style.display = 'none';
    }
}

// ==================== 历史行程相关函数 ====================

// 显示历史行程页面
async function showHistoryPage() {
    // 检查是否已登录（使用全局状态）
    if (!currentUser) {
        showMessage('请先登录', '查看历史行程需要登录，请先登录或注册');
        showLoginModal();
        return;
    }

    // 加载历史行程
    loadHistoryItineraries();
}

// 加载历史行程列表
async function loadHistoryItineraries(page = 1, city = '') {
    console.log('loadHistoryItineraries called with page:', page, 'city:', city);
    try {
        const params = new URLSearchParams({ page, per_page: 10 });
        if (city) params.append('destination_city', city);

        console.log('Fetching history from:', `http://localhost:8888/api/itinerary/history?${params}`);
        const response = await fetch(`http://localhost:8888/api/itinerary/history?${params}`, {
            credentials: 'include'
        });

        console.log('History response status:', response.status);
        if (response.ok) {
            const data = await response.json();
            console.log('History data received:', data);
            renderHistoryList(data);
        } else {
            const errorText = await response.text();
            console.error('History load failed:', response.status, errorText);
            showMessage('错误', '加载历史行程失败');
        }
    } catch (error) {
        console.error('Load history error:', error);
        showMessage('错误', '网络错误，请稍后重试');
    }
}

// 渲染历史行程列表
function renderHistoryList(data) {
    console.log('Rendering history list with data:', data);

    // 检查是否有数据
    const hasItems = data.items && data.items.length > 0;

    // 创建历史行程界面HTML
    const historyHTML = `
        <div class="history-screen">
            <div class="history-header">
                <h2><i class="fas fa-history"></i> 历史行程</h2>
                <button class="btn btn-secondary" onclick="backToWelcomeFromHistory()">
                    <i class="fas fa-arrow-left"></i> 返回
                </button>
            </div>
            <div class="history-filter">
                <input type="text" id="city-filter" placeholder="筛选城市..." />
                <button class="btn btn-primary" onclick="filterHistory()">筛选</button>
            </div>
            <div class="history-list" id="history-list">
                ${hasItems ? data.items.map(item => `
                    <div class="history-item" data-id="${item.id}">
                        <div class="history-item-header">
                            <h3>${item.title || item.destination_city + '之旅'}</h3>
                            <span class="history-date">${item.created_at}</span>
                        </div>
                        <div class="history-item-details">
                            <p><i class="fas fa-map-marker-alt"></i> ${item.destination_city}</p>
                            <p><i class="fas fa-calendar"></i> ${item.start_date} 至 ${item.end_date}</p>
                        </div>
                        <div class="history-item-actions">
                            <button class="btn btn-outline" onclick="loadHistoryItinerary(${item.id})">查看详情</button>
                            <button class="btn btn-secondary" onclick="deleteHistory(${item.id})">删除</button>
                        </div>
                    </div>
                `).join('') : `
                    <div class="empty-state">
                        <i class="fas fa-inbox" style="font-size: 48px; color: #ccc; margin-bottom: 16px;"></i>
                        <p style="color: #666;">暂无历史行程</p>
                        <p style="color: #999; font-size: 14px;">开始规划您的第一次旅程吧！</p>
                    </div>
                `}
            </div>
            ${hasItems ? `
                <div class="history-pagination">
                    ${data.page > 1 ? `<button class="btn btn-outline" onclick="loadHistoryItineraries(${data.page - 1})">上一页</button>` : ''}
                    <span>第 ${data.page} / ${data.pages} 页</span>
                    ${data.page < data.pages ? `<button class="btn btn-outline" onclick="loadHistoryItineraries(${data.page + 1})">下一页</button>` : ''}
                </div>
            ` : ''}
        </div>
    `;

    // 隐藏其他界面，显示历史行程界面
    welcomeScreen.style.display = 'none';
    settingsScreen.style.display = 'none';
    itineraryScreen.style.display = 'none';

    // 将历史界面插入到main-panel中
    const mainPanel = document.querySelector('.main-panel');
    let historyScreen = document.getElementById('history-screen');
    if (!historyScreen) {
        historyScreen = document.createElement('div');
        historyScreen.id = 'history-screen';
        historyScreen.className = 'screen';
        mainPanel.appendChild(historyScreen);
    }
    historyScreen.innerHTML = historyHTML;
    historyScreen.style.display = 'block';
}

// 从历史界面返回欢迎界面
function backToWelcomeFromHistory() {
    const historyScreen = document.getElementById('history-screen');
    if (historyScreen) {
        historyScreen.style.display = 'none';
    }
    welcomeScreen.style.display = 'flex';
}

// 筛选历史行程
function filterHistory() {
    const city = document.getElementById('city-filter').value.trim();
    loadHistoryItineraries(1, city);
}

// 加载历史行程详情
async function loadHistoryItinerary(id) {
    try {
        const response = await fetch(`http://localhost:8888/api/itinerary/history/${id}`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            // 将历史行程数据转换为当前行程格式
            itinerary = data.days.map(day => ({
                day: day.day_number,
                activities: JSON.parse(day.activities)
            }));

            // 设置用户偏好
            userPreferences.destinationCity = data.destination_city;
            userPreferences.startDate = data.start_date;
            userPreferences.endDate = data.end_date;

            // 显示行程界面
            const historyScreen = document.getElementById('history-screen');
            if (historyScreen) {
                historyScreen.style.display = 'none';
            }

            // 生成行程显示
            generateDailySessions(itinerary, JSON.parse(data.summary || '{}'));

            settingsScreen.style.display = 'none';
            itineraryScreen.style.display = 'block';
        } else {
            showMessage('错误', '加载行程详情失败');
        }
    } catch (error) {
        console.error('Load itinerary detail error:', error);
        showMessage('错误', '网络错误，请稍后重试');
    }
}

// 删除历史行程
async function deleteHistory(id) {
    if (!confirm('确定要删除这条历史行程吗？')) {
        return;
    }

    try {
        const response = await fetch(`http://localhost:8888/api/itinerary/history/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            showMessage('删除成功', '历史行程已删除');
            // 重新加载列表
            loadHistoryItineraries();
        } else {
            showMessage('错误', '删除失败');
        }
    } catch (error) {
        console.error('Delete history error:', error);
        showMessage('错误', '网络错误，请稍后重试');
    }
}

// ==================== POI管理相关函数 ====================

// 搜索POI
async function searchPOI() {
    const query = window.poiSearchInput.value.trim();
    const city = destinationCityInput.value.trim();

    if (!query) {
        showMessage('提示', '请输入景点名称');
        return;
    }

    if (!city) {
        showMessage('提示', '请先选择目的地城市');
        return;
    }

    try {
        const response = await fetch(`http://localhost:8888/api/poi/autocomplete?query=${encodeURIComponent(query)}&city=${encodeURIComponent(city)}&limit=5`);

        if (response.ok) {
            const data = await response.json();
            renderSearchResults(data.suggestions);
        } else {
            showMessage('错误', '搜索失败');
        }
    } catch (error) {
        console.error('Search POI error:', error);
        showMessage('错误', '网络错误，请稍后重试');
    }
}

// 渲染搜索结果
function renderSearchResults(suggestions) {
    const resultsDiv = window.poiSearchResults;

    if (suggestions.length === 0) {
        resultsDiv.innerHTML = '<div class="poi-search-item"><div class="poi-search-item-name">未找到相关景点</div></div>';
        resultsDiv.style.display = 'block';
        return;
    }

    resultsDiv.innerHTML = suggestions.map(poi => `
        <div class="poi-search-item" onclick="addPOI('${poi.id}', '${poi.name.replace(/'/g, "\\'")}', '${poi.location}', '${poi.type}')">
            <div class="poi-search-item-name">${poi.name}</div>
            <div class="poi-search-item-address">${poi.address}</div>
        </div>
    `).join('');

    resultsDiv.style.display = 'block';
}

// 添加POI到用户列表
async function addPOI(id, name, location, type) {
    const city = destinationCityInput.value.trim();

    if (!city) {
        showMessage('提示', '请先选择目的地城市');
        return;
    }

    try {
        const response = await fetch('http://localhost:8888/api/user-pois/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                poi: { id, name, location, type },
                city
            })
        });

        const data = await response.json();

        if (response.ok) {
            // 隐藏搜索结果
            window.poiSearchResults.style.display = 'none';
            window.poiSearchInput.value = '';

            // 重新加载POI列表
            loadUserPOIs(city);

            showMessage('成功', `已添加 ${name}`);
        } else {
            showMessage('错误', data.error || '添加失败');
        }
    } catch (error) {
        console.error('Add POI error:', error);
        showMessage('错误', '网络错误，请稍后重试');
    }
}

// 加载用户已添加的POI列表
async function loadUserPOIs(city) {
    if (!city) {
        console.warn('loadUserPOIs: city参数为空');
        return;
    }

    console.log('loadUserPOIs: 正在加载POI列表，城市=', city);

    try {
        const response = await fetch(`http://localhost:8888/api/user-pois/list?city=${encodeURIComponent(city)}`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            console.log('loadUserPOIs: 成功获取数据', data);
            renderUserPOIs(data.pois, city);
        } else {
            console.error('loadUserPOIs: API返回错误', response.status);
        }
    } catch (error) {
        console.error('Load user POIs error:', error);
    }
}

// 渲染用户POI列表
function renderUserPOIs(pois, city) {
    const listDiv = window.userPoiList;

    console.log('renderUserPOIs: 渲染POI列表，数量=', pois ? pois.length : 0);

    if (!pois || pois.length === 0) {
        listDiv.innerHTML = '<p class="poi-empty-hint">还没有添加景点，搜索并添加您想去的地方</p>';
        return;
    }

    listDiv.innerHTML = pois.map(poi => `
        <div class="poi-item">
            <div class="poi-item-info">
                <div class="poi-item-name">${poi.name}</div>
                <div class="poi-item-type">${poi.type || '景点'}</div>
            </div>
            <div class="poi-item-actions">
                <button class="btn btn-secondary" onclick="removePOI('${poi.id}', '${city}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');

    console.log('renderUserPOIs: POI列表已渲染完成');
}

// 删除POI
async function removePOI(poiId, city) {
    try {
        const response = await fetch(`http://localhost:8888/api/user-pois/remove/${poiId}?city=${encodeURIComponent(city)}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            loadUserPOIs(city);
            showMessage('成功', 'POI已删除');
        } else {
            showMessage('错误', '删除失败');
        }
    } catch (error) {
        console.error('Remove POI error:', error);
        showMessage('错误', '网络错误，请稍后重试');
    }
}