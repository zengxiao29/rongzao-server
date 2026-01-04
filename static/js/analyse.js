/**
 * PC 端数据分析页面
 * 使用 analyse_common.js 提供的公共业务逻辑
 */

// 全局变量（PC 端特有）
let editingTab = null;
let currentDatePicker = null;
let currentMonth = new Date();

// 初始化
document.addEventListener('DOMContentLoaded', async function() {
    // 初始化公共逻辑
    initAnalyseCommon({
        onTabsLoaded: handleTabsLoaded,
        onDataLoaded: handleDataLoaded,
        onDateChanged: handleDateChanged,
        onTabChanged: handleTabChanged
    });

    // 设置文件上传
    setupFileUpload();

    // 加载 Tab 配置
    await loadTabConfig();

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
 * 渲染表格数据（PC 端表格形式）
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

    // 创建表格容器
    let containerHTML = `
        <div class="table-wrapper">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>商品类型</th>
                        <th>有效订购数</th>
                        <th>抖音</th>
                        <th>天猫</th>
                        <th>有赞</th>
                        <th>让利后金额</th>
                    </tr>
                </thead>
                <tbody>
    `;

    currentTabData.data.forEach(item => {
        containerHTML += `
            <tr>
                <td>${item.product_type}</td>
                <td>${item.valid_orders}</td>
                <td>${item.douyin_orders}</td>
                <td>${item.tmall_orders}</td>
                <td>${item.youzan_orders}</td>
                <td>¥${parseFloat(item.discount_amount).toFixed(2)}</td>
            </tr>
        `;
    });

    containerHTML += `
                </tbody>
            </table>
        </div>
    `;

    tableContainer.innerHTML = containerHTML;
}

// ==================== 文件上传相关（仅 PC 端） ====================

/**
 * 设置文件上传功能
 */
function setupFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const toggleUploadBtn = document.getElementById('toggleUploadBtn');

    if (!uploadArea || !fileInput || !toggleUploadBtn) {
        return;
    }

    // 切换上传区域显示
    toggleUploadBtn.onclick = function() {
        if (uploadArea.style.display === 'none') {
            uploadArea.style.display = 'block';
            toggleUploadBtn.textContent = '收起';
        } else {
            uploadArea.style.display = 'none';
            toggleUploadBtn.textContent = '上传';
        }
    };

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
        const response = await fetch('/api/upload/excel', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            const uploadResult = document.getElementById('uploadResult');
            uploadResult.style.display = 'block';
            uploadResult.querySelector('p').textContent = result.message;

            // 重新加载数据，并显示未匹配商品的提示
            await loadDataFromDb(true);
        } else {
            alert('上传失败: ' + result.error);
        }
    } catch (error) {
        console.error('上传失败:', error);
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

        html += `
            <div class="date-picker-day ${isSelected ? 'selected' : ''}" onclick="selectDate('${dateStr}')">
                ${day}
            </div>
        `;
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