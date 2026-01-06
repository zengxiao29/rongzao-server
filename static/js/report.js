// 获取 URL 参数
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        startDate: params.get('startDate'),
        endDate: params.get('endDate')
    };
}

// 渲染报表表格
function renderReportTable(data) {
    const table = document.getElementById('reportTable');
    table.innerHTML = '';

    if (!data || data.length === 0) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('reportContent').innerHTML = '<div class="empty-state"><p>暂无数据</p></div>';
        document.getElementById('reportContent').style.display = 'block';
        return;
    }

    // 渲染表格行
    data.forEach(row => {
        const tr = document.createElement('tr');

        if (row.type === 'title') {
            tr.className = 'title-row';
            tr.innerHTML = `<td colspan="4">${row.value}</td>`;
        } else if (row.type === 'subtitle') {
            tr.className = 'subtitle-row';
            tr.innerHTML = `<td colspan="4">${row.value}</td>`;
        } else if (row.type === 'header') {
            tr.className = 'header-row';
            tr.innerHTML = `
                <td>${row.product_type || ''}</td>
                <td>${row.date || ''}</td>
                <td class="text-right">${row.quantity !== undefined ? row.quantity : ''}</td>
                <td class="text-right">${row.amount !== undefined ? row.amount : ''}</td>
            `;
        } else if (row.type === 'subtotal') {
            tr.className = 'subtotal-row';
            tr.innerHTML = `
                <td>${row.product_type || ''}</td>
                <td>${row.date || ''}</td>
                <td class="text-right">${row.quantity !== undefined ? row.quantity : ''}</td>
                <td class="text-right">${row.amount !== undefined ? row.amount : ''}</td>
            `;
        } else if (row.type === 'total') {
            tr.className = 'total-row';
            tr.innerHTML = `
                <td>${row.product_type || ''}</td>
                <td>${row.date || ''}</td>
                <td class="text-right">${row.quantity !== undefined ? row.quantity : ''}</td>
                <td class="text-right">${row.amount !== undefined ? row.amount : ''}</td>
            `;
        } else {
            // 数据行
            const productTypeCell = document.createElement('td');
            productTypeCell.textContent = row.product_type || '';

            // 如果有 rowspan，应用它
            if (row.rowspan && row.rowspan > 1) {
                productTypeCell.rowSpan = row.rowspan;
                productTypeCell.style.verticalAlign = 'middle';
            } else if (row.product_type === '') {
                // 如果商品类型为空，跳过这个单元格
                productTypeCell.style.display = 'none';
            }

            tr.appendChild(productTypeCell);

            const dateCell = document.createElement('td');
            dateCell.textContent = row.date || '';
            tr.appendChild(dateCell);

            const quantityCell = document.createElement('td');
            quantityCell.className = 'text-right';
            quantityCell.textContent = row.quantity !== undefined ? row.quantity : '';
            tr.appendChild(quantityCell);

            const amountCell = document.createElement('td');
            amountCell.className = 'text-right';
            amountCell.textContent = row.amount !== undefined ? row.amount : '';
            tr.appendChild(amountCell);
        }

        table.appendChild(tr);
    });

    document.getElementById('loading').style.display = 'none';
    document.getElementById('reportContent').style.display = 'block';
}

// 加载报表数据
async function loadReportData() {
    const params = getUrlParams();

    if (!params.startDate || !params.endDate) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('errorMessage').textContent = '缺少日期参数';
        document.getElementById('errorMessage').style.display = 'block';
        return;
    }

    // 显示日期信息
    document.getElementById('dateInfo').textContent = `日期范围：${params.startDate} 至 ${params.endDate}`;

    try {
        const token = getToken();
        const headers = {
            'Content-Type': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch('/api/analyse/generate-report', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                startDate: params.startDate,
                endDate: params.endDate
            })
        });

        // 检查是否需要重新登录
        if (response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }

        const result = await response.json();

        if (response.ok && result.success) {
            renderReportTable(result.data);
        } else {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('errorMessage').textContent = result.error || '加载报表数据失败';
            document.getElementById('errorMessage').style.display = 'block';
        }
    } catch (error) {
        console.error('加载报表数据失败:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('errorMessage').textContent = '加载报表数据失败: ' + error.message;
        document.getElementById('errorMessage').style.display = 'block';
    }
}

// 导出为 PDF
async function exportToPDF() {
    const params = getUrlParams();

    if (!params.startDate || !params.endDate) {
        alert('缺少日期参数');
        return;
    }

    try {
        const token = getToken();
        const headers = {
            'Content-Type': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch('/api/analyse/export-weekly-report', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                startDate: params.startDate,
                endDate: params.endDate
            })
        });

        // 检查是否需要重新登录
        if (response.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('user');
            window.location.href = '/login';
            return;
        }

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `报表_${params.startDate}_${params.endDate}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } else {
            const result = await response.json();
            alert('导出失败: ' + (result.error || '未知错误'));
        }
    } catch (error) {
        console.error('导出失败:', error);
        alert('导出失败: ' + error.message);
    }
}

// 页面加载时加载数据
document.addEventListener('DOMContentLoaded', function() {
    loadReportData();
});