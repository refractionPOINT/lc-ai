/**
 * LimaCharlie Chart Library
 *
 * D3.js-based chart implementations for LimaCharlie dashboards.
 *
 * DATA ACCURACY GUARDRAILS:
 * - Charts ONLY render data that is provided
 * - Missing data shows "No data available" message
 * - No interpolation, estimation, or fabrication
 * - All values come directly from input data
 */

const LC = window.LC || {};
LC.charts = LC.charts || {};

// Color palette
LC.colors = {
    primary: '#0ea5e9',
    primaryDark: '#0284c7',
    success: '#22c55e',
    warning: '#f59e0b',
    danger: '#ef4444',
    purple: '#8b5cf6',
    pink: '#ec4899',
    teal: '#14b8a6',
    indigo: '#6366f1',
    palette: ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#6366f1']
};

// Utility functions
LC.utils = {
    formatNumber: (n) => {
        if (n === null || n === undefined || n === 'N/A') return 'N/A';
        return Number(n).toLocaleString();
    },

    formatBytes: (bytes) => {
        if (bytes === null || bytes === undefined) return 'N/A';
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let i = 0;
        let value = bytes;
        while (value >= 1024 && i < units.length - 1) {
            value /= 1024;
            i++;
        }
        return `${value.toFixed(1)} ${units[i]}`;
    },

    formatPercent: (n) => {
        if (n === null || n === undefined) return 'N/A';
        return `${Number(n).toFixed(1)}%`;
    },

    responsiveSize: (container) => {
        const rect = container.getBoundingClientRect();
        return {
            width: Math.max(rect.width, 200),
            height: Math.min(Math.max(rect.width * 0.6, 200), 400)
        };
    },

    // Show "no data" message in chart container
    showNoData: (containerId, message = 'No data available') => {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="chart-unavailable">
                <span class="icon">📊</span>
                <p>${message}</p>
            </div>
        `;
    }
};

/**
 * Pie/Donut Chart
 *
 * @param {Array} data - Array of {label, value} objects. MUST be actual data.
 * @param {Object} config - Configuration options
 */
LC.charts.pie = function(data, config) {
    const containerId = config.id;
    const container = d3.select(`#${containerId}`);

    // GUARDRAIL: Check for valid data
    if (!data || !Array.isArray(data) || data.length === 0) {
        LC.utils.showNoData(containerId, 'No data available for this chart');
        return;
    }

    // GUARDRAIL: Filter out invalid entries but don't fabricate
    const validData = data.filter(d => d && d.value !== null && d.value !== undefined && d.value > 0);

    if (validData.length === 0) {
        LC.utils.showNoData(containerId, 'All values are zero or unavailable');
        return;
    }

    const parentNode = container.node()?.parentNode;
    if (!parentNode) return;

    const { width, height } = LC.utils.responsiveSize(parentNode);
    const radius = Math.min(width, height) / 2 - 20;
    const innerRadius = config.donut ? radius * 0.55 : 0;

    container
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`);

    // Clear any existing content
    container.selectAll('*').remove();

    const svg = container.append('g')
        .attr('transform', `translate(${width/2}, ${height/2})`);

    const pie = d3.pie()
        .value(d => d.value)
        .sort(null);

    const arc = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(radius);

    const arcHover = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(radius + 5);

    const color = d3.scaleOrdinal()
        .domain(validData.map(d => d.label))
        .range(config.colors || LC.colors.palette);

    const total = d3.sum(validData, d => d.value);

    const arcs = svg.selectAll('.arc')
        .data(pie(validData))
        .enter()
        .append('g')
        .attr('class', 'arc');

    // Draw slices
    arcs.append('path')
        .attr('d', arc)
        .attr('fill', d => color(d.data.label))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('d', arcHover);

            // Show tooltip
            const percent = ((d.data.value / total) * 100).toFixed(1);
            tooltip
                .style('display', 'block')
                .html(`<strong>${d.data.label}</strong><br/>
                       ${LC.utils.formatNumber(d.data.value)} (${percent}%)`);
        })
        .on('mousemove', function(event) {
            tooltip
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function() {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('d', arc);
            tooltip.style('display', 'none');
        });

    // Labels (if enabled and space permits)
    if (config.showLabels !== false && validData.length <= 6) {
        arcs.append('text')
            .attr('transform', d => `translate(${arc.centroid(d)})`)
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .style('font-size', '11px')
            .style('font-weight', '500')
            .style('fill', '#fff')
            .style('pointer-events', 'none')
            .text(d => {
                const percent = (d.data.value / total) * 100;
                return percent >= 5 ? `${percent.toFixed(0)}%` : '';
            });
    }

    // Legend
    if (config.showLegend !== false) {
        const legendContainer = document.getElementById(`${containerId}-legend`);
        if (legendContainer) {
            legendContainer.innerHTML = '';
            validData.forEach((d, i) => {
                const item = document.createElement('div');
                item.className = 'legend-item';
                item.innerHTML = `
                    <span class="legend-color" style="background-color: ${color(d.label)}"></span>
                    <span class="legend-label">${d.label} (${LC.utils.formatNumber(d.value)})</span>
                `;
                legendContainer.appendChild(item);
            });
        }
    }

    // Tooltip element
    let tooltip = d3.select(`#${containerId}-tooltip`);
    if (tooltip.empty()) {
        tooltip = d3.select('body').append('div')
            .attr('id', `${containerId}-tooltip`)
            .attr('class', 'chart-tooltip')
            .style('display', 'none');
    }
};

/**
 * Bar Chart
 *
 * @param {Array} data - Array of {label, value} objects. MUST be actual data.
 * @param {Object} config - Configuration options
 */
LC.charts.bar = function(data, config) {
    const containerId = config.id;
    const container = d3.select(`#${containerId}`);

    // GUARDRAIL: Check for valid data
    if (!data || !Array.isArray(data) || data.length === 0) {
        LC.utils.showNoData(containerId, 'No data available for this chart');
        return;
    }

    // GUARDRAIL: Don't filter out zero values (they might be meaningful)
    // but do filter out null/undefined
    const validData = data.filter(d => d && d.value !== null && d.value !== undefined);

    if (validData.length === 0) {
        LC.utils.showNoData(containerId, 'All values are unavailable');
        return;
    }

    const parentNode = container.node()?.parentNode;
    if (!parentNode) return;

    const margin = config.horizontal
        ? { top: 20, right: 60, bottom: 30, left: 120 }
        : { top: 20, right: 30, bottom: 60, left: 60 };

    const { width, height } = LC.utils.responsiveSize(parentNode);
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    container
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`);

    // Clear existing
    container.selectAll('*').remove();

    const svg = container.append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const barColor = config.barColor || LC.colors.primary;
    const hoverColor = config.hoverColor || LC.colors.primaryDark;

    if (config.horizontal) {
        // Horizontal bar chart
        const x = d3.scaleLinear()
            .domain([0, d3.max(validData, d => d.value) * 1.1])
            .range([0, innerWidth]);

        const y = d3.scaleBand()
            .domain(validData.map(d => d.label))
            .range([0, innerHeight])
            .padding(0.2);

        // X axis
        svg.append('g')
            .attr('class', 'axis x-axis')
            .attr('transform', `translate(0, ${innerHeight})`)
            .call(d3.axisBottom(x).ticks(5).tickFormat(d => LC.utils.formatNumber(d)));

        // Y axis
        svg.append('g')
            .attr('class', 'axis y-axis')
            .call(d3.axisLeft(y));

        // Bars
        svg.selectAll('.bar')
            .data(validData)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('y', d => y(d.label))
            .attr('height', y.bandwidth())
            .attr('fill', barColor)
            .attr('x', 0)
            .attr('width', 0)
            .transition()
            .duration(config.animate !== false ? 750 : 0)
            .attr('width', d => x(d.value));

        // Values
        if (config.showValues !== false) {
            svg.selectAll('.bar-value')
                .data(validData)
                .enter()
                .append('text')
                .attr('class', 'bar-value')
                .attr('x', d => x(d.value) + 5)
                .attr('y', d => y(d.label) + y.bandwidth() / 2)
                .attr('dy', '0.35em')
                .style('font-size', '11px')
                .style('fill', 'var(--color-text-secondary)')
                .text(d => LC.utils.formatNumber(d.value));
        }
    } else {
        // Vertical bar chart
        const x = d3.scaleBand()
            .domain(validData.map(d => d.label))
            .range([0, innerWidth])
            .padding(0.2);

        const y = d3.scaleLinear()
            .domain([0, d3.max(validData, d => d.value) * 1.1])
            .nice()
            .range([innerHeight, 0]);

        // X axis
        svg.append('g')
            .attr('class', 'axis x-axis')
            .attr('transform', `translate(0, ${innerHeight})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .attr('transform', 'rotate(-45)')
            .attr('text-anchor', 'end')
            .attr('dx', '-0.5em')
            .attr('dy', '0.5em');

        // Y axis
        svg.append('g')
            .attr('class', 'axis y-axis')
            .call(d3.axisLeft(y).ticks(5).tickFormat(d => LC.utils.formatNumber(d)));

        // Bars
        const bars = svg.selectAll('.bar')
            .data(validData)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.label))
            .attr('width', x.bandwidth())
            .attr('fill', barColor)
            .attr('y', innerHeight)
            .attr('height', 0)
            .style('cursor', 'pointer');

        bars.transition()
            .duration(config.animate !== false ? 750 : 0)
            .attr('y', d => y(d.value))
            .attr('height', d => innerHeight - y(d.value));

        // Hover effects
        bars.on('mouseover', function() {
            d3.select(this).attr('fill', hoverColor);
        })
        .on('mouseout', function() {
            d3.select(this).attr('fill', barColor);
        });

        // Values on top
        if (config.showValues !== false) {
            svg.selectAll('.bar-value')
                .data(validData)
                .enter()
                .append('text')
                .attr('class', 'bar-value')
                .attr('x', d => x(d.label) + x.bandwidth() / 2)
                .attr('y', d => y(d.value) - 5)
                .attr('text-anchor', 'middle')
                .style('font-size', '11px')
                .style('fill', 'var(--color-text-secondary)')
                .text(d => LC.utils.formatNumber(d.value));
        }
    }
};

/**
 * Line Chart (Time Series)
 *
 * GUARDRAIL: Does NOT interpolate missing data points.
 * Gaps in data will appear as gaps in the line.
 *
 * @param {Array} data - Array of {date, value} objects. MUST be actual data.
 * @param {Object} config - Configuration options
 */
LC.charts.line = function(data, config) {
    const containerId = config.id;
    const container = d3.select(`#${containerId}`);

    // GUARDRAIL: Check for valid data
    if (!data || !Array.isArray(data) || data.length === 0) {
        LC.utils.showNoData(containerId, 'Time series data not available');
        return;
    }

    // GUARDRAIL: Filter invalid but don't interpolate
    const validData = data.filter(d => d && d.date && d.value !== null && d.value !== undefined);

    if (validData.length === 0) {
        LC.utils.showNoData(containerId, 'All time series values are unavailable');
        return;
    }

    if (validData.length === 1) {
        LC.utils.showNoData(containerId,
            `Insufficient data for trend (single point: ${validData[0].date} = ${LC.utils.formatNumber(validData[0].value)})`);
        return;
    }

    const parentNode = container.node()?.parentNode;
    if (!parentNode) return;

    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const { width, height } = LC.utils.responsiveSize(parentNode);
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    container
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`);

    container.selectAll('*').remove();

    const svg = container.append('g')
        .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const parseDate = d3.timeParse(config.dateFormat || '%Y-%m-%d');
    const parsedData = validData.map(d => ({
        date: typeof d.date === 'string' ? parseDate(d.date) : new Date(d.date),
        value: d.value
    })).filter(d => d.date); // Remove entries where date parsing failed

    if (parsedData.length < 2) {
        LC.utils.showNoData(containerId, 'Insufficient valid dates for trend');
        return;
    }

    const x = d3.scaleTime()
        .domain(d3.extent(parsedData, d => d.date))
        .range([0, innerWidth]);

    const y = d3.scaleLinear()
        .domain([0, d3.max(parsedData, d => d.value) * 1.1])
        .nice()
        .range([innerHeight, 0]);

    // Grid
    if (config.showGrid !== false) {
        svg.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(y)
                .tickSize(-innerWidth)
                .tickFormat(''))
            .style('stroke-dasharray', '3,3')
            .style('opacity', 0.2);
    }

    // Axes
    svg.append('g')
        .attr('class', 'axis x-axis')
        .attr('transform', `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(x).ticks(7).tickFormat(d3.timeFormat('%b %d')));

    svg.append('g')
        .attr('class', 'axis y-axis')
        .call(d3.axisLeft(y).ticks(5).tickFormat(d => LC.utils.formatNumber(d)));

    // Line generator - defined() ensures gaps for missing data
    const line = d3.line()
        .defined(d => d.value !== null && d.value !== undefined)
        .x(d => x(d.date))
        .y(d => y(d.value))
        .curve(d3.curveMonotoneX);

    // Area (if enabled)
    if (config.showArea) {
        const area = d3.area()
            .defined(d => d.value !== null && d.value !== undefined)
            .x(d => x(d.date))
            .y0(innerHeight)
            .y1(d => y(d.value))
            .curve(d3.curveMonotoneX);

        svg.append('path')
            .datum(parsedData)
            .attr('class', 'area')
            .attr('fill', LC.colors.primary)
            .attr('fill-opacity', 0.15)
            .attr('d', area);
    }

    // Line
    const path = svg.append('path')
        .datum(parsedData)
        .attr('class', 'line')
        .attr('fill', 'none')
        .attr('stroke', LC.colors.primary)
        .attr('stroke-width', 2)
        .attr('d', line);

    // Animate line drawing
    if (config.animate !== false) {
        const totalLength = path.node().getTotalLength();
        path
            .attr('stroke-dasharray', totalLength)
            .attr('stroke-dashoffset', totalLength)
            .transition()
            .duration(1500)
            .ease(d3.easeLinear)
            .attr('stroke-dashoffset', 0);
    }

    // Points
    if (config.showPoints !== false) {
        svg.selectAll('.point')
            .data(parsedData.filter(d => d.value !== null && d.value !== undefined))
            .enter()
            .append('circle')
            .attr('class', 'point')
            .attr('cx', d => x(d.date))
            .attr('cy', d => y(d.value))
            .attr('r', 4)
            .attr('fill', LC.colors.primary)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer');
    }

    // Tooltip
    let tooltip = d3.select(`#${containerId}-tooltip`);
    if (tooltip.empty()) {
        tooltip = d3.select('body').append('div')
            .attr('id', `${containerId}-tooltip`)
            .attr('class', 'chart-tooltip')
            .style('display', 'none');
    }

    svg.selectAll('.point')
        .on('mouseover', function(event, d) {
            tooltip
                .style('display', 'block')
                .html(`<strong>${d3.timeFormat('%Y-%m-%d')(d.date)}</strong><br/>
                       Value: ${LC.utils.formatNumber(d.value)}`);
            d3.select(this).attr('r', 6);
        })
        .on('mousemove', function(event) {
            tooltip
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function() {
            tooltip.style('display', 'none');
            d3.select(this).attr('r', 4);
        });
};

/**
 * Gauge Chart
 *
 * @param {Object} config - Configuration with value and thresholds
 */
LC.charts.gauge = function(config) {
    const containerId = config.id;
    const container = d3.select(`#${containerId}`);

    // GUARDRAIL: Check for valid value
    if (config.value === null || config.value === undefined) {
        const parent = container.node()?.parentNode;
        if (parent) {
            parent.innerHTML = `
                <div class="chart-unavailable">
                    <span class="icon">📊</span>
                    <p>Value unavailable</p>
                </div>
            `;
        }
        return;
    }

    const width = 180;
    const height = 100;
    const radius = 70;

    container
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`);

    container.selectAll('*').remove();

    const svg = container.append('g')
        .attr('transform', `translate(${width/2}, ${height - 10})`);

    const min = config.min || 0;
    const max = config.max || 100;
    const value = Math.max(min, Math.min(max, config.value)); // Clamp value

    // Background arc
    const bgArc = d3.arc()
        .innerRadius(radius - 15)
        .outerRadius(radius)
        .startAngle(-Math.PI / 2)
        .endAngle(Math.PI / 2);

    svg.append('path')
        .attr('d', bgArc)
        .attr('fill', '#e5e7eb');

    // Determine color from thresholds
    const thresholds = config.thresholds || [
        { value: 50, color: LC.colors.danger },
        { value: 75, color: LC.colors.warning },
        { value: 100, color: LC.colors.success }
    ];

    let gaugeColor = thresholds[thresholds.length - 1].color;
    for (const threshold of thresholds) {
        if (value <= threshold.value) {
            gaugeColor = threshold.color;
            break;
        }
    }

    // Value arc
    const scale = d3.scaleLinear()
        .domain([min, max])
        .range([-Math.PI / 2, Math.PI / 2]);

    const valueArc = d3.arc()
        .innerRadius(radius - 15)
        .outerRadius(radius)
        .startAngle(-Math.PI / 2);

    const arc = svg.append('path')
        .attr('fill', gaugeColor);

    if (config.animate !== false) {
        arc.transition()
            .duration(1000)
            .attrTween('d', function() {
                const interpolate = d3.interpolate(-Math.PI / 2, scale(value));
                return function(t) {
                    return valueArc.endAngle(interpolate(t))();
                };
            });
    } else {
        arc.attr('d', valueArc.endAngle(scale(value)));
    }

    // Center value text
    svg.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '-0.5em')
        .style('font-size', '24px')
        .style('font-weight', '700')
        .style('fill', 'var(--color-text)')
        .text(LC.utils.formatNumber(value));

    svg.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '1em')
        .style('font-size', '12px')
        .style('fill', 'var(--color-text-secondary)')
        .text('%');
};

/**
 * Table Sorting
 */
LC.tables = {
    init: function() {
        document.querySelectorAll('.data-table[data-sortable="true"]').forEach(table => {
            table.querySelectorAll('th[data-sort-key]').forEach(th => {
                th.addEventListener('click', () => {
                    LC.tables.sortTable(table, th.dataset.sortKey, th.dataset.sortType || 'string');
                });
            });
        });
    },

    sortTable: function(table, key, type) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        const th = table.querySelector(`th[data-sort-key="${key}"]`);
        const currentOrder = th.dataset.sortOrder || 'asc';
        const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';

        // Reset all headers
        table.querySelectorAll('th').forEach(h => {
            h.dataset.sortOrder = '';
            h.classList.remove('sort-asc', 'sort-desc');
        });

        th.dataset.sortOrder = newOrder;
        th.classList.add(`sort-${newOrder}`);

        rows.sort((a, b) => {
            const aCell = a.querySelector(`td:nth-child(${th.cellIndex + 1})`);
            const bCell = b.querySelector(`td:nth-child(${th.cellIndex + 1})`);

            let aVal = aCell?.textContent?.trim() || '';
            let bVal = bCell?.textContent?.trim() || '';

            // Handle N/A values
            if (aVal === 'N/A') aVal = newOrder === 'asc' ? 'zzz' : '';
            if (bVal === 'N/A') bVal = newOrder === 'asc' ? 'zzz' : '';

            if (type === 'number') {
                aVal = parseFloat(aCell?.dataset?.value || aVal.replace(/[^0-9.-]/g, '')) || 0;
                bVal = parseFloat(bCell?.dataset?.value || bVal.replace(/[^0-9.-]/g, '')) || 0;
            }

            if (aVal < bVal) return newOrder === 'asc' ? -1 : 1;
            if (aVal > bVal) return newOrder === 'asc' ? 1 : -1;
            return 0;
        });

        rows.forEach(row => tbody.appendChild(row));
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    LC.tables.init();
});

// Export for use
window.LC = LC;
