// Exercise Module - Path-based Pronunciation Practice
window.ExerciseModule = window.ExerciseModule || class ExerciseModule {
  constructor() {
    this.currentScenario = null;
    this.currentSentenceIndex = 0;
    this.isRecording = false;
    this.hasPlayedAudio = false;
    this.userRecording = null;
    this.completedSentences = new Set();
    
    // Timer functionality
    this.startTime = null;
    this.endTime = null;
    this.totalPracticeTime = 0;
    
    this.scenarios = {
      basic: {
        id: 'basic',
        title: 'Basic Greetings',
        description: 'Practice common greeting expressions',
        color: 'blue',
        sentences: [
          {
            chinese: '你好',
            translation: 'Hello',
            pronunciation: 'Nǐ hǎo'
          },
          {
            chinese: '早上好',
            translation: 'Good morning',
            pronunciation: 'Zǎo shàng hǎo'
          },
          {
            chinese: '谢谢你',
            translation: 'Thank you',
            pronunciation: 'Xiè xiè nǐ'
          },
          {
            chinese: '再见',
            translation: 'Goodbye',
            pronunciation: 'Zài jiàn'
          },
          {
            chinese: '很高兴见到你',
            translation: 'Nice to meet you',
            pronunciation: 'Hěn gāo xìng jiàn dào nǐ'
          }
        ]
      },
      ordering: {
        id: 'ordering',
        title: 'Ordering Food',
        description: 'Practice ordering at restaurants',
        color: 'green',
        sentences: [
          {
            chinese: '我想要一份饺子',
            translation: 'I want a serving of dumplings',
            pronunciation: 'Wǒ xiǎng yào yī fèn jiǎo zi'
          },
          {
            chinese: '请给我菜单',
            translation: 'Please give me the menu',
            pronunciation: 'Qǐng gěi wǒ cài dān'
          },
          {
            chinese: '这个多少钱？',
            translation: 'How much is this?',
            pronunciation: 'Zhè ge duō shǎo qián?'
          },
          {
            chinese: '我要买单',
            translation: 'I want to pay the bill',
            pronunciation: 'Wǒ yào mǎi dān'
          },
          {
            chinese: '太好吃了',
            translation: 'It\'s delicious',
            pronunciation: 'Tài hǎo chī le'
          }
        ]
      },
      directions: {
        id: 'directions',
        title: 'Asking Directions',
        description: 'Practice asking for and giving directions',
        color: 'orange',
        sentences: [
          {
            chinese: '请问厕所在哪里？',
            translation: 'Where is the restroom?',
            pronunciation: 'Qǐng wèn cè suǒ zài nǎ lǐ?'
          },
          {
            chinese: '怎么去火车站？',
            translation: 'How to get to the train station?',
            pronunciation: 'Zěn me qù huǒ chē zhàn?'
          },
          {
            chinese: '直走然后左转',
            translation: 'Go straight then turn left',
            pronunciation: 'Zhí zǒu rán hòu zuǒ zhuǎn'
          },
          {
            chinese: '这里是哪里？',
            translation: 'Where is this place?',
            pronunciation: 'Zhè lǐ shì nǎ lǐ?'
          },
          {
            chinese: '谢谢你的帮助',
            translation: 'Thank you for your help',
            pronunciation: 'Xiè xiè nǐ de bāng zhù'
          }
        ]
      }
    };
    
    this.init();
  }

  init() {
    this.bindEvents();
    this.loadCompletedScenarios();
  }

  bindEvents() {
    // Scenario selection
    document.querySelectorAll('.scenario-card').forEach(card => {
      card.addEventListener('click', (e) => {
        const scenarioId = card.dataset.scenario;
        this.startScenario(scenarioId);
      });
    });

    // Back to selection
    const backBtn = document.getElementById('backToSelection');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        this.showScenarioSelection();
      });
    }

    // Back to path from practice
    const backToPathBtn = document.getElementById('backToPath');
    if (backToPathBtn) {
      backToPathBtn.addEventListener('click', () => {
        this.showLearningPath();
      });
    }

    // Audio controls
    const playBtn = document.getElementById('playSentence');
    if (playBtn) {
      playBtn.addEventListener('click', () => {
        this.playCurrentSentence();
      });
    }

    const readyBtn = document.getElementById('readyToSpeak');
    if (readyBtn) {
      readyBtn.addEventListener('click', () => {
        this.showSpeakPhase();
      });
    }

    // Recording controls
    const recordBtn = document.getElementById('recordSpeech');
    if (recordBtn) {
      recordBtn.addEventListener('mousedown', () => this.startRecording());
      recordBtn.addEventListener('mouseup', () => this.stopRecording());
      recordBtn.addEventListener('mouseleave', () => this.stopRecording());
      // Touch events
      recordBtn.addEventListener('touchstart', (e) => {
        if (e.cancelable) {
          e.preventDefault();
        }
        this.startRecording();
      });
      recordBtn.addEventListener('touchend', (e) => {
        if (e.cancelable) {
          e.preventDefault();
        }
        this.stopRecording();
      });
    }

    // Replay original
    const replayBtn = document.getElementById('replayOriginal');
    if (replayBtn) {
      replayBtn.addEventListener('click', () => {
        this.playCurrentSentence();
      });
    }

    // Playback controls
    const playMyRecordingBtn = document.getElementById('playMyRecording');
    if (playMyRecordingBtn) {
      playMyRecordingBtn.addEventListener('click', () => {
        this.playUserRecording();
      });
    }

    const acceptBtn = document.getElementById('acceptRecording');
    if (acceptBtn) {
      acceptBtn.addEventListener('click', () => {
        this.acceptRecording();
      });
    }

    const retryBtn = document.getElementById('retryRecording');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.retryRecording();
      });
    }

    // Completion page buttons
    const reviewExerciseBtn = document.getElementById('reviewExercise');
    if (reviewExerciseBtn) {
      reviewExerciseBtn.addEventListener('click', () => {
        this.showReview();
      });
    }

    const practiceAgainBtn = document.getElementById('practiceAgain');
    if (practiceAgainBtn) {
      practiceAgainBtn.addEventListener('click', () => {
        console.log('Practice Again button clicked');
        this.restartScenario();
      });
    } else {
      console.log('Practice Again button not found');
    }

    const chooseNewScenarioBtn = document.getElementById('chooseNewScenario');
    if (chooseNewScenarioBtn) {
      chooseNewScenarioBtn.addEventListener('click', () => {
        this.showScenarioSelection();
      });
    }

    // Review page buttons
    const backToCompletionBtn = document.getElementById('backToCompletion');
    if (backToCompletionBtn) {
      backToCompletionBtn.addEventListener('click', () => {
        this.showCompletion();
      });
    }

    const retryFromReviewBtn = document.getElementById('retryFromReview');
    if (retryFromReviewBtn) {
      retryFromReviewBtn.addEventListener('click', () => {
        this.restartScenario();
      });
    }

    const newScenarioFromReviewBtn = document.getElementById('newScenarioFromReview');
    if (newScenarioFromReviewBtn) {
      newScenarioFromReviewBtn.addEventListener('click', () => {
        this.showScenarioSelection();
      });
    }
  }

  startScenario(scenarioId) {
    this.currentScenario = this.scenarios[scenarioId];
    if (!this.currentScenario) return;

    // Start timing the practice session
    this.startTime = Date.now();
    this.totalPracticeTime = 0;
    this.currentSentenceIndex = 0;
    this.completedSentences.clear();
    this.hasPlayedAudio = false;

    // Apply theme color
    const practiceView = document.getElementById('exercisePractice');
    practiceView.className = 'exercise-practice';
    practiceView.classList.add(`${this.currentScenario.color}-theme`);

    // Update header
    document.getElementById('currentScenarioTitle').textContent = this.currentScenario.title;
    document.getElementById('currentScenarioDescription').textContent = this.currentScenario.description;

    // Update scenario image
    const scenarioImage = document.getElementById('scenarioImage');
    const imageMap = {
      'basic': 'assets/img/person/person-f-13.webp',
      'ordering': 'assets/img/person/person-m-11.webp',
      'directions': 'assets/img/services/services-5.webp'
    };
    
    if (scenarioImage && imageMap[scenarioId]) {
      scenarioImage.src = `/static/${imageMap[scenarioId]}`;
      scenarioImage.alt = this.currentScenario.title;
    }

    // Reset state
    this.currentSentenceIndex = 0;
    this.completedSentences.clear();

    // Show practice view with learning path
    document.getElementById('exerciseSelection').classList.add('d-none');
    document.getElementById('exercisePractice').classList.remove('d-none');
    document.getElementById('exerciseCompletion').classList.add('d-none');

    this.showScenarioDecorations(scenarioId);
    this.showLearningPath();
  }

  showLearningPath() {
    console.log('showLearningPath method called');
    
    // Hide completion view
    document.getElementById('exerciseCompletion').classList.add('d-none');
    console.log('Hidden completion view');
    
    // Hide sentence practice
    document.getElementById('sentencePractice').classList.add('d-none');
    console.log('Hidden sentence practice');
    
    // Show learning path
    document.getElementById('learningPath').classList.remove('d-none');
    console.log('Shown learning path');
    
    this.generatePathNodes();
    console.log('Generated path nodes');
    
    // Scroll to learning path
    setTimeout(() => {
      const learningPath = document.getElementById('learningPath');
      if (learningPath) {
        learningPath.scrollIntoView({ behavior: 'smooth', block: 'center' });
        console.log('Scrolled to learning path');
      }
    }, 100);
  }

  generatePathNodes() {
    const nodesContainer = document.getElementById('pathNodes');
    nodesContainer.innerHTML = '';

    // Calculate node positions for logo movement
    const nodePositions = [];

    this.currentScenario.sentences.forEach((sentence, index) => {
      const node = document.createElement('div');
      node.className = 'path-node';
      node.dataset.sentenceIndex = index;

      // Calculate position percentage for this node (across the container width)
      const positionPercent = (index / (this.currentScenario.sentences.length - 1)) * 100;
      nodePositions.push(positionPercent);

      // Determine node state
      if (this.completedSentences.has(index)) {
        node.classList.add('completed');
        node.innerHTML = '<i class="bi bi-check-lg node-check"></i>';
      } else if (index === 0 || this.completedSentences.has(index - 1)) {
        node.classList.add('current');
        node.innerHTML = `<span class="node-number">${index + 1}</span>`;
      } else {
        node.classList.add('locked');
        node.innerHTML = `<span class="node-number">${index + 1}</span>`;
      }

      // Add click event for available nodes
      if (!node.classList.contains('locked')) {
        node.addEventListener('click', () => {
          this.startSentencePractice(index);
        });
      }

      nodesContainer.appendChild(node);
    });

    // Position the logo at the current active node
    this.updateLogoPosition();
  }

  updateLogoPosition() {
    const movingLogo = document.getElementById('movingLogo');
    if (!movingLogo) return;

    // Find the current active node (either current or the last completed)
    let activeNodeIndex = 0;
    
    // If we have completed sentences, position logo at the next available node
    if (this.completedSentences.size > 0) {
      activeNodeIndex = Math.min(this.completedSentences.size, this.currentScenario.sentences.length - 1);
    }
    
    // Calculate position based on node distribution
    const totalNodes = this.currentScenario.sentences.length;
    const containerWidth = 700; // Approximate container width minus padding
    const nodeSpacing = containerWidth / (totalNodes - 1);
    const logoPosition = 50 + (activeNodeIndex * nodeSpacing); // 50px is the starting padding

    movingLogo.style.left = `${logoPosition}px`;
  }

  startSentencePractice(sentenceIndex) {
    this.currentSentenceIndex = sentenceIndex;
    
    // Hide learning path
    document.getElementById('learningPath').classList.add('d-none');
    
    // Show sentence practice
    document.getElementById('sentencePractice').classList.remove('d-none');
    
    // Update sentence info
    document.getElementById('currentSentenceNum').textContent = sentenceIndex + 1;
    document.getElementById('totalSentences').textContent = this.currentScenario.sentences.length;

    // Reset practice state
    this.hasPlayedAudio = false;
    this.userRecording = null;
    
    // Show listen phase
    this.showListenPhase();
  }

  showScenarioSelection() {
    // Hide theme decorations when returning to selection
    this.hideScenarioDecorations();
    
    document.getElementById('exerciseSelection').classList.remove('d-none');
    document.getElementById('exercisePractice').classList.add('d-none');
    document.getElementById('exerciseCompletion').classList.add('d-none');
  }

  showListenPhase() {
    const currentSentence = this.currentScenario.sentences[this.currentSentenceIndex];
    
    // Update sentence display
    document.getElementById('sentenceText').textContent = currentSentence.chinese;
    document.getElementById('sentenceTranslation').textContent = currentSentence.translation;
    
    // Show listen phase, hide speak phase
    document.getElementById('listenPhase').classList.remove('d-none');
    document.getElementById('speakPhase').classList.add('d-none');
    
    // Reset controls
    document.getElementById('readyToSpeak').disabled = true;
    this.hasPlayedAudio = false;
  }

  showSpeakPhase() {
    const currentSentence = this.currentScenario.sentences[this.currentSentenceIndex];
    
    // Update sentence display for speak phase
    document.getElementById('speakSentenceText').textContent = currentSentence.chinese;
    document.getElementById('pronunciationGuide').textContent = currentSentence.pronunciation;
    
    // Show speak phase, hide listen phase
    document.getElementById('listenPhase').classList.add('d-none');
    document.getElementById('speakPhase').classList.remove('d-none');
    
    // Reset recording controls
    this.resetRecordingControls();
  }

  playCurrentSentence() {
    // Simulate audio playback
    const playBtn = document.getElementById('playSentence');
    const replayBtn = document.getElementById('replayOriginal');
    
    // Update button states
    if (playBtn) {
      playBtn.disabled = true;
      playBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Playing...';
    }
    if (replayBtn) {
      replayBtn.disabled = true;
      replayBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Playing...';
    }
    
    // Simulate audio duration
    setTimeout(() => {
      if (playBtn) {
        playBtn.disabled = false;
        playBtn.innerHTML = '<i class="bi bi-play-fill"></i> Play Again';
        document.getElementById('readyToSpeak').disabled = false;
      }
      if (replayBtn) {
        replayBtn.disabled = false;
        replayBtn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Replay Original';
      }
      this.hasPlayedAudio = true;
    }, 2000);
  }

  startRecording() {
    if (this.isRecording) return;
    
    this.isRecording = true;
    document.getElementById('recordingStatus').classList.remove('d-none');
    document.getElementById('recordSpeech').classList.add('recording');
    
    // Simulate recording
    console.log('Started recording...');
  }

  stopRecording() {
    if (!this.isRecording) return;
    
    this.isRecording = false;
    document.getElementById('recordingStatus').classList.add('d-none');
    document.getElementById('recordSpeech').classList.remove('recording');
    
    // Simulate processing
    this.userRecording = { duration: Math.random() * 3 + 1 }; // Simulate recording data
    document.getElementById('playbackControls').classList.remove('d-none');
    
    console.log('Stopped recording...');
  }

  playUserRecording() {
    if (!this.userRecording) return;
    
    const playBtn = document.getElementById('playMyRecording');
    playBtn.disabled = true;
    playBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Playing...';
    
    setTimeout(() => {
      playBtn.disabled = false;
      playBtn.innerHTML = '<i class="bi bi-play"></i> Play My Voice';
    }, this.userRecording.duration * 1000);
  }

  acceptRecording() {
    // Mark sentence as completed
    this.completedSentences.add(this.currentSentenceIndex);
    
    // Update logo position after completion
    setTimeout(() => {
      this.updateLogoPosition();
    }, 300);
    
    // Check if all sentences are completed
    if (this.completedSentences.size === this.currentScenario.sentences.length) {
      setTimeout(() => {
        this.completeScenario();
      }, 1000); // Give time for logo animation
    } else {
      // Go back to learning path after a short delay to see logo movement
      setTimeout(() => {
        this.showLearningPath();
      }, 800);
    }
  }

  retryRecording() {
    this.resetRecordingControls();
  }

  resetRecordingControls() {
    this.userRecording = null;
    document.getElementById('playbackControls').classList.add('d-none');
    document.getElementById('recordingStatus').classList.add('d-none');
    
    const recordBtn = document.getElementById('recordSpeech');
    recordBtn.classList.remove('recording');
    recordBtn.disabled = false;
    recordBtn.innerHTML = '<i class="bi bi-mic"></i> Hold to Record';
  }

  completeScenario() {
    // Save progress
    this.saveProgress();
    
    // Calculate practice time
    this.endTime = Date.now();
    this.totalPracticeTime = Math.floor((this.endTime - this.startTime) / 1000); // in seconds
    
    // Show completion view
    document.getElementById('exercisePractice').classList.add('d-none');
    document.getElementById('exerciseCompletion').classList.remove('d-none');
    
    // Update completion message
    const completionTitle = document.getElementById('completionTitle');
    const completionMessage = document.getElementById('completionMessage');
    
    if (completionTitle && completionMessage) {
      completionTitle.textContent = `${this.currentScenario.title} Complete!`;
      completionMessage.textContent = 'Great job! You\'ve completed all sentences in this scenario.';
    }

    // Update practice time display
    this.updatePracticeTimeDisplay();
  }

  // Format time from seconds to readable format (e.g., "2m 30s")
  formatTime(seconds) {
    if (seconds < 60) {
      return `${seconds}s`;
    } else {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      if (remainingSeconds === 0) {
        return `${minutes}m`;
      } else {
        return `${minutes}m ${remainingSeconds}s`;
      }
    }
  }

  // Update the practice time display in the completion view
  updatePracticeTimeDisplay() {
    const practiceTimeElement = document.getElementById('practiceTime');
    if (practiceTimeElement) {
      practiceTimeElement.textContent = this.formatTime(this.totalPracticeTime);
    }

    // Also update completed sentences count
    const completedSentencesElement = document.getElementById('completedSentences');
    if (completedSentencesElement && this.currentScenario) {
      completedSentencesElement.textContent = this.currentScenario.sentences.length;
    }
  }

  loadCompletedScenarios() {
    const saved = localStorage.getItem('exercise_completed_scenarios');
    if (saved) {
      const completed = JSON.parse(saved);
      // Update UI to show completed scenarios
      completed.forEach(scenarioId => {
        const card = document.querySelector(`[data-scenario="${scenarioId}"]`);
        if (card) {
          card.classList.add('completed');
          const badge = card.querySelector('.scenario-badge');
          if (badge) {
            badge.textContent = 'Completed';
            badge.className = 'scenario-badge completed';
          }
        }
      });
    }
  }

  saveProgress() {
    const saved = localStorage.getItem('exercise_completed_scenarios');
    const completed = saved ? JSON.parse(saved) : [];
    
    if (!completed.includes(this.currentScenario.id)) {
      completed.push(this.currentScenario.id);
      localStorage.setItem('exercise_completed_scenarios', JSON.stringify(completed));
    }
  }

  showReview() {
    // Hide completion view
    document.getElementById('exerciseCompletion').classList.add('d-none');
    document.getElementById('exerciseReview').classList.remove('d-none');
    
    // Update review title
    const reviewTitle = document.getElementById('reviewScenarioTitle');
    if (reviewTitle) {
      reviewTitle.textContent = `Review: ${this.currentScenario.title}`;
    }
    
    // Generate review content
    this.generateReviewContent();
  }

  generateReviewContent() {
    const reviewContainer = document.getElementById('reviewSentences');
    if (!reviewContainer || !this.currentScenario) return;
    
    reviewContainer.innerHTML = '';
    
    this.currentScenario.sentences.forEach((sentence, index) => {
      const reviewItem = document.createElement('div');
      reviewItem.className = 'review-sentence';
      
      reviewItem.innerHTML = `
        <div class="sentence-number">${index + 1}</div>
        <div class="review-sentence-text">${sentence.chinese}</div>
        <div class="review-sentence-pinyin">${sentence.pronunciation}</div>
        <div class="review-sentence-translation">${sentence.translation}</div>
      `;
      
      reviewContainer.appendChild(reviewItem);
    });
  }

  restartScenario() {
    console.log('restartScenario called');
    if (!this.currentScenario) {
      console.log('No current scenario');
      return;
    }
    
    console.log('Restarting scenario:', this.currentScenario.id);
    
    // Reset state
    this.currentSentenceIndex = 0;
    this.completedSentences.clear();
    this.hasPlayedAudio = false;
    this.userRecording = null;
    
    // Hide completion view and show the learning path navigation
    document.getElementById('exerciseCompletion').classList.add('d-none');
    document.getElementById('exerciseReview').classList.add('d-none');
    document.getElementById('sentencePractice').classList.add('d-none');
    
    // Show the practice view (which contains the learning path)
    document.getElementById('exercisePractice').classList.remove('d-none');
    
    // Show learning path navigation
    this.showLearningPath();
    console.log('showLearningPath called');
  }

  showCompletion() {
    // Hide review view
    document.getElementById('exerciseReview').classList.add('d-none');
    document.getElementById('exerciseCompletion').classList.remove('d-none');
  }

  showScenarioDecorations(scenarioId) {
    // Hide all theme decorations first
    const themeDecorations = document.querySelectorAll('.theme-clouds, .theme-elements');
    themeDecorations.forEach(decoration => {
      decoration.classList.remove('active');
    });

    // Hide all ground decorations first
    const groundDecorations = document.querySelectorAll('.ground-decoration');
    groundDecorations.forEach(decoration => {
      decoration.classList.remove('active');
    });

    // Hide old decoration elements if they exist
    const decorations = document.querySelectorAll('.decoration-element');
    decorations.forEach(decoration => {
      decoration.classList.remove('active');
    });

    // Show theme decorations for the current scenario
    const currentThemeDecorations = document.querySelectorAll(`[data-theme="${scenarioId}"]`);
    currentThemeDecorations.forEach((decoration, index) => {
      setTimeout(() => {
        decoration.classList.add('active');
      }, index * 300 + 500); // Staggered appearance
    });

    // Show ground decorations for the current scenario
    const currentGroundDecorations = document.querySelectorAll(`[data-ground-theme="${scenarioId}"]`);
    currentGroundDecorations.forEach((decoration, index) => {
      setTimeout(() => {
        decoration.classList.add('active');
      }, index * 200 + 800); // Delayed appearance after theme decorations
    });
  }

  hideScenarioDecorations() {
    // Hide theme decorations
    const themeDecorations = document.querySelectorAll('.theme-clouds, .theme-elements');
    themeDecorations.forEach(decoration => {
      decoration.classList.remove('active');
    });

    // Hide ground decorations
    const groundDecorations = document.querySelectorAll('.ground-decoration');
    groundDecorations.forEach(decoration => {
      decoration.classList.remove('active');
    });

    // Hide old decoration elements if they exist
    const decorations = document.querySelectorAll('.decoration-element');
    decorations.forEach(decoration => {
      decoration.classList.remove('active');
    });
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.exercise-container')) {
        window.exerciseModule = new ExerciseModule();
    }
});

// Also make sure it's available globally for dashboard loading
if (typeof window !== 'undefined') {
    window.ExerciseModule = ExerciseModule;
}