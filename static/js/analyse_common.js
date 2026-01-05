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
 * 从数据库加载 Tab 配置（已废弃，不再使用）
 * Tab 配置现在直接从 /api/analyse/data 返回的数据中获取
 */
async function loadTabConfig() {
    // 不再需要单独加载 Tab 配置
    // Tab 列表现在从 loadDataFromDb 返回的数据中获取
    return;
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
        const response = await fetch('/api/analyse/dates');
        const data = await response.json();

        if (response.ok && data.dates) {
            availableDates = data.dates;
        }
    } catch (error) {
        console.error('加载可用日期失败:', error);
    }
}

/**
 * 从数据库加载数据
 * @param {boolean} showUnmatchedAlert - 是否显示未匹配商品的提示（默认 false）
 */
async function loadDataFromDb(showUnmatchedAlert = false) {
    try {
        const response = await fetch('/api/analyse/data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                startDate: selectedStartDate,
                endDate: selectedEndDate
            })
        });
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
    }
}

/**
 * 显示未匹配商品的弹窗提示
 */
function showUnmatchedProductsAlert(unmatchedProducts) {
    const message = `以下商品名称未在ProductInfo表中找到匹配的映射规则：\n\n${unmatchedProducts.join('\n')}\n\n请在ProductInfo表中添加对应的mapped_title字段。`;
    alert(message);
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
 * 导出周报
 */
async function exportWeeklyReport() {
    if (!selectedStartDate || !selectedEndDate) {
        alert('请先选择日期范围');
        return;
    }

    try {
        const response = await fetch('/api/analyse/export-weekly-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                startDate: selectedStartDate,
                endDate: selectedEndDate
            })
        });

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
 * 导出上周周报
 */
async function exportLastWeekReport() {
    const today = new Date();
    const dayOfWeek = today.getDay();

    const thisSunday = new Date(today);
    thisSunday.setDate(today.getDate() - dayOfWeek);

    const lastSunday = new Date(thisSunday);
    lastSunday.setDate(thisSunday.getDate() - 7);

    const lastSaturday = new Date(lastSunday);
    lastSaturday.setDate(lastSunday.getDate() + 6);

    selectedStartDate = formatDate(lastSunday);
    selectedEndDate = formatDate(lastSaturday);

    document.getElementById('startDate').value = selectedStartDate;
    document.getElementById('endDate').value = selectedEndDate;

    // 调用回调
    if (onDateChanged) {
        onDateChanged(selectedStartDate, selectedEndDate);
    }

    await exportWeeklyReport();
}

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
