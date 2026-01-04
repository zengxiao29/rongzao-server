/**
 * 移动端数据分析页面
 * 使用 analyse_common.js 提供的公共业务逻辑
 */

// 初始化
document.addEventListener('DOMContentLoaded', async function() {
    // 初始化公共逻辑
    initAnalyseCommon({
        onTabsLoaded: handleTabsLoaded,
        onDataLoaded: handleDataLoaded,
        onDateChanged: handleDateChanged
    });

    // 加载可用的日期
    await loadAvailableDates();

    // 自动设置为最近一个月的数据
    await setQuickDateRange(30);
});

/**
 * Tab 加载完成后的回调
 */
function handleTabsLoaded(tabs) {
    renderTabs();

    // 显示相关区域
    if (tabs.length > 0) {
        document.getElementById('tabSection').style.display = 'block';
    }
}

/**
 * 数据加载完成后的回调
 */
function handleDataLoaded(tabs, unmatchedProducts) {
    renderTableData(tabs);
}

/**
 * 日期变更后的回调
 */
function handleDateChanged(startDate, endDate) {
    // 移动端可以在这里添加额外的日期变更处理
}

/**
 * 渲染 Tab 按钮（移动端样式）
 */
function renderTabs() {
    const tabContainer = document.getElementById('tabContainer');
    tabContainer.innerHTML = '';

    const tabs = getTabsConfig();

    tabs.forEach(tab => {
        const button = document.createElement('button');
        button.className = 'tab-button' + (tab.name === getCurrentTab() ? ' active' : '');
        button.textContent = tab.name;
        button.onclick = () => switchTab(tab.name);
        tabContainer.appendChild(button);
    });
}

/**
 * 渲染表格数据（移动端卡片式布局）
 */
function renderTableData(tabs) {
    const tableContainer = document.getElementById('tableContainer');

    if (!tabs || tabs.length === 0) {
        tableContainer.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📊</div><p>暂无数据</p></div>';
        return;
    }

    // 找到当前 Tab 的数据
    const currentTabData = tabs.find(tab => tab.name === getCurrentTab());

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