// 美观的柱状图实现
class BeautifulBarChart {
    constructor(canvasId, data) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.data = data;
        this.padding = { top: 60, right: 40, bottom: 80, left: 80 };
        this.animationProgress = 0;
        this.animationId = null;
        this.barColors = [];
        this.generateColors();
    }

    generateColors() {
        // 生成渐变色
        const baseColor = { r: 102, g: 126, b: 234 };
        this.barColors = this.data.map((_, index) => {
            const alpha = 0.5 + (index / this.data.length) * 0.4;
            return `rgba(${baseColor.r}, ${baseColor.g}, ${baseColor.b}, ${alpha})`;
        });
    }

    render() {
        const { canvas, ctx, data, padding } = this;
        const width = canvas.width = canvas.offsetWidth * 2; // 高分辨率
        const height = canvas.height = 500 * 2;
        ctx.scale(2, 2); // 缩放以保持清晰度

        const actualWidth = width / 2;
        const actualHeight = height / 2;

        if (!data || data.length === 0) return;

        const maxValue = Math.max(...data.map(item => item.sales));
        const chartWidth = actualWidth - padding.left - padding.right;
        const chartHeight = actualHeight - padding.top - padding.bottom;

        // 绘制背景
        ctx.fillStyle = '#fafafa';
        ctx.fillRect(0, 0, actualWidth, actualHeight);

        // 绘制标题
        ctx.font = 'bold 18px Arial, sans-serif';
        ctx.fillStyle = '#333';
        ctx.textAlign = 'center';
        ctx.fillText('商品销量统计直方图', actualWidth / 2, 35);

        // 绘制Y轴
        ctx.beginPath();
        ctx.moveTo(padding.left, padding.top);
        ctx.lineTo(padding.left, actualHeight - padding.bottom);
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 1;
        ctx.stroke();

        // 绘制X轴
        ctx.beginPath();
        ctx.moveTo(padding.left, actualHeight - padding.bottom);
        ctx.lineTo(actualWidth - padding.right, actualHeight - padding.bottom);
        ctx.stroke();

        // 绘制Y轴刻度和网格线
        ctx.font = '12px Arial, sans-serif';
        ctx.fillStyle = '#666';
        ctx.textAlign = 'right';
        const ySteps = 6;
        for (let i = 0; i <= ySteps; i++) {
            const value = Math.round((maxValue / ySteps) * i);
            const y = actualHeight - padding.bottom - (chartHeight / ySteps) * i;
            ctx.fillText(value, padding.left - 10, y + 4);

            // 绘制水平网格线
            if (i > 0) {
                ctx.beginPath();
                ctx.moveTo(padding.left, y);
                ctx.lineTo(actualWidth - padding.right, y);
                ctx.strokeStyle = '#e8e8e8';
                ctx.lineWidth = 1;
                ctx.setLineDash([5, 5]); // 虚线
                ctx.stroke();
                ctx.setLineDash([]); // 恢复实线
            }
        }

        // 绘制Y轴标题
        ctx.save();
        ctx.translate(20, actualHeight / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.textAlign = 'center';
        ctx.font = 'bold 13px Arial, sans-serif';
        ctx.fillStyle = '#666';
        ctx.fillText('销量', 0, 0);
        ctx.restore();

        // 计算柱子宽度
        const barWidth = Math.min(80, (chartWidth / data.length) * 0.6);
        const barGap = (chartWidth - barWidth * data.length) / (data.length + 1);

        // 绘制柱状图（带动画）
        data.forEach((item, index) => {
            const x = padding.left + barGap + index * (barWidth + barGap);
            const fullBarHeight = (item.sales / maxValue) * chartHeight;
            const barHeight = fullBarHeight * this.animationProgress;
            const y = actualHeight - padding.bottom - barHeight;

            // 绘制柱子阴影
            ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
            ctx.fillRect(x + 3, y + 3, barWidth, barHeight);

            // 绘制柱子（渐变色）
            const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
            gradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
            gradient.addColorStop(1, 'rgba(102, 126, 234, 0.4)');
            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth, barHeight);

            // 绘制柱子边框
            ctx.strokeStyle = 'rgba(102, 126, 234, 1)';
            ctx.lineWidth = 2;
            ctx.strokeRect(x, y, barWidth, barHeight);

            // 绘制数值标签（带背景）
            if (this.animationProgress > 0.8) {
                const labelY = y - 10;
                const labelText = item.sales.toString();
                ctx.font = 'bold 12px Arial, sans-serif';
                const textWidth = ctx.measureText(labelText).width;

                // 绘制标签背景
                ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                ctx.fillRect(x + barWidth / 2 - textWidth / 2 - 4, labelY - 14, textWidth + 8, 18);
                ctx.strokeStyle = '#667eea';
                ctx.lineWidth = 1;
                ctx.strokeRect(x + barWidth / 2 - textWidth / 2 - 4, labelY - 14, textWidth + 8, 18);

                // 绘制标签文字
                ctx.fillStyle = '#667eea';
                ctx.textAlign = 'center';
                ctx.fillText(labelText, x + barWidth / 2, labelY);
            }

            // 绘制X轴标签（商品名称）
            ctx.save();
            ctx.translate(x + barWidth / 2, actualHeight - padding.bottom + 20);
            ctx.rotate(Math.PI / 6); // 30度旋转
            ctx.textAlign = 'left';
            ctx.fillStyle = '#555';
            ctx.font = '11px Arial, sans-serif';
            const displayName = item.name.length > 12 ? item.name.substring(0, 12) + '...' : item.name;
            ctx.fillText(displayName, 5, 0);
            ctx.restore();
        });

        // 绘制X轴标题
        ctx.fillStyle = '#666';
        ctx.textAlign = 'center';
        ctx.font = 'bold 13px Arial, sans-serif';
        ctx.fillText('商品名称', actualWidth / 2, actualHeight - 15);

        // 绘制图例
        const legendX = actualWidth - 150;
        const legendY = 20;
        ctx.fillStyle = 'rgba(102, 126, 234, 0.8)';
        ctx.fillRect(legendX, legendY, 20, 15);
        ctx.strokeStyle = 'rgba(102, 126, 234, 1)';
        ctx.lineWidth = 2;
        ctx.strokeRect(legendX, legendY, 20, 15);
        ctx.fillStyle = '#666';
        ctx.textAlign = 'left';
        ctx.font = '12px Arial, sans-serif';
        ctx.fillText('销量', legendX + 28, legendY + 12);
    }

    animate() {
        const duration = 1000; // 1秒动画
        const startTime = performance.now();

        const animateFrame = (currentTime) => {
            const elapsed = currentTime - startTime;
            this.animationProgress = Math.min(elapsed / duration, 1);

            // 使用缓动函数
            this.animationProgress = 1 - Math.pow(1 - this.animationProgress, 3);

            this.render();

            if (this.animationProgress < 1) {
                this.animationId = requestAnimationFrame(animateFrame);
            }
        };

        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.animationId = requestAnimationFrame(animateFrame);
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        const { canvas, ctx } = this;
        if (canvas && ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }
}