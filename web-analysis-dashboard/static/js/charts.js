Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
Chart.defaults.font.size = 12;
Chart.defaults.color = '#666';

const chartColors = {
    positive: '#28a745',
    negative: '#dc3545',
    neutral: '#ffc107',
    primary: '#007bff',
    secondary: '#6c757d',
    info: '#17a2b8',
    light: '#f8f9fa',
    dark: '#343a40'
};

function createGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, color + '40');
    gradient.addColorStop(1, color + '10');
    return gradient;
}

function formatTooltipLabel(context) {
    let label = context.dataset.label || '';
    if (label) {
        label += ': ';
    }
    if (context.parsed.y !== null) {
        label += context.parsed.y.toFixed(3);
    }
    return label;
}

function formatPercentage(value, total) {
    if (total === 0) return '0%';
    return ((value / total) * 100).toFixed(1) + '%';
}

function getChartOptions(type, config = {}) {
    const baseOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: config.showLegend !== false,
                position: config.legendPosition || 'top',
                labels: {
                    padding: 15,
                    font: {
                        size: 11
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 10,
                cornerRadius: 5,
                displayColors: true,
                callbacks: {}
            }
        }
    };

    if (type === 'line') {
        baseOptions.plugins.tooltip.callbacks.label = formatTooltipLabel;
        baseOptions.scales = {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                grid: {
                    borderDash: [5, 5],
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    padding: 10
                }
            }
        };
    } else if (type === 'bar') {
        baseOptions.scales = {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                grid: {
                    borderDash: [5, 5],
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    padding: 10
                }
            }
        };
    } else if (type === 'doughnut' || type === 'pie') {
        baseOptions.plugins.tooltip.callbacks.label = function(context) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = formatPercentage(value, total);
            return `${label}: ${value} (${percentage})`;
        };
    }

    return Object.assign(baseOptions, config);
}

function updateChartData(chart, labels, datasets) {
    chart.data.labels = labels;
    chart.data.datasets = datasets;
    chart.update('none');
}

function animateChart(chart) {
    chart.update();
}

function downloadChart(chartId, filename) {
    const canvas = document.getElementById(chartId);
    const url = canvas.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = filename || 'chart.png';
    link.href = url;
    link.click();
}

function resizeChart(chart) {
    chart.resize();
}

window.ChartHelpers = {
    colors: chartColors,
    createGradient,
    formatTooltipLabel,
    formatPercentage,
    getChartOptions,
    updateChartData,
    animateChart,
    downloadChart,
    resizeChart
};