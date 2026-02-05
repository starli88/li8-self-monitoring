/**
 * Accountability Dashboard - Calendar JavaScript
 */

// Persian month names
const MONTH_NAMES = [
    'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
];

// Status labels in Persian
const STATUS_LABELS = {
    'safe': 'سالم',
    'nsfw': 'نامناسب',
    'error': 'خطا',
    'no_data': 'بدون داده'
};

// Current displayed month/year
let displayYear = window.CURRENT_YEAR || new Date().getFullYear();
let displayMonth = window.CURRENT_MONTH || 1;

/**
 * Initialize the calendar page
 */
function initCalendar() {
    if (!document.getElementById('calendar-grid')) return;
    
    // Set initial values
    displayYear = window.CURRENT_YEAR;
    displayMonth = window.CURRENT_MONTH;
    
    // Setup navigation
    document.getElementById('prev-month').addEventListener('click', () => {
        displayMonth--;
        if (displayMonth < 1) {
            displayMonth = 12;
            displayYear--;
        }
        loadMonth();
    });
    
    document.getElementById('next-month').addEventListener('click', () => {
        displayMonth++;
        if (displayMonth > 12) {
            displayMonth = 1;
            displayYear++;
        }
        loadMonth();
    });
    
    // Load initial month
    loadMonth();
    
    // Load last update time
    loadLastUpdate();
    
    // Refresh last update every 30 seconds
    setInterval(loadLastUpdate, 30000);
}

/**
 * Load and display a month's data
 */
async function loadMonth() {
    const grid = document.getElementById('calendar-grid');
    const title = document.getElementById('month-title');
    
    // Update title
    title.textContent = `${MONTH_NAMES[displayMonth - 1]} ${displayYear}`;
    
    // Show loading
    grid.innerHTML = '<div class="loading">در حال بارگذاری...</div>';
    
    try {
        const response = await fetch(`/api/month/${displayYear}/${displayMonth}`);
        const data = await response.json();
        
        if (data.error) {
            grid.innerHTML = `<div class="loading">خطا: ${data.error}</div>`;
            return;
        }
        
        renderCalendar(data);
    } catch (error) {
        grid.innerHTML = '<div class="loading">خطا در بارگذاری داده‌ها</div>';
        console.error('Error loading month:', error);
    }
}

/**
 * Render the calendar grid
 */
function renderCalendar(data) {
    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = '';
    
    // Calculate first day of month (Saturday = 0 in Jalali calendar)
    // We need to find which day of week the 1st falls on
    const firstDayOffset = getFirstDayOffset(data.year, data.month);
    
    // Add empty cells for days before the 1st
    for (let i = 0; i < firstDayOffset; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        grid.appendChild(emptyDay);
    }
    
    // Add days
    for (let day = 1; day <= data.days_in_month; day++) {
        const dayEl = document.createElement('div');
        const status = data.days[day] || 'no_data';
        
        dayEl.className = `calendar-day ${status}`;
        dayEl.textContent = day;
        
        // Mark today
        if (data.year === window.CURRENT_YEAR && 
            data.month === window.CURRENT_MONTH && 
            day === window.CURRENT_DAY) {
            dayEl.classList.add('today');
        }
        
        // Add click handler
        dayEl.addEventListener('click', () => {
            window.location.href = `/day/${data.year}/${data.month}/${day}`;
        });
        
        grid.appendChild(dayEl);
    }
}

/**
 * Get the offset for the first day of the month (0 = Saturday)
 * This is a simplified calculation
 */
function getFirstDayOffset(year, month) {
    // Use a reference point: 1 Farvardin 1404 is a Saturday (offset 0)
    // This is a simplified calculation and may need adjustment
    
    // Calculate total days from reference point
    let totalDays = 0;
    
    // Days from reference year to target year
    for (let y = 1404; y < year; y++) {
        totalDays += isLeapYear(y) ? 366 : 365;
    }
    for (let y = year; y < 1404; y++) {
        totalDays -= isLeapYear(y) ? 366 : 365;
    }
    
    // Days from start of year to start of target month
    for (let m = 1; m < month; m++) {
        if (m <= 6) totalDays += 31;
        else if (m <= 11) totalDays += 30;
        else totalDays += isLeapYear(year) ? 30 : 29;
    }
    
    // 1 Farvardin 1404 is a Saturday (index 0)
    // Adjust: Actually need to check real calendar
    // For now, using approximate calculation
    return ((totalDays % 7) + 7) % 7;
}

/**
 * Check if a Jalali year is a leap year
 */
function isLeapYear(year) {
    const remainder = year % 33;
    return [1, 5, 9, 13, 17, 22, 26, 30].includes(remainder);
}

/**
 * Load and display the last update time
 */
async function loadLastUpdate() {
    const lastUpdateEl = document.getElementById('last-update-time');
    if (!lastUpdateEl) return;
    
    try {
        const response = await fetch('/api/last-update');
        const data = await response.json();
        
        if (data.has_data) {
            lastUpdateEl.textContent = data.jalali;
        } else {
            lastUpdateEl.textContent = 'هیچ داده‌ای دریافت نشده';
        }
    } catch (error) {
        lastUpdateEl.textContent = 'خطا در بارگذاری';
        console.error('Error loading last update:', error);
    }
}

/**
 * Initialize the day detail page
 */
function initDayDetail() {
    if (!document.getElementById('hours-grid')) return;
    
    loadDayData();
}

/**
 * Load and display day detail data
 */
async function loadDayData() {
    const grid = document.getElementById('hours-grid');
    const year = window.DAY_YEAR;
    const month = window.DAY_MONTH;
    const day = window.DAY_DAY;
    
    grid.innerHTML = '<div class="loading">در حال بارگذاری...</div>';
    
    try {
        const response = await fetch(`/api/day/${year}/${month}/${day}`);
        const data = await response.json();
        
        if (data.error) {
            grid.innerHTML = `<div class="loading">خطا: ${data.error}</div>`;
            return;
        }
        
        renderHours(data);
    } catch (error) {
        grid.innerHTML = '<div class="loading">خطا در بارگذاری داده‌ها</div>';
        console.error('Error loading day:', error);
    }
}

/**
 * Render the hours grid
 */
function renderHours(data) {
    const grid = document.getElementById('hours-grid');
    grid.innerHTML = '';
    
    // Store data for detail view
    window.dayData = data;
    
    for (let hour = 0; hour < 24; hour++) {
        const hourData = data.hours[hour] || { status: 'no_data', count: 0, logs: [] };
        
        const hourEl = document.createElement('div');
        hourEl.className = `hour-block ${hourData.status}`;
        hourEl.innerHTML = `
            <div class="hour-label">${hour.toString().padStart(2, '0')}:00</div>
            <div class="hour-count">${hourData.count} رکورد</div>
        `;
        
        hourEl.addEventListener('click', () => {
            // Remove selected from others
            document.querySelectorAll('.hour-block').forEach(el => el.classList.remove('selected'));
            hourEl.classList.add('selected');
            showHourDetails(hour, hourData);
        });
        
        grid.appendChild(hourEl);
    }
}

/**
 * Show details for a specific hour
 */
function showHourDetails(hour, hourData) {
    const detailsEl = document.getElementById('hour-details');
    
    if (hourData.logs.length === 0) {
        detailsEl.innerHTML = `
            <h3>ساعت ${hour.toString().padStart(2, '0')}:00</h3>
            <p class="no-selection">هیچ رکوردی در این ساعت ثبت نشده</p>
        `;
        return;
    }
    
    let logsHtml = hourData.logs.map(log => `
        <li class="log-item">
            <span class="log-time">${log.time}</span>
            <span class="log-status ${log.status}">${STATUS_LABELS[log.status] || log.status}</span>
            ${log.details ? `<span class="log-details">${log.details}</span>` : ''}
        </li>
    `).join('');
    
    detailsEl.innerHTML = `
        <h3>ساعت ${hour.toString().padStart(2, '0')}:00</h3>
        <ul class="log-list">${logsHtml}</ul>
    `;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initCalendar();
    initDayDetail();
});
