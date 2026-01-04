// 全局变量
let tabsConfig = [];
let currentTab = null;
let availableDates = [];
let selectedStartDate = null;
let selectedEndDate = null;

// 初始化
document.addEventListener('DOMContentLoaded', async function() {
    loadTabConfig();
    // 加载可用的日期
    await loadAvailableDates();
    // 自动设置为最近一个月的数据
    await setQuickDateRange(30);
});

// 从数据库加载 Tab 配置
async function loadTabConfig() {
    try {
        const response = await fetch('/api/analyse/config');
        const data = await response.json();

        if (response.ok) {
            tabsConfig = data.tabs || [];
            if (tabsConfig.length > 0) {
                currentTab = tabsConfig[0].name;
                renderTabs();
            }
        }
    } catch (error) {
        console.error('加载 Tab 配置失败:', error);
    }
}

// 加载可用的日期
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

// 渲染 Tab 按钮
function renderTabs() {
    const tabContainer = document.getElementById('tabContainer');
    tabContainer.innerHTML = '';

    tabsConfig.forEach(tab => {
        const button = document.createElement('button');
        button.className = 'tab-button' + (tab.name === currentTab ? ' active' : '');
        button.textContent = tab.name;
        button.onclick = () => switchTab(tab.name);
        tabContainer.appendChild(button);
    });
}

// 切换 Tab
function switchTab(tabName) {
    currentTab = tabName;
    renderTabs();
    loadDataFromDb();
}

// 从数据库加载数据
async function loadDataFromDb() {
    try {
        const tableContainer = document.getElementById('tableContainer');
        tableContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p>加载中...</p></div>';

        const response = await fetch('/api/analyse/data');
        const data = await response.json();

        if (response.ok) {
            window.tabData = data.tabs;
            document.getElementById('tabSection').style.display = 'block';
            renderTableData(data.tabs);

            // 检查是否有未匹配的商品
            if (data.unmatched_products && data.unmatched_products.length > 0) {
                showUnmatchedProductsAlert(data.unmatched_products);
            }
        } else {
            alert('加载数据失败: ' + data.error);
            tableContainer.innerHTML = '<div class="empty-state"><div class="empty-state-icon">❌</div><p>加载失败</p></div>';
        }
    } catch (error) {
        console.error('加载数据失败:', error);
        alert('加载数据失败: ' + error.message);
        document.getElementById('tableContainer').innerHTML = '<div class="empty-state"><div class="empty-state-icon">❌</div><p>加载失败</p></div>';
    }
}

// 显示未匹配商品的弹窗提示
function showUnmatchedProductsAlert(unmatchedProducts) {
    const message = `以下商品名称未在ProductInfo表中找到匹配的映射规则：\n\n${unmatchedProducts.join('\n')}\n\n请在ProductInfo表中添加对应的mapped_title字段。`;
    alert(message);
}

// 渲染表格数据（使用卡片式布局）
function renderTableData(tabs) {
    const tableContainer = document.getElementById('tableContainer');

    if (!tabs || tabs.length === 0) {
        tableContainer.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📊</div><p>暂无数据</p></div>';
        return;
    }

    // 找到当前 Tab 的数据
    const currentTabData = tabs.find(tab => tab.name === currentTab);

    if (!currentTabData || !currentTabData.data || currentTabData.data.length === 0) {
        tableContainer.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📊</div><p>暂无数据</p></div>';
        return;
    }

    // 使用卡片式布局渲染数据
    let containerHTML = '';

    currentTabData.data.forEach(item => {
        containerHTML += `
            <div class="data-card">
                <div class="data-card-header">
                    <div class="data-card-title">${item.product_type}</div>
                </div>
                <div class="data-card-stats">
                    <div class="stat-item">
                        <div class="stat-label">有效订购数</div>
                        <div class="stat-value">${item.valid_orders}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">让利后金额</div>
                        <div class="stat-value secondary">¥${parseFloat(item.discount_amount).toFixed(2)}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">抖音</div>
                        <div class="stat-value">${item.douyin_orders}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">天猫</div>
                        <div class="stat-value">${item.tmall_orders}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">有赞</div>
                        <div class="stat-value">${item.youzan_orders}</div>
                    </div>
                </div>
            </div>
        `;
    });

    tableContainer.innerHTML = containerHTML;
}

// 应用日期筛选
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

    await loadDataFromDb();
}

// 设置快捷日期范围
async function setQuickDateRange(days) {
    const today = new Date();
    const endDate = new Date(today);
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - days);

    selectedStartDate = formatDate(startDate);
    selectedEndDate = formatDate(endDate);

    document.getElementById('startDate').value = selectedStartDate;
    document.getElementById('endDate').value = selectedEndDate;

    await loadDataFromDb();
}

// 设置当前周
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

    await loadDataFromDb();
}

// 导出周报
async function exportWeeklyReport() {
    if (!selectedStartDate || !selectedEndDate) {
        alert('请先选择日期范围');
        return;
    }

    try {
        const response = await fetch('/api/export/weekly-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                start_date: selectedStartDate,
                end_date: selectedEndDate
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

// 导出上周周报
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

    await exportWeeklyReport();
}

// 格式化日期为 YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}