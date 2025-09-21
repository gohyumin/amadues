// Reveal dashboard content after overlay animation
window.addEventListener('load', function(){
  setTimeout(function(){
    var overlay=document.getElementById('dashWelcome');
    var content=document.getElementById('dashContent');
    var topbar=document.getElementById('dashTopbar');
    if (content) content.classList.remove('d-none');
    if (topbar) topbar.classList.remove('d-none');
    if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
    
    // Initialize charts after dashboard is revealed
    initializeCharts();
    
    // Note: Calendar module is now loaded on-demand when user clicks calendar panel
  }, 2100);

  var logoutBtn=document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function(){
      if (confirm('Are you sure you want to logout?')) {
        var form=document.getElementById('logoutForm');
        if (form) form.submit();
      }
    });
  }

  // Sidebar navigation switching
  var menu=document.getElementById('dashMenu');
  if (menu) {
    menu.addEventListener('click', function(e){
      var btn=e.target.closest('.menu-item');
      if (!btn) return;
      var target=btn.getAttribute('data-target');
      if (!target) return;
      // activate button
      var items=menu.querySelectorAll('.menu-item');
      items.forEach(function(i){ i.classList.toggle('active', i===btn); });
      // show panel
      var panels=document.querySelectorAll('.dash-main .panel');
      panels.forEach(function(p){ p.classList.remove('active'); });
      var panel=document.getElementById('panel-'+target);
      if (panel) panel.classList.add('active');

      // Lazy-load assets for chatbot panel
      if (target==='chatbot') {
        // Load CSS once
        if (!document.querySelector('link[data-chatbot-css]')) {
          var l=document.createElement('link');
          l.rel='stylesheet';
          l.href='/static/assets/css/chatbot.css';
          l.setAttribute('data-chatbot-css','1');
          document.head.appendChild(l);
        }
        // Load JS once (and init after load if needed)
        if (!window.__chatbotLoaded) {
          var s=document.createElement('script');
          s.src='/static/assets/js/chatbot.js';
          s.onload=function(){ window.__chatbotLoaded=true; };
          document.body.appendChild(s);
        }
      }

      // Lazy-load assets for exercises panel
      if (target==='exercises') {
        // Load CSS once
        if (!document.querySelector('link[data-exercise-css]')) {
          var l=document.createElement('link');
          l.rel='stylesheet';
          l.href='/static/assets/css/exercise.css';
          l.setAttribute('data-exercise-css','1');
          document.head.appendChild(l);
        }
        // Load JS once (and init after load if needed)
        if (!window.__exerciseLoaded) {
          var s=document.createElement('script');
          s.src='/static/assets/js/exercise.js';
          s.onload=function(){ 
            window.__exerciseLoaded=true;
            console.log('Exercise module loaded successfully');
            // Initialize exercise after loading
            setTimeout(function() {
              if (!window.exerciseModule && window.ExerciseModule) {
                console.log('Initializing exercise after loading...');
                const exercise = new window.ExerciseModule();
                window.exerciseModule = exercise;
              }
            }, 100);
          };
          document.body.appendChild(s);
        } else {
          // Already loaded, just initialize if needed
          setTimeout(function() {
            if (!window.exerciseModule && window.ExerciseModule) {
              console.log('Initializing existing exercise...');
              const exercise = new window.ExerciseModule();
              window.exerciseModule = exercise;
            }
          }, 100);
        }
      }

      // Lazy-load assets for calendar panel
      if (target==='calendar') {
        // Load CSS once
        if (!document.querySelector('link[data-calendar-css]')) {
          var l=document.createElement('link');
          l.rel='stylesheet';
          l.href='/static/assets/css/calendar.css';
          l.setAttribute('data-calendar-css','1');
          document.head.appendChild(l);
        }
        // Load JS once (and init after load if needed)
        if (!window.__calendarLoaded) {
          var s=document.createElement('script');
          s.src='/static/assets/js/calendar.js';
          s.onload=function(){ 
            window.__calendarLoaded=true;
            console.log('Calendar module loaded successfully');
            // Initialize calendar after loading
            setTimeout(function() {
              if (!window.learningCalendar) {
                console.log('Initializing calendar after loading...');
                const calendar = new LearningCalendar();
                calendar.init();
                
                // Set both global variable and window property
                window.learningCalendar = calendar;
                if (typeof window !== 'undefined') {
                  window.learningCalendar = calendar;
                }
              }
            }, 100);
          };
          document.body.appendChild(s);
        } else {
          // Already loaded, just initialize if needed
          setTimeout(function() {
            if (!window.learningCalendar) {
              console.log('Initializing existing calendar...');
              const calendar = new LearningCalendar();
              calendar.init();
              
              // Set both global variable and window property
              window.learningCalendar = calendar;
              if (typeof window !== 'undefined') {
                window.learningCalendar = calendar;
              }
            }
          }, 100);
        }
      }
    });
  }

  // Theme toggle
  var themeBtn = document.getElementById('themeToggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', function(){
      var html = document.documentElement;
      var dark = (html.getAttribute('data-theme') === 'dark');
      var next = dark ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      // Switch page background class
      var body = document.body;
      if (next === 'dark') {
        body.classList.remove('light-background');
        body.classList.add('dark-background');
      } else {
        body.classList.remove('dark-background');
        body.classList.add('light-background');
      }
      localStorage.setItem('amadeus_theme', next);
      themeBtn.innerHTML = next === 'dark' ? '<i class="bi bi-moon"></i>' : '<i class="bi bi-sun"></i>';
    });
    // Init from storage
    var saved = localStorage.getItem('amadeus_theme');
    if (saved) {
      document.documentElement.setAttribute('data-theme', saved);
      themeBtn.innerHTML = saved === 'dark' ? '<i class="bi bi-moon"></i>' : '<i class="bi bi-sun"></i>';
      if (saved === 'dark') { document.body.classList.remove('light-background'); document.body.classList.add('dark-background'); }
    }
  }
});

// Load calendar module function
function loadCalendarModule() {
  console.log('Loading calendar module...');
  
  // Load calendar CSS
  if (!document.querySelector('link[data-calendar-css]')) {
    var l = document.createElement('link');
    l.rel = 'stylesheet';
    l.href = '/static/assets/css/calendar.css';
    l.setAttribute('data-calendar-css', '1');
    document.head.appendChild(l);
    console.log('Calendar CSS loaded');
  }
  
  // Load calendar JS
  if (!window.__calendarLoaded) {
    var s = document.createElement('script');
    s.src = '/static/assets/js/calendar.js';
    s.onload = function() {
      window.__calendarLoaded = true;
      console.log('Calendar module loaded successfully');
    };
    document.body.appendChild(s);
  }
}

// Chart initialization function
function initializeCharts() {
  // Weekly Progress Bar Chart
  const weeklyProgressCtx = document.getElementById('weeklyProgressChart');
  if (weeklyProgressCtx) {
    new Chart(weeklyProgressCtx, {
      type: 'bar',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
          label: 'Study Minutes',
          data: [45, 30, 60, 20, 55, 40, 0],
          backgroundColor: [
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 99, 132, 0.8)',
            'rgba(255, 205, 86, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)',
            'rgba(255, 159, 64, 0.8)',
            'rgba(201, 203, 207, 0.8)'
          ],
          borderColor: [
            'rgba(54, 162, 235, 1)',
            'rgba(255, 99, 132, 1)',
            'rgba(255, 205, 86, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)',
            'rgba(201, 203, 207, 1)'
          ],
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 80,
            ticks: {
              stepSize: 20,
              callback: function(value) {
                return value + 'm';
              }
            },
            grid: {
              color: 'rgba(0,0,0,0.1)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        },
        animation: {
          duration: 2000,
          easing: 'easeOutBounce'
        }
      }
    });
  }

  // Language Distribution Doughnut Chart
  const languageDistCtx = document.getElementById('languageDistributionChart');
  if (languageDistCtx) {
    new Chart(languageDistCtx, {
      type: 'doughnut',
      data: {
        labels: ['Chinese', 'Japanese', 'Korean', 'English'],
        datasets: [{
          data: [35, 25, 20, 20],
          backgroundColor: [
            '#FF6B6B',
            '#4ECDC4',
            '#45B7D1',
            '#96CEB4'
          ],
          borderColor: '#fff',
          borderWidth: 3,
          hoverOffset: 10
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true,
              font: {
                size: 12
              }
            }
          }
        },
        animation: {
          animateRotate: true,
          duration: 2000
        },
        cutout: '60%'
      }
    });
  }
}

// Add smooth animations for stat cards
document.addEventListener('DOMContentLoaded', function() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe stat cards for animation
  document.querySelectorAll('.stat-card, .chart-card, .dash-card').forEach(card => {
    observer.observe(card);
  });

  // Initialize dashboard learning check-in functionality
  initializeDashboardCheckin();
});

// Dashboard Check-in Functionality
let dashboardStats = {
  total_days: 0,
  current_streak: 0,
  this_month: 0,
  checked_today: false
};

// Initialize dashboard check-in system
function initializeDashboardCheckin() {
  loadDashboardStats();
}

// Load learning statistics for dashboard
async function loadDashboardStats() {
  try {
    const response = await fetch('/api/checkin/stats');
    const data = await response.json();
    
    if (data.success) {
      dashboardStats = data.stats;
      updateDashboardStats();
      updateCheckinButton();
    }
  } catch (error) {
    console.error('Failed to load dashboard stats:', error);
  }
}

// Update dashboard statistics (exported for use by calendar module)
function updateDashboardStats() {
  const totalDaysElement = document.getElementById('totalDaysLearned');
  const streakDaysElement = document.getElementById('streakDays');
  const monthDaysElement = document.getElementById('monthDays');
  
  if (totalDaysElement) totalDaysElement.textContent = dashboardStats.total_days;
  if (streakDaysElement) streakDaysElement.textContent = dashboardStats.current_streak;
  if (monthDaysElement) monthDaysElement.textContent = dashboardStats.this_month;
}

// Update check-in button status
function updateCheckinButton() {
  const statusElement = document.getElementById('checkinStatus');
  const btnElement = document.getElementById('checkinBtn');
  
  if (!statusElement || !btnElement) return;
  
  if (dashboardStats.checked_today) {
    statusElement.textContent = 'Checked in today ✅';
    statusElement.className = 'text-success';
    btnElement.disabled = true;
    btnElement.textContent = 'Already Checked In';
    btnElement.className = 'btn btn-success btn-sm';
  } else {
    statusElement.textContent = 'Not checked in';
    statusElement.className = 'text-muted';
    btnElement.disabled = false;
    btnElement.textContent = 'Check In Now';
    btnElement.className = 'btn btn-primary btn-sm';
  }
}

// Perform daily check-in (global function)
async function dailyCheckin() {
  const btnElement = document.getElementById('checkinBtn');
  const originalText = btnElement.textContent;
  
  try {
    btnElement.disabled = true;
    btnElement.textContent = 'Checking in...';
    
    const response = await fetch('/api/checkin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Check-in successful, reload stats
      await loadDashboardStats();
      showCheckinSuccess();
      
      // Refresh calendar if it's loaded
      if (window.learningCalendar && window.learningCalendar.refresh) {
        window.learningCalendar.refresh();
      }
    } else {
      alert(data.error || 'Check-in failed');
      btnElement.disabled = false;
      btnElement.textContent = originalText;
    }
  } catch (error) {
    console.error('Check-in request failed:', error);
    alert('Check-in request failed, please try again');
    btnElement.disabled = false;
    btnElement.textContent = originalText;
  }
}

// Show check-in success animation
function showCheckinSuccess() {
  const checkinCard = document.getElementById('checkinCard');
  if (checkinCard) {
    checkinCard.style.animation = 'pulse 0.6s ease-in-out';
    setTimeout(() => {
      checkinCard.style.animation = '';
    }, 600);
  }
  
  // Show success message
  const statusElement = document.getElementById('checkinStatus');
  if (statusElement) {
    statusElement.innerHTML = '🎉 Great job! Keep it up!';
    statusElement.className = 'text-success';
  }
}

// Export functions for use by other modules
window.updateDashboardStats = updateDashboardStats;
