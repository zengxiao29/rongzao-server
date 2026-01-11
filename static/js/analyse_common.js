/**
 * 数据分析页面公共业务逻辑
 * 供 analyse.js 使用
 */

// 全局变量
let tabsConfig = [];
let currentTab = null;
let availableDates = [];
let selectedStartDate = null;
let selectedEndDate = null;

// 回调函数（由各页面实现）
let onTabsLoaded = null; // Tab 加载完成后的回调
let onDataLoaded = null; // 数据加载完成后的回调
let onDateChanged = null; // 日期变更后的回调
let onTabChanged = null; // Tab 切换后的回调

/**
 * 初始化公共逻辑
 * @param {Object} callbacks - 回调函数对象
 */
function initAnalyseCommon(callbacks = {}) {
    onTabsLoaded = callbacks.onTabsLoaded || null;
    onDataLoaded = callbacks.onDataLoaded || null;
    onDateChanged = callbacks.onDateChanged || null;
    onTabChanged = callbacks.onTabChanged || null;
}

/**
 * 更新 Tab 配置（从后端返回的数据中提取）
 */
function updateTabsConfig(tabs) {
    if (tabs && tabs.length > 0) {
        tabsConfig = tabs;
        // 设置默认 Tab（如果当前 Tab 不在列表中，使用第一个）
        if (!tabsConfig.find(tab => tab.name === currentTab)) {
            currentTab = tabsConfig[0].name;
        }
        // 调用回调
        if (onTabsLoaded) {
            onTabsLoaded(tabsConfig);
        }
    }
}

/**
 * 加载可用的日期
 */
async function loadAvailableDates() {
    try {
        const token = getToken();
        const headers = {};

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // 获取CSRF token并添加到请求头
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                         document.querySelector('input[name="csrf_token"]')?.value;
        
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        const response = await fetch('/api/analyse/dates', { headers: headers });

        // 检查是否需要重新登录
        if (response.status === 401) {
            // 清除过期的 token
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }

        const data = await response.json();

        if (response.ok && data.dates) {
            availableDates = data.dates;
        }
    } catch (error) {
        console.error('加载可用日期失败:', error);
    }
}

/**
 * 显示加载状态
 */
function showLoading() {
    // 防止重复创建
    if (document.getElementById('tableLoadingOverlay')) {
        return;
    }
    
    const tableContainer = document.getElementById('tableContainer');
    if (!tableContainer) {
        console.warn('未找到表格容器，无法显示加载状态');
        return;
    }
    
    // 创建加载覆盖层
    const overlay = document.createElement('div');
    overlay.id = 'tableLoadingOverlay';
    overlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 100;
        border-radius: 10px;
    `;
    
    // 创建旋转图标
    const spinner = document.createElement('div');
    spinner.style.cssText = `
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 15px;
    `;
    
    // 创建加载文本
    const text = document.createElement('div');
    text.textContent = '正在加载数据...';
    text.style.cssText = `
        color: #333;
        font-size: 14px;
        font-weight: bold;
    `;
    
    overlay.appendChild(spinner);
    overlay.appendChild(text);
    
    // 添加旋转动画样式（如果不存在）
    if (!document.querySelector('style#loading-spin-style')) {
        const style = document.createElement('style');
        style.id = 'loading-spin-style';
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    // 设置表格容器为相对定位以便绝对定位覆盖层
    if (window.getComputedStyle(tableContainer).position === 'static') {
        tableContainer.style.position = 'relative';
    }
    
    tableContainer.appendChild(overlay);
    
    // 禁用相关按钮
    disableLoadingButtons(true);
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const overlay = document.getElementById('tableLoadingOverlay');
    if (overlay) {
        overlay.remove();
    }
    
    // 重新启用按钮
    disableLoadingButtons(false);
}

/**
 * 禁用或启用加载相关按钮
 */
function disableLoadingButtons(disabled) {
    // 应用筛选按钮
    const applyBtn = document.querySelector('.action-button.add-button[onclick="applyDateFilter()"]');
    if (applyBtn) {
        applyBtn.disabled = disabled;
        applyBtn.style.opacity = disabled ? '0.6' : '1';
        applyBtn.style.cursor = disabled ? 'not-allowed' : 'pointer';
    }
    
    // 快捷日期按钮
    const quickButtons = document.querySelectorAll('.quick-date-btn');
    quickButtons.forEach(btn => {
        btn.disabled = disabled;
        btn.style.opacity = disabled ? '0.6' : '1';
        btn.style.cursor = disabled ? 'not-allowed' : 'pointer';
    });
    
    // 报表按钮
    const reportBtn = document.querySelector('.action-button.add-button[onclick="openReportPage()"]');
    if (reportBtn) {
        reportBtn.disabled = disabled;
        reportBtn.style.opacity = disabled ? '0.6' : '1';
        reportBtn.style.cursor = disabled ? 'not-allowed' : 'pointer';
    }
}

/**
 * 从数据库加载数据
 * @param {boolean} showUnmatchedAlert - 是否显示未匹配商品的提示（默认 false）
 */
async function loadDataFromDb(showUnmatchedAlert = false) {
    let loadingTimeout = null;
    let hasTimedOut = false;
    
    try {
        // 显示加载状态
        showLoading();
        
        // 设置超时检测（15秒）
        loadingTimeout = setTimeout(() => {
            hasTimedOut = true;
            const overlay = document.getElementById('tableLoadingOverlay');
            if (overlay) {
                const text = overlay.querySelector('div:last-child');
                if (text) {
                    text.textContent = '数据加载较慢，请耐心等待...';
                    text.style.color = '#ff6b6b';
                }
            }
        }, 15000);
        
        const token = getToken();
        const headers = {
            'Content-Type': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // 获取CSRF token并添加到请求头
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                         document.querySelector('input[name="csrf_token"]')?.value;
        
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        const response = await fetch('/api/analyse/data', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                startDate: selectedStartDate,
                endDate: selectedEndDate
            })
        });

        // 检查是否需要重新登录
        if (response.status === 401) {
            // 清除过期的 token
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }
        
        const data = await response.json();

        if (response.ok) {
            window.tabData = data.tabs;

            // 更新 Tab 配置（从后端返回的数据中提取）
            updateTabsConfig(data.tabs);

            // 调用回调
            if (onDataLoaded) {
                onDataLoaded(data.tabs, data.unmatched_products);
            }

            // 检查是否有未匹配的商品（仅在需要时显示提示）
            if (showUnmatchedAlert && data.unmatched_products && data.unmatched_products.length > 0) {
                showUnmatchedProductsAlert(data.unmatched_products);
            }
        } else {
            alert('加载数据失败: ' + data.error);
        }
    } catch (error) {
        console.error('加载数据失败:', error);
        alert('加载数据失败: ' + error.message);
    } finally {
        // 清除超时定时器
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
        }
        
        // 隐藏加载状态
        hideLoading();
        
        // 如果超时了，显示完成提示
        if (hasTimedOut) {
            setTimeout(() => {
                alert('数据加载完成！如果经常遇到加载缓慢的情况，请检查网络连接或联系管理员。');
            }, 300);
        }
    }
}

/**
 * 切换 Tab
 * @param {string} tabName - Tab 名称
 */
function switchTab(tabName) {
    currentTab = tabName;

    // 调用回调，让页面重新渲染
    if (onDataLoaded && window.tabData) {
        onDataLoaded(window.tabData, null);
    }

    // 调用 Tab 切换回调，更新 Tab 按钮的选中状态
    if (onTabChanged) {
        onTabChanged(tabName);
    }
}

/**
 * 应用日期筛选
 */
async function applyDateFilter() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    if (!startDate || !endDate) {
        alert('请选择开始日期和结束日期');
        return;
    }

    if (startDate > endDate) {
        alert('开始日期不能晚于结束日期');
        return;
    }

    selectedStartDate = startDate;
    selectedEndDate = endDate;

    // 调用回调
    if (onDateChanged) {
        onDateChanged(selectedStartDate, selectedEndDate);
    }

    await loadDataFromDb();
}

/**
 * 设置快捷日期范围
 * @param {number} days - 总天数（包括今天）
 */
async function setQuickDateRange(days) {
    const today = new Date();
    const endDate = new Date(today);
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - (days - 1)); // 往前数 days-1 天

    selectedStartDate = formatDate(startDate);
    selectedEndDate = formatDate(endDate);

    document.getElementById('startDate').value = selectedStartDate;
    document.getElementById('endDate').value = selectedEndDate;

    // 调用回调
    if (onDateChanged) {
        onDateChanged(selectedStartDate, selectedEndDate);
    }

    await loadDataFromDb();
}

/**
 * 设置当前周
 */
async function setCurrentWeek() {
    const today = new Date();
    const dayOfWeek = today.getDay();

    const sunday = new Date(today);
    sunday.setDate(today.getDate() - dayOfWeek);

    const saturday = new Date(sunday);
    saturday.setDate(sunday.getDate() + 6);

    selectedStartDate = formatDate(sunday);
    selectedEndDate = formatDate(saturday);

    document.getElementById('startDate').value = selectedStartDate;
    document.getElementById('endDate').value = selectedEndDate;

    // 调用回调
    if (onDateChanged) {
        onDateChanged(selectedStartDate, selectedEndDate);
    }

    await loadDataFromDb();
}

/**
 * 设置本月
 */
async function setCurrentMonth() {
    const today = new Date();

    // 获取本月第一天
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);

    // 获取本月最后一天
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    selectedStartDate = formatDate(firstDay);
    selectedEndDate = formatDate(lastDay);

    document.getElementById('startDate').value = selectedStartDate;
    document.getElementById('endDate').value = selectedEndDate;

    // 调用回调
    if (onDateChanged) {
        onDateChanged(selectedStartDate, selectedEndDate);
    }

    await loadDataFromDb();
}

/**
 * 导出周报
 */
async function exportWeeklyReport() {
    // 自动设置为当前周（周日到周六）
    const today = new Date();
    const dayOfWeek = today.getDay();

    const sunday = new Date(today);
    sunday.setDate(today.getDate() - dayOfWeek);

    const saturday = new Date(sunday);
    saturday.setDate(sunday.getDate() + 6);

    selectedStartDate = formatDate(sunday);
    selectedEndDate = formatDate(saturday);

    document.getElementById('startDate').value = selectedStartDate;
    document.getElementById('endDate').value = selectedEndDate;

    // 调用回调
    if (onDateChanged) {
        onDateChanged(selectedStartDate, selectedEndDate);
    }

    try {
        const token = getToken();
        const headers = {
            'Content-Type': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // 获取CSRF token并添加到请求头
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                         document.querySelector('input[name="csrf_token"]')?.value;
        
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        const response = await fetch('/api/analyse/export-weekly-report', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                startDate: selectedStartDate,
                endDate: selectedEndDate
            })
        });

        // 检查是否需要重新登录
        if (response.status === 401) {
            // 清除过期的 token
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `周报_${selectedStartDate}_至_${selectedEndDate}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const data = await response.json();
            alert('导出失败: ' + data.error);
        }
    } catch (error) {
        console.error('导出周报失败:', error);
        alert('导出周报失败: ' + error.message);
    }
}

/**
 * 打开报表页面
 */
function openReportPage() {
    if (!selectedStartDate || !selectedEndDate) {
        alert('请先选择日期范围');
        return;
    }

    // 在新窗口打开报表页面
    const reportUrl = `/report?startDate=${selectedStartDate}&endDate=${selectedEndDate}`;
    window.open(reportUrl, '_blank');
}

/**
 * 导出上周周报
 */
/**
 * 格式化日期为 YYYY-MM-DD
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的日期字符串
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * 获取当前选中的 Tab
 * @returns {string} 当前 Tab 名称
 */
function getCurrentTab() {
    return currentTab;
}

/**
 * 获取所有 Tab 配置
 * @returns {Array} Tab 配置数组
 */
function getTabsConfig() {
    return tabsConfig;
}
