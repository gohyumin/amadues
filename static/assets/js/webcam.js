// Webcam Module - Real-time Vocabulary Discovery
window.WebcamModule = window.WebcamModule || class WebcamModule {
  constructor() {
    this.video = null;
    this.canvas = null;
    this.stream = null;
    this.isRecording = false;
    this.discoveredWords = [];
    this.statistics = {
      totalDiscovered: 0,
      todayDiscovered: 0,
      savedWords: 0
    };
    
    this.init();
  }

  init() {
    this.video = document.getElementById('webcamVideo');
    this.canvas = document.getElementById('captureCanvas');
    
    this.bindEvents();
    this.loadStatistics();
    this.renderRecentDiscoveries();
  }

  bindEvents() {
    const startBtn = document.getElementById('startCameraBtn');
    const stopBtn = document.getElementById('stopCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const clearBtn = document.getElementById('clearResultsBtn');

    if (startBtn) startBtn.addEventListener('click', () => this.startCamera());
    if (stopBtn) stopBtn.addEventListener('click', () => this.stopCamera());
    if (captureBtn) captureBtn.addEventListener('click', () => this.captureAndAnalyze());
    if (clearBtn) clearBtn.addEventListener('click', () => this.clearResults());
  }

  async startCamera() {
    try {
      this.updateStatus('Requesting camera access...', 'processing');
      
      const constraints = {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'environment' // Use rear camera if available
        }
      };

      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.stream;
      this.isRecording = true;

      // Update UI
      document.getElementById('startCameraBtn').classList.add('d-none');
      document.getElementById('stopCameraBtn').classList.remove('d-none');
      document.getElementById('captureBtn').classList.remove('d-none');
      
      this.updateStatus('Camera active - Ready to capture', 'recording');
      
    } catch (error) {
      console.error('Error accessing camera:', error);
      this.updateStatus('Camera access failed', 'error');
      this.showError('Unable to access camera. Please check your permissions and try again.');
    }
  }

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    
    this.video.srcObject = null;
    this.isRecording = false;

    // Update UI
    document.getElementById('startCameraBtn').classList.remove('d-none');
    document.getElementById('stopCameraBtn').classList.add('d-none');
    document.getElementById('captureBtn').classList.add('d-none');
    
    this.updateStatus('Camera ready', '');
  }

  async captureAndAnalyze() {
    if (!this.isRecording) {
      this.showError('Please start the camera first');
      return;
    }

    try {
      this.updateStatus('Capturing image...', 'processing');
      
      // Capture frame from video
      const context = this.canvas.getContext('2d');
      this.canvas.width = this.video.videoWidth;
      this.canvas.height = this.video.videoHeight;
      context.drawImage(this.video, 0, 0);
      
      // Convert to blob
      const blob = await new Promise(resolve => this.canvas.toBlob(resolve, 'image/jpeg', 0.8));
      
      this.updateStatus('Analyzing image...', 'processing');
      
      // Simulate AI analysis (in real implementation, this would call an AI service)
      const analysisResult = await this.simulateAnalysis(blob);
      
      this.updateStatus('Camera active - Ready to capture', 'recording');
      this.displayAnalysisResults(analysisResult);
      
    } catch (error) {
      console.error('Error during capture and analysis:', error);
      this.updateStatus('Analysis failed', 'error');
      this.showError('Failed to analyze image. Please try again.');
    }
  }

  async simulateAnalysis(imageBlob) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Mock analysis results - in real implementation, this would be actual AI results
    const mockResults = [
      { word: 'Computer', translation: '电脑', confidence: 0.95, category: 'Technology' },
      { word: 'Book', translation: '书', confidence: 0.88, category: 'Education' },
      { word: 'Cup', translation: '杯子', confidence: 0.92, category: 'Daily Items' },
      { word: 'Phone', translation: '手机', confidence: 0.87, category: 'Technology' }
    ];
    
    // Randomly select 1-3 results
    const numResults = Math.floor(Math.random() * 3) + 1;
    const results = [];
    const usedIndices = new Set();
    
    for (let i = 0; i < numResults; i++) {
      let randomIndex;
      do {
        randomIndex = Math.floor(Math.random() * mockResults.length);
      } while (usedIndices.has(randomIndex));
      
      usedIndices.add(randomIndex);
      results.push({
        ...mockResults[randomIndex],
        timestamp: new Date().toISOString()
      });
    }
    
    return results;
  }

  displayAnalysisResults(results) {
    const resultsContainer = document.getElementById('analysisResults');
    const vocabularyGrid = document.getElementById('vocabularyGrid');
    
    // Clear previous results
    vocabularyGrid.innerHTML = '';
    
    // Display new results
    results.forEach(result => {
      const vocabItem = this.createVocabularyItem(result);
      vocabularyGrid.appendChild(vocabItem);
    });
    
    // Show results container
    resultsContainer.classList.remove('d-none');
    
    // Add to discovered words
    this.discoveredWords = [...results, ...this.discoveredWords];
    
    // Update statistics
    this.statistics.totalDiscovered += results.length;
    this.statistics.todayDiscovered += results.length;
    this.updateStatistics();
    this.renderRecentDiscoveries();
  }

  createVocabularyItem(vocab) {
    const item = document.createElement('div');
    item.className = 'vocabulary-item';
    
    item.innerHTML = `
      <div class="vocab-word">${vocab.word}</div>
      <div class="vocab-translation">${vocab.translation}</div>
      <div class="vocab-confidence">
        <span>Confidence:</span>
        <div class="confidence-bar">
          <div class="confidence-fill" style="width: ${vocab.confidence * 100}%"></div>
        </div>
        <span>${Math.round(vocab.confidence * 100)}%</span>
      </div>
      <div class="vocab-actions">
        <button class="btn btn-primary btn-sm save-vocab" data-word="${vocab.word}" data-translation="${vocab.translation}">
          <i class="bi bi-bookmark-plus"></i> Save
        </button>
        <button class="btn btn-outline-secondary btn-sm speak-word" data-word="${vocab.word}">
          <i class="bi bi-volume-up"></i> Listen
        </button>
      </div>
    `;
    
    // Bind events
    const saveBtn = item.querySelector('.save-vocab');
    const speakBtn = item.querySelector('.speak-word');
    
    saveBtn.addEventListener('click', (e) => {
      this.saveVocabulary(e.target.dataset.word, e.target.dataset.translation);
      e.target.innerHTML = '<i class="bi bi-bookmark-check"></i> Saved';
      e.target.classList.remove('btn-primary');
      e.target.classList.add('btn-success');
      e.target.disabled = true;
    });
    
    speakBtn.addEventListener('click', (e) => {
      this.speakWord(e.target.dataset.word);
    });
    
    return item;
  }

  saveVocabulary(word, translation) {
    // In real implementation, this would save to backend
    console.log(`Saving vocabulary: ${word} - ${translation}`);
    this.statistics.savedWords++;
    this.updateStatistics();
    this.showSuccess(`"${word}" saved to your vocabulary!`);
  }

  speakWord(word) {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(word);
      utterance.lang = 'en-US';
      utterance.rate = 0.8;
      speechSynthesis.speak(utterance);
    }
  }

  clearResults() {
    const resultsContainer = document.getElementById('analysisResults');
    const vocabularyGrid = document.getElementById('vocabularyGrid');
    
    vocabularyGrid.innerHTML = '';
    resultsContainer.classList.add('d-none');
  }

  updateStatus(message, type = '') {
    const statusElement = document.getElementById('cameraStatus');
    statusElement.textContent = message;
    statusElement.className = `status-text ${type}`;
  }

  updateStatistics() {
    document.getElementById('totalDiscovered').textContent = this.statistics.totalDiscovered;
    document.getElementById('todayDiscovered').textContent = this.statistics.todayDiscovered;
    document.getElementById('savedWords').textContent = this.statistics.savedWords;
  }

  loadStatistics() {
    // Load from localStorage or backend
    const saved = localStorage.getItem('webcam-statistics');
    if (saved) {
      this.statistics = { ...this.statistics, ...JSON.parse(saved) };
    }
    this.updateStatistics();
  }

  saveStatistics() {
    localStorage.setItem('webcam-statistics', JSON.stringify(this.statistics));
  }

  renderRecentDiscoveries() {
    const discoveriesList = document.getElementById('discoveriesList');
    
    if (this.discoveredWords.length === 0) {
      discoveriesList.innerHTML = '<p class="empty-state">No discoveries yet. Start using your camera to find new vocabulary!</p>';
      return;
    }
    
    const recentWords = this.discoveredWords.slice(0, 10); // Show last 10
    discoveriesList.innerHTML = recentWords.map(word => `
      <div class="discovery-item">
        <div class="discovery-time">${this.formatTime(word.timestamp)}</div>
        <div class="discovery-word">${word.word}</div>
        <div class="discovery-translation">${word.translation}</div>
      </div>
    `).join('');
  }

  formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  }

  showError(message) {
    // Simple alert for now - could be enhanced with a toast system
    alert(`Error: ${message}`);
  }

  showSuccess(message) {
    // Simple alert for now - could be enhanced with a toast system
    alert(`Success: ${message}`);
  }

  // Cleanup when module is destroyed
  destroy() {
    if (this.stream) {
      this.stopCamera();
    }
    this.saveStatistics();
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  if (document.querySelector('.webcam-container')) {
    window.webcamModule = new WebcamModule();
  }
});

// Also make it available globally for dashboard loading
if (typeof window !== 'undefined') {
  window.WebcamModule = WebcamModule;
}