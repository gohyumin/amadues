
// 分页词语数据
const wordsPages = [
  [
    { word: '苹果', pinyin: 'píng guǒ', meaning: 'apple' },
    { word: '书', pinyin: 'shū', meaning: 'book' },
    { word: '猫', pinyin: 'māo', meaning: 'cat' }
  ],
  [
    { word: '狗', pinyin: 'gǒu', meaning: 'dog' },
    { word: '桌子', pinyin: 'zhuō zi', meaning: 'table' },
    { word: '椅子', pinyin: 'yǐ zi', meaning: 'chair' }
  ]
];
let currentPage = 0;

function renderWordsPage(pageIdx) {
  const page = wordsPages[pageIdx];
  const ul = document.createElement('ul');
  page.forEach(item => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="word">${item.word}</span> <span class="pinyin">${item.pinyin}</span> <span class="meaning">${item.meaning}</span>`;
    ul.appendChild(li);
  });
  const pageDiv = document.getElementById('wordsPage');
  if (pageDiv) {
    pageDiv.innerHTML = '';
    pageDiv.appendChild(ul);
  }
}

document.addEventListener('DOMContentLoaded', function() {
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
    if (currentPage < wordsPages.length - 1) {
      currentPage++;
      renderWordsPage(currentPage);
    }
  });
  // 初始渲染第一页
  renderWordsPage(currentPage);
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
