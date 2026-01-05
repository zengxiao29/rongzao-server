// 当前页码
let currentPage = 1;
// 每页显示数量
let pageSize = 50;
// 总记录数
let totalRecords = 0;
// 当前搜索关键词
let currentIncludeKeyword = '';
let currentExcludeKeyword = '';

// 筛选条件
let filterNoAlias = false;
let filterNoCategory = false;
let filterNoMapping = false;

// 搜索列
let searchColumn = 'name'; // name, alias, category, mapped_title

// 排序状态
let currentSortColumn = -1;
let currentSortDirection = 'desc'; // 'asc' 或 'desc'

// 权限控制
let isAuthorized = false;
let authorizationExpiry = null;
const AUTH_PASSWORD = 'xl12345678xl';
const AUTH_DURATION = 24 * 60 * 60 * 1000; // 24小时

// 正在编辑的单元格
let editingCell = null;
let originalValue = null;

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    // 绑定搜索输入框的回车事件
    document.getElementById('includeInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchProducts();
        }
    });

    document.getElementById('excludeInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchProducts();
        }
    });

    // 页面默认不加载数据，等待用户点击搜索
    renderEmptyState();
});

/**
 * 搜索商品
 */
async function searchProducts() {
    const includeKeyword = document.getElementById('includeInput').value.trim();
    const excludeKeyword = document.getElementById('excludeInput').value.trim();
    
    // 获取选择的搜索列
    const searchColumnRadio = document.querySelector('input[name="searchColumn"]:checked');
    searchColumn = searchColumnRadio ? searchColumnRadio.value : 'name';
    
    currentIncludeKeyword = includeKeyword;
    currentExcludeKeyword = excludeKeyword;
    currentPage = 1;

    await loadProducts();
}

/**
 * 处理筛选条件变化
 */
function handleFilterChange() {
    filterNoAlias = document.getElementById('filterNoAlias').checked;
    filterNoCategory = document.getElementById('filterNoCategory').checked;
    filterNoMapping = document.getElementById('filterNoMapping').checked;
    
    // 立即重新搜索
    currentPage = 1;
    loadProducts();
}

/**
 * 加载商品数据
 */
async function loadProducts() {
    try {
        const response = await fetch(`/api/product-manage/search?include=${encodeURIComponent(currentIncludeKeyword)}&exclude=${encodeURIComponent(currentExcludeKeyword)}&searchColumn=${searchColumn}&filterNoAlias=${filterNoAlias}&filterNoCategory=${filterNoCategory}&filterNoMapping=${filterNoMapping}&sortColumn=${currentSortColumn}&sortDirection=${currentSortDirection}&page=${currentPage}&pageSize=${pageSize}`);
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
 * 渲染空状态
 */
function renderEmptyState() {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = `
        <tr>
            <td colspan="6">
                <div class="empty-state">
                    <div style="font-size: 3rem;">🔍</div>
                    <p>请输入搜索条件后点击"搜索"按钮</p>
                </div>
            </td>
        </tr>
    `;
    document.getElementById('pagination').innerHTML = '';
}

/**
 * 渲染表格
 */
function renderTable(products) {
    const tableBody = document.getElementById('tableBody');

    if (!products || products.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5">
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
            <tr data-product-id="${product.id}">
                <td>${product.id}</td>
                <td>${product.name || ''}</td>
                <td class="editable" data-field="alias" data-value="${product.alias || ''}">${product.alias || ''}</td>
                <td class="editable" data-field="category" data-value="${product.category_name || ''}">${product.category_name || '-'}</td>
                <td class="editable" data-field="mapped_title" data-value="${product.mapped_title || ''}">${product.mapped_title || '-'}</td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;

    // 为可编辑单元格添加双击事件
    const editableCells = tableBody.querySelectorAll('.editable');
    editableCells.forEach(cell => {
        cell.addEventListener('dblclick', function() {
            const productId = this.closest('tr').dataset.productId;
            const field = this.dataset.field;
            const currentValue = this.dataset.value;
            enterEditMode(this, productId, field, currentValue);
        });
    });
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

/**
 * 检查权限是否过期
 */
function checkAuthorizationExpiry() {
    if (!authorizationExpiry) return false;
    return Date.now() < authorizationExpiry;
}

/**
 * 请求权限验证
 */
async function requestAuthorization() {
    // 检查权限是否已授权且未过期
    if (isAuthorized && checkAuthorizationExpiry()) {
        return true;
    }

    const password = prompt('请输入编辑密码：');
    if (password === AUTH_PASSWORD) {
        isAuthorized = true;
        authorizationExpiry = Date.now() + AUTH_DURATION;
        return true;
    } else {
        alert('密码错误，无法进入编辑模式');
        return false;
    }
}

/**
 * 进入编辑模式
 */
function enterEditMode(cell, productId, field, currentValue) {
    if (!requestAuthorization()) {
        return;
    }

    // 如果已经有单元格在编辑，先完成编辑
    if (editingCell) {
        finishEditing();
    }

    editingCell = {
        element: cell,
        productId: productId,
        field: field,
        originalValue: currentValue
    };

    // 添加编辑样式
    cell.classList.add('editing');

    if (field === 'category') {
        // 分类字段：显示下拉列表
        renderCategorySelect(cell, currentValue);
    } else {
        // 别名和映射标题：显示文本输入框
        renderTextInput(cell, currentValue);
    }
}

/**
 * 渲染文本输入框
 */
function renderTextInput(cell, currentValue) {
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentValue || '';
    input.style.width = '100%';
    input.style.padding = '8px';
    input.style.border = '2px solid #667eea';
    input.style.borderRadius = '4px';
    input.style.fontSize = '14px';

    // 保存事件
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            finishEditing();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEditing();
        }
    });

    // 失焦事件
    input.addEventListener('blur', function() {
        // 延迟执行，避免与回车事件冲突
        setTimeout(() => {
            if (editingCell) {
                finishEditing();
            }
        }, 100);
    });

    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();
}

/**
 * 渲染分类下拉列表
 */
async function renderCategorySelect(cell, currentValue) {
    try {
        // 获取所有分类
        const response = await fetch('/api/product-manage/categories');
        const result = await response.json();

        if (!response.ok || !result.success) {
            alert('加载分类列表失败');
            return;
        }

        const select = document.createElement('select');
        select.style.width = '100%';
        select.style.padding = '8px';
        select.style.border = '2px solid #667eea';
        select.style.borderRadius = '4px';
        select.style.fontSize = '14px';

        // 添加空选项
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '未分类';
        select.appendChild(emptyOption);

        // 添加分类选项
        result.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            if (category.name === currentValue) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        // 保存事件
        select.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                finishEditing();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelEditing();
            }
        });

        // 失焦事件
        select.addEventListener('blur', function() {
            setTimeout(() => {
                if (editingCell) {
                    finishEditing();
                }
            }, 100);
        });

        cell.innerHTML = '';
        cell.appendChild(select);
        select.focus();

    } catch (error) {
        console.error('加载分类列表失败:', error);
        alert('加载分类列表失败');
    }
}

/**
 * 完成编辑
 */
async function finishEditing() {
    if (!editingCell) return;

    const { element, productId, field, originalValue } = editingCell;
    const inputElement = element.querySelector('input, select');

    if (!inputElement) {
        cancelEditing();
        return;
    }

    const newValue = inputElement.value;

    // 如果值没有改变，不发送更新请求
    if (newValue === originalValue) {
        cancelEditing();
        return;
    }

    // 发送更新请求
    try {
        const response = await fetch('/api/product-manage/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: productId,
                field: field,
                value: newValue
            })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // 更新成功，重新加载数据
            await loadProducts();
        } else {
            // 更新失败，恢复原始值
            alert('更新失败: ' + (result.error || '未知错误'));
            cancelEditing();
        }
    } catch (error) {
        console.error('更新商品信息失败:', error);
        alert('更新失败: ' + error.message);
        cancelEditing();
    }

    editingCell = null;
}

/**
 * 取消编辑
 */
function cancelEditing() {
    if (!editingCell) return;

    const { element, originalValue } = editingCell;

    // 移除编辑样式
    element.classList.remove('editing');

    // 恢复原始值
    if (editingCell.field === 'category') {
        element.textContent = originalValue || '-';
    } else {
        element.textContent = originalValue || '';
    }

    editingCell = null;
}

/**
 * 商品表格排序函数
 * @param {number} columnIndex - 列索引（从1开始，对应表格中的列）
 */
function sortProductTable(columnIndex) {
    // 如果点击的是同一列，切换排序方向
    if (currentSortColumn === columnIndex) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        // 点击新列，默认升序
        currentSortColumn = columnIndex;
        currentSortDirection = 'asc';
    }

    // 重置到第一页，并重新加载数据
    currentPage = 1;
    loadProducts();

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