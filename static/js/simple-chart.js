// 简单的柱状图实现，不依赖外部库
class SimpleBarChart {
    constructor(canvasId, data) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.data = data;
        this.padding = { top: 40, right: 20, bottom: 60, left: 60 };
    }

    render() {
        const { canvas, ctx, data, padding } = this;
        const width = canvas.width = canvas.offsetWidth;
        const height = canvas.height = 500;

        // 清空画布
        ctx.clearRect(0, 0, width, height);

        if (!data || data.length === 0) return;

        // 计算最大值
        const maxValue = Math.max(...data.map(item => item.sales));
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;

        // 绘制标题
        ctx.font = 'bold 16px Arial';
        ctx.fillStyle = '#333';
        ctx.textAlign = 'center';
        ctx.fillText('商品销量统计直方图', width / 2, 25);

        // 绘制Y轴
        ctx.beginPath();
        ctx.moveTo(padding.left, padding.top);
        ctx.lineTo(padding.left, height - padding.bottom);
        ctx.strokeStyle = '#666';
        ctx.stroke();

        // 绘制X轴
        ctx.beginPath();
        ctx.moveTo(padding.left, height - padding.bottom);
        ctx.lineTo(width - padding.right, height - padding.bottom);
        ctx.stroke();

        // 绘制Y轴刻度和标签
        ctx.font = '12px Arial';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'right';
        const ySteps = 5;
        for (let i = 0; i <= ySteps; i++) {
            const value = Math.round((maxValue / ySteps) * i);
            const y = height - padding.bottom - (chartHeight / ySteps) * i;
            ctx.fillText(value, padding.left - 10, y + 4);

            // 绘制水平网格线
            if (i > 0) {
                ctx.beginPath();
                ctx.moveTo(padding.left, y);
                ctx.lineTo(width - padding.right, y);
                ctx.strokeStyle = '#e0e0e0';
                ctx.stroke();
            }
        }

        // 绘制Y轴标题
        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.textAlign = 'center';
        ctx.fillText('销量', 0, 0);
        ctx.restore();

        // 绘制柱状图
        const barWidth = Math.min(60, (chartWidth / data.length) * 0.7);
        const barGap = (chartWidth - barWidth * data.length) / (data.length + 1);

        data.forEach((item, index) => {
            const x = padding.left + barGap + index * (barWidth + barGap);
            const barHeight = (item.sales / maxValue) * chartHeight;
            const y = height - padding.bottom - barHeight;

            // 绘制柱子
            ctx.fillStyle = 'rgba(102, 126, 234, 0.6)';
            ctx.fillRect(x, y, barWidth, barHeight);

            // 绘制柱子边框
            ctx.strokeStyle = 'rgba(102, 126, 234, 1)';
            ctx.strokeRect(x, y, barWidth, barHeight);

            // 绘制数值标签
            ctx.fillStyle = '#333';
            ctx.textAlign = 'center';
            ctx.font = '11px Arial';
            ctx.fillText(item.sales, x + barWidth / 2, y - 5);

            // 绘制X轴标签（商品名称）
            ctx.save();
            ctx.translate(x + barWidth / 2, height - padding.bottom + 15);
            ctx.rotate(Math.PI / 4);
            ctx.textAlign = 'left';
            ctx.fillStyle = '#666';
            ctx.font = '10px Arial';
            const displayName = item.name.length > 10 ? item.name.substring(0, 10) + '...' : item.name;
            ctx.fillText(displayName, 0, 0);
            ctx.restore();
        });

        // 绘制X轴标题
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.font = '12px Arial';
        ctx.fillText('商品名称', width / 2, height - 10);
    }

    destroy() {
        // 清空画布
        const { canvas, ctx } = this;
        if (canvas && ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }
}