(function(){
  // 防止重复初始化
  if (window.chatbotInitialized) {
    console.log('⚠️ Chatbot already initialized, skipping...');
    return;
  }
  window.chatbotInitialized = true;
  
  var chatForm = document.getElementById('chatForm');
  var chatText = document.getElementById('chatText');
  var chatLog = document.getElementById('chatLog');
  var recordBtn = document.getElementById('recordBtn');
  var recHint = document.getElementById('recHint');
  if (!chatForm || !chatLog) return;

  // 加载聊天历史记录
  function loadChatHistory() {
    console.log('📜 开始加载聊天历史记录...');
    
    fetch('/api/chatbot/history', {
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
      console.log('✅ 聊天历史加载成功:', data);
      
      if (data.success && data.messages && Array.isArray(data.messages)) {
        // 清空当前聊天记录（如果有的话）
        chatLog.innerHTML = '';
        
        // 添加详细的调试信息
        console.log('📊 历史消息详情:');
        data.messages.forEach(function(msg, index) {
          console.log(`消息 ${index + 1}:`, {
            sender: msg.sender,
            message_type: msg.message_type,
            message: msg.message,
            audio_url: msg.audio_url,
            timestamp: msg.timestamp
          });
        });
        
        // 消息已经按正确顺序从后端返回，直接显示
        data.messages.forEach(function(msg) {
          displayHistoryMessage(msg);
        });
        
        console.log('📝 显示了 ' + data.messages.length + ' 条历史消息');
        
        // 滚动到底部
        chatLog.scrollTop = chatLog.scrollHeight;
      } else {
        console.log('📋 没有找到聊天历史记录');
      }
    })
    .catch(function(error) {
      console.error('❌ 加载聊天历史失败:', error);
      // 不显示错误给用户，静默处理
    });
  }

  // 显示历史消息 - 使用与当前聊天相同的样式
  function displayHistoryMessage(msg) {
    console.log('🎨 显示历史消息:', msg);
    var isSystemMessage = (msg.sender === 'system');
    
    if (isSystemMessage) {
      // 机器人/系统消息 - 使用与 appendMessage 相同的结构
      var container = document.createElement('div');
      container.className = 'msg-row';
      
      var avatarWrap = document.createElement('div');
      avatarWrap.className = 'avatar';
      var img = document.createElement('img');
      var botAvatar = document.querySelector('.chat-container')?.getAttribute('data-bot-avatar');
      if (botAvatar) img.src = botAvatar;
      avatarWrap.appendChild(img);
      
      var bubble = document.createElement('div');
      bubble.className = 'msg bot';
      bubble.textContent = msg.message || '';
      
      container.appendChild(avatarWrap);
      container.appendChild(bubble);
      chatLog.appendChild(container);
    } else {
      // 用户消息 - 使用与 appendMessage 相同的结构
      console.log('👤 用户消息 - 类型:', msg.message_type, '音频URL:', msg.audio_url);
      
      if (msg.message_type === 'audio' && msg.audio_url) {
        console.log('🎵 显示音频消息，URL:', msg.audio_url);
        // 音频消息
        var messageContainer = document.createElement('div');
        messageContainer.className = 'user-message-container';
        
        var el = document.createElement('div');
        el.className = 'msg user';
        
        var wrapU = document.createElement('div');
        wrapU.className = 'audio-bubble';
        var audioU = document.createElement('audio');
        audioU.controls = true;
        audioU.src = msg.audio_url;
        wrapU.appendChild(audioU);
        
        if (msg.message && msg.message.trim()) {
          var captionU = document.createElement('div');
          captionU.textContent = msg.message;
          wrapU.appendChild(captionU);
        }
        
        el.appendChild(wrapU);
        messageContainer.appendChild(el);
        chatLog.appendChild(messageContainer);
      } else {
        console.log('📝 显示文本消息:', msg.message);
        // 文本消息
        var el = document.createElement('div');
        el.className = 'msg user';
        el.textContent = msg.message || '';
        chatLog.appendChild(el);
      }
    }
  }

  // 页面加载完成后自动加载聊天历史
  setTimeout(function() {
    loadChatHistory();
  }, 500); // 延迟500ms确保页面完全加载

  // 创建语音识别结果的彩色显示
  function createSpeechAnalysisDisplay(recognizedText, wordsAnalysis, referenceText) {
    console.log('🎨 创建语音分析显示:', { recognizedText, wordsAnalysis, referenceText });
    
    if (!wordsAnalysis || !Array.isArray(wordsAnalysis) || wordsAnalysis.length === 0) {
      // 如果没有单词分析数据，返回普通文本
      console.log('⚠️ 没有单词分析数据，显示普通文本');
      return '<div class="recognized-text">' + (recognizedText || '') + '</div>';
    }
    
    console.log('📝 单词分析数据:', wordsAnalysis);
    
    // 创建单词映射
    var wordMap = {};
    wordsAnalysis.forEach(function(wordInfo, idx) {
      if (wordInfo.word && wordInfo.index) {
        wordMap[wordInfo.index] = wordInfo;
        console.log('📍 映射单词 ' + wordInfo.index + ': ' + wordInfo.word + ' (' + wordInfo.colorClass + ')');
      }
    });
    
    // 使用识别文本作为主要显示文本
    var textToProcess = recognizedText || '';
    console.log('📄 处理文本:', textToProcess);
    
    if (!textToProcess) {
      console.log('⚠️ 没有要处理的文本');
      return '<div class="recognized-text">无识别文本</div>';
    }
    
    // 将文本按单词和空格分割
    var segments = textToProcess.split(/(\s+)/); // 保留空格
    var htmlParts = [];
    var wordIndex = 1; // 单词索引从1开始
    
    segments.forEach(function(segment, segmentIdx) {
      if (segment.trim() === '') {
        // 保留空格和换行
        htmlParts.push(segment);
      } else {
        // 处理单词
        var wordInfo = wordMap[wordIndex];
        console.log('🔍 处理片段 ' + segmentIdx + ': "' + segment + '", 单词索引: ' + wordIndex, wordInfo);
        
        if (wordInfo) {
          var colorClass = wordInfo.colorClass || 'word-normal';
          var tooltip = '';
          
          // 构建工具提示
          if (wordInfo.errorType && wordInfo.errorType !== '') {
            tooltip += '错误类型: ' + wordInfo.errorType;
          }
          if (wordInfo.accuracyScore !== undefined && wordInfo.accuracyScore > 0) {
            if (tooltip) tooltip += ' | ';
            tooltip += '准确度: ' + wordInfo.accuracyScore + '%';
          }
          
          // 遗漏的单词特殊处理
          if (wordInfo.errorTypeEn === 'Omission') {
            console.log('  -> 遗漏单词，特殊样式');
            htmlParts.push('<span class="word-highlight word-omission" title="' + 
              (tooltip || '遗漏') + '">' + segment + '</span>');
          } else {
            console.log('  -> 普通单词，颜色类: ' + colorClass);
            htmlParts.push('<span class="word-highlight ' + colorClass + '" title="' + 
              (tooltip || '正确') + '">' + segment + '</span>');
          }
        } else {
          // 没有分析数据的单词，使用普通样式
          console.log('  -> 没有分析数据，普通样式');
          htmlParts.push('<span class="word-normal">' + segment + '</span>');
        }
        wordIndex++;
      }
    });
    
    var analysisHtml = '<div class="speech-analysis">';
    analysisHtml += '<div class="recognized-text">' + htmlParts.join('') + '</div>';
    
    // 如果有参考文本且与识别文本不同，也显示出来
    if (referenceText && referenceText !== recognizedText) {
      analysisHtml += '<div style="margin-top: 8px; font-size: 12px; color: #6c757d;">';
      analysisHtml += '<strong>参考文本:</strong> ' + referenceText;
      analysisHtml += '</div>';
    }
    

    
    analysisHtml += '</div>';
    console.log('✅ 生成的HTML:', analysisHtml);
    return analysisHtml;
  }

  function formatBotAnalysisReport(text) {
    // 将Markdown样式的文本转换为HTML
    var html = text
      // 处理粗体标记
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // 处理表情符号和项目符号
      .replace(/^• /gm, '<span class="bullet">•</span> ')
      // 处理换行
      .replace(/\n/g, '<br>')
      // 处理标题样式
      .replace(/📥 <strong>接收数据:<\/strong>/g, '<div class="analysis-section"><h4>📥 接收数据:</h4>')
      .replace(/🎤 <strong>语音转录:<\/strong>/g, '</div><div class="analysis-section"><h4>🎤 语音转录:</h4>')
      .replace(/📊 <strong>发音评估结果:<\/strong>/g, '</div><div class="analysis-section"><h4>📊 发音评估结果:</h4>')
      .replace(/📝 <strong>词汇分析:<\/strong>/g, '</div><div class="analysis-section"><h4>📝 词汇分析:</h4>')
      .replace(/⏱️ <strong>API响应时间:<\/strong>/g, '</div><div class="analysis-section"><h4>⏱️ API响应时间:</h4>')
      .replace(/💬 <strong>你说的内容:<\/strong>/g, '</div><div class="analysis-section"><h4>💬 你说的内容:</h4>')
      .replace(/✅ <strong>处理状态:<\/strong>/g, '</div><div class="analysis-section"><h4>✅处理状态:</h4>')
      .replace(/📝 <strong>用户消息ID:<\/strong>/g, '</div><div class="analysis-section"><h4>📝 用户消息ID:</h4>')
      .replace(/🤖 <strong>机器人回复ID:<\/strong>/g, '</div><div class="analysis-section"><h4>🤖 机器人回复ID:</h4>');
      
    return '<div class="analysis-report-content">' + html + '</div></div>';
  }

  function appendMessage(text, role, audioUrl, speechData) {
    var isBot = (role !== 'user');
    var container = document.createElement('div');
    if (isBot) {
      container.className = 'msg-row bot-reply-row';
      var avatarWrap = document.createElement('div');
      avatarWrap.className = 'avatar';
      var img = document.createElement('img');
      var botAvatar = document.querySelector('.chat-container')?.getAttribute('data-bot-avatar');
      if (botAvatar) img.src = botAvatar;
      avatarWrap.appendChild(img);

      var bubble = document.createElement('div');
      bubble.className = 'msg bot bot-reply-bubble';

      if (audioUrl) {
        // 语音在上方
        var audioWrap = document.createElement('div');
        audioWrap.className = 'audio-bubble bot-audio-bubble';
        var audio = document.createElement('audio');
        audio.controls = true;
        // 兼容 TTS base64 wav 播放
        if (audioUrl.startsWith('data:audio/wav;base64,')) {
          audio.src = audioUrl.replace('data:audio/wav;base64,', 'data:audio/x-wav;base64,');
        } else {
          audio.src = audioUrl;
        }
        console.log('机器人语音 audio.src:', audio.src.slice(0, 80));
        audioWrap.appendChild(audio);
        bubble.appendChild(audioWrap);
      }

      // 文本在下方
      if (text) {
        var textDiv = document.createElement('div');
        textDiv.className = 'bot-reply-text';
        textDiv.textContent = text;
        bubble.appendChild(textDiv);
      }

      container.appendChild(avatarWrap);
      container.appendChild(bubble);
      chatLog.appendChild(container);
    } else {
      var el = document.createElement('div');
      el.className = 'msg user';
      if (audioUrl) {
        var wrapU = document.createElement('div');
        wrapU.className = 'audio-bubble';
        var audioU = document.createElement('audio');
        audioU.controls = true;
        audioU.src = audioUrl;
        wrapU.appendChild(audioU);
        el.appendChild(wrapU);
        
        // 创建容器来包含用户消息和语音分析
        var messageContainer = document.createElement('div');
        messageContainer.className = 'user-message-container';
        messageContainer.appendChild(el);
        
        // 先添加到聊天记录中，只显示音频
        chatLog.appendChild(messageContainer);
        chatLog.scrollTop = chatLog.scrollHeight;
        
        // 延迟显示文字内容
        setTimeout(function() {
          // 如果是语音消息且有语音分析数据，在消息下方单独显示
          if (speechData && (speechData.wordsAnalysis || speechData.recognizedText)) {
            var speechAnalysisDiv = document.createElement('div');
            speechAnalysisDiv.className = 'speech-analysis-below';
            speechAnalysisDiv.style.opacity = '0';
            speechAnalysisDiv.style.transform = 'translateY(10px)';
            speechAnalysisDiv.style.transition = 'all 0.5s ease';
            speechAnalysisDiv.innerHTML = createSpeechAnalysisDisplay(
              speechData.recognizedText || speechData.transcript || text,
              speechData.wordsAnalysis,
              speechData.referenceText
            );
            messageContainer.appendChild(speechAnalysisDiv);
            
            // 触发动画显示文字
            setTimeout(function() {
              speechAnalysisDiv.style.opacity = '1';
              speechAnalysisDiv.style.transform = 'translateY(0)';
            }, 100);
          } else if (text) {
            // 如果有普通文字，也延迟显示
            var textDiv = document.createElement('div');
            textDiv.className = 'message-text';
            textDiv.style.opacity = '0';
            textDiv.style.transform = 'translateY(10px)';
            textDiv.style.transition = 'all 0.5s ease';
            textDiv.textContent = text;
            wrapU.appendChild(textDiv);
            
            setTimeout(function() {
              textDiv.style.opacity = '1';
              textDiv.style.transform = 'translateY(0)';
            }, 100);
          }
          chatLog.scrollTop = chatLog.scrollHeight;
        }, 800); // 延迟800ms显示文字
        
        return; // 提前返回，不执行后面的代码
      } else {
        el.textContent = text;
        chatLog.appendChild(el);
      }
    }
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  // 防重复提交标志
  var isProcessingAudio = false;
  var isProcessingText = false;

  chatForm.addEventListener('submit', function(e){
    e.preventDefault();
    
    // 防止重复发送文本消息
    if (isProcessingText) {
      console.log('⚠️ 文本消息正在处理中，请稍候...');
      return;
    }
    
    var text = (chatText.value || '').trim();
    if (!text) return;
    
    isProcessingText = true;
    appendMessage(text, 'user');
    chatText.value = '';
    
    fetch('/api/chatbot/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    }).then(function(r){ return r.json(); }).then(function(res){
        // 通用调试输出，完整打印每个响应对象内容
        if (Array.isArray(res)) {
          res.forEach(function(item, idx) {
            console.log('Response item', idx, ':', item);
            if (item.data && typeof item.data === 'string') {
              console.log('Base64 data found at index', idx, ':', item.data);
            } else if (item.data && typeof item.data === 'object' && item.data !== null) {
              Object.keys(item.data).forEach(function(key) {
                if (typeof item.data[key] === 'string' && item.data[key].match(/^[A-Za-z0-9+/=]+$/)) {
                  console.log('Base64 data found in object at index', idx, 'key', key, ':', item.data[key]);
                }
              });
            }
          });
        } else {
          console.log('Response:', res);
          if (res.data && typeof res.data === 'string') {
            console.log('Base64 data found:', res.data);
          } else if (res.data && typeof res.data === 'object' && res.data !== null) {
            Object.keys(res.data).forEach(function(key) {
              if (typeof res.data[key] === 'string' && res.data[key].match(/^[A-Za-z0-9+/=]+$/)) {
                console.log('Base64 data found in key', key, ':', res.data[key]);
              }
            });
          }
        }
        // 检查并输出 base64 数据
        if (Array.isArray(res)) {
          res.forEach(function(item, idx) {
            if (item.data && typeof item.data === 'string') {
              console.log('Base64 data found at index', idx, ':', item.data);
            } else if (item.data && typeof item.data === 'object' && item.data !== null) {
              Object.keys(item.data).forEach(function(key) {
                if (typeof item.data[key] === 'string' && item.data[key].match(/^[A-Za-z0-9+/=]+$/)) {
                  console.log('Base64 data found in object at index', idx, 'key', key, ':', item.data[key]);
                }
              });
            }
          });
        } else if (res.data && typeof res.data === 'string') {
          console.log('Base64 data found:', res.data);
        } else if (res.data && typeof res.data === 'object' && res.data !== null) {
          Object.keys(res.data).forEach(function(key) {
            if (typeof res.data[key] === 'string' && res.data[key].match(/^[A-Za-z0-9+/=]+$/)) {
              console.log('Base64 data found in key', key, ':', res.data[key]);
            }
          });
        }
        appendMessage(res.reply || '...');
        isProcessingText = false;
    }).catch(function(){ 
      appendMessage('Failed to reach server.'); 
      isProcessingText = false;
    });
  });

  // Audio recording - 使用新的 Recorder 类
  var recorder = null;
  var audioContext = null;
  var audioStream = null;
  var blobStore = new Map(); // Map objectURL => Blob for local transcription
  
  function startRecording() {
    if (isProcessingAudio) {
      console.log('⚠️ 音频正在处理中，请稍候...');
      return;
    }
    
    if (recorder && audioContext) {
      console.log('⚠️ 已经在录音中，请先停止当前录音...');
      return;
    }
    
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream){
      console.log('🎤 开始录音...');
      audioStream = stream;
      
      // 创建 Audio Context 和 Recorder
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      var input = audioContext.createMediaStreamSource(stream);
      recorder = new Recorder(input, { numChannels: 1 });
      
      recorder.record();
      recordBtn.classList.add('active');
      recHint.classList.remove('d-none');
      console.log("Recording...");
    }).catch(function(err){ 
      console.error('❌ 麦克风权限被拒绝:', err);
      appendMessage('Microphone permission denied.'); 
    });
  }

  function stopRecording() {
    if (recorder && audioContext) {
      console.log('⏹️ 停止录音...');
      recorder.stop();
      
      recorder.exportWAV(function(blob) {
        console.log('🎤 录音结束，开始处理音频...');
        
        // 防止重复处理
        if (isProcessingAudio) {
          console.log('⚠️ 音频已在处理中，跳过重复请求');
          return;
        }
        isProcessingAudio = true;
        
        var localUrl = URL.createObjectURL(blob);
        blobStore.set(localUrl, blob);
        
        console.log('📤 开始处理音频并发送到服务器...');
        
        // 使用与frontend.html相同的方式：转换为base64并发送JSON
        console.log('🔄 转换音频为base64...');
        blob.arrayBuffer().then(function(arrayBuffer) {
          // 转换为base64（与frontend.html完全一致）
          var bytes = new Uint8Array(arrayBuffer);
          var binaryString = '';
          for (var i = 0; i < bytes.length; i++) {
            binaryString += String.fromCharCode(bytes[i]);
          }
          var base64Audio = btoa(binaryString);
          console.log('📊 Base64编码长度:', base64Audio.length);
          // 与 frontend.html 保持一致的 payload
          var payload = {
            audio: base64Audio,
            referenceText: "各个国家有各个国家的国歌",
            language: "zh-CN"
          };
          console.log('📤 发送JSON数据到服务器...');
          return fetch('/api/chatbot/message-audio', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
          });
        }).then(function(r){
          console.log('📥 服务器响应状态:', r.status);
          return r.json();
        }).then(function(res){
          console.log('✅ 服务器响应数据:', res);
          console.log('🟢 后端完整响应:', res);

          // 新格式：数组 [base64, text, 评估]
          if (Array.isArray(res) && res.length >= 3) {
            // 用户音频消息
            var userAudioUrl = localUrl;
            var speechAnalysisData = res[2].data || {};
            // 重新显示用户音频消息（带分析）
            appendMessage(speechAnalysisData.recognizedText || speechAnalysisData.transcript || '', 'user', userAudioUrl, {
              recognizedText: speechAnalysisData.recognizedText,
              referenceText: speechAnalysisData.referenceText,
              wordsAnalysis: speechAnalysisData.words,
              pronunciationScore: speechAnalysisData.overall?.pronunciationScore,
              accuracyScore: speechAnalysisData.overall?.accuracyScore,
              fluencyScore: speechAnalysisData.overall?.fluencyScore
            });

            // system语音回复
            var base64Audio = res[0].data;
            var botText = res[1].text;
            if (base64Audio) {
              // 与 frontend.html 保持一致，拼接 audio src
              var botAudioUrl = "data:audio/wav;base64," + base64Audio;
              appendMessage(botText, 'bot', botAudioUrl);
            } else {
              appendMessage(botText, 'bot');
            }
            isProcessingAudio = false;
            return;
          }

          // 兼容旧格式
          var speechAnalysisData = {
            transcript: res.transcript || '',
            recognizedText: res.recognized_text || res.transcript || '',
            referenceText: res.reference_text || "各个国家有各个国家的国歌",
            wordsAnalysis: res.words_analysis || [],
            pronunciationScore: res.pronunciation_score || 0,
            accuracyScore: res.accuracy_score || 0,
            fluencyScore: res.fluency_score || 0
          };
          console.log('🎯 语音分析数据:', speechAnalysisData);
          var lastUserMsg = chatLog.querySelector('.msg.user:last-of-type');
          if (lastUserMsg && lastUserMsg.parentNode) {
            lastUserMsg.parentNode.removeChild(lastUserMsg);
          }
          var audioUrlToUse = res.user_audio_url || localUrl;
          console.log('🎵 使用的音频URL:', audioUrlToUse);
          console.log('🎵 是否为S3 URL:', audioUrlToUse && audioUrlToUse.includes('s3.'));
          appendMessage(speechAnalysisData.transcript, 'user', audioUrlToUse, speechAnalysisData);
          var replyText = res.reply || speechAnalysisData.transcript || '...';
          appendMessage(replyText, 'bot', res.tts_url);
          isProcessingAudio = false;
        }).catch(function(err){
          console.error('❌ 音频处理失败:', err);
          appendMessage('Failed to process audio.');
          isProcessingAudio = false;
        });
      });
      
      recordBtn.classList.remove('active');
      recHint.classList.add('d-none');
      
      // 停止所有媒体轨道以释放麦克风
      if (audioStream) {
        audioStream.getTracks().forEach(function(track) {
          track.stop();
        });
      }
      
      // 清理资源
      if (audioContext) {
        audioContext.close();
        audioContext = null;
      }
      recorder = null;
      audioStream = null;
    }
  }

  recordBtn.addEventListener('click', function(){
    console.log('🎤 录音按钮被点击, 当前状态:', recorder ? '已初始化' : '未初始化');
    
    // 防止在音频处理期间点击录音按钮
    if (isProcessingAudio) {
      console.log('⚠️ 音频正在处理中，请等待处理完成...');
      return;
    }
    
    if (!recorder || !audioContext) {
      console.log('▶️ 开始录音...');
      startRecording();
    } else {
      console.log('⏹️ 停止录音...');
      stopRecording();
    }
  });

  // Right-click to transcribe audio bubble
  chatLog.addEventListener('contextmenu', function(e){
    var audio = e.target.closest('audio');
    if (!audio) return;
    e.preventDefault();
    var src = audio.currentSrc || audio.src;
    if (!src) return;
    var bubble = audio.closest('.audio-bubble');
    // Avoid duplicate caption
    if (bubble && bubble.querySelector('.transcript-caption')) return;

    function appendTranscript(text){
      if (!bubble) return;
      var cap = document.createElement('div');
      cap.className = 'transcript-caption';
      cap.textContent = text;
      bubble.appendChild(cap);
    }

    var blob = blobStore.get(src);
    if (blob) {
      var form = new FormData();
      form.append('audio', blob, 'clip.webm');
      fetch('/api/chatbot/transcribe', { method: 'POST', body: form })
        .then(function(r){ return r.json(); })
        .then(function(res){ appendTranscript(res.transcript || '(no transcript)'); })
        .catch(function(){ appendTranscript('(transcribe failed)'); });
    } else {
      fetch('/api/chatbot/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: src })
      })
        .then(function(r){ return r.json(); })
        .then(function(res){ appendTranscript(res.transcript || '(no transcript)'); })
        .catch(function(){ appendTranscript('(transcribe failed)'); });
    }
  });
})();


