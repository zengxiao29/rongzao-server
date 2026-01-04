// 全局变量
let tabsConfig = [];
let currentTab = null;
let editingTab = null;
let availableDates = []; // 可用的付款时间日期
let currentDatePicker = null; // 当前打开的日期选择器（'start' 或 'end'）
let selectedStartDate = null; // 选中的开始日期
let selectedEndDate = null; // 选中的结束日期
let currentMonth = new Date(); // 当前显示的月份

// 初始化
document.addEventListener('DOMContentLoaded', async function() {
    loadTabConfig();
    setupFileUpload();
    // 加载可用的日期
    await loadAvailableDates();
    // 自动设置为最近一个月的数据
    await setQuickDateRange(30);
});

// 从数据库加载数据
async function loadDataFromDb() {
    try {
        const response = await fetch('/api/analyse/data');
        const data = await response.json();

        if (response.ok) {
            window.tabData = data.tabs;
            document.getElementById('tabSection').style.display = 'block';
            document.getElementById('dateFilterSection').style.display = 'block';
            renderTableData(data.tabs);

            // 检查是否有未匹配的商品
            if (data.unmatched_products && data.unmatched_products.length > 0) {
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

// 显示未匹配商品的弹窗提示
function showUnmatchedProductsAlert(unmatchedProducts) {
    const message = `以下商品名称未在ProductInfo表中找到匹配的映射规则：\n\n${unmatchedProducts.join('\n')}\n\n请在ProductInfo表中添加对应的mapped_title字段。`;
    alert(message);
}

// 加载 Tab 配置
async function loadTabConfig() {
    try {
        const response = await fetch('/api/analyse/config');
        const data = await response.json();
        tabsConfig = data.tabs || [];
        renderTabs();
    } catch (error) {
        console.error('加载 Tab 配置失败:', error);
    }
}

// 渲染 Tab 按钮
function renderTabs() {
    const tabContainer = document.getElementById('tabContainer');
    const existingTabs = tabContainer.querySelectorAll('.tab-button:not(.tab-actions button)');
    existingTabs.forEach(tab => tab.remove());

    tabsConfig.forEach((tab, index) => {
        const tabButton = document.createElement('button');
        tabButton.className = 'tab-button';
        tabButton.textContent = tab.name;
        tabButton.dataset.index = index;

        if (index === 0) {
            tabButton.classList.add('active');
            currentTab = index;
        }

        tabButton.onclick = function() {
            switchTab(index);
        };

        // 插入到 tab-actions 之前
        const tabActions = tabContainer.querySelector('.tab-actions');
        tabContainer.insertBefore(tabButton, tabActions);
    });

    // 如果没有 Tab，显示空状态
    if (tabsConfig.length === 0) {
        document.getElementById('tableContainer').innerHTML = `
            <div class="empty-state">
                <div style="font-size: 3rem;">📊</div>
                <p>请先添加 Tab 配置，然后点击"刷新数据"按钮</p>
            </div>
        `;
    }
}

// 切换 Tab
function switchTab(index) {
    currentTab = index;

    // 更新 Tab 按钮样式
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach((button, i) => {
        if (i === index) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });

    // 如果已有数据，重新渲染表格
    if (window.tabData) {
        renderTableData(window.tabData);
    }
}

// 设置文件上传
function setupFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');

    uploadArea.addEventListener('click', (e) => {
        if (e.target.tagName !== 'BUTTON') {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');

        const file = e.dataTransfer.files[0];
        if (file) {
            const fileName = file.name.toLowerCase();
            const isExcel = fileName.endsWith('.xlsx') || fileName.endsWith('.xls');

            if (isExcel) {
                handleFile(file);
            } else {
                alert('请上传Excel文件（.xlsx 或 .xls 格式）');
            }
        }
    });
}

// 切换上传区域的显示/隐藏
function toggleUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        if (uploadArea.style.display === 'none') {
            uploadArea.style.display = 'block';
        } else {
            uploadArea.style.display = 'none';
        }
    }
}

// 处理文件
function handleFile(file) {
    // 直接上传文件，不显示文件信息
    uploadExcelFile(file);
}

// 上传 Excel 文件到数据库
async function uploadExcelFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/analyse/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
                    // 显示上传结果
                    const resultDiv = document.getElementById('uploadResult');
                    const resultText = document.getElementById('uploadResultText');
                    
                    resultText.innerHTML = `
                        <strong>上传完成！</strong>&nbsp;&nbsp;&nbsp;总记录数: ${data.total}&nbsp;&nbsp;&nbsp;成功插入: ${data.success_count}&nbsp;&nbsp;&nbsp;重复忽略: ${data.duplicate_count}&nbsp;&nbsp;&nbsp;过滤忽略: ${data.filtered_count}&nbsp;&nbsp;&nbsp;错误: ${data.error_count}
                    `;            resultDiv.style.display = 'block';

            // 隐藏上传区域
            const uploadArea = document.getElementById('uploadArea');
            if (uploadArea) {
                uploadArea.style.display = 'none';
            }
            
            // 显示日期筛选区域
            document.getElementById('dateFilterSection').style.display = 'block';
            
            // 重新加载可用日期
            await loadAvailableDates();
            
            // 自动从数据库加载数据
            await loadDataFromDb();
        } else {
            alert('上传失败: ' + data.error);
        }
    } catch (error) {
        console.error('上传文件失败:', error);
        alert('上传文件失败: ' + error.message);
    }
}

// 渲染表格数据
function renderTableData(tabsData) {
    const tableContainer = document.getElementById('tableContainer');

    if (!tabsData || tabsData.length === 0) {
        tableContainer.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 3rem;">📊</div>
                <p>没有数据可显示</p>
            </div>
        `;
        return;
    }

    // 显示当前选中的 Tab 数据
    const currentTabData = tabsData[currentTab] || tabsData[0];

    if (!currentTabData || !currentTabData.data || currentTabData.data.length === 0) {
        tableContainer.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 3rem;">📊</div>
                <p>该 Tab 下没有数据</p>
            </div>
        `;
        return;
    }

    // 创建表格容器，包含编辑按钮
    let containerHTML = `
        <div class="table-wrapper">
            <div class="table-header">
                <button class="table-edit-button" onclick="openEditTabModal()">✎</button>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>商品类型</th>
                        <th>有效订购数</th>
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
                <td>${item.discount_amount.toFixed(2)}</td>
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

// 打开新增 Tab 弹窗
function openAddTabModal() {
    editingTab = null;
    document.getElementById('modalTitle').textContent = '新增 Tab';
    document.getElementById('tabName').value = '';

    // 清空映射配置
    const mappingsContainer = document.getElementById('mappingsContainer');
    mappingsContainer.innerHTML = `
        <div class="mapping-row">
            <input type="text" class="product-input" placeholder="商品名称" />
            <input type="text" class="type-input" placeholder="商品类型名称" />
            <button class="remove-mapping" onclick="removeMapping(this)">删除</button>
        </div>
    `;

    document.getElementById('tabModal').classList.add('show');
}

// 打开编辑 Tab 弹窗
function openEditTabModal(index) {
    if (index === undefined) {
        index = currentTab;
    }

    if (index === null || !tabsConfig[index]) {
        alert('请先选择一个 Tab');
        return;
    }

    editingTab = index;
    const tab = tabsConfig[index];

    document.getElementById('modalTitle').textContent = '编辑 Tab';
    document.getElementById('tabName').value = tab.name;

    // 填充映射配置
    const mappingsContainer = document.getElementById('mappingsContainer');
    mappingsContainer.innerHTML = '';

    tab.mappings.forEach(mapping => {
        addMappingRow(mapping.product, mapping.type);
    });

    // 如果没有映射，添加一个空行
    if (tab.mappings.length === 0) {
        addMappingRow();
    }

    document.getElementById('tabModal').classList.add('show');
}

// 添加映射行
function addMapping() {
    addMappingRow();
}

function addMappingRow(product = '', type = '') {
    const mappingsContainer = document.getElementById('mappingsContainer');
    const row = document.createElement('div');
    row.className = 'mapping-row';
    row.innerHTML = `
        <input type="text" class="product-input" placeholder="商品名称" value="${product}" />
        <input type="text" class="type-input" placeholder="商品类型名称" value="${type}" />
        <button class="remove-mapping" onclick="removeMapping(this)">删除</button>
    `;
    mappingsContainer.appendChild(row);
}

// 删除映射行
function removeMapping(button) {
    const mappingsContainer = document.getElementById('mappingsContainer');
    if (mappingsContainer.children.length > 1) {
        button.parentElement.remove();
    } else {
        alert('至少保留一个映射配置');
    }
}

// 关闭弹窗
function closeModal() {
    document.getElementById('tabModal').classList.remove('show');
}

// 保存 Tab 配置
async function saveTabConfig() {
    const tabName = document.getElementById('tabName').value.trim();

    if (!tabName) {
        alert('请输入 Tab 名称');
        return;
    }

    // 获取映射配置
    const mappingRows = document.querySelectorAll('.mapping-row');
    const mappings = [];

    mappingRows.forEach(row => {
        const product = row.querySelector('.product-input').value.trim();
        const type = row.querySelector('.type-input').value.trim();

        if (product && type) {
            mappings.push({ product, type });
        }
    });

    if (mappings.length === 0) {
        alert('请至少添加一个商品映射配置');
        return;
    }

    const tabData = {
        name: tabName,
        mappings: mappings
    };

    if (editingTab !== null) {
        // 编辑现有 Tab
        tabsConfig[editingTab] = tabData;
    } else {
        // 新增 Tab
        tabsConfig.push(tabData);
    }

    // 保存到服务器
    try {
        const response = await fetch('/api/analyse/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tabs: tabsConfig })
        });

        const data = await response.json();

        if (response.ok) {
            renderTabs();
            closeModal();

            // 从数据库重新加载数据
            await loadDataFromDb();

            alert('保存成功');
        } else {
            alert('保存失败: ' + data.error);
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败: ' + error.message);
    }
}

// 删除 Tab
async function deleteTab(index) {
    if (index === undefined) {
        index = currentTab;
    }

    if (index === null || !tabsConfig[index]) {
        alert('请先选择一个 Tab');
        return;
    }

    if (!confirm(`确定要删除 Tab "${tabsConfig[index].name}" 吗？`)) {
        return;
    }

    tabsConfig.splice(index, 1);
    currentTab = tabsConfig.length > 0 ? 0 : null;

    // 保存到服务器
    try {
        const response = await fetch('/api/analyse/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tabs: tabsConfig })
        });

        const data = await response.json();

        if (response.ok) {
            renderTabs();
            // 从数据库重新加载数据
            await loadDataFromDb();
            alert('删除成功');
        } else {
            alert('删除失败: ' + data.error);
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败: ' + error.message);
    }
}

// 加载可用的付款时间日期
async function loadAvailableDates() {
    try {
        const response = await fetch('/api/db/dates');
        const data = await response.json();

        if (response.ok) {
            availableDates = data.dates || [];
            console.log('加载到可用日期:', availableDates);
        } else {
            console.error('加载可用日期失败:', data.error);
        }
    } catch (error) {
        console.error('加载可用日期失败:', error);
    }
}

// 打开日期选择器
function openDatePicker(type) {
    console.log('===== openDatePicker 开始 =====');
    console.log('type:', type);
    console.log('selectedStartDate:', selectedStartDate);
    console.log('selectedEndDate:', selectedEndDate);
    console.log('currentMonth before:', currentMonth);
    
    currentDatePicker = type;
    
    // 如果已有选择的日期，设置当前月份为选择日期的月份
    if (type === 'start' && selectedStartDate) {
        currentMonth = new Date(selectedStartDate);
        console.log('使用selectedStartDate设置月份:', selectedStartDate);
    } else if (type === 'end' && selectedEndDate) {
        currentMonth = new Date(selectedEndDate);
        console.log('使用selectedEndDate设置月份:', selectedEndDate);
    } else {
        // 否则，定位到最后可选日期所在的月份
        if (availableDates.length > 0) {
            const lastAvailableDate = availableDates[availableDates.length - 1];
            currentMonth = new Date(lastAvailableDate);
            console.log('使用最后可用日期设置月份:', lastAvailableDate);
        } else {
            currentMonth = new Date();
            console.log('使用当前日期设置月份');
        }
    }
    
    console.log('currentMonth after:', currentMonth);
    
    renderDatePicker();
    document.getElementById('datePickerModal').classList.add('show');
    console.log('===== openDatePicker 结束 =====');
}

// 关闭日期选择器
function closeDatePicker() {
    document.getElementById('datePickerModal').classList.remove('show');
}

// 渲染日期选择器
function renderDatePicker() {
    console.log('===== renderDatePicker 开始 =====');
    console.log('currentDatePicker:', currentDatePicker);
    console.log('selectedStartDate:', selectedStartDate);
    console.log('selectedEndDate:', selectedEndDate);
    console.log('currentMonth:', currentMonth);
    
    const grid = document.getElementById('datePickerGrid');
    const monthYearSpan = document.getElementById('currentMonthYear');
    
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
    monthYearSpan.textContent = `${year}年 ${monthNames[month]}`;
    
    // 获取当月第一天和最后一天
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDayOfWeek = firstDay.getDay(); // 0=周日, 1=周一, ...
    
    // 生成日历网格
    let html = '';
    
    // 添加星期标题
    const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
    weekDays.forEach(day => {
        html += `<div class="date-picker-day" style="background:#667eea;color:white;cursor:default;">${day}</div>`;
    });
    
    // 添加空白格子（填充月初）
    for (let i = 0; i < startDayOfWeek; i++) {
        html += `<div class="date-picker-day disabled"></div>`;
    }
    
    // 添加日期
    let selectedDateCount = 0;
    
    for (let day = 1; day <= lastDay.getDate(); day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isAvailable = availableDates.includes(dateStr);
        const isSelected = (currentDatePicker === 'start' && selectedStartDate === dateStr) || 
                           (currentDatePicker === 'end' && selectedEndDate === dateStr);
        
        if (isSelected) {
            selectedDateCount++;
            console.log('找到选中的日期:', dateStr, 'currentDatePicker:', currentDatePicker);
        }
        
        let classes = 'date-picker-day';
        if (!isAvailable) {
            classes += ' disabled';
        }
        if (isSelected) {
            classes += ' selected';
        }
        
        html += `<div class="${classes}" data-date="${dateStr}" onclick="${isAvailable ? `selectDate('${dateStr}')` : ''}">${day}</div>`;
    }
    
    grid.innerHTML = html;
    
    console.log('选中的日期数量:', selectedDateCount);
    console.log('===== renderDatePicker 结束 =====');
}

// 选择日期
function selectDate(dateStr) {
    if (currentDatePicker === 'start') {
        selectedStartDate = dateStr;
    } else {
        selectedEndDate = dateStr;
    }
    renderDatePicker();
}

// 切换月份
function changeMonth(delta) {
    currentMonth.setMonth(currentMonth.getMonth() + delta);
    renderDatePicker();
}

// 确认日期选择
function confirmDate() {
    if (currentDatePicker === 'start' && selectedStartDate) {
        document.getElementById('startDate').value = selectedStartDate;
    } else if (currentDatePicker === 'end' && selectedEndDate) {
        document.getElementById('endDate').value = selectedEndDate;
    }
    closeDatePicker();
}

// 应用日期筛选
async function applyDateFilter(showAlert = true) {
    if (!selectedStartDate || !selectedEndDate) {
        if (showAlert) {
            alert('请先选择开始日期和结束日期');
        }
        return;
    }
    
    if (selectedStartDate > selectedEndDate) {
        alert('开始日期不能晚于结束日期');
        return;
    }
    
    try {
        const response = await fetch('/api/analyse/data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                startDate: selectedStartDate,
                endDate: selectedEndDate
            })
        });

        const data = await response.json();

        if (response.ok) {
            window.tabData = data.tabs;
            renderTableData(data.tabs);
        } else {
            alert('应用筛选失败: ' + data.error);
        }
    } catch (error) {
        console.error('应用筛选失败:', error);
        alert('应用筛选失败: ' + error.message);
    }
}

// 重置日期筛选
async function resetDateFilter() {
    selectedStartDate = null;
    selectedEndDate = null;
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    
    // 重新加载所有数据
    await loadDataFromDb();
}

// 设置当前周的日期范围（周日到周六）
async function setCurrentWeek() {
    console.log('===== setCurrentWeek 开始 =====');
    
    if (availableDates.length === 0) {
        alert('数据库中没有可用日期数据');
        console.log('数据库中没有可用日期数据，跳过设置当前周');
        return;
    }
    
    // 确保dateFilterSection是可见的
    const dateFilterSection = document.getElementById('dateFilterSection');
    if (dateFilterSection && dateFilterSection.style.display === 'none') {
        dateFilterSection.style.display = 'block';
    }
    
    // 确保tabSection是可见的
    const tabSection = document.getElementById('tabSection');
    if (tabSection && tabSection.style.display === 'none') {
        tabSection.style.display = 'block';
    }
    
    // 获取今天
    const today = new Date();
    const todayDay = today.getDay(); // 0=周日, 1=周一, ..., 6=周六
    
    // 计算本周日（开始日期）
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - todayDay);
    
    // 计算本周六（结束日期）
    const endDate = new Date(today);
    endDate.setDate(today.getDate() + (6 - todayDay));
    
    // 格式化日期为 YYYY-MM-DD
    const formatDate = (date) => {
        if (!(date instanceof Date) || isNaN(date.getTime())) {
            console.error('formatDate接收到无效的日期对象');
            return '';
        }
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    // 设置选中的日期
    selectedStartDate = formatDate(startDate);
    selectedEndDate = formatDate(endDate);
    
    console.log('当前周日期范围:', selectedStartDate, '到', selectedEndDate);
    console.log('selectedStartDate:', selectedStartDate);
    console.log('selectedEndDate:', selectedEndDate);
    
    // 等待一小段时间确保DOM更新
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // 更新输入框显示
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput) {
        startDateInput.value = selectedStartDate;
        console.log('开始日期输入框已更新:', selectedStartDate);
    } else {
        console.error('找不到开始日期输入框');
    }
    
    if (endDateInput) {
        endDateInput.value = selectedEndDate;
        console.log('结束日期输入框已更新:', selectedEndDate);
    } else {
        console.error('找不到结束日期输入框');
    }
    
    // 应用日期筛选
    await applyDateFilter();
    
    console.log('===== setCurrentWeek 结束 =====');
}

// 设置快捷日期范围
async function setQuickDateRange(days, showAlert = true) {
    console.log('===== setQuickDateRange 开始 =====');
    console.log('参数:', days);
    console.log('availableDates:', availableDates);
    console.log('availableDates.length:', availableDates.length);
    
    if (availableDates.length === 0) {
        if (showAlert) {
            alert('数据库中没有可用日期数据');
        }
        console.log('数据库中没有可用日期数据，跳过设置快捷日期范围');
        return;
    }
    
    // 确保dateFilterSection是可见的
    const dateFilterSection = document.getElementById('dateFilterSection');
    console.log('dateFilterSection:', dateFilterSection);
    console.log('dateFilterSection.style.display:', dateFilterSection ? dateFilterSection.style.display : 'not found');
    
    if (dateFilterSection && dateFilterSection.style.display === 'none') {
        console.log('dateFilterSection是隐藏的，设置为可见');
        dateFilterSection.style.display = 'block';
    }
    
    // 确保tabSection是可见的
    const tabSection = document.getElementById('tabSection');
    console.log('tabSection:', tabSection);
    console.log('tabSection.style.display:', tabSection ? tabSection.style.display : 'not found');
    
    if (tabSection && tabSection.style.display === 'none') {
        console.log('tabSection是隐藏的，设置为可见');
        tabSection.style.display = 'block';
    }
    
    // 获取最后有数据的日期作为结束日期
    const lastAvailableDate = availableDates[availableDates.length - 1];
    console.log('最后可用日期:', lastAvailableDate);
    console.log('最后可用日期类型:', typeof lastAvailableDate);
    
    // 计算开始日期（往前推days-1天，包含截止日期）
    const endDate = new Date(lastAvailableDate);
    console.log('endDate:', endDate);
    console.log('endDate类型:', typeof endDate);
    console.log('endDate是否有效:', !isNaN(endDate.getTime()));
    
    if (isNaN(endDate.getTime())) {
        console.error('endDate是无效的日期');
        alert('无效的日期格式');
        return;
    }
    
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - (days - 1));
    
    console.log('startDate:', startDate);
    console.log('startDate是否有效:', !isNaN(startDate.getTime()));
    
    // 格式化日期为 YYYY-MM-DD
    const formatDate = (date) => {
        console.log('formatDate接收到的参数:', date);
        console.log('formatDate接收到的参数类型:', typeof date);
        
        if (!(date instanceof Date) || isNaN(date.getTime())) {
            console.error('formatDate接收到无效的日期对象');
            return '';
        }
        
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    
    // 设置选中的日期
    selectedStartDate = formatDate(startDate);
    selectedEndDate = formatDate(endDate);
    
    console.log('计算出的日期范围:', selectedStartDate, '到', selectedEndDate);
    console.log('日期范围天数:', days, '天（包含截止日期）');
    console.log('selectedStartDate:', selectedStartDate);
    console.log('selectedEndDate:', selectedEndDate);
    
    // 等待一小段时间确保DOM更新
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // 更新输入框显示
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    console.log('startDateInput:', startDateInput);
    console.log('endDateInput:', endDateInput);
    
    if (!startDateInput) {
        console.error('找不到startDate输入框元素');
        alert('找不到开始日期输入框');
        return;
    }
    
    if (!endDateInput) {
        console.error('找不到endDate输入框元素');
        alert('找不到结束日期输入框');
        return;
    }
    
    // 设置输入框的值
    startDateInput.setAttribute('value', selectedStartDate);
    endDateInput.setAttribute('value', selectedEndDate);
    startDateInput.value = selectedStartDate;
    endDateInput.value = selectedEndDate;
    
    console.log('设置后的startDateInput.value:', startDateInput.value);
    console.log('设置后的startDateInput.getAttribute("value"):', startDateInput.getAttribute('value'));
    console.log('设置后的endDateInput.value:', endDateInput.value);
    console.log('设置后的endDateInput.getAttribute("value"):', endDateInput.getAttribute('value'));
    
    // 检查设置是否成功
    if (startDateInput.value !== selectedStartDate) {
        console.error('startDate输入框值设置失败');
        console.error('期望值:', selectedStartDate);
        console.error('实际值:', startDateInput.value);
    } else {
        console.log('startDate输入框值设置成功');
    }
    
    if (endDateInput.value !== selectedEndDate) {
        console.error('endDate输入框值设置失败');
        console.error('期望值:', selectedEndDate);
        console.error('实际值:', endDateInput.value);
    } else {
        console.log('endDate输入框值设置成功');
    }
    
    // 强制触发input事件，确保值被正确设置
    startDateInput.dispatchEvent(new Event('input', { bubbles: true }));
    endDateInput.dispatchEvent(new Event('input', { bubbles: true }));
    
    // 强制触发change事件
    startDateInput.dispatchEvent(new Event('change', { bubbles: true }));
    endDateInput.dispatchEvent(new Event('change', { bubbles: true }));
    
    console.log('===== 准备调用applyDateFilter =====');
    
    // 等待一小段时间确保DOM更新
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // 自动应用筛选
    await applyDateFilter(showAlert);
    
    console.log('===== applyDateFilter调用完成 =====');
}

// 导出周报
async function exportWeeklyReport() {
    console.log('===== exportWeeklyReport 开始 =====');
    
    try {
        // 计算当前自然周（周日到周六）
        const today = new Date();
        const dayOfWeek = today.getDay(); // 0=周日, 1=周一, ..., 6=周六
        
        // 计算本周日（如果是周日，就是今天；否则往前推到周日）
        const sunday = new Date(today);
        sunday.setDate(today.getDate() - dayOfWeek);
        
        // 计算本周六
        const saturday = new Date(sunday);
        saturday.setDate(sunday.getDate() + 6);
        
        // 格式化日期为 YYYY-MM-DD
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };
        
        const startDate = formatDate(sunday);
        const endDate = formatDate(saturday);
        
        console.log('导出周报日期范围:', startDate, '到', endDate);
        
        // 调用后端API生成PDF
        const response = await fetch('/api/analyse/export-weekly-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                startDate: startDate,
                endDate: endDate
            })
        });
        
        if (response.ok) {
            // 获取PDF文件
            const blob = await response.blob();
            
            // 创建下载链接
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // 生成文件名：周报_YYYY-MM-DD_YYYY-MM-DD.pdf
            a.download = `周报_${startDate}_${endDate}.pdf`;
            
            // 触发下载
            document.body.appendChild(a);
            a.click();
            
            // 清理
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('===== exportWeeklyReport 完成 =====');
        } else {
            const data = await response.json();
            alert('导出周报失败: ' + data.error);
            console.error('导出周报失败:', data.error);
        }
    } catch (error) {
        console.error('导出周报失败:', error);
        alert('导出周报失败: ' + error.message);
    }
}

// 导出上周周报
async function exportLastWeekReport() {
    console.log('===== exportLastWeekReport 开始 =====');
    
    try {
        // 计算当前自然周（周日到周六）
        const today = new Date();
        const dayOfWeek = today.getDay(); // 0=周日, 1=周一, ..., 6=周六
        
        // 计算本周日
        const thisSunday = new Date(today);
        thisSunday.setDate(today.getDate() - dayOfWeek);
        
        // 计算上周日（本周日往前推7天）
        const lastSunday = new Date(thisSunday);
        lastSunday.setDate(thisSunday.getDate() - 7);
        
        // 计算上周六（上周日往后推6天）
        const lastSaturday = new Date(lastSunday);
        lastSaturday.setDate(lastSunday.getDate() + 6);
        
        // 格式化日期为 YYYY-MM-DD
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };
        
        const startDate = formatDate(lastSunday);
        const endDate = formatDate(lastSaturday);
        
        console.log('导出上周周报日期范围:', startDate, '到', endDate);
        
        // 调用后端API生成PDF
        const response = await fetch('/api/analyse/export-weekly-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                startDate: startDate,
                endDate: endDate
            })
        });
        
        if (response.ok) {
            // 获取PDF文件
            const blob = await response.blob();
            
            // 创建下载链接
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // 生成文件名：周报_YYYY-MM-DD_YYYY-MM-DD.pdf
            a.download = `周报_${startDate}_${endDate}.pdf`;
            
            // 触发下载
            document.body.appendChild(a);
            a.click();
            
            // 清理
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('===== exportLastWeekReport 完成 =====');
        } else {
            const data = await response.json();
            alert('导出上周周报失败: ' + data.error);
            console.error('导出上周周报失败:', data.error);
        }
    } catch (error) {
        console.error('导出上周周报失败:', error);
        alert('导出上周周报失败: ' + error.message);
    }
}