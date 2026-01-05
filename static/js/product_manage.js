// 当前页码
let currentPage = 1;
// 每页显示数量
let pageSize = 20;
// 总记录数
let totalRecords = 0;
// 当前搜索关键词
let currentKeyword = '';

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 绑定搜索输入框的回车事件
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchProducts();
        }
    });

    // 初始加载所有数据
    searchProducts();
});

/**
 * 搜索商品
 */
async function searchProducts() {
    const keyword = document.getElementById('searchInput').value.trim();
    currentKeyword = keyword;
    currentPage = 1;

    await loadProducts();
}

/**
 * 加载商品数据
 */
async function loadProducts() {
    try {
        const response = await fetch(`/api/product-manage/search?keyword=${encodeURIComponent(currentKeyword)}&page=${currentPage}&pageSize=${pageSize}`);
        const result = await response.json();

        if (response.ok && result.success) {
            totalRecords = result.total;
            renderTable(result.data);
            renderPagination();
        } else {
            alert('加载商品数据失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        console.error('加载商品数据失败:', error);
        alert('加载商品数据失败: ' + error.message);
    }
}

/**
 * 渲染表格
 */
function renderTable(products) {
    const tableBody = document.getElementById('tableBody');

    if (!products || products.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div style="font-size: 3rem;">📦</div>
                        <p>暂无商品数据</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    products.forEach(product => {
        html += `
            <tr>
                <td>${product.id}</td>
                <td>${product.name || ''}</td>
                <td>${product.alias || ''}</td>
                <td>${product.category_name || '-'}</td>
                <td>${product.mapped_title || '-'}</td>
                <td>${product.reviewed || '-'}</td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
}

/**
 * 渲染分页控件
 */
function renderPagination() {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(totalRecords / pageSize);

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = `<div class="pagination-info">共 ${totalRecords} 条记录，第 ${currentPage} / ${totalPages} 页</div>`;

    // 上一页按钮
    html += `
        <button onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>上一页</button>
    `;

    // 页码按钮（最多显示5个页码）
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);

    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button onclick="goToPage(${i})" ${i === currentPage ? 'class="active"' : ''}>${i}</button>
        `;
    }

    // 下一页按钮
    html += `
        <button onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>下一页</button>
    `;

    pagination.innerHTML = html;
}

/**
 * 跳转到指定页
 */
function goToPage(page) {
    currentPage = page;
    loadProducts();
}