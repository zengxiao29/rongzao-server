/**
 * 按商品分析模块
 * 显示单个商品的详细销售数据
 */

// 全局变量
let salesChart = null;
let channelChart = null;
let currentProductType = null;
let currentDataType = 'quantity'; // quantity 或 amount

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
    
    // 生成 HTML
    let html = `
        <div class="details-container">
            <h2 class="details-title">${data.product_type}销售详情</h2>
            
            <!-- 销售曲线 -->
            <div class="chart-section">
                <div class="chart-header">
                    <h3>销售曲线</h3>
                    <div class="chart-toggle">
                        <button class="toggle-btn active" onclick="toggleDataType('quantity', this)">销售数量</button>
                        <button class="toggle-btn" onclick="toggleDataType('amount', this)">销售额</button>
                    </div>
                </div>
                <div id="salesChart" class="chart-container"></div>
            </div>
            
            <!-- 客单价与渠道分布 -->
            <div class="stats-section">
                <div class="stats-header">
                    <h3>客单价 : ${data.average_order_value}</h3>
                    <div class="growth-indicator"></div>
                </div>
                <div id="channelChart" class="chart-container"></div>
            </div>
        </div>
    `;
    
    detailsSection.innerHTML = html;
    
    // 渲染图表
    renderSalesChart(data.sales_curve);
    renderChannelChart(data.channel_sales);
}

/**
 * 渲染销售曲线图
 */
function renderSalesChart(salesCurveData) {
    const chartElement = document.getElementById('salesChart');
    if (!chartElement) return;
    
    const seriesData = currentDataType === 'quantity' ? salesCurveData.quantities : salesCurveData.amounts;
    const seriesName = currentDataType === 'quantity' ? '销售数量' : '销售额';
    
    const options = {
        series: [{
            name: seriesName,
            data: seriesData
        }],
        chart: {
            type: 'line',
            height: 350,
            toolbar: {
                show: false
            }
        },
        stroke: {
            curve: 'smooth',
            width: 3
        },
        colors: ['#FF6B35'],
        xaxis: {
            categories: salesCurveData.dates,
            labels: {
                rotate: -45,
                style: {
                    fontSize: '11px'
                },
                offsetY: 5
            }
        },
        yaxis: {
            labels: {
                formatter: function (value) {
                    return currentDataType === 'quantity' ? value : '¥' + value.toFixed(2);
                }
            }
        },
        tooltip: {
            y: {
                formatter: function (value) {
                    return currentDataType === 'quantity' ? value + ' 件' : '¥' + value.toFixed(2);
                }
            }
        },
        grid: {
            borderColor: '#e7e7e7',
            row: {
                colors: ['#f3f3f3', 'transparent'],
                opacity: 0.5
            }
        }
    };
    
    salesChart = new ApexCharts(chartElement, options);
    salesChart.render();
}

/**
 * 渲染渠道分布图
 */
function renderChannelChart(channelSales) {
    const chartElement = document.getElementById('channelChart');
    if (!chartElement) return;
    
    const categories = Object.keys(channelSales);
    const data = Object.values(channelSales);
    
    const options = {
        series: [{
            data: data
        }],
        chart: {
            type: 'bar',
            height: 300,
            toolbar: {
                show: false
            }
        },
        plotOptions: {
            bar: {
                borderRadius: 4,
                columnWidth: '50%'
            }
        },
        colors: ['#4A5C9E'],
        xaxis: {
            categories: categories
        },
        yaxis: {
            labels: {
                formatter: function (value) {
                    return value + ' 件';
                }
            }
        },
        tooltip: {
            y: {
                formatter: function (value) {
                    return value + ' 件';
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
        dataLabels: {
            enabled: true,
            formatter: function (value) {
                return value;
            },
            offsetY: -20,
            style: {
                fontSize: '12px',
                colors: ["#304758"]
            }
        }
    };
    
    channelChart = new ApexCharts(chartElement, options);
    channelChart.render();
}

/**
 * 切换数据类型
 */
function toggleDataType(type, button) {
    currentDataType = type;
    
    // 更新按钮样式
    const buttons = document.querySelectorAll('.toggle-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');
    
    // 重新加载并渲染
    if (currentProductType) {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        loadProductDetails(currentProductType, startDate, endDate);
    }
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
window.toggleDataType = toggleDataType;

// 页面加载时自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAnalyseByProduct);
} else {
    initAnalyseByProduct();
}
