// Register/Login page behaviors

// Initialize AOS animations
if (window.AOS) {
  AOS.init();
}

// ===== 用户资料管理接口 =====

/**
 * 获取当前登录用户的资料和偏好设置
 * 类似于 chatbot.js 中的接口模式
 */
function loadUserProfile() {
  console.log('📜 开始加载用户资料...');
  
  fetch('/api/user/profile', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(function(response) {
    if (!response.ok) {
      throw new Error('HTTP ' + response.status);
    }
    return response.json();
  })
  .then(function(data) {
    console.log('✅ 用户资料加载成功:', data);
    
    if (data.success) {
      displayUserProfile(data.user);
      console.log('📝 显示用户资料: ' + data.user.username);
    } else {
      console.log('📋 加载用户资料失败:', data.error);
      displayError('加载用户资料失败: ' + (data.error || '未知错误'));
    }
  })
  .catch(function(error) {
    console.error('❌ 加载用户资料失败:', error);
    if (error.message.includes('401')) {
      displayError('请先登录');
    } else {
      displayError('网络错误: ' + error.message);
    }
  });
}

/**
 * 更新当前用户的偏好设置
 * @param {Object} preferences 偏好设置对象
 */
function updateUserPreferences(preferences) {
  console.log('📝 开始更新用户偏好:', preferences);
  
  fetch('/api/user/preferences', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(preferences)
  })
  .then(function(response) {
    if (!response.ok) {
      throw new Error('HTTP ' + response.status);
    }
    return response.json();
  })
  .then(function(data) {
    console.log('✅ 偏好设置更新响应:', data);
    
    if (data.success) {
      console.log('📝 偏好设置更新成功');
      displaySuccess('偏好设置更新成功');
      // 重新加载用户资料
      loadUserProfile();
    } else {
      console.log('📋 更新偏好设置失败:', data.error);
      displayError('更新失败: ' + (data.error || '未知错误'));
    }
  })
  .catch(function(error) {
    console.error('❌ 更新偏好设置失败:', error);
    if (error.message.includes('401')) {
      displayError('请先登录');
    } else {
      displayError('网络错误: ' + error.message);
    }
  });
}

/**
 * 显示用户资料到页面
 * @param {Object} user 用户对象
 */
function displayUserProfile(user) {
  console.log('� 用户资料:', user);
  
  // 示例：如果页面上有用户资料显示容器
  var profileContainer = document.getElementById('userProfileContainer');
  if (profileContainer) {
    var preferences = user.preferences || {};
    
    profileContainer.innerHTML = 
      '<div class="user-profile">' +
        '<h3>用户资料</h3>' +
        '<div class="profile-item"><strong>用户名:</strong> ' + (user.username || '未设置') + '</div>' +
        '<div class="profile-item"><strong>邮箱:</strong> ' + (user.email || '未设置') + '</div>' +
        '<h4>学习偏好</h4>' +
        '<div class="profile-item"><strong>目标语言:</strong> ' + (preferences.target_language || '未设置') + '</div>' +
        '<div class="profile-item"><strong>母语:</strong> ' + (preferences.native_language || '未设置') + '</div>' +
        '<div class="profile-item"><strong>水平:</strong> ' + (preferences.level || '未设置') + '</div>' +
        '<div class="profile-item"><strong>年龄:</strong> ' + (preferences.age || '未设置') + '</div>' +
        '<div class="profile-item"><strong>国家:</strong> ' + (preferences.country || '未设置') + '</div>' +
        '<div class="profile-item"><strong>兴趣1:</strong> ' + (preferences.interest1 || '未设置') + '</div>' +
        '<div class="profile-item"><strong>兴趣2:</strong> ' + (preferences.interest2 || '未设置') + '</div>' +
      '</div>';
  }
  
  // 如果有偏好设置表单，填充数据
  fillPreferencesForm(user.preferences || {});
}

/**
 * 填充偏好设置表单
 * @param {Object} preferences 偏好设置对象
 */
function fillPreferencesForm(preferences) {
  // 示例：填充表单字段
  var formFields = [
    'target_language', 'native_language', 'level', 
    'age', 'country', 'interest1', 'interest2'
  ];
  
  formFields.forEach(function(fieldName) {
    var field = document.getElementById(fieldName);
    if (field && preferences[fieldName]) {
      field.value = preferences[fieldName];
    }
  });
}

/**
 * 显示错误消息
 * @param {String} message 错误消息
 */
function displayError(message) {
  console.error('❌ 错误:', message);
  
  // 查找错误显示容器
  var errorContainer = document.getElementById('errorContainer');
  if (errorContainer) {
    errorContainer.innerHTML = '<div class="alert alert-danger">' + message + '</div>';
    errorContainer.style.display = 'block';
  } else {
    // 备用：使用alert显示错误
    alert('错误: ' + message);
  }
}

/**
 * 显示成功消息
 * @param {String} message 成功消息
 */
function displaySuccess(message) {
  console.log('✅ 成功:', message);
  
  // 查找成功消息显示容器
  var successContainer = document.getElementById('successContainer');
  if (successContainer) {
    successContainer.innerHTML = '<div class="alert alert-success">' + message + '</div>';
    successContainer.style.display = 'block';
  }
}

// 示例：页面加载完成后自动加载用户资料 (可选，根据需要启用)
// setTimeout(function() {
//   loadUserProfile();
// }, 1000);

// ===== 原有的注册/登录逻辑 =====

// Confirm password check on register form
(function () {
  var form = document.getElementById('registerForm');
  if (!form) return;
  form.addEventListener('submit', function (e) {
    var pwd = form.querySelector('input[name="password"]').value;
    var cpwd = form.querySelector('input[name="confirm_password"]').value;
    if (pwd !== cpwd) {
      e.preventDefault();
      alert('Passwords do not match.');
    }
  });
})();

// If success message exists, switch to Login tab automatically
(function () {
  var alerts = document.querySelectorAll('.alert.alert-success');
  if (alerts.length) {
    var loginTab = document.getElementById('login-tab');
    if (loginTab) loginTab.click();
  }
})();

// Handle URL params for tab switching and email prefill
(function () {
  var urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('tab') === 'login') {
    var loginTab = document.getElementById('login-tab');
    if (loginTab) loginTab.click();
  }
  var preEmail = urlParams.get('email');
  if (preEmail) {
    var lf = document.getElementById('loginForm');
    if (lf) {
      var emailInput = lf.querySelector('input[name="email"]');
      if (emailInput) emailInput.value = preEmail;
    }
  }
})();


