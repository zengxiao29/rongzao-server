/**
 * PC 端数据分析页面
 * 使用 analyse_common.js 提供的公共业务逻辑
 */

// 全局变量（PC 端特有）
let editingTab = null;
let currentDatePicker = null;
let currentMonth = new Date();

// 排序状态
let currentSortColumn = -1;
let currentSortDirection = 'desc'; // 'asc' 或 'desc'

// 初始化
document.addEventListener('DOMContentLoaded', async function() {
    // 检查用户角色，如果是 admin 则显示商品管理按钮
    const user = getCurrentUser();
    if (user && user.role === 'admin') {
        const productManageBtn = document.getElementById('productManageBtn');
        if (productManageBtn) {
            productManageBtn.style.display = 'block';
        }
    }

    // 初始化公共逻辑
    initAnalyseCommon({
        onTabsLoaded: handleTabsLoaded,
        onDataLoaded: handleDataLoaded,
        onDateChanged: handleDateChanged,
        onTabChanged: handleTabChanged
    });

    // 设置文件上传
    setupFileUpload();
    setupInventoryFileUpload();

    // 加载可用的日期
    await loadAvailableDates();

    // 设置默认日期范围：起止日期都为最后可用日期（最新一天）
    if (availableDates.length > 0) {
        const lastDate = availableDates[availableDates.length - 1];
        
        selectedStartDate = lastDate;
        selectedEndDate = lastDate;
        
        document.getElementById('startDate').value = selectedStartDate;
        document.getElementById('endDate').value = selectedEndDate;
        
        // 加载数据
        await loadDataFromDb();
    }

    // 监听窗口大小变化，自动切换渲染方式
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            // 重新渲染当前数据
            if (window.tabData) {
                handleDataLoaded(window.tabData, null);
            }
        }, 250); // 防抖，250ms 后执行
    });
});

/**
 * Tab 加载完成后的回调
 */
function handleTabsLoaded(tabs) {
    renderTabs();

    // 显示相关区域
    if (tabs.length > 0) {
        document.getElementById('tabSection').style.display = 'block';
        document.getElementById('dateFilterSection').style.display = 'block';
    }
}

/**
 * 数据加载完成后的回调
 */
function handleDataLoaded(tabs, unmatchedProducts) {
    console.log('handleDataLoaded 被调用');
    console.log('tabs:', tabs);
    console.log('currentTab:', getCurrentTab());
    renderTableData(tabs);
}

/**
 * 日期变更后的回调
 */
function handleDateChanged(startDate, endDate) {
    // PC 端可以在这里添加额外的日期变更处理
}

/**
 * Tab 切换后的回调
 */
function handleTabChanged(tabName) {
    // 更新所有 Tab 按钮的选中状态
    const tabButtons = document.querySelectorAll('.tab-button:not(.tab-actions button)');
    tabButtons.forEach(button => {
        if (button.textContent === tabName) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
}

/**
 * 渲染 Tab 按钮（PC 端样式）
 */
function renderTabs() {
    const tabContainer = document.getElementById('tabContainer');
    const existingTabs = tabContainer.querySelectorAll('.tab-button:not(.tab-actions button)');
    existingTabs.forEach(tab => tab.remove());

    const tabs = getTabsConfig();

    tabs.forEach((tab, index) => {
        const tabButton = document.createElement('button');
        tabButton.className = 'tab-button';
        tabButton.textContent = tab.name;
        tabButton.dataset.index = index;

        if (tab.name === getCurrentTab()) {
            tabButton.classList.add('active');
        }

        tabButton.onclick = function() {
            switchTab(tab.name);
        };

        // 插入到 tab-actions 之前
        const tabActions = tabContainer.querySelector('.tab-actions');
        if (tabActions) {
            tabContainer.insertBefore(tabButton, tabActions);
        } else {
            tabContainer.appendChild(tabButton);
        }
    });

    // 如果没有 Tab，显示空状态
    if (tabs.length === 0) {
        document.getElementById('tableContainer').innerHTML = `
            <div class="empty-state">
                <div style="font-size: 3rem;">📊</div>
                <p>请先添加 Tab 配置，然后点击"刷新数据"按钮</p>
            </div>
        `;
    }
}

/**
 * 渲染表格数据（根据屏幕尺寸自动切换表格/卡片形式）
 */
function renderTableData(tabs) {
    console.log('renderTableData 被调用');
    const tableContainer = document.getElementById('tableContainer');

    if (!tabs || tabs.length === 0) {
        console.log('tabs 为空或长度为 0');
        tableContainer.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 3rem;">📊</div>
                <p>暂无数据</p>
            </div>
        `;
        return;
    }

    // 找到当前 Tab 的数据
    const currentTabName = getCurrentTab();
    console.log('当前 Tab 名称:', currentTabName);
    console.log('可用的 Tabs:', tabs.map(t => t.name));
    const currentTabData = tabs.find(tab => tab.name === currentTabName);

    if (!currentTabData || !currentTabData.data || currentTabData.data.length === 0) {
        console.log('当前 Tab 数据为空或不存在');
        tableContainer.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 3rem;">📊</div>
                <p>暂无数据</p>
            </div>
        `;
        return;
    }

    // 根据屏幕宽度选择渲染方式
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        // 移动端：渲染卡片式布局
        renderMobileCards(currentTabData.data, tableContainer);
    } else {
        // PC 端：渲染表格形式
        renderPCTable(currentTabData.data, tableContainer);
    }
}

/**
 * 计算客单价
 * @param {number} orders - 订单数
 * @param {number} amount - 让利后金额
 * @returns {string} 客单价（四舍五入取整）
 */
function calculateAOV(orders, amount) {
    if (orders === 0) {
        return '0';
    }
    const aov = amount / orders;
    return aov.toFixed(0);
}

/**
 * 渲染 PC 端表格
 */
function renderPCTable(data, container) {
    // 计算合计
    let totalValidOrders = 0;
    let totalDouyinOrders = 0;
    let totalDouyinAmount = 0;
    let totalTmallOrders = 0;
    let totalTmallAmount = 0;
    let totalYouzanOrders = 0;
    let totalYouzanAmount = 0;
    let totalJdOrders = 0;
    let totalJdAmount = 0;
    let totalDiscountAmount = 0;
    let totalInventory = 0;

    data.forEach(item => {
        totalValidOrders += item.valid_orders;
        totalDouyinOrders += item.douyin_orders;
        totalDouyinAmount += item.douyin_amount;
        totalTmallOrders += item.tmall_orders;
        totalTmallAmount += item.tmall_amount;
        totalYouzanOrders += item.youzan_orders;
        totalYouzanAmount += item.youzan_amount;
        totalJdOrders += item.jd_orders;
        totalJdAmount += item.jd_amount;
        totalDiscountAmount += item.discount_amount;
        totalInventory += item.inventory || 0;
    });

    let containerHTML = `
        <div class="table-wrapper">
            <table class="data-table" id="dataTable">
                <thead>
                    <tr>
                        <th>商品类型</th>
                        <th>
                            有效订购数
                            <button class="sort-btn" data-column="1" onclick="sortTable(1)">▼</button>
                        </th>
                        <th>
                            抖音
                            <button class="sort-btn" data-column="2" onclick="sortTable(2)">▼</button>
                        </th>
                        <th>
                            天猫
                            <button class="sort-btn" data-column="3" onclick="sortTable(3)">▼</button>
                        </th>
                        <th>
                            有赞
                            <button class="sort-btn" data-column="4" onclick="sortTable(4)">▼</button>
                        </th>
                        <th>
                            京东
                            <button class="sort-btn" data-column="5" onclick="sortTable(5)">▼</button>
                        </th>
                        <th>
                            让利后金额
                            <button class="sort-btn" data-column="6" onclick="sortTable(6)">▼</button>
                        </th>
                        <th>
                            库存
                            <button class="sort-btn" data-column="7" onclick="sortTable(7)">▼</button>
                        </th>
                    </tr>
                </thead>
                <tbody id="tableBody">
    `;

    data.forEach((item, index) => {
        containerHTML += `
            <tr data-index="${index}" data-product-type="${item.product_type}" onclick="handleTableRowClick(this)">
                <td>${item.product_type}</td>
                <td>${item.valid_orders}</td>
                <td>${item.douyin_orders}${item.douyin_orders > 0 ? `<span style="color: #999;">\t<i>¥${calculateAOV(item.douyin_orders, item.douyin_amount)}</i></span>` : ''}</td>
                <td>${item.tmall_orders}${item.tmall_orders > 0 ? `<span style="color: #999;">\t<i>¥${calculateAOV(item.tmall_orders, item.tmall_amount)}</i></span>` : ''}</td>
                <td>${item.youzan_orders}</td>
                <td>${item.jd_orders}${item.jd_orders > 0 ? `<span style="color: #999;">\t<i>¥${calculateAOV(item.jd_orders, item.jd_amount)}</i></span>` : ''}</td>
                <td>¥${parseFloat(item.discount_amount).toFixed(2)}</td>
                <td>${item.inventory || 0}</td>
            </tr>
        `;
    });

    // 添加合计行
    containerHTML += `
            <tr class="total-row" style="background-color: #f0f0f0; font-weight: bold;">
                <td>合计</td>
                <td>${totalValidOrders}</td>
                <td>${totalDouyinOrders}${totalDouyinOrders > 0 ? `<span style="color: #999;">\t<i>¥${calculateAOV(totalDouyinOrders, totalDouyinAmount)}</i></span>` : ''}</td>
                <td>${totalTmallOrders}${totalTmallOrders > 0 ? `<span style="color: #999;">\t<i>¥${calculateAOV(totalTmallOrders, totalTmallAmount)}</i></span>` : ''}</td>
                <td>${totalYouzanOrders}</td>
                <td>${totalJdOrders}${totalJdOrders > 0 ? `<span style="color: #999;">\t<i>¥${calculateAOV(totalJdOrders, totalJdAmount)}</i></span>` : ''}</td>
                <td>¥${totalDiscountAmount.toFixed(2)}</td>
                <td>${totalInventory}</td>
            </tr>
    `;

    containerHTML += `
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = containerHTML;
}

/**
 * 表格排序函数
 * @param {number} columnIndex - 列索引（0开始）
 */
function sortTable(columnIndex) {
    // 如果点击的是同一列，切换排序方向
    if (currentSortColumn === columnIndex) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        // 点击新列，默认降序
        currentSortColumn = columnIndex;
        currentSortDirection = 'desc';
    }

    const tableBody = document.getElementById('tableBody');
    const allRows = Array.from(tableBody.querySelectorAll('tr'));

    // 分离数据行和合计行
    const dataRows = allRows.filter(row => !row.classList.contains('total-row'));
    const totalRow = allRows.find(row => row.classList.contains('total-row'));

    // 对数据行进行排序
    dataRows.sort((a, b) => {
        const aValue = parseFloat(a.cells[columnIndex].textContent.replace(/[¥,]/g, ''));
        const bValue = parseFloat(b.cells[columnIndex].textContent.replace(/[¥,]/g, ''));
        
        if (currentSortDirection === 'asc') {
            return aValue - bValue;
        } else {
            return bValue - aValue;
        }
    });

    // 清空表格内容
    tableBody.innerHTML = '';

    // 重新插入排序后的数据行
    dataRows.forEach(row => {
        tableBody.appendChild(row);
    });

    // 最后插入合计行
    if (totalRow) {
        tableBody.appendChild(totalRow);
    }

    // 更新所有排序按钮的显示
    updateSortButtons();
}

/**
 * 更新排序按钮的显示
 */
function updateSortButtons() {
    const buttons = document.querySelectorAll('.sort-btn');
    buttons.forEach(btn => {
        const column = parseInt(btn.dataset.column);
        if (column === currentSortColumn) {
            btn.textContent = currentSortDirection === 'asc' ? '▲' : '▼';
            btn.classList.add('active');
        } else {
            btn.textContent = '▼';
            btn.classList.remove('active');
        }
    });
}

/**
 * 渲染移动端卡片
 */
function renderMobileCards(data, container) {
    // 计算合计
    let totalValidOrders = 0;
    let totalDouyinOrders = 0;
    let totalTmallOrders = 0;
    let totalYouzanOrders = 0;
    let totalJdOrders = 0;
    let totalDiscountAmount = 0;
    let totalInventory = 0;

    data.forEach(item => {
        totalValidOrders += item.valid_orders;
        totalDouyinOrders += item.douyin_orders;
        totalTmallOrders += item.tmall_orders;
        totalYouzanOrders += item.youzan_orders;
        totalJdOrders += item.jd_orders;
        totalDiscountAmount += item.discount_amount;
        totalInventory += item.inventory || 0;
    });

    let containerHTML = '<div class="mobile-cards">';

    data.forEach(item => {
        containerHTML += `
            <div class="mobile-card">
                <div class="mobile-card-title">${item.product_type}</div>
                <div class="mobile-card-item">
                    <span class="mobile-card-label">有效订购数</span>
                    <span class="mobile-card-value">${item.valid_orders}</span>
                </div>
                <div class="mobile-card-item">
                    <span class="mobile-card-label">抖音</span>
                    <span class="mobile-card-value">${item.douyin_orders}</span>
                </div>
                <div class="mobile-card-item">
                    <span class="mobile-card-label">天猫</span>
                    <span class="mobile-card-value">${item.tmall_orders}</span>
                </div>
                <div class="mobile-card-item">
                    <span class="mobile-card-label">有赞</span>
                    <span class="mobile-card-value">${item.youzan_orders}</span>
                </div>
                <div class="mobile-card-item">
                    <span class="mobile-card-label">京东</span>
                    <span class="mobile-card-value">${item.jd_orders}</span>
                </div>
                <div class="mobile-card-item">
                    <span class="mobile-card-label">让利后金额</span>
                    <span class="mobile-card-value highlight">¥${parseFloat(item.discount_amount).toFixed(2)}</span>
                </div>
                <div class="mobile-card-item">
                    <span class="mobile-card-label">库存</span>
                    <span class="mobile-card-value">${item.inventory || 0}</span>
                </div>
            </div>
        `;
    });

    // 添加合计卡片
    containerHTML += `
        <div class="mobile-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <div class="mobile-card-title" style="border-bottom-color: rgba(255, 255, 255, 0.3);">合计</div>
            <div class="mobile-card-item">
                <span class="mobile-card-label" style="color: rgba(255, 255, 255, 0.8);">有效订购数</span>
                <span class="mobile-card-value" style="color: white;">${totalValidOrders}</span>
            </div>
            <div class="mobile-card-item">
                <span class="mobile-card-label" style="color: rgba(255, 255, 255, 0.8);">抖音</span>
                <span class="mobile-card-value" style="color: white;">${totalDouyinOrders}</span>
            </div>
            <div class="mobile-card-item">
                <span class="mobile-card-label" style="color: rgba(255, 255, 255, 0.8);">天猫</span>
                <span class="mobile-card-value" style="color: white;">${totalTmallOrders}</span>
            </div>
            <div class="mobile-card-item">
                <span class="mobile-card-label" style="color: rgba(255, 255, 255, 0.8);">有赞</span>
                <span class="mobile-card-value" style="color: white;">${totalYouzanOrders}</span>
            </div>
            <div class="mobile-card-item">
                <span class="mobile-card-label" style="color: rgba(255, 255, 255, 0.8);">京东</span>
                <span class="mobile-card-value" style="color: white;">${totalJdOrders}</span>
            </div>
            <div class="mobile-card-item">
                <span class="mobile-card-label" style="color: rgba(255, 255, 255, 0.8);">让利后金额</span>
                <span class="mobile-card-value" style="color: white;">¥${totalDiscountAmount.toFixed(2)}</span>
            </div>
            <div class="mobile-card-item">
                <span class="mobile-card-label" style="color: rgba(255, 255, 255, 0.8);">库存</span>
                <span class="mobile-card-value" style="color: white;">${totalInventory}</span>
            </div>
        </div>
    `;

    containerHTML += '</div>';
    container.innerHTML = containerHTML;
}

// ==================== 文件上传相关（仅 PC 端） ====================

/**
 * 设置文件上传功能
 */
function setupFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (!uploadArea || !fileInput) {
        return;
    }

    // 文件选择
    fileInput.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            handleFileUpload(file);
        }
    };

    // 拖拽上传
    uploadArea.ondragover = function(e) {
        e.preventDefault();
        uploadArea.style.background = '#f0f9ff';
    };

    uploadArea.ondragleave = function(e) {
        e.preventDefault();
        uploadArea.style.background = '';
    };

    uploadArea.ondrop = function(e) {
        e.preventDefault();
        uploadArea.style.background = '';

        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileUpload(file);
        }
    };
}

/**
 * 处理文件上传
 */
async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

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

        const response = await fetch('/api/analyse/upload', {
            method: 'POST',
            headers: headers,
            body: formData
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

        const result = await response.json();

        if (response.ok) {
            const uploadResult = document.getElementById('uploadResult');
            uploadResult.style.display = 'block';
            const message = `上传完成！总计 ${result.total} 条，成功 ${result.success_count} 条，重复 ${result.duplicate_count} 条，错误 ${result.error_count} 条`;
            uploadResult.querySelector('p').textContent = message;
            
            // 根据错误数量设置颜色：有错误时显示红色，否则显示绿色
            if (result.error_count > 0) {
                uploadResult.style.color = '#dc3545';
            } else {
                uploadResult.style.color = '#28a745';
            }
        
            // 检查是否有警告信息
            if (result.warning) {
                const warningDiv = document.createElement('div');
                warningDiv.style.backgroundColor = '#fff3cd';
                warningDiv.style.border = '1px solid #ffc107';
                warningDiv.style.color = '#856404';
                warningDiv.style.padding = '10px 15px';
                warningDiv.style.marginTop = '10px';
                warningDiv.style.borderRadius = '5px';
                warningDiv.textContent = '⚠️ ' + result.warning;
                uploadResult.appendChild(warningDiv);
            }
        
            // 重新加载可用日期和数据
            await loadAvailableDates();
            await loadDataFromDb();
        } else {
            const uploadResult = document.getElementById('uploadResult');
            uploadResult.style.display = 'block';
            uploadResult.querySelector('p').textContent = '上传失败: ' + result.error;
            uploadResult.style.color = '#dc3545';
            alert('上传失败: ' + result.error);
        }
    } catch (error) {
        console.error('上传失败:', error);
        const uploadResult = document.getElementById('uploadResult');
        uploadResult.style.display = 'block';
        uploadResult.querySelector('p').textContent = '上传失败: ' + error.message;
        uploadResult.style.color = '#dc3545';
        alert('上传失败: ' + error.message);
    }
}

// ==================== 日期选择器相关（仅 PC 端） ====================

/**
 * 打开日期选择器
 */
function openDatePicker(type) {
    currentDatePicker = type;
    const modal = document.getElementById('datePickerModal');
    modal.classList.add('show');
    renderDatePicker();
}

/**
 * 关闭日期选择器
 */
function closeDatePicker() {
    const modal = document.getElementById('datePickerModal');
    modal.classList.remove('show');
    currentDatePicker = null;
}

/**
 * 切换月份
 */
function changeMonth(delta) {
    currentMonth.setMonth(currentMonth.getMonth() + delta);
    renderDatePicker();
}

/**
 * 切换年份
 */
function changeYear(delta) {
    currentMonth.setFullYear(currentMonth.getFullYear() + delta);
    renderDatePicker();
}

/**
 * 定位到本月
 */
function goToCurrentMonth() {
    const today = new Date();
    currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    renderDatePicker();
}

/**
 * 渲染日期选择器
 */
function renderDatePicker() {
    const grid = document.getElementById('datePickerGrid');
    const monthYear = document.getElementById('currentMonthYear');

    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    monthYear.textContent = `${year}年${month + 1}月`;

    // 获取当月第一天和最后一天
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    // 获取当月第一天是星期几
    const startDay = firstDay.getDay();

    // 生成日历
    let html = '';

    // 添加星期标题
    const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
    weekDays.forEach(day => {
        html += `<div style="text-align:center; font-weight:bold; color:#666;">${day}</div>`;
    });

    // 添加空白日期
    for (let i = 0; i < startDay; i++) {
        html += `<div></div>`;
    }

    // 添加日期
    for (let day = 1; day <= lastDay.getDate(); day++) {
        const date = new Date(year, month, day);
        const dateStr = formatDate(date);
        const isSelected = dateStr === document.getElementById(currentDatePicker === 'start' ? 'startDate' : 'endDate').value;

        // 检查该日期是否在可用日期列表中
        const isAvailable = availableDates.includes(dateStr);

        if (isAvailable) {
            // 可用的日期，可以点击
            html += `
                <div class="date-picker-day ${isSelected ? 'selected' : ''}" onclick="selectDate('${dateStr}')">
                    ${day}
                </div>
            `;
        } else {
            // 不可用的日期，置灰且不可点击
            html += `
                <div class="date-picker-day disabled">
                    ${day}
                </div>
            `;
        }
    }

    grid.innerHTML = html;
}

/**
 * 选择日期
 */
function selectDate(dateStr) {
    const inputId = currentDatePicker === 'start' ? 'startDate' : 'endDate';
    document.getElementById(inputId).value = dateStr;
    closeDatePicker();
}

/**
 * 确认日期选择
 */
function confirmDate() {
    closeDatePicker();
}

/**
 * 切换上传区域显示
 */
function toggleUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const toggleBtn = document.getElementById('toggleUploadBtn');

    if (uploadArea.style.display === 'none') {
        uploadArea.style.display = 'block';
        toggleBtn.textContent = '收起';
    } else {
        uploadArea.style.display = 'none';
        toggleBtn.textContent = '上传';
    }
}

/**
 * 打开上传模态弹层
 */
function openUploadModal() {
    const modal = document.getElementById('uploadModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
}

/**
 * 关闭上传模态弹层
 */
function closeUploadModal() {
    const modal = document.getElementById('uploadModal');
    modal.style.display = 'none';
    modal.classList.remove('show');
}

/**
 * 打开库存上传模态弹层
 */
function openInventoryUploadModal() {
    const modal = document.getElementById('inventoryUploadModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
}

/**
 * 关闭库存上传模态弹层
 */
function closeInventoryUploadModal() {
    const modal = document.getElementById('inventoryUploadModal');
    modal.style.display = 'none';
    modal.classList.remove('show');
}

/**
 * 处理表格行点击事件
 */
function handleTableRowClick(row) {
    // 获取商品类型
    const productType = row.getAttribute('data-product-type');
    
    // 移除所有行的高亮
    const allRows = document.querySelectorAll('#tableBody tr');
    allRows.forEach(r => r.style.backgroundColor = '');
    
    // 高亮当前行
    row.style.backgroundColor = '#7ED321';
    
    // 获取日期范围
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    // 加载商品详情
    if (typeof loadProductDetails === 'function') {
        loadProductDetails(productType, startDate, endDate);
        
        // 延迟滚动，等待曲线图加载完成
        setTimeout(() => {
            const detailsSection = document.getElementById('detailsSection');
            if (detailsSection && detailsSection.style.display !== 'none') {
                // 平滑滚动到曲线图区域，让曲线图的上半部分可见
                detailsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 300); // 延迟300ms，确保曲线图已经显示
    } else {
        console.error('loadProductDetails 函数未定义');
    }
}

/**
 * 设置库存文件上传
 */
function setupInventoryFileUpload() {
    const uploadArea = document.getElementById('inventoryUploadArea');
    const fileInput = document.getElementById('inventoryFileInput');

    if (!uploadArea || !fileInput) {
        console.warn('库存上传元素未找到');
        return;
    }

    // 文件选择
    fileInput.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            handleInventoryFileUpload(file);
        }
    };

    // 拖拽上传
    uploadArea.ondragover = function(e) {
        e.preventDefault();
        uploadArea.style.background = '#f0f9ff';
    };

    uploadArea.ondragleave = function(e) {
        e.preventDefault();
        uploadArea.style.background = '';
    };

    uploadArea.ondrop = function(e) {
        e.preventDefault();
        uploadArea.style.background = '';

        const file = e.dataTransfer.files[0];
        if (file) {
            handleInventoryFileUpload(file);
        }
    };
}

/**
 * 处理库存文件上传
 */
async function handleInventoryFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const token = getToken();
        const headers = {};

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // 显示上传中状态
        const uploadResult = document.getElementById('inventoryUploadResult');
        uploadResult.style.display = 'block';
        uploadResult.querySelector('p').textContent = '正在上传库存文件...';
        uploadResult.style.color = '#666';

        // 获取CSRF token并添加到请求头
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                         document.querySelector('input[name="csrf_token"]')?.value;
        
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        const response = await fetch('/api/upload/inventory', {
            method: 'POST',
            headers: headers,
            body: formData
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

        const result = await response.json();

        if (response.ok) {
            let message = `上传完成！ 文件总行数: ${result.total} 新增记录: ${result.inserted} 更新记录: ${result.updated} 失败记录: ${result.failed}`;
            
            uploadResult.querySelector('p').textContent = message;
            // 根据失败记录数量设置颜色：有失败记录时显示红色，否则显示绿色
            if (result.failed > 0) {
                uploadResult.style.color = '#dc3545';
            } else {
                uploadResult.style.color = '#28a745';
            }

            // 检查是否有警告信息
            if (result.warning) {
                const warningDiv = document.createElement('div');
                warningDiv.style.backgroundColor = '#fff3cd';
                warningDiv.style.border = '1px solid #ffc107';
                warningDiv.style.color = '#856404';
                warningDiv.style.padding = '10px 15px';
                warningDiv.style.marginTop = '10px';
                warningDiv.style.borderRadius = '5px';
                warningDiv.textContent = '⚠️ ' + result.warning;
                uploadResult.appendChild(warningDiv);
            }


            
        } else {
            uploadResult.querySelector('p').textContent = '库存上传失败: ' + result.error;
            uploadResult.style.color = '#dc3545';
            alert('库存上传失败: ' + result.error);
        }
    } catch (error) {
        console.error('库存上传失败:', error);
        const uploadResult = document.getElementById('inventoryUploadResult');
        uploadResult.style.display = 'block';
        uploadResult.querySelector('p').textContent = '库存上传失败: ' + error.message;
        uploadResult.style.color = '#dc3545';
        alert('库存上传失败: ' + error.message);
    }
}
