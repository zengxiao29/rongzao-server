/**
 * 按商品分析模块
 * 显示单个商品的详细销售数据
 */

// 全局变量
let salesChart = null;
let currentProductType = null;
let currentDataType = 'quantity'; // quantity 或 amount

// 图表缓存
let chartCache = {
    quantity: null,      // 销售数量图表实例
    amount: null,        // 销售额图表实例
    average_price: null  // 客单价图表实例
};

// 图表数据缓存
let chartDataCache = {
    quantity: null,      // 销售数量数据
    amount: null,        // 销售额数据
    average_price: null  // 客单价数据
};

// 渠道颜色方案
const channelColors = {
    '整体': 'rgba(255,107,53,1)',     // 橙色
    '抖音': 'rgba(30,136,229,1)',     // 蓝色
    '天猫': 'rgba(229,57,53,1)',      // 红色
    '有赞': 'rgba(67,160,71,1)',      // 绿色
    '京东': 'rgba(142,36,170,1)'      // 紫色
};

// 渠道显示顺序
const channelOrder = ['整体', '抖音', '天猫', '有赞', '京东'];

/**
 * 初始化按商品分析模块
 */
function initAnalyseByProduct() {
    console.log('初始化按商品分析模块');
    
    // 检查 ApexCharts 是否加载
    if (typeof ApexCharts === 'undefined') {
        console.error('ApexCharts 未加载');
        return;
    }
}

/**
 * 加载并显示商品详情
 */
async function loadProductDetails(productType, startDate, endDate) {
    console.log('加载商品详情:', productType, startDate, endDate);
    
    currentProductType = productType;
    
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
        
        const response = await fetch(`/api/analyse/product-details?product_type=${encodeURIComponent(productType)}&start_date=${startDate}&end_date=${endDate}&data_type=${currentDataType}`, {
            method: 'GET',
            headers: headers
        });
        
        if (response.status === 401) {
            // Token 过期
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            renderDetailsSection(result);
        } else {
            console.error('加载商品详情失败:', result.error);
        }
    } catch (error) {
        console.error('加载商品详情出错:', error);
    }
}

/**
 * 渲染详情区
 */
function renderDetailsSection(data) {
    const detailsSection = document.getElementById('detailsSection');
    if (!detailsSection) {
        console.error('未找到详情区容器');
        return;
    }
    
    // 显示详情区
    detailsSection.style.display = 'block';
    
    // 重置图表缓存 - 清理旧图表实例
    if (chartCache.quantity) {
        try {
            chartCache.quantity.destroy();
        } catch (e) {
            console.log('清理销售数量图表缓存:', e.message);
        }
        chartCache.quantity = null;
    }
    
    if (chartCache.amount) {
        try {
            chartCache.amount.destroy();
        } catch (e) {
            console.log('清理销售额图表缓存:', e.message);
        }
        chartCache.amount = null;
    }
    
    if (chartCache.average_price) {
        try {
            chartCache.average_price.destroy();
        } catch (e) {
            console.log('清理客单价图表缓存:', e.message);
        }
        chartCache.average_price = null;
    }
    
    // 重置数据缓存
    chartDataCache.quantity = null;
    chartDataCache.amount = null;
    chartDataCache.average_price = null;
    
    // 生成 HTML
    let html = `
        <div class="details-container">
            <h2 class="details-title">${data.product_type}销售详情</h2>
            
            <!-- 销售曲线 -->
            <div class="chart-section">
                <!-- 销售曲线tab页 -->
                <div class="sales-tab-container">
                    <div class="tab-container" style="margin-top: 15px; margin-bottom: 15px;">
                        <button class="tab-button active" data-tab="quantity">销售数量</button>
                        <button class="tab-button" data-tab="amount">销售额</button>
                        <button class="tab-button" data-tab="average_price">客单价</button>
                    </div>
                    
                    <!-- 销售数量tab内容 -->
                    <div class="tab-content active" id="salesQuantityTab">
                        <div id="salesQuantityChart" class="chart-container"></div>
                    </div>
                    
                    <!-- 销售额tab内容 -->
                    <div class="tab-content" id="salesAmountTab">
                        <div id="salesAmountChart" class="chart-container"></div>
                    </div>
                    
                    <!-- 客单价tab内容 -->
                    <div class="tab-content" id="salesAveragePriceTab">
                        <div id="salesAveragePriceChart" class="chart-container"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    detailsSection.innerHTML = html;
    
    // 缓存销售曲线数据（支持多渠道）
    chartDataCache.quantity = {
        dates: data.sales_curve.dates,
        aggregation_level: data.aggregation_level || 'day', // 默认为day
        series: [
            {
                name: '整体',
                data: data.sales_curve.overall.quantities,
                color: channelColors['整体']
            },
            {
                name: '抖音',
                data: data.sales_curve.channels.抖音.quantities,
                color: channelColors['抖音']
            },
            {
                name: '天猫',
                data: data.sales_curve.channels.天猫.quantities,
                color: channelColors['天猫']
            },
            {
                name: '有赞',
                data: data.sales_curve.channels.有赞.quantities,
                color: channelColors['有赞']
            },
            {
                name: '京东',
                data: data.sales_curve.channels.京东.quantities,
                color: channelColors['京东']
            }
        ]
    };
    
    chartDataCache.amount = {
        dates: data.sales_curve.dates,
        aggregation_level: data.aggregation_level || 'day', // 默认为day
        series: [
            {
                name: '整体',
                data: data.sales_curve.overall.amounts,
                color: channelColors['整体']
            },
            {
                name: '抖音',
                data: data.sales_curve.channels.抖音.amounts,
                color: channelColors['抖音']
            },
            {
                name: '天猫',
                data: data.sales_curve.channels.天猫.amounts,
                color: channelColors['天猫']
            },
            {
                name: '有赞',
                data: data.sales_curve.channels.有赞.amounts,
                color: channelColors['有赞']
            },
            {
                name: '京东',
                data: data.sales_curve.channels.京东.amounts,
                color: channelColors['京东']
            }
        ]
    };
    
    // 缓存客单价数据
    chartDataCache.average_price = {
        dates: data.sales_curve.dates,
        aggregation_level: data.aggregation_level || 'day', // 默认为day
        series: [
            {
                name: '整体',
                data: data.sales_curve.overall.average_prices,
                color: channelColors['整体']
            },
            {
                name: '抖音',
                data: data.sales_curve.channels.抖音.average_prices,
                color: channelColors['抖音']
            },
            {
                name: '天猫',
                data: data.sales_curve.channels.天猫.average_prices,
                color: channelColors['天猫']
            },
            {
                name: '有赞',
                data: data.sales_curve.channels.有赞.average_prices,
                color: channelColors['有赞']
            },
            {
                name: '京东',
                data: data.sales_curve.channels.京东.average_prices,
                color: channelColors['京东']
            }
        ]
    };
    
    // 初始化tab页事件
    initSalesChartTabs();
    
    // 默认显示销售数量tab
    showSalesChartTab('quantity');
    
}



/**
 * 隐藏详情区
 */
function hideDetailsSection() {
    const detailsSection = document.getElementById('detailsSection');
    if (detailsSection) {
        detailsSection.style.display = 'none';
    }
}

// 导出函数供外部使用
window.initAnalyseByProduct = initAnalyseByProduct;
window.loadProductDetails = loadProductDetails;
window.hideDetailsSection = hideDetailsSection;

/**
 * 初始化销售曲线tab页事件
 */
function initSalesChartTabs() {
    const tabButtons = document.querySelectorAll('.sales-tab-container .tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabType = this.getAttribute('data-tab');
            
            // 更新按钮样式
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // 显示对应的tab内容
            showSalesChartTab(tabType);
        });
    });
    
    // 确保第一个tab被激活并显示对应的图表
    const firstTabButton = tabButtons[0];
    if (firstTabButton) {
        firstTabButton.classList.add('active');
        const firstTabType = firstTabButton.getAttribute('data-tab');
        
        // 显示第一个tab内容
        let firstTabContentId;
        if (firstTabType === 'quantity') {
            firstTabContentId = 'salesQuantityTab';
        } else if (firstTabType === 'amount') {
            firstTabContentId = 'salesAmountTab';
        } else if (firstTabType === 'average_price') {
            firstTabContentId = 'salesAveragePriceTab';
        }
        
        const firstTabContent = document.getElementById(firstTabContentId);
        if (firstTabContent) {
            firstTabContent.classList.add('active');
        }
        
        // 延迟渲染第一个图表，确保DOM已准备好
        setTimeout(() => {
            renderSalesChartByType(firstTabType);
        }, 100);
    }
}

/**
 * 显示销售曲线tab页
 * @param {string} tabType - 'quantity'、'amount' 或 'average_price'
 */
function showSalesChartTab(tabType) {
    // 隐藏所有tab内容
    document.querySelectorAll('.sales-tab-container .tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 显示选中的tab内容
    let tabContentId;
    if (tabType === 'quantity') {
        tabContentId = 'salesQuantityTab';
    } else if (tabType === 'amount') {
        tabContentId = 'salesAmountTab';
    } else if (tabType === 'average_price') {
        tabContentId = 'salesAveragePriceTab';
    }
    
    const tabContent = document.getElementById(tabContentId);
    if (tabContent) {
        tabContent.classList.add('active');
    }
    
    // 使用setTimeout确保DOM已更新后再渲染图表
    setTimeout(() => {
        renderSalesChartByType(tabType);
    }, 50);
}

/**
 * 根据类型渲染销售曲线图
 * @param {string} type - 'quantity' 或 'amount'
 */
function renderSalesChartByType(type) {
    let chartElementId;
    if (type === 'quantity') {
        chartElementId = 'salesQuantityChart';
    } else if (type === 'amount') {
        chartElementId = 'salesAmountChart';
    } else if (type === 'average_price') {
        chartElementId = 'salesAveragePriceChart';
    }
    
    const chartElement = document.getElementById(chartElementId);
    
    if (!chartElement) {
        console.error(`未找到图表元素: ${chartElementId}`);
        return;
    }
    
    // 检查是否已有缓存的图表实例
    if (chartCache[type]) {
        // 图表已存在，确保图表容器正确显示
        console.log(`使用缓存的 ${type} 图表`);
        return;
    }
    
    // 检查是否有缓存的数据
    const chartData = chartDataCache[type];
    if (!chartData) {
        console.error(`没有找到 ${type} 类型的数据`);
        return;
    }
    
    // 验证数据格式
    if (!chartData.dates || !Array.isArray(chartData.dates)) {
        console.error(`${type} 数据错误: dates 不是数组`);
        return;
    }
    
    if (!chartData.series || !Array.isArray(chartData.series)) {
        console.error(`${type} 数据错误: series 不是数组`);
        return;
    }
    
    // 处理数据，确保金额和客单价数据是数字格式
    const processedSeries = chartData.series.map(series => {
        const processedData = series.data.map(value => {
            // 对于金额和客单价类型，确保数据是数字格式
            if ((type === 'amount' || type === 'average_price') && typeof value === 'string') {
                // 尝试转换为数字
                const num = parseFloat(value);
                return isNaN(num) ? 0 : num;
            }
            return Number(value) || 0;
        });
        
        return {
            name: series.name,
            data: processedData,
            color: series.color || channelColors[series.name] || '#000000'
        };
    });
    
    // 根据聚合级别计算标签样式
    const aggregationLevel = chartData.aggregation_level || 'day';
    let labelRotation = -30;
    let labelFontSize = '11px';
    
    switch(aggregationLevel) {
        case 'day':
            labelRotation = -30;
            labelFontSize = '11px';
            break;
        case 'week':
            labelRotation = -45;
            labelFontSize = '10px';
            break;
        case 'month':
            labelRotation = -45;
            labelFontSize = '10px';
            break;
        case 'quarter':
            labelRotation = -45;
            labelFontSize = '10px';
            break;
        case 'year':
            labelRotation = 0; // 年份标签不需要旋转
            labelFontSize = '12px'; // 年份标签可以大一些
            break;
        default:
            labelRotation = -30;
            labelFontSize = '11px';
    }
    
    // 创建新的图表
    const options = {
        series: processedSeries,
        chart: {
            type: 'line',
            height: 240,
            toolbar: {
                show: false
            },
            margin: {
                top: 10,
                right: 10,
                bottom: 20,
                left: 10
            }
        },
        stroke: {
            curve: 'smooth',
            width: processedSeries.map(series => series.name === '整体' ? 3 : 1.5)
        },
        colors: processedSeries.map(series => series.color),
        xaxis: {
            categories: chartData.dates,
            labels: {
                rotate: labelRotation,
                style: {
                    fontSize: labelFontSize
                },
                formatter: function(value) {
                    // 根据聚合级别格式化标签
                    const level = chartData.aggregation_level || 'day';
                    
                    if (!value) return '';
                    
                    if (level === 'day') {
                        // 按天显示：YYYY-MM-DD -> MM-DD
                        if (typeof value === 'string' && value.includes('-')) {
                            const parts = value.split('-');
                            if (parts.length >= 3) {
                                return parts[1] + '-' + parts[2];
                            }
                        }
                        return value;
                    }
                    else if (level === 'week') {
                        // 按周显示：YYYY-W01 -> 第01周
                        if (typeof value === 'string' && value.includes('-W')) {
                            const parts = value.split('-W');
                            if (parts.length === 2) {
                                return `第${parts[1]}周`;
                            }
                        }
                        return value;
                    }
                    else if (level === 'month') {
                        // 按月显示：YYYY-MM -> YYYY年MM月
                        if (typeof value === 'string' && value.includes('-')) {
                            const parts = value.split('-');
                            if (parts.length >= 2) {
                                return `${parts[0]}年${parts[1]}月`;
                            }
                        }
                        return value;
                    }
                    else if (level === 'quarter') {
                        // 按季度显示：YYYY-Q1 -> YYYY年Q1
                        if (typeof value === 'string' && value.includes('-Q')) {
                            const parts = value.split('-Q');
                            if (parts.length === 2) {
                                return `${parts[0]}年Q${parts[1]}`;
                            }
                        }
                        return value;
                    }
                    else if (level === 'year') {
                        // 按年显示：YYYY -> YYYY年
                        if (typeof value === 'string' && value.length === 4) {
                            return `${value}年`;
                        }
                        return value;
                    }
                    
                    return value;
                }
            }
        },
        yaxis: {
            min: 0,
            labels: {
                formatter: function (value) {
                    if (type === 'quantity') {
                        return value;
                    } else if (type === 'amount') {
                        return '¥' + value.toFixed(2);
                    } else if (type === 'average_price') {
                        return '¥' + value;
                    }
                    return value;
                }
            }
        },
        tooltip: {
            x: {
                formatter: function(value) {
                    // 根据聚合级别显示完整的日期信息
                    const level = chartData.aggregation_level || 'day';
                    
                    if (!value) return '';
                    
                    if (level === 'day') {
                        // 按天显示：YYYY-MM-DD -> YYYY年MM月DD日
                        if (typeof value === 'string' && value.includes('-')) {
                            const parts = value.split('-');
                            if (parts.length >= 3) {
                                return `${parts[0]}年${parts[1]}月${parts[2]}日`;
                            }
                        }
                        return value;
                    }
                    else if (level === 'week') {
                        // 按周显示：YYYY-W01 -> YYYY年第01周
                        if (typeof value === 'string' && value.includes('-W')) {
                            const parts = value.split('-W');
                            if (parts.length === 2) {
                                return `${parts[0]}年第${parts[1]}周`;
                            }
                        }
                        return value;
                    }
                    else if (level === 'month') {
                        // 按月显示：YYYY-MM -> YYYY年MM月
                        if (typeof value === 'string' && value.includes('-')) {
                            const parts = value.split('-');
                            if (parts.length >= 2) {
                                return `${parts[0]}年${parts[1]}月`;
                            }
                        }
                        return value;
                    }
                    else if (level === 'quarter') {
                        // 按季度显示：YYYY-Q1 -> YYYY年第1季度
                        if (typeof value === 'string' && value.includes('-Q')) {
                            const parts = value.split('-Q');
                            if (parts.length === 2) {
                                return `${parts[0]}年第${parts[1]}季度`;
                            }
                        }
                        return value;
                    }
                    else if (level === 'year') {
                        // 按年显示：YYYY -> YYYY年
                        if (typeof value === 'string' && value.length === 4) {
                            return `${value}年`;
                        }
                        return value;
                    }
                    
                    return value;
                }
            },
            y: {
                formatter: function (value) {
                    if (type === 'quantity') {
                        return value + ' 件';
                    } else if (type === 'amount') {
                        return '¥' + value.toFixed(2);
                    } else if (type === 'average_price') {
                        return '¥' + value;
                    }
                    return value;
                }
            }
        },
        grid: {
            borderColor: '#e7e7e7',
            row: {
                colors: ['#f3f3f3', 'transparent'],
                opacity: 0.5
            }
        },
        fill: {
            type: 'solid',
            opacity: 0
        },
        legend: {
            show: true,
            position: 'top',
            horizontalAlign: 'left',
            fontSize: '12px',
            fontFamily: 'Helvetica, Arial, sans-serif',
            fontWeight: 400,
            labels: {
                colors: '#333333',
                useSeriesColors: false
            },
            markers: {
                width: 12,
                height: 12,
                strokeWidth: 0,
                fillColors: processedSeries.map(series => series.color),
                radius: 6
            },
            itemMargin: {
                horizontal: 10,
                vertical: 5
            }
        }
    };
    
    // 创建并渲染图表
    const chart = new ApexCharts(chartElement, options);
    chart.render();
    
    // 缓存图表实例
    chartCache[type] = chart;
}

// 页面加载时自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAnalyseByProduct);
} else {
    initAnalyseByProduct();
}
