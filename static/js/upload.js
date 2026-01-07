const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');

// 全局变量存储Excel数据
let excelData = null;

// 点击上传区域触发文件选择
uploadArea.addEventListener('click', (e) => {
    if (e.target.tagName !== 'BUTTON') {
        fileInput.click();
    }
});

// 文件选择处理
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
});

// 拖拽处理
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
        // 检查文件类型
        const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
        const fileName = file.name.toLowerCase();
        const isExcel = fileName.endsWith('.xlsx') || fileName.endsWith('.xls');

        if (isExcel) {
            handleFile(file);
        } else {
            alert('请上传Excel文件（.xlsx 或 .xls 格式）');
        }
    }
});

// 处理文件
function handleFile(file) {
    fileName.textContent = file.name;
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'block';

    // 在浏览器端读取Excel文件
    loadExcelFile(file);
}

// 在浏览器端加载Excel文件
function loadExcelFile(file) {
    const reader = new FileReader();

    reader.onload = function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });

            // 读取第一个工作表
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];

            // 转换为JSON数据
            excelData = XLSX.utils.sheet_to_json(worksheet);

            console.log('成功加载Excel文件，共', excelData.length, '行数据');
            console.log('数据预览:', excelData.slice(0, 3));

            // 处理数据并显示图表
            processDataAndRenderChart();
        } catch (error) {
            console.error('读取Excel文件失败:', error);
            alert('读取Excel文件失败: ' + error.message);
        }
    };

    reader.onerror = function() {
        alert('文件读取失败');
    };

    reader.readAsArrayBuffer(file);
}

// 处理数据并渲染图表
function processDataAndRenderChart() {
    console.log('开始处理数据...');
    console.log('excelData:', excelData);
    console.log('excelData长度:', excelData ? excelData.length : 0);

    if (!excelData || excelData.length === 0) {
        alert('Excel文件为空或格式不正确');
        return;
    }

    // 标准化商品名称并计算销量
    const salesMap = new Map();

    excelData.forEach(row => {
        const productName = mapProductName(row['商品名称']);
        const orderCount = Number(row['订购数']) || 0;
        const isRefunded = row['是否退款'] === '退款成功';
        const shopType = row['店铺类型'] || '未知';

        if (!productName) return;

        if (salesMap.has(productName)) {
            const current = salesMap.get(productName);
            if (isRefunded) {
                salesMap.set(productName, current - orderCount);
            } else {
                salesMap.set(productName, current + orderCount);
            }
        } else {
            if (isRefunded) {
                salesMap.set(productName, -orderCount);
            } else {
                salesMap.set(productName, orderCount);
            }
        }
    });

    // 转换为数组并排序
    const salesData = Array.from(salesMap.entries())
        .map(([name, sales]) => ({ name, sales }))
        .filter(item => item.sales > 0) // 只显示有销量的商品
        .sort((a, b) => b.sales - a.sales);

    console.log('处理后的销量数据:', salesData);

    // 统计每个商品的店铺类型信息
    const productShopInfo = new Map();
    salesData.forEach(item => {
        const shopTypes = new Set();
        excelData.forEach(row => {
            const productName = mapProductName(row['商品名称']);
            if (productName === item.name && row['店铺类型']) {
                shopTypes.add(row['店铺类型']);
            }
        });
        productShopInfo.set(item.name, Array.from(shopTypes).join(', '));
    });

    // 统计按店铺类型的订单量
    const shopOrderStats = new Map();
    excelData.forEach(row => {
        const shopType = row['店铺类型'] || '未知';
        const orderCount = Number(row['订购数']) || 0;
        const isRefunded = row['是否退款'] === '退款成功';

        if (shopOrderStats.has(shopType)) {
            const current = shopOrderStats.get(shopType);
            if (isRefunded) {
                shopOrderStats.set(shopType, current - orderCount);
            } else {
                shopOrderStats.set(shopType, current + orderCount);
            }
        } else {
            if (isRefunded) {
                shopOrderStats.set(shopType, -orderCount);
            } else {
                shopOrderStats.set(shopType, orderCount);
            }
        }
    });

    // 渲染表格（按商品统计和按店铺类型统计）
    renderTable(salesData, excelData, productShopInfo, shopOrderStats);
}

// 渲染表格
function renderTable(salesData, originalData, productShopInfo, shopOrderStats) {
    console.log('开始渲染表格，数据:', salesData);
    console.log('salesData长度:', salesData.length);

    const chartSection = document.getElementById('chartSection');
    if (!chartSection) {
        console.error('找不到容器元素');
        return;
    }
    console.log('找到chartSection元素，准备显示');
    chartSection.style.display = 'block';

    // 清空现有内容
    chartSection.innerHTML = '';

    // 创建标题
    const title = document.createElement('h2');
    title.textContent = '商品销量统计';
    chartSection.appendChild(title);

    // 创建饼图容器
    const pieChartContainer = document.createElement('div');
    pieChartContainer.style.marginTop = '30px';
    pieChartContainer.style.marginBottom = '30px';
    pieChartContainer.style.textAlign = 'center';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '800');
    svg.setAttribute('height', '500');
    svg.style.display = 'inline-block';
    pieChartContainer.appendChild(svg);
    chartSection.appendChild(pieChartContainer);

    // 绘制SVG饼图
    drawSVGPieChart(svg, salesData);

    // 创建商品分类统计模块
    createCategoryStatisticsModule(excelData);

    // 创建Tab筛选容器
    const tabContainer = document.createElement('div');
    tabContainer.style.marginTop = '20px';
    tabContainer.style.marginBottom = '20px';
    tabContainer.style.borderBottom = '2px solid #667eea';

    const filterOptions = [
        { value: 'all', text: '全部' },
        { value: 'date', text: '按付款日期' },
        { value: 'shop', text: '按店铺类型' },
        { value: 'product', text: '按商品类型' },
        { value: 'quantity', text: '按订购数' }
    ];

    filterOptions.forEach(option => {
        const tab = document.createElement('button');
        tab.textContent = option.text;
        tab.dataset.filter = option.value;
        tab.style.padding = '10px 25px';
        tab.style.border = 'none';
        tab.style.borderBottom = '3px solid transparent';
        tab.style.backgroundColor = 'transparent';
        tab.style.color = '#666';
        tab.style.cursor = 'pointer';
        tab.style.fontSize = '14px';
        tab.style.fontWeight = 'bold';
        tab.style.transition = 'all 0.3s ease';
        tab.style.marginRight = '5px';

        // 默认选中"全部"
        if (option.value === 'all') {
            tab.style.borderBottom = '3px solid #667eea';
            tab.style.color = '#667eea';
        }

        tab.onmouseover = function() {
            if (this.style.color !== 'rgb(102, 126, 234)') {
                this.style.color = '#667eea';
                this.style.backgroundColor = '#f8f9ff';
            }
        };

        tab.onmouseout = function() {
            if (this.style.color !== 'rgb(102, 126, 234)') {
                this.style.color = '#666';
                this.style.backgroundColor = 'transparent';
            }
        };

        tab.onclick = function() {
            // 更新Tab样式
            const tabs = tabContainer.querySelectorAll('button');
            tabs.forEach(t => {
                t.style.borderBottom = '3px solid transparent';
                t.style.color = '#666';
                t.style.backgroundColor = 'transparent';
            });
            this.style.borderBottom = '3px solid #667eea';
            this.style.color = '#667eea';

            // 重新渲染表格
            const filterType = this.dataset.filter;
            renderFilteredTable(productTable, productTbody, filteredData, filterType);
        };

        tabContainer.appendChild(tab);
    });

    chartSection.appendChild(tabContainer);

    // 创建商品销量表格容器
    const productTableContainer = document.createElement('div');
    productTableContainer.style.overflowX = 'auto';
    productTableContainer.style.marginTop = '20px';

    // 创建商品销量表格
    const productTable = document.createElement('table');
    productTable.style.width = '100%';
    productTable.style.borderCollapse = 'collapse';
    productTable.style.backgroundColor = 'white';

    // 创建商品销量表头
    const productThead = document.createElement('thead');
    const productHeaderRow = document.createElement('tr');
    productHeaderRow.style.backgroundColor = '#667eea';
    productHeaderRow.style.color = 'white';

    const productHeaders = ['付款日期', '店铺类型', '商品类型', '订购数'];
    productHeaders.forEach((headerText, index) => {
        const th = document.createElement('th');
        th.textContent = headerText;
        th.style.padding = '12px';
        th.style.textAlign = 'left';
        th.style.border = '1px solid #5568d3';
        if (index === 0) {
            th.style.width = '120px';
        } else if (index === 1) {
            th.style.width = '150px';
        } else if (index === 2) {
            th.style.width = 'auto';
            th.style.minWidth = '200px';
        } else {
            th.style.width = '100px';
        }
        productHeaderRow.appendChild(th);
    });

    productThead.appendChild(productHeaderRow);
    productTable.appendChild(productThead);

    // 创建商品销量表体
    const productTbody = document.createElement('tbody');

    // 显示原始数据，过滤掉退款成功的订单
    let filteredData = originalData.filter(row => row['是否退款'] !== '退款成功');

    // 初始渲染表格（显示全部）
    renderFilteredTable(productTable, productTbody, filteredData, 'all');

    // 筛选并渲染表格函数
    function renderFilteredTable(table, tbody, data, filterType) {
        // 清空表体
        tbody.innerHTML = '';

        // 根据筛选类型处理数据
        let displayData = [...data];

        if (filterType !== 'all') {
            // 按筛选类型分组并汇总
            const groupMap = new Map();

            data.forEach(row => {
                let key;
                switch (filterType) {
                    case 'date':
                        // 按付款日期分组
                        if (row['付款时间']) {
                            const dateValue = row['付款时间'];
                            if (typeof dateValue === 'number') {
                                const jsDate = new Date((dateValue - 25569) * 86400 * 1000);
                                key = jsDate.toISOString().split('T')[0];
                            } else {
                                key = row['付款时间'];
                            }
                        } else {
                            key = '无';
                        }
                        break;
                    case 'shop':
                        // 按店铺类型分组
                        key = row['店铺类型'] || '无';
                        break;
                    case 'product':
                        // 按商品类型分组
                        key = mapProductName(row['商品名称']) || row['商品名称'];
                        break;
                    case 'quantity':
                        // 按订购数分组
                        const qty = Number(row['订购数']) || 0;
                        key = qty.toString();
                        break;
                }

                if (groupMap.has(key)) {
                    groupMap.set(key, groupMap.get(key) + (Number(row['订购数']) || 0));
                } else {
                    groupMap.set(key, Number(row['订购数']) || 0);
                }
            });

            // 转换为数组
            displayData = Array.from(groupMap.entries()).map(([name, orders]) => ({
                name: name,
                orders: orders,
                filterType: filterType
            }));

            // 排序
            displayData.sort((a, b) => {
                if (filterType === 'date') {
                    // 日期降序
                    return b.name.localeCompare(a.name);
                } else if (filterType === 'quantity') {
                    // 数值降序
                    return b.orders - a.orders;
                } else {
                    // 字母顺序
                    return a.name.localeCompare(b.name);
                }
            });
        }

        // 渲染数据行
        displayData.forEach((item, index) => {
            const tr = document.createElement('tr');
            tr.style.backgroundColor = index % 2 === 0 ? '#f8f9ff' : 'white';

            if (filterType === 'all') {
                // 显示原始数据
                // 付款日期
                const dateCell = document.createElement('td');
                dateCell.style.width = '120px';
                if (item['付款时间']) {
                    const dateValue = item['付款时间'];
                    if (typeof dateValue === 'number') {
                        const jsDate = new Date((dateValue - 25569) * 86400 * 1000);
                        dateCell.textContent = jsDate.toISOString().split('T')[0];
                    } else {
                        dateCell.textContent = item['付款时间'];
                    }
                } else {
                    dateCell.textContent = '无';
                }
                dateCell.style.padding = '10px';
                dateCell.style.border = '1px solid #e0e0e0';
                dateCell.style.fontSize = '12px';
                dateCell.style.color = '#666';
                tr.appendChild(dateCell);

                // 店铺类型
                const shopCell = document.createElement('td');
                shopCell.textContent = item['店铺类型'] || '无';
                shopCell.style.padding = '10px';
                shopCell.style.border = '1px solid #e0e0e0';
                shopCell.style.width = '150px';
                shopCell.style.fontSize = '12px';
                shopCell.style.color = '#666';
                tr.appendChild(shopCell);

                // 商品类型
                const productCell = document.createElement('td');
                productCell.textContent = mapProductName(item['商品名称']) || item['商品名称'];
                productCell.style.padding = '10px';
                productCell.style.border = '1px solid #e0e0e0';
                productCell.style.width = 'auto';
                productCell.style.minWidth = '200px';
                tr.appendChild(productCell);

                // 订购数
                const orderCell = document.createElement('td');
                orderCell.textContent = item['订购数'] || 0;
                orderCell.style.padding = '10px';
                orderCell.style.textAlign = 'right';
                orderCell.style.fontWeight = 'bold';
                orderCell.style.color = '#667eea';
                orderCell.style.border = '1px solid #e0e0e0';
                orderCell.style.width = '100px';
                tr.appendChild(orderCell);
            } else {
                // 显示汇总数据
                // 第一列：显示筛选类型名称
                const filterCell = document.createElement('td');
                filterCell.style.width = '120px';

                if (filterType === 'date') {
                    filterCell.textContent = item.name;
                } else if (filterType === 'shop') {
                    filterCell.textContent = '店铺类型';
                } else if (filterType === 'product') {
                    filterCell.textContent = '商品类型';
                } else if (filterType === 'quantity') {
                    filterCell.textContent = '订购数';
                }

                filterCell.style.padding = '10px';
                filterCell.style.border = '1px solid #e0e0e0';
                filterCell.style.fontSize = '12px';
                filterCell.style.color = '#666';
                tr.appendChild(filterCell);

                // 第二列：显示分组名称
                const nameCell = document.createElement('td');
                nameCell.textContent = item.name;
                nameCell.style.padding = '10px';
                nameCell.style.border = '1px solid #e0e0e0';
                nameCell.style.width = '150px';
                nameCell.style.fontSize = '12px';
                nameCell.style.color = '#666';
                tr.appendChild(nameCell);

                // 第三列：显示汇总值
                const valueCell = document.createElement('td');
                valueCell.textContent = item.orders;
                valueCell.style.padding = '10px';
                valueCell.style.textAlign = 'right';
                valueCell.style.fontWeight = 'bold';
                valueCell.style.color = '#667eea';
                valueCell.style.border = '1px solid #e0e0e0';
                valueCell.style.width = '100px';
                tr.appendChild(valueCell);

                // 第四列：空
                const emptyCell = document.createElement('td');
                emptyCell.style.border = '1px solid #e0e0e0';
                tr.appendChild(emptyCell);
            }

            tbody.appendChild(tr);
        });
    }

    productTable.appendChild(productTbody);
    productTableContainer.appendChild(productTable);
    chartSection.appendChild(productTableContainer);

    // 创建店铺类型统计表格标题
    const shopTitle = document.createElement('h2');
    shopTitle.textContent = '按店铺类型统计订单量';
    shopTitle.style.marginTop = '40px';
    chartSection.appendChild(shopTitle);

    // 创建日期范围选择器容器
    const dateRangeContainer = document.createElement('div');
    dateRangeContainer.style.marginTop = '15px';
    dateRangeContainer.style.marginBottom = '15px';
    dateRangeContainer.style.padding = '15px';
    dateRangeContainer.style.backgroundColor = '#fff5f5';
    dateRangeContainer.style.borderRadius = '8px';
    dateRangeContainer.style.border = '1px solid #f0f0f0';
    dateRangeContainer.style.display = 'flex';
    dateRangeContainer.style.alignItems = 'center';
    dateRangeContainer.style.gap = '10px';
    dateRangeContainer.style.flexWrap = 'wrap';

    const dateLabel = document.createElement('span');
    dateLabel.textContent = '日期范围：';
    dateLabel.style.fontWeight = 'bold';
    dateLabel.style.color = '#333';
    dateRangeContainer.appendChild(dateLabel);

    // 开始日期输入
    const startDateInput = document.createElement('input');
    startDateInput.type = 'date';
    startDateInput.id = 'shopStartDate';
    startDateInput.style.padding = '8px';
    startDateInput.style.border = '1px solid #f5576c';
    startDateInput.style.borderRadius = '5px';
    startDateInput.style.fontSize = '14px';
    dateRangeContainer.appendChild(startDateInput);

    const toLabel = document.createElement('span');
    toLabel.textContent = '至';
    toLabel.style.color = '#666';
    dateRangeContainer.appendChild(toLabel);

    // 结束日期输入
    const endDateInput = document.createElement('input');
    endDateInput.type = 'date';
    endDateInput.id = 'shopEndDate';
    endDateInput.style.padding = '8px';
    endDateInput.style.border = '1px solid #f5576c';
    endDateInput.style.borderRadius = '5px';
    endDateInput.style.fontSize = '14px';
    dateRangeContainer.appendChild(endDateInput);

    // 应用按钮
    const applyButton = document.createElement('button');
    applyButton.textContent = '应用';
    applyButton.style.padding = '8px 20px';
    applyButton.style.backgroundColor = '#f5576c';
    applyButton.style.color = 'white';
    applyButton.style.border = 'none';
    applyButton.style.borderRadius = '5px';
    applyButton.style.cursor = 'pointer';
    applyButton.style.fontSize = '14px';
    applyButton.style.fontWeight = 'bold';
    applyButton.onmouseover = function() {
        this.style.backgroundColor = '#d6455e';
    };
    applyButton.onmouseout = function() {
        this.style.backgroundColor = '#f5576c';
    };
    applyButton.onclick = function() {
        updateShopTableWithDateRange(shopTbody, originalData, startDateInput.value, endDateInput.value);
    };
    dateRangeContainer.appendChild(applyButton);

    // 重置按钮
    const resetButton = document.createElement('button');
    resetButton.textContent = '重置';
    resetButton.style.padding = '8px 20px';
    resetButton.style.backgroundColor = 'white';
    resetButton.style.color = '#f5576c';
    resetButton.style.border = '2px solid #f5576c';
    resetButton.style.borderRadius = '5px';
    resetButton.style.cursor = 'pointer';
    resetButton.style.fontSize = '14px';
    resetButton.style.fontWeight = 'bold';
    resetButton.onmouseover = function() {
        this.style.backgroundColor = '#fff5f5';
    };
    resetButton.onmouseout = function() {
        this.style.backgroundColor = 'white';
    };
    resetButton.onclick = function() {
        startDateInput.value = '';
        endDateInput.value = '';
        updateShopTableWithDateRange(shopTbody, originalData, '', '');
    };
    dateRangeContainer.appendChild(resetButton);

    // 显示当前日期范围
    const dateRangeDisplay = document.createElement('span');
    dateRangeDisplay.id = 'shopDateRangeDisplay';
    dateRangeDisplay.style.marginLeft = '20px';
    dateRangeDisplay.style.padding = '5px 15px';
    dateRangeDisplay.style.backgroundColor = 'white';
    dateRangeDisplay.style.border = '1px solid #f5576c';
    dateRangeDisplay.style.borderRadius = '15px';
    dateRangeDisplay.style.fontSize = '12px';
    dateRangeDisplay.style.color = '#f5576c';
    dateRangeDisplay.textContent = '当前显示：全部日期';
    dateRangeContainer.appendChild(dateRangeDisplay);

    chartSection.appendChild(dateRangeContainer);

    // 创建店铺类型统计表格容器
    const shopTableContainer = document.createElement('div');
    shopTableContainer.style.overflowX = 'auto';
    shopTableContainer.style.marginTop = '20px';

    // 创建店铺类型统计表格
    const shopTable = document.createElement('table');
    shopTable.style.width = '100%';
    shopTable.style.borderCollapse = 'collapse';
    shopTable.style.backgroundColor = 'white';

    // 创建店铺类型统计表头
    const shopThead = document.createElement('thead');
    const shopHeaderRow = document.createElement('tr');
    shopHeaderRow.style.backgroundColor = '#f5576c';
    shopHeaderRow.style.color = 'white';

    const shopHeaders = ['日期', '店铺类型', '订单量'];
    shopHeaders.forEach((headerText, index) => {
        const th = document.createElement('th');
        th.textContent = headerText;
        th.style.padding = '12px';
        th.style.textAlign = 'left';
        th.style.border = '1px solid #d6455e';
        if (index === 0) {
            th.style.width = '200px';
        } else if (index === 1) {
            th.style.width = '200px';
        } else {
            th.style.width = '150px';
        }
        shopHeaderRow.appendChild(th);
    });

    shopThead.appendChild(shopHeaderRow);
    shopTable.appendChild(shopThead);

    // 创建店铺类型统计表体
    const shopTbody = document.createElement('tbody');

    // 初始渲染店铺类型统计表格（显示全部数据）
    updateShopTableWithDateRange(shopTbody, originalData, '', '');

    // 更新店铺类型统计表格函数
    function updateShopTableWithDateRange(tbody, data, startDate, endDate) {
        // 清空表体
        tbody.innerHTML = '';

        // 过滤数据
        let filteredData = data.filter(row => row['是否退款'] !== '退款成功');

        // 应用日期范围过滤
        if (startDate || endDate) {
            filteredData = filteredData.filter(row => {
                if (!row['付款时间']) return false;

                const dateValue = row['付款时间'];
                let rowDate;

                if (typeof dateValue === 'number') {
                    rowDate = new Date((dateValue - 25569) * 86400 * 1000);
                } else {
                    rowDate = new Date(dateValue);
                }

                const rowDateStr = rowDate.toISOString().split('T')[0];

                if (startDate && rowDateStr < startDate) return false;
                if (endDate && rowDateStr > endDate) return false;

                return true;
            });
        }

        // 统计每个店铺类型的订单量
        const shopStats = new Map();

        filteredData.forEach(row => {
            const shopType = row['店铺类型'] || '未知';
            const orderCount = Number(row['订购数']) || 0;

            if (shopStats.has(shopType)) {
                shopStats.set(shopType, shopStats.get(shopType) + orderCount);
            } else {
                shopStats.set(shopType, orderCount);
            }
        });

        // 转换为数组并排序
        const shopData = Array.from(shopStats.entries())
            .map(([name, orders]) => ({ name, orders }))
            .filter(item => item.orders > 0)
            .sort((a, b) => b.orders - a.orders);

        // 确定日期范围显示
        let dateRangeText = '全部日期';
        if (startDate && endDate) {
            dateRangeText = `${startDate} 至 ${endDate}`;
        } else if (startDate) {
            dateRangeText = `${startDate} 之后`;
        } else if (endDate) {
            dateRangeText = `${endDate} 之前`;
        }

        // 更新日期范围显示
        const displayElement = document.getElementById('shopDateRangeDisplay');
        if (displayElement) {
            displayElement.textContent = `当前显示：${dateRangeText}`;
        }

        // 渲染数据行
        shopData.forEach((item, index) => {
            const row = document.createElement('tr');
            row.style.backgroundColor = index % 2 === 0 ? '#fff5f5' : 'white';

            // 日期
            const dateCell = document.createElement('td');
            dateCell.textContent = dateRangeText;
            dateCell.style.padding = '10px';
            dateCell.style.border = '1px solid #e0e0e0';
            dateCell.style.width = '200px';
            dateCell.style.fontSize = '12px';
            dateCell.style.color = '#666';
            row.appendChild(dateCell);

            // 店铺类型
            const nameCell = document.createElement('td');
            nameCell.textContent = item.name;
            nameCell.style.padding = '10px';
            nameCell.style.border = '1px solid #e0e0e0';
            nameCell.style.width = '200px';
            row.appendChild(nameCell);

            // 订单量
            const ordersCell = document.createElement('td');
            ordersCell.textContent = item.orders;
            ordersCell.style.padding = '10px';
            ordersCell.style.textAlign = 'right';
            ordersCell.style.fontWeight = 'bold';
            ordersCell.style.color = '#f5576c';
            ordersCell.style.border = '1px solid #e0e0e0';
            ordersCell.style.width = '150px';
            row.appendChild(ordersCell);

            tbody.appendChild(row);
        });

        // 如果没有数据，显示提示
        if (shopData.length === 0) {
            const emptyRow = document.createElement('tr');
            const emptyCell = document.createElement('td');
            emptyCell.textContent = '该日期范围内无数据';
            emptyCell.colSpan = 3;
            emptyCell.style.padding = '20px';
            emptyCell.style.textAlign = 'center';
            emptyCell.style.color = '#999';
            emptyCell.style.border = '1px solid #e0e0e0';
            emptyRow.appendChild(emptyCell);
            tbody.appendChild(emptyRow);
        }
    }

    shopTable.appendChild(shopTbody);
    shopTableContainer.appendChild(shopTable);
    chartSection.appendChild(shopTableContainer);

    // 添加导出按钮
    const buttonContainer = document.createElement('div');
    buttonContainer.style.textAlign = 'right';
    buttonContainer.style.marginTop = '20px';

    const exportButton = document.createElement('button');
    exportButton.textContent = '导出Excel';
    exportButton.style.padding = '10px 30px';
    exportButton.style.backgroundColor = '#667eea';
    exportButton.style.color = 'white';
    exportButton.style.border = 'none';
    exportButton.style.borderRadius = '5px';
    exportButton.style.cursor = 'pointer';
    exportButton.style.fontSize = '14px';
    exportButton.style.fontWeight = 'bold';
    exportButton.onmouseover = function() {
        this.style.backgroundColor = '#5568d3';
    };
    exportButton.onmouseout = function() {
        this.style.backgroundColor = '#667eea';
    };

    exportButton.onclick = function() {
        exportToExcel(salesData, originalData, shopData);
    };

    buttonContainer.appendChild(exportButton);
    chartSection.appendChild(buttonContainer);

    console.log('表格渲染完成');
}

// 导出Excel函数
function exportToExcel(salesData, originalData, shopData) {
    // 创建工作簿
    const wb = XLSX.utils.book_new();

    // 准备商品销量数据（原始数据格式）
    const filteredData = originalData.filter(row => row['是否退款'] !== '退款成功');

    const productExportData = filteredData.map(row => {
        // 格式化付款日期
        let paymentDate = '无';
        if (row['付款时间']) {
            const dateValue = row['付款时间'];
            if (typeof dateValue === 'number') {
                const jsDate = new Date((dateValue - 25569) * 86400 * 1000);
                paymentDate = jsDate.toISOString().split('T')[0];
            } else {
                paymentDate = row['付款时间'];
            }
        }

        return {
            '付款日期': paymentDate,
            '店铺类型': row['店铺类型'] || '无',
            '商品类型': normalizeProductName(row['商品名称']) || row['商品名称'],
            '订购数': row['订购数'] || 0
        };
    });

    // 创建商品销量工作表
    const productWs = XLSX.utils.json_to_sheet(productExportData);
    productWs['!cols'] = [
        { wch: 12 }, // 付款日期列宽
        { wch: 15 }, // 店铺类型列宽
        { wch: 30 }, // 商品类型列宽
        { wch: 10 }  // 订购数列宽
    ];
    XLSX.utils.book_append_sheet(wb, productWs, '订单明细');

    // 创建店铺类型统计工作表
    const shopWs = XLSX.utils.json_to_sheet(shopData);
    shopWs['!cols'] = [
        { wch: 20 }, // 店铺类型列宽
        { wch: 15 }  // 订单量列宽
    ];
    XLSX.utils.book_append_sheet(wb, shopWs, '店铺类型统计');

    // 生成默认文件名（当前时间）
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hour = String(now.getHours()).padStart(2, '0');
    const minute = String(now.getMinutes()).padStart(2, '0');
    const defaultFileName = `订单统计_${year}${month}${day}_${hour}${minute}.xlsx`;

    // 导出文件
    XLSX.writeFile(wb, defaultFileName);

    alert(`已导出文件: ${defaultFileName}\n包含两个工作表：\n1. 订单明细\n2. 店铺类型统计`);
}

// 绘制SVG饼图
function drawSVGPieChart(svg, data) {
    const width = 800;
    const height = 500;
    const centerX = width / 2 - 80;
    const centerY = height / 2;
    const radius = 180;

    // 计算总销量
    const total = data.reduce((sum, item) => sum + item.sales, 0);

    // 生成颜色
    const colors = [
        '#667eea', '#f5576c', '#00f2fe', '#38f9d7',
        '#fee140', '#fed6e3', '#fecfef', '#fcb69f',
        '#c2e9fb', '#fef9d7', '#ff6b6b', '#4ecdc4'
    ];

    // 清空SVG
    svg.innerHTML = '';

    // 添加标题
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    title.setAttribute('x', centerX);
    title.setAttribute('y', 30);
    title.setAttribute('text-anchor', 'middle');
    title.setAttribute('font-size', '18');
    title.setAttribute('font-weight', 'bold');
    title.setAttribute('fill', '#333');
    title.textContent = '商品销量分布';
    svg.appendChild(title);

    // 创建扇形路径
    let startAngle = -Math.PI / 2;

    data.forEach((item, index) => {
        const sliceAngle = (item.sales / total) * 2 * Math.PI;
        const endAngle = startAngle + sliceAngle;

        // 计算扇形路径
        const x1 = centerX + radius * Math.cos(startAngle);
        const y1 = centerY + radius * Math.sin(startAngle);
        const x2 = centerX + radius * Math.cos(endAngle);
        const y2 = centerY + radius * Math.sin(endAngle);

        // 判断是否是优弧（大于180度）
        const largeArcFlag = sliceAngle > Math.PI ? 1 : 0;

        // 创建路径
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const d = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
        path.setAttribute('d', d);
        path.setAttribute('fill', colors[index % colors.length]);
        path.setAttribute('stroke', 'white');
        path.setAttribute('stroke-width', '2');
        path.style.cursor = 'pointer';
        path.style.transition = 'opacity 0.3s, transform 0.3s';

        // 添加交互事件
        path.addEventListener('mouseenter', function() {
            this.style.opacity = '0.8';
            this.style.transform = 'scale(1.05)';
            this.style.transformOrigin = `${centerX}px ${centerY}px`;

            // 显示tooltip
            showTooltip(svg, item, total, index);
        });

        path.addEventListener('mouseleave', function() {
            this.style.opacity = '1';
            this.style.transform = 'scale(1)';

            // 隐藏tooltip
            hideTooltip(svg);
        });

        svg.appendChild(path);

        // 计算标签位置
        const labelAngle = startAngle + sliceAngle / 2;
        const labelRadius = radius * 0.7;
        const labelX = centerX + Math.cos(labelAngle) * labelRadius;
        const labelY = centerY + Math.sin(labelAngle) * labelRadius;

        // 绘制百分比标签
        const percentage = ((item.sales / total) * 100).toFixed(1);
        if (percentage > 2) {
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', labelX);
            text.setAttribute('y', labelY);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'middle');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-size', '12');
            text.setAttribute('font-weight', 'bold');
            text.textContent = `${percentage}%`;
            text.style.pointerEvents = 'none';
            svg.appendChild(text);
        }

        startAngle = endAngle;
    });

    // 绘制图例
    const legendX = width - 180;
    const legendY = 60;

    data.forEach((item, index) => {
        const y = legendY + index * 30;

        // 绘制颜色方块
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', legendX);
        rect.setAttribute('y', y - 8);
        rect.setAttribute('width', 16);
        rect.setAttribute('height', 16);
        rect.setAttribute('fill', colors[index % colors.length]);
        rect.setAttribute('rx', '2');
        svg.appendChild(rect);

        // 绘制商品名称
        const displayName = item.name.length > 10 ? item.name.substring(0, 10) + '...' : item.name;
        const nameText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        nameText.setAttribute('x', legendX + 25);
        nameText.setAttribute('y', y);
        nameText.setAttribute('fill', '#333');
        nameText.setAttribute('font-size', '12');
        nameText.textContent = displayName;
        svg.appendChild(nameText);

        // 绘制销量
        const salesText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        salesText.setAttribute('x', legendX + 25);
        salesText.setAttribute('y', y + 14);
        salesText.setAttribute('fill', '#666');
        salesText.setAttribute('font-size', '11');
        salesText.textContent = `销量: ${item.sales}`;
        svg.appendChild(salesText);
    });
}

// 显示tooltip
function showTooltip(svg, item, total, index) {
    const percentage = ((item.sales / total) * 100).toFixed(2);

    // 创建tooltip组
    const tooltipGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    tooltipGroup.setAttribute('id', 'tooltip');

    // 计算tooltip位置（跟随鼠标或固定位置）
    const tooltipX = 20;
    const tooltipY = 80;

    // 创建tooltip背景
    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bg.setAttribute('x', tooltipX);
    bg.setAttribute('y', tooltipY);
    bg.setAttribute('width', 200);
    bg.setAttribute('height', 80);
    bg.setAttribute('fill', 'rgba(0, 0, 0, 0.8)');
    bg.setAttribute('rx', '8');
    bg.setAttribute('ry', '8');
    tooltipGroup.appendChild(bg);

    // 创建商品名称文本
    const nameText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    nameText.setAttribute('x', tooltipX + 15);
    nameText.setAttribute('y', tooltipY + 25);
    nameText.setAttribute('fill', 'white');
    nameText.setAttribute('font-size', '14');
    nameText.setAttribute('font-weight', 'bold');
    nameText.textContent = item.name;
    tooltipGroup.appendChild(nameText);

    // 创建销量文本
    const salesText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    salesText.setAttribute('x', tooltipX + 15);
    salesText.setAttribute('y', tooltipY + 45);
    salesText.setAttribute('fill', '#ccc');
    salesText.setAttribute('font-size', '12');
    salesText.textContent = `销量: ${item.sales}`;
    tooltipGroup.appendChild(salesText);

    // 创建占比文本
    const percentText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    percentText.setAttribute('x', tooltipX + 15);
    percentText.setAttribute('y', tooltipY + 65);
    percentText.setAttribute('fill', '#ccc');
    percentText.setAttribute('font-size', '12');
    percentText.textContent = `占比: ${percentage}%`;
    tooltipGroup.appendChild(percentText);

    svg.appendChild(tooltipGroup);
}

// 隐藏tooltip
function hideTooltip(svg) {
    const tooltip = svg.querySelector('#tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// 商品名称标准化函数（需要在全局作用域）
function normalizeProductName(name) {
    if (!name) return '';
    name = String(name);

    // 特殊规则1: 所有以"航母岗位章"开头的商品 -> 航母岗位章
    if (name.startsWith('航母岗位章')) {
        return '航母岗位章';
    }

    // 特殊规则2: 所有以"舰载熊猫公仔"开头的商品 -> 舰载熊猫公仔
    if (name.startsWith('舰载熊猫公仔')) {
        return '舰载熊猫公仔';
    }

    // 特殊规则3: 所有以"王牌飞行系列头盔章"开头的商品 -> 王牌飞行系列头盔章
    if (name.startsWith('王牌飞行系列头盔章')) {
        return '王牌飞行系列头盔章';
    }

    // 特殊规则4: 所有以"舰载熊猫挂件"开头的商品 -> 舰载熊猫挂件
    if (name.startsWith('舰载熊猫挂件')) {
        return '舰载熊猫挂件';
    }

    // 特殊规则5: 所有以"荣造共和国天空系列"开头的商品 -> 荣造共和国天空系列
    if (name.startsWith('荣造共和国天空系列')) {
        return '荣造共和国天空系列';
    }

    // 特殊规则6: 所有以"舰载飞行头盔包"开头的商品 -> 舰载飞行头盔包
    if (name.startsWith('舰载飞行头盔包')) {
        return '舰载飞行头盔包';
    }

    // 特殊规则7: 钢笔EF-舰载熊猫礼盒-黑 -> 钢笔EF-舰载熊猫礼盒（去掉末尾的-黑等颜色）
    if (name.includes('钢笔EF-舰载熊猫礼盒')) {
        // 移除末尾的 -黑、-白、-灰等颜色后缀
        name = name.replace(/-黑$/, '');
        name = name.replace(/-白$/, '');
        name = name.replace(/-灰$/, '');
        name = name.replace(/-蓝$/, '');
    }

    // 通用规则1: 移除 -- 后面的内容
    name = name.replace(/--.*/, '');

    // 通用规则2: 移除 - 后面跟着数字或字母的内容（尺码）
    name = name.replace(/-\s*\d+[A-Za-z]*/, '');
    name = name.replace(/-\s*[A-Za-z]+$/, ''); // 只移除末尾的字母

    // 通用规则3: 移除末尾的数字+单位（如 58CM）
    name = name.replace(/\d+CM$/, '');
    name = name.replace(/\d+$/, '');

    return name.trim();
}

// 移除文件
function removeFile() {
    fileInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    excelData = null;

    // 隐藏图表
    const chartSection = document.getElementById('chartSection');
    chartSection.style.display = 'none';

    // 销毁图表
    if (window.salesChart && typeof window.salesChart.destroy === 'function') {
        window.salesChart.destroy();
        window.salesChart = null;
    }
}

// 创建商品分类统计模块
function createCategoryStatisticsModule(excelData) {
    const chartSection = document.getElementById('chartSection');
    if (!chartSection) return;

    // 创建模块标题
    const categoryTitle = document.createElement('h2');
    categoryTitle.textContent = '商品分类统计';
    categoryTitle.style.marginTop = '40px';
    categoryTitle.style.marginBottom = '20px';
    categoryTitle.style.color = '#333';
    chartSection.appendChild(categoryTitle);

    // 定义分类
    const categories = [
        { name: '夹克', keyword: '夹克' },
        { name: '帽子', keyword: '帽' },
        { name: '包', keyword: '包' },
        { name: '羽绒服', keyword: '羽绒服' },
        { name: '章', keyword: '章' },
        { name: '舰载熊猫', keyword: '舰载熊猫' }
    ];

    // 创建Tab容器
    const categoryTabContainer = document.createElement('div');
    categoryTabContainer.style.display = 'flex';
    categoryTabContainer.style.gap = '10px';
    categoryTabContainer.style.marginBottom = '20px';
    categoryTabContainer.style.borderBottom = '2px solid #f5576c';
    categoryTabContainer.style.paddingBottom = '10px';

    // 创建Tab按钮
    const tabs = [];
    categories.forEach((category, index) => {
        const tab = document.createElement('button');
        tab.textContent = category.name;
        tab.style.padding = '10px 25px';
        tab.style.border = 'none';
        tab.style.borderBottom = '3px solid transparent';
        tab.style.backgroundColor = 'transparent';
        tab.style.color = '#666';
        tab.style.cursor = 'pointer';
        tab.style.fontSize = '14px';
        tab.style.fontWeight = 'bold';
        tab.style.transition = 'all 0.3s ease';
        tab.style.marginRight = '5px';

        // 默认选中第一个tab
        if (index === 0) {
            tab.style.borderBottom = '3px solid #f5576c';
            tab.style.color = '#f5576c';
        }

        tab.onmouseover = function() {
            if (this.style.color !== 'rgb(245, 87, 108)') {
                this.style.color = '#f5576c';
                this.style.backgroundColor = '#fff5f5';
            }
        };

        tab.onmouseout = function() {
            if (this.style.color !== 'rgb(245, 87, 108)') {
                this.style.color = '#666';
                this.style.backgroundColor = 'transparent';
            }
        };

        tab.onclick = function() {
            // 更新Tab样式
            tabs.forEach(t => {
                t.style.borderBottom = '3px solid transparent';
                t.style.color = '#666';
                t.style.backgroundColor = 'transparent';
            });
            this.style.borderBottom = '3px solid #f5576c';
            this.style.color = '#f5576c';

            // 更新表格数据
            renderCategoryTable(categoryTable, categoryTbody, excelData, category.keyword);
        };

        categoryTabContainer.appendChild(tab);
        tabs.push(tab);
    });

    chartSection.appendChild(categoryTabContainer);

    // 创建表格容器
    const categoryTableContainer = document.createElement('div');
    categoryTableContainer.style.overflowX = 'auto';

    // 创建表格
    const categoryTable = document.createElement('table');
    categoryTable.style.width = '100%';
    categoryTable.style.borderCollapse = 'collapse';
    categoryTable.style.backgroundColor = 'white';

    // 创建表头
    const categoryThead = document.createElement('thead');
    const categoryHeaderRow = document.createElement('tr');
    categoryHeaderRow.style.backgroundColor = '#f5576c';
    categoryHeaderRow.style.color = 'white';

    const categoryHeaders = ['商品名称', '有效订购数', '让利后金额'];
    categoryHeaders.forEach((headerText, index) => {
        const th = document.createElement('th');
        th.textContent = headerText;
        th.style.padding = '12px';
        th.style.textAlign = 'left';
        th.style.border = '1px solid #d6455e';
        if (index === 0) {
            th.style.width = 'auto';
            th.style.minWidth = '250px';
        } else if (index === 1) {
            th.style.width = '120px';
        } else {
            th.style.width = '150px';
        }
        categoryHeaderRow.appendChild(th);
    });

    categoryThead.appendChild(categoryHeaderRow);
    categoryTable.appendChild(categoryThead);

    // 创建表体
    const categoryTbody = document.createElement('tbody');

    categoryTable.appendChild(categoryTbody);
    categoryTableContainer.appendChild(categoryTable);
    chartSection.appendChild(categoryTableContainer);

    // 初始渲染第一个分类的数据
    renderCategoryTable(categoryTable, categoryTbody, excelData, categories[0].keyword);
}

// 渲染分类表格
function renderCategoryTable(table, tbody, data, keyword) {
    // 清空表体
    tbody.innerHTML = '';

    // 过滤包含关键词的商品（排除退款成功的订单）
    const categoryProducts = new Map();

    data.forEach(row => {
        if (row['是否退款'] === '退款成功') {
            return; // 跳过退款成功的订单
        }

        const productName = mapProductName(row['商品名称']);
        if (!productName || !productName.includes(keyword)) {
            return; // 跳过不包含关键词的商品
        }

        // 特殊处理：帽子分类排除帽衫
        if (keyword === '帽' && productName.includes('帽衫')) {
            return; // 帽衫不属于帽子分类
        }

        const orderCount = Number(row['订购数']) || 0;
        const discountAmount = Number(row['让利后金额']) || 0;

        if (categoryProducts.has(productName)) {
            const current = categoryProducts.get(productName);
            current.orderCount += orderCount;
            current.discountAmount += discountAmount;
        } else {
            categoryProducts.set(productName, {
                orderCount: orderCount,
                discountAmount: discountAmount
            });
        }
    });

    // 转换为数组并排序（按有效订购数降序）
    const sortedProducts = Array.from(categoryProducts.entries())
        .map(([name, stats]) => ({
            name: name,
            orderCount: stats.orderCount,
            discountAmount: stats.discountAmount
        }))
        .sort((a, b) => b.orderCount - a.orderCount);

    // 渲染数据行
    sortedProducts.forEach((item, index) => {
        const row = document.createElement('tr');
        row.style.backgroundColor = index % 2 === 0 ? '#fff5f5' : 'white';

        // 商品名称
        const nameCell = document.createElement('td');
        nameCell.textContent = item.name;
        nameCell.style.padding = '10px';
        nameCell.style.border = '1px solid #e0e0e0';
        row.appendChild(nameCell);

        // 有效订购数
        const orderCell = document.createElement('td');
        orderCell.textContent = item.orderCount;
        orderCell.style.padding = '10px';
        orderCell.style.textAlign = 'right';
        orderCell.style.fontWeight = 'bold';
        orderCell.style.color = '#f5576c';
        orderCell.style.border = '1px solid #e0e0e0';
        row.appendChild(orderCell);

        // 让利后金额
        const amountCell = document.createElement('td');
        amountCell.textContent = item.discountAmount.toFixed(2);
        amountCell.style.padding = '10px';
        amountCell.style.textAlign = 'right';
        amountCell.style.fontWeight = 'bold';
        amountCell.style.color = '#667eea';
        amountCell.style.border = '1px solid #e0e0e0';
        row.appendChild(amountCell);

        tbody.appendChild(row);
    });

    // 如果没有数据，显示提示
    if (sortedProducts.length === 0) {
        const emptyRow = document.createElement('tr');
        const emptyCell = document.createElement('td');
        emptyCell.textContent = `该分类下暂无数据`;
        emptyCell.colSpan = 3;
        emptyCell.style.padding = '20px';
        emptyCell.style.textAlign = 'center';
        emptyCell.style.color = '#999';
        emptyCell.style.border = '1px solid #e0e0e0';
        emptyRow.appendChild(emptyCell);
        tbody.appendChild(emptyRow);
    }
}