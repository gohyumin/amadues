// 统一API请求方法，兼容 demo_fixed.html
const API_URL = '/api/words';
async function makeApiRequest(endpoint, method = 'GET', data = null) {
  try {
    const options = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    };
    const payload = { endpoint, method, data };
    console.log('makeApiRequest payload:', payload); // 调试输出
    options.body = JSON.stringify(payload);
    const response = await fetch(API_URL, options);
    const result = await response.json();
    if (!response.ok || result.success === false) {
      throw new Error(result.error || result.message || `HTTP ${response.status}`);
    }
    return result;
  } catch (error) {
    console.error('API请求失败:', error);
    showWordsError(error.message || error);
    throw error;
  }
}

function showWordsError(message) {
  let errorContainer = document.getElementById('wordsErrorContainer');
  if (!errorContainer) {
    errorContainer = document.createElement('div');
    errorContainer.id = 'wordsErrorContainer';
    errorContainer.className = 'alert alert-danger';
    document.body.appendChild(errorContainer);
  }
  errorContainer.textContent = '词语数据加载失败: ' + message;
  errorContainer.style.display = 'block';
}
// 动态词语数据
let wordsList = [];
let currentPage = 0;
const pageSize = 6; // 每页显示6个词语


function renderWordsPage(pageIdx) {
  const startIdx = pageIdx * pageSize;
  const page = wordsList.slice(startIdx, startIdx + pageSize);
  const ul = document.createElement('ul');
  page.forEach(item => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="word">${item.native_word || item.word_main || item.word}</span> <span class="pinyin">${item.pinyin || item.word_pinyin || ''}</span> <span class="meaning">${item.meaning || item.word_meaning || item.target_word || ''}</span>`;
    ul.appendChild(li);
  });
  const pageDiv = document.getElementById('wordsPage');
  if (pageDiv) {
    pageDiv.innerHTML = '';
    pageDiv.appendChild(ul);
  }
}


document.addEventListener('DOMContentLoaded', function() {
  // GET 示例：获取词语数据
  makeApiRequest('/api/words', 'GET', null)
    .then(data => {
      console.log('前端收到 response:', data); // 新增调试输出
      if (Array.isArray(data.words)) {
        wordsList = data.words;
      } else if (Array.isArray(data)) {
        wordsList = data;
      } else {
        wordsList = [];
      }
      renderWordsPage(currentPage);
    })
    .catch(() => {
      wordsList = [];
      renderWordsPage(currentPage);
    });

  // POST 示例：添加单词
  // makeApiRequest('/api/words', 'POST', { native_word: '苹果', target_word: 'apple' })
  //   .then(data => { console.log('POST 响应:', data); })
  //   .catch(err => { console.error('POST 错误:', err); });

  if (window.location.hash === '#words') {
    showWordsPanel();
  }
  document.querySelectorAll('.menu-item').forEach(function(btn) {
    btn.addEventListener('click', function() {
      if (btn.dataset.target === 'words') {
        showWordsPanel();
        window.location.hash = '#words';
      }
    });
  });
  // 分页按钮事件
  document.getElementById('wordsPrev')?.addEventListener('click', function() {
    if (currentPage > 0) {
      currentPage--;
      renderWordsPage(currentPage);
    }
  });
  document.getElementById('wordsNext')?.addEventListener('click', function() {
    if ((currentPage + 1) * pageSize < wordsList.length) {
      currentPage++;
      renderWordsPage(currentPage);
    }
  });
});


function showWordsPanel() {
  document.querySelectorAll('.panel').forEach(function(panel) {
    panel.classList.remove('active');
  });
  var wordsPanel = document.getElementById('panel-words');
  if (wordsPanel) {
    wordsPanel.classList.add('active');
    renderWordsPage(currentPage);
  }
}
