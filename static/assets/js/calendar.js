// Learning Calendar JavaScript
class LearningCalendar {
  constructor() {
    this.currentMonth = new Date();
    this.checkinDates = [];
    this.stats = {
      total_days: 0,
      current_streak: 0,
      longest_streak: 0,
      this_month: 0,
      checked_today: false
    };
    this.initialized = false;
  }

  // Initialize the calendar
  async init() {
    if (this.initialized) return;
    
    console.log('Initializing Learning Calendar...');
    
    try {
      await this.loadStats();
      this.generateCalendar(); // 简化：只生成日历，不更新统计
      this.initialized = true;
      console.log('Learning Calendar initialized successfully');
    } catch (error) {
      console.error('Failed to initialize calendar:', error);
      // 即使加载失败，也要显示基本日历
      this.generateCalendar();
      this.initialized = true;
    }
  }

  // Load statistics from server
  async loadStats() {
    try {
      const response = await fetch('/api/checkin/stats');
      const data = await response.json();
      
      if (data.success) {
        this.stats = data.stats;
        this.checkinDates = data.checkin_dates || [];
        console.log('Loaded stats:', this.stats);
        console.log('Loaded checkin dates:', this.checkinDates);
      } else {
        console.error('Failed to load stats:', data.error);
        this.setDefaultValues();
      }
    } catch (error) {
      console.error('Error loading stats:', error);
      this.setDefaultValues();
    }
  }

  // Set default values when loading fails
  setDefaultValues() {
    this.stats = {
      total_days: 0,
      current_streak: 0,
      longest_streak: 0,
      this_month: 0,
      checked_today: false
    };
    this.checkinDates = [];
  }

  // Update statistics display (简化版：不再需要更新统计卡片)
  updateStats() {
    // 这个方法现在什么都不做，因为我们移除了统计卡片
    console.log('Stats updated (no UI elements to update)');
  }

  // Generate activity level (1-4) based on date for GitHub-style heatmap
  getActivityLevel(dateStr) {
    // Create a pseudo-random number based on date string for consistent results
    let hash = 0;
    for (let i = 0; i < dateStr.length; i++) {
      const char = dateStr.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    
    // Use absolute value and modulo to get a number between 0-99
    const pseudoRandom = Math.abs(hash) % 100;
    
    // Weight the distribution to look more realistic (most days are low activity)
    if (pseudoRandom < 50) return 1;      // 50% chance - Low activity (darkest)
    else if (pseudoRandom < 75) return 2; // 25% chance - Medium activity
    else if (pseudoRandom < 90) return 3; // 15% chance - High activity  
    else return 4;                        // 10% chance - Very high activity (lightest)
  }

  // Generate calendar grid
  generateCalendar() {
    console.log('generateCalendar() called');
    const calendarDays = document.getElementById('calendarDays');
    const currentMonthElement = document.getElementById('calendarCurrentMonth');
    
    console.log('calendarDays element:', calendarDays);
    console.log('currentMonthElement:', currentMonthElement);
    
    if (!calendarDays || !currentMonthElement) {
      console.warn('Calendar elements not found');
      console.log('Available elements:', {
        calendarDays: !!calendarDays,
        currentMonthElement: !!currentMonthElement
      });
      return;
    }
    
    const year = this.currentMonth.getFullYear();
    const month = this.currentMonth.getMonth();
    
    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    
    // 更新月份显示
    currentMonthElement.textContent = `${monthNames[month]} ${year}`;
    console.log(`Generating calendar for ${monthNames[month]} ${year}`);
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const firstDayWeekday = firstDay.getDay();
    const daysInMonth = lastDay.getDate();
    
    // Clear previous calendar
    calendarDays.innerHTML = '';
    console.log(`Month has ${daysInMonth} days, starts on day ${firstDayWeekday}`);
    
    // Add empty cells for days before the first day of month
    for (let i = 0; i < firstDayWeekday; i++) {
      const emptyDay = document.createElement('div');
      emptyDay.className = 'calendar-day other-month';
      const prevMonthLastDay = new Date(year, month, 0).getDate();
      emptyDay.textContent = prevMonthLastDay - firstDayWeekday + i + 1;
      calendarDays.appendChild(emptyDay);
    }
    
    // Add days of the current month
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    console.log(`Today is: ${todayStr}`);
    console.log('Available checkin dates:', this.checkinDates);
    
    for (let day = 1; day <= daysInMonth; day++) {
      const dayElement = document.createElement('div');
      dayElement.className = 'calendar-day';
      dayElement.textContent = day;
      
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      
      // Check if this is today
      if (dateStr === todayStr) {
        dayElement.classList.add('today');
        console.log(`Found today: ${dateStr}`);
      }
      
      // Check if this day has a learning record
      if (this.checkinDates && this.checkinDates.includes(dateStr)) {
        dayElement.classList.add('learned');
        
        // Add random activity level (GitHub-style)
        const activityLevel = this.getActivityLevel(dateStr);
        if (activityLevel > 0) {
          dayElement.classList.add(`level-${activityLevel}`);
        }
        
        console.log(`Found learning day: ${dateStr} (level ${activityLevel})`);
      }
      
      // Add click event for future interactivity
      dayElement.addEventListener('click', () => {
        this.onDayClick(dateStr, dayElement);
      });
      
      calendarDays.appendChild(dayElement);
    }
    
    // Add empty cells for days after the last day of month
    const currentCells = calendarDays.children.length;
    const maxCells = 42; // 6 rows × 7 days
    let nextMonthDay = 1;
    
    while (currentCells + nextMonthDay - 1 < maxCells && nextMonthDay <= 14) {
      const emptyDay = document.createElement('div');
      emptyDay.className = 'calendar-day other-month';
      emptyDay.textContent = nextMonthDay;
      calendarDays.appendChild(emptyDay);
      nextMonthDay++;
    }
    
    console.log(`Calendar generated with ${calendarDays.children.length} total cells`);
  }

  // Handle day click events
  onDayClick(dateStr, element) {
    const today = new Date().toISOString().split('T')[0];
    
    if (dateStr === today && !this.stats.checked_today) {
      // If clicking on today and not checked in yet, suggest check-in
      if (confirm('Would you like to check in for today?')) {
        this.performCheckin();
      }
    } else {
      // Show day details
      const hasLearning = this.checkinDates.includes(dateStr);
      const message = hasLearning 
        ? `✅ You learned on ${dateStr}! Great job!`
        : `No learning record for ${dateStr}`;
      
      // Create a small tooltip or modal (simple alert for now)
      this.showDayTooltip(element, message);
    }
  }

  // Show day tooltip
  showDayTooltip(element, message) {
    // Simple implementation - you can enhance this with a proper tooltip
    const existingTooltip = document.querySelector('.calendar-tooltip');
    if (existingTooltip) {
      existingTooltip.remove();
    }

    const tooltip = document.createElement('div');
    tooltip.className = 'calendar-tooltip';
    tooltip.textContent = message;
    tooltip.style.cssText = `
      position: absolute;
      background: var(--surface-color);
      border: 1px solid var(--accent-color);
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 12px;
      z-index: 1000;
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
      pointer-events: none;
    `;

    document.body.appendChild(tooltip);

    const rect = element.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;

    setTimeout(() => {
      if (tooltip.parentNode) {
        tooltip.remove();
      }
    }, 2000);
  }

  // Perform check-in
  async performCheckin() {
    try {
      const response = await fetch('/api/checkin', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.success) {
        await this.loadStats();
        this.updateStats();
        this.generateCalendar();
        
        // Also update main dashboard if available
        if (window.updateDashboardStats) {
          window.updateDashboardStats();
        }
        
        alert('✅ Check-in successful! Keep up the great work!');
      } else {
        alert(data.error || 'Check-in failed');
      }
    } catch (error) {
      console.error('Check-in error:', error);
      alert('Check-in request failed, please try again');
    }
  }

  // Change month
  changeMonth(direction) {
    this.currentMonth.setMonth(this.currentMonth.getMonth() + direction);
    this.generateCalendar();
  }

  // Refresh calendar data
  async refresh() {
    await this.loadStats();
    this.generateCalendar(); // 简化：不需要更新统计了
  }
}

// Global calendar instance
let learningCalendar;

// Global function for month navigation (called from HTML)
function changeCalendarMonth(direction) {
  console.log('changeCalendarMonth called with direction:', direction);
  
  // Try both global variable and window property
  const calendar = window.learningCalendar || learningCalendar;
  
  if (calendar) {
    console.log('Calendar instance found, changing month...');
    calendar.changeMonth(direction);
  } else {
    console.warn('No calendar instance found for month navigation');
    console.log('Available instances:', {
      'window.learningCalendar': !!window.learningCalendar,
      'learningCalendar': typeof learningCalendar !== 'undefined' ? !!learningCalendar : false
    });
  }
}

// Make function globally available
window.changeCalendarMonth = changeCalendarMonth;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  console.log('Calendar.js DOM ready event fired');
  
  // Only initialize if we're on a page with calendar elements
  const calendarDays = document.getElementById('calendarDays');
  if (calendarDays) {
    console.log('Calendar elements found, initializing...');
    learningCalendar = new LearningCalendar();
    learningCalendar.init();
  } else {
    console.log('Calendar elements not found, waiting for dynamic load...');
    
    // Use a MutationObserver to detect when calendar elements are added
    const observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        if (mutation.type === 'childList') {
          const calendarDays = document.getElementById('calendarDays');
          if (calendarDays && !learningCalendar) {
            console.log('Calendar elements detected, initializing...');
            learningCalendar = new LearningCalendar();
            learningCalendar.init();
            observer.disconnect(); // Stop observing once initialized
          }
        }
      });
    });
    
    // Start observing
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LearningCalendar;
}