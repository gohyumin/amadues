// Quiz Module - Interactive Quiz System
window.QuizModule = window.QuizModule || class QuizModule {
  constructor() {
    this.currentQuiz = null;
    this.currentQuestionIndex = 0;
    this.userAnswers = [];
    this.startTime = null;
    this.timerInterval = null;
    this.timeLimit = 180; // 3 minutes in seconds
    this.timeRemaining = this.timeLimit;
    
    this.quizzes = {
      basic: {
        id: 'basic',
        title: 'Basic Greetings Quiz',
        description: 'Fill in the blanks with greeting expressions',
        color: 'blue',
        timeLimit: 180, // 3 minutes
        questions: [
          {
            id: 1,
            type: 'fill-blank',
            chinese: '你___，你好吗？',
            translation: 'Hello, how are you?',
            question: 'Fill in the blank with the correct greeting:',
            correctAnswer: '好',
            options: ['好', '早', '再见', '谢谢'],
            explanation: '好 (hǎo) means "good" and is used in "你好" (nǐ hǎo) which means "hello".'
          },
          {
            id: 2,
            type: 'fill-blank',
            chinese: '___上好！',
            translation: 'Good morning!',
            question: 'Complete this morning greeting:',
            correctAnswer: '早',
            options: ['早', '晚', '午', '夜'],
            explanation: '早 (zǎo) means "early" and is used in "早上好" (zǎo shàng hǎo) meaning "good morning".'
          },
          {
            id: 3,
            type: 'fill-blank',
            chinese: '___谢你的帮助。',
            translation: 'Thank you for your help.',
            question: 'How do you say "thank" in Chinese?',
            correctAnswer: '谢',
            options: ['谢', '请', '对', '很'],
            explanation: '谢 (xiè) is used in "谢谢" (xiè xiè) meaning "thank you".'
          },
          {
            id: 4,
            type: 'fill-blank',
            chinese: '很高兴___到你。',
            translation: 'Nice to meet you.',
            question: 'What word means "meet" in this context?',
            correctAnswer: '见',
            options: ['见', '看', '听', '说'],
            explanation: '见 (jiàn) means "to meet" or "to see" in formal contexts.'
          },
          {
            id: 5,
            type: 'fill-blank',
            chinese: '___见！',
            translation: 'Goodbye!',
            question: 'Complete this farewell greeting:',
            correctAnswer: '再',
            options: ['再', '不', '还', '又'],
            explanation: '再 (zài) means "again" and is used in "再见" (zài jiàn) meaning "goodbye".'
          }
        ]
      },
      ordering: {
        id: 'ordering',
        title: 'Ordering Food Quiz',
        description: 'Complete restaurant conversation blanks',
        color: 'green',
        timeLimit: 240, // 4 minutes
        questions: [
          {
            id: 1,
            type: 'fill-blank',
            chinese: '我想___一杯咖啡。',
            translation: 'I would like to order a cup of coffee.',
            question: 'What verb means "to order" in a restaurant?',
            correctAnswer: '要',
            options: ['要', '给', '有', '是'],
            explanation: '要 (yào) means "to want" and is commonly used when ordering food.'
          },
          {
            id: 2,
            type: 'fill-blank',
            chinese: '请给我___单。',
            translation: 'Please give me the menu.',
            question: 'What word means "menu"?',
            correctAnswer: '菜',
            options: ['菜', '饭', '茶', '水'],
            explanation: '菜 (cài) means "dish" and 菜单 (cài dān) means "menu".'
          },
          {
            id: 3,
            type: 'fill-blank',
            chinese: '这个菜很___。',
            translation: 'This dish is delicious.',
            question: 'How do you say "delicious"?',
            correctAnswer: '好吃',
            options: ['好吃', '好看', '好听', '好玩'],
            explanation: '好吃 (hǎo chī) literally means "good to eat" and translates to "delicious".'
          },
          {
            id: 4,
            type: 'fill-blank',
            chinese: '买___，谢谢。',
            translation: 'Check, please.',
            question: 'What do you ask for when you want to pay?',
            correctAnswer: '单',
            options: ['单', '钱', '卡', '票'],
            explanation: '单 (dān) refers to the bill or check in a restaurant context.'
          },
          {
            id: 5,
            type: 'fill-blank',
            chinese: '我对海鲜___。',
            translation: 'I am allergic to seafood.',
            question: 'What word indicates an allergic reaction?',
            correctAnswer: '过敏',
            options: ['过敏', '喜欢', '讨厌', '害怕'],
            explanation: '过敏 (guò mǐn) means "allergic" or "allergy".'
          }
        ]
      },
      directions: {
        id: 'directions',
        title: 'Asking Directions Quiz',
        description: 'Fill in direction-related vocabulary',
        color: 'orange',
        timeLimit: 180, // 3 minutes
        questions: [
          {
            id: 1,
            type: 'fill-blank',
            chinese: '请问，___站怎么走？',
            translation: 'Excuse me, how do I get to the subway station?',
            question: 'What word means "subway" in Chinese?',
            correctAnswer: '地铁',
            options: ['地铁', '公交', '出租', '火车'],
            explanation: '地铁 (dì tiě) literally means "ground iron" and refers to the subway.'
          },
          {
            id: 2,
            type: 'fill-blank',
            chinese: '一直往___走。',
            translation: 'Go straight ahead.',
            question: 'What direction means "forward/ahead"?',
            correctAnswer: '前',
            options: ['前', '后', '左', '右'],
            explanation: '前 (qián) means "front" or "ahead".'
          },
          {
            id: 3,
            type: 'fill-blank',
            chinese: '在第二个路口___转。',
            translation: 'Turn right at the second intersection.',
            question: 'Which direction is "right"?',
            correctAnswer: '右',
            options: ['右', '左', '直', '回'],
            explanation: '右 (yòu) means "right" (direction).'
          },
          {
            id: 4,
            type: 'fill-blank',
            chinese: '医院就在___边。',
            translation: 'The hospital is on the left side.',
            question: 'What word means "left"?',
            correctAnswer: '左',
            options: ['左', '右', '中', '旁'],
            explanation: '左 (zuǒ) means "left" (direction).'
          },
          {
            id: 5,
            type: 'fill-blank',
            chinese: '大约___十分钟。',
            translation: 'It takes about 10 minutes to walk.',
            question: 'What verb means "to walk"?',
            correctAnswer: '走',
            options: ['走', '跑', '开', '坐'],
            explanation: '走 (zǒu) means "to walk" or "to go".'
          }
        ]
      }
    };
    
    this.init();
  }

  init() {
    this.bindEvents();
  }

  bindEvents() {
    // Quiz selection
    document.addEventListener('click', (e) => {
      if (e.target.closest('.quiz-card')) {
        const quizCard = e.target.closest('.quiz-card');
        const quizId = quizCard.dataset.quiz;
        this.startQuiz(quizId);
      }
    });

    // Back to quiz selection
    document.addEventListener('click', (e) => {
      if (e.target.closest('#backToQuizSelection')) {
        this.backToSelection();
      }
    });

    // Answer selection
    document.addEventListener('change', (e) => {
      if (e.target.name === 'quiz-answer') {
        document.getElementById('submitAnswer').disabled = false;
      }
    });

    // Submit answer
    document.addEventListener('click', (e) => {
      if (e.target.closest('#submitAnswer')) {
        this.submitAnswer();
      }
    });

    // Next question
    document.addEventListener('click', (e) => {
      if (e.target.closest('#nextQuestion')) {
        this.nextQuestion();
      }
    });

    // Results actions
    document.addEventListener('click', (e) => {
      if (e.target.closest('#retryQuiz')) {
        this.retryQuiz();
      } else if (e.target.closest('#chooseNewQuiz')) {
        this.backToSelection();
      } else if (e.target.closest('#reviewAnswers')) {
        this.showReview();
      }
    });

    // Review actions
    document.addEventListener('click', (e) => {
      if (e.target.closest('#backToResults') || e.target.closest('#backToResultsBottom')) {
        this.backToResults();
      } else if (e.target.closest('#retryFromReview')) {
        this.retryQuiz();
      }
    });
  }

  startQuiz(quizId) {
    this.currentQuiz = this.quizzes[quizId];
    if (!this.currentQuiz) return;

    // Reset state
    this.currentQuestionIndex = 0;
    this.userAnswers = [];
    this.startTime = Date.now();
    this.timeRemaining = this.currentQuiz.timeLimit;

    // Update UI
    document.getElementById('totalQuestions').textContent = this.currentQuiz.questions.length;

    // Apply theme
    const practiceView = document.getElementById('quizPractice');
    practiceView.className = 'quiz-practice';
    practiceView.classList.add(`${this.currentQuiz.color}-theme`);

    // Show views
    document.getElementById('quizSelection').classList.add('d-none');
    document.getElementById('quizPractice').classList.remove('d-none');
    document.getElementById('quizResults').classList.add('d-none');

    // Start timer
    this.startTimer();

    // Load first question
    this.loadQuestion();
  }

  loadQuestion() {
    const question = this.currentQuiz.questions[this.currentQuestionIndex];
    if (!question) {
      this.showResults();
      return;
    }

    // Update progress
    document.getElementById('currentQuestionNum').textContent = this.currentQuestionIndex + 1;
    const progressPercent = ((this.currentQuestionIndex + 1) / this.currentQuiz.questions.length) * 100;
    document.getElementById('quizProgressFill').style.width = `${progressPercent}%`;

    // Update question content
    document.getElementById('questionText').innerHTML = `<p>${question.chinese}</p>`;
    document.getElementById('questionTranslation').innerHTML = `<p><em>Translation: ${question.translation}</em></p>`;
    
    // Update question header with separate titles
    document.getElementById('quizTitleHeader').textContent = this.currentQuiz.title;
    document.getElementById('questionHeaderTitle').textContent = question.question;

    // Generate answer options
    this.generateAnswerOptions(question);

    // Hide feedback
    document.getElementById('answerFeedback').classList.add('d-none');

    // Reset buttons
    document.getElementById('submitAnswer').disabled = true;
  }

  generateAnswerOptions(question) {
    const optionsContainer = document.getElementById('answerOptions');
    optionsContainer.innerHTML = '';

    question.options.forEach((option, index) => {
      const optionDiv = document.createElement('div');
      optionDiv.className = 'answer-option';
      optionDiv.dataset.answer = option;

      optionDiv.innerHTML = `
        <input type="radio" name="quiz-answer" id="option-${index + 1}" value="${option}">
        <label for="option-${index + 1}">${option}</label>
      `;

      optionsContainer.appendChild(optionDiv);
    });
  }

  submitAnswer() {
    const selectedAnswer = document.querySelector('input[name="quiz-answer"]:checked');
    if (!selectedAnswer) return;

    const question = this.currentQuiz.questions[this.currentQuestionIndex];
    const userAnswer = selectedAnswer.value;
    const isCorrect = userAnswer === question.correctAnswer;

    // Store answer
    this.userAnswers.push({
      questionId: question.id,
      question: question.chinese,
      userAnswer: userAnswer,
      correctAnswer: question.correctAnswer,
      isCorrect: isCorrect,
      timeSpent: Date.now() - this.startTime
    });

    // Show feedback
    this.showAnswerFeedback(isCorrect, question.explanation);
  }

  showAnswerFeedback(isCorrect, explanation) {
    const feedbackDiv = document.getElementById('answerFeedback');
    const feedbackIcon = feedbackDiv.querySelector('.feedback-icon i');
    const feedbackTitle = feedbackDiv.querySelector('.feedback-text h5');
    const feedbackText = feedbackDiv.querySelector('.feedback-text p');

    // Update feedback content
    if (isCorrect) {
      feedbackIcon.className = 'bi bi-check-circle-fill text-success';
      feedbackTitle.textContent = 'Correct!';
      feedbackDiv.className = 'answer-feedback';
    } else {
      feedbackIcon.className = 'bi bi-x-circle-fill text-danger';
      feedbackTitle.textContent = 'Incorrect';
      feedbackDiv.className = 'answer-feedback incorrect';
    }

    feedbackText.textContent = explanation;

    // Show feedback
    feedbackDiv.classList.remove('d-none');
    
    // Auto scroll to feedback section
    setTimeout(() => {
      feedbackDiv.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center',
        inline: 'nearest'
      });
    }, 100);
  }

  nextQuestion() {
    this.currentQuestionIndex++;
    
    if (this.currentQuestionIndex >= this.currentQuiz.questions.length) {
      this.showResults();
    } else {
      this.loadQuestion();
    }
  }

  startTimer() {
    this.updateTimerDisplay();
    
    this.timerInterval = setInterval(() => {
      this.timeRemaining--;
      this.updateTimerDisplay();
      
      if (this.timeRemaining <= 0) {
        this.timeUp();
      }
    }, 1000);
  }

  updateTimerDisplay() {
    const minutes = Math.floor(this.timeRemaining / 60);
    const seconds = this.timeRemaining % 60;
    const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    document.getElementById('quizTimer').textContent = display;

    // Change color when time is running low
    const timerElement = document.querySelector('.quiz-timer');
    if (this.timeRemaining <= 30) {
      timerElement.style.color = 'var(--danger-color)';
    } else if (this.timeRemaining <= 60) {
      timerElement.style.color = 'var(--warning-color)';
    }
  }

  timeUp() {
    clearInterval(this.timerInterval);
    
    // Auto-submit current question if not answered
    if (this.currentQuestionIndex < this.currentQuiz.questions.length) {
      const question = this.currentQuiz.questions[this.currentQuestionIndex];
      this.userAnswers.push({
        questionId: question.id,
        question: question.chinese,
        userAnswer: null,
        correctAnswer: question.correctAnswer,
        isCorrect: false,
        timeSpent: this.currentQuiz.timeLimit * 1000,
        timedOut: true
      });
    }
    
    this.showResults();
  }

  showResults() {
    clearInterval(this.timerInterval);
    
    const totalQuestions = this.currentQuiz.questions.length;
    const correctAnswers = this.userAnswers.filter(answer => answer.isCorrect).length;
    const accuracy = Math.round((correctAnswers / totalQuestions) * 100);
    const timeSpent = this.currentQuiz.timeLimit - this.timeRemaining;
    const timeSpentMinutes = Math.floor(timeSpent / 60);
    const timeSpentSeconds = timeSpent % 60;

    // Update results display
    document.getElementById('correctAnswers').textContent = correctAnswers;
    document.getElementById('totalQuestionsResult').textContent = totalQuestions;
    document.getElementById('accuracyPercentage').textContent = `${accuracy}%`;
    document.getElementById('timeSpent').textContent = `${timeSpentMinutes}:${timeSpentSeconds.toString().padStart(2, '0')}`;

    // Update results message
    let message;
    if (accuracy >= 80) {
      message = "Excellent work! You have a great understanding of the material.";
    } else if (accuracy >= 60) {
      message = "Good job! Keep practicing to improve your skills.";
    } else {
      message = "Keep studying! Practice makes perfect.";
    }
    document.getElementById('resultsMessage').textContent = message;

    // Generate breakdown
    this.generateResultsBreakdown();

    // Show results view
    document.getElementById('quizPractice').classList.add('d-none');
    document.getElementById('quizResults').classList.remove('d-none');
  }

  generateResultsBreakdown() {
    const breakdownList = document.getElementById('breakdownList');
    breakdownList.innerHTML = '';

    this.userAnswers.forEach((answer, index) => {
      const itemDiv = document.createElement('div');
      itemDiv.className = `breakdown-item ${answer.isCorrect ? 'correct' : 'incorrect'}`;

      let statusText, statusIcon;
      if (answer.timedOut) {
        statusText = 'Timed Out';
        statusIcon = 'bi bi-clock';
      } else if (answer.isCorrect) {
        statusText = 'Correct';
        statusIcon = 'bi bi-check-circle';
      } else {
        statusText = 'Incorrect';
        statusIcon = 'bi bi-x-circle';
      }

      itemDiv.innerHTML = `
        <div class="breakdown-question">
          Question ${index + 1}: ${answer.question}
        </div>
        <div class="breakdown-status ${answer.isCorrect ? 'correct' : 'incorrect'}">
          <i class="${statusIcon}"></i>
          <span>${statusText}</span>
        </div>
      `;

      breakdownList.appendChild(itemDiv);
    });
  }

  retryQuiz() {
    this.startQuiz(this.currentQuiz.id);
  }

  backToSelection() {
    clearInterval(this.timerInterval);
    
    // Reset state
    this.currentQuiz = null;
    this.currentQuestionIndex = 0;
    this.userAnswers = [];

    // Show selection view
    document.getElementById('quizSelection').classList.remove('d-none');
    document.getElementById('quizPractice').classList.add('d-none');
    document.getElementById('quizResults').classList.add('d-none');
    document.getElementById('quizReview').classList.add('d-none');
  }

  continueToExercise() {
    // Switch to exercise panel (if available)
    if (window.dashboardModule && window.dashboardModule.showPanel) {
      window.dashboardModule.showPanel('exercise');
    } else {
      // Fallback to just going back to selection
      this.backToSelection();
    }
  }

  showReview() {
    console.log('Starting review with:', {
      currentQuiz: this.currentQuiz,
      userAnswers: this.userAnswers,
      questions: this.currentQuiz?.questions
    });
    
    // Update review title
    document.getElementById('reviewQuizTitle').textContent = `Review: ${this.currentQuiz.title}`;
    
    // Generate review content
    this.generateReviewContent();
    
    // Show review view
    document.getElementById('quizResults').classList.add('d-none');
    document.getElementById('quizReview').classList.remove('d-none');
  }

  backToResults() {
    // Show results view
    document.getElementById('quizReview').classList.add('d-none');
    document.getElementById('quizResults').classList.remove('d-none');
  }

  generateReviewContent() {
    const reviewContainer = document.getElementById('reviewQuestions');
    reviewContainer.innerHTML = '';

    this.userAnswers.forEach((answer, index) => {
      // Find the question by questionId
      const question = this.currentQuiz.questions.find(q => q.id === answer.questionId);
      
      // Skip if question not found
      if (!question) {
        console.warn('Question not found for answer:', answer);
        return;
      }
      
      const reviewItem = document.createElement('div');
      reviewItem.className = `review-item ${answer.isCorrect ? 'correct' : 'incorrect'}`;
      
      // Create pinyin for Chinese text
      const chinesePinyin = this.addPinyin(question.chinese, question.correctAnswer);
      
      reviewItem.innerHTML = `
        <div class="review-question-header">
          <h5>Question ${index + 1}</h5>
          <div class="review-status ${answer.isCorrect ? 'correct' : 'incorrect'}">
            <i class="bi bi-${answer.isCorrect ? 'check-circle-fill' : 'x-circle-fill'}"></i>
            <span>${answer.isCorrect ? 'Correct' : 'Incorrect'}</span>
          </div>
        </div>
        
        <div class="review-question-content">
          <div class="chinese-sentence">
            <p class="chinese-text">${chinesePinyin}</p>
            <p class="english-translation"><em>${question.translation}</em></p>
          </div>
          
          <div class="answer-comparison">
            <div class="user-answer">
              <label>Your Answer:</label>
              <span class="answer-value ${answer.isCorrect ? 'correct' : 'incorrect'}">${answer.userAnswer || 'No answer'}</span>
            </div>
            
            <div class="correct-answer">
              <label>Correct Answer:</label>
              <span class="answer-value correct">${question.correctAnswer}</span>
            </div>
          </div>
          
          <div class="explanation">
            <h6>Explanation:</h6>
            <p>${question.explanation}</p>
          </div>
        </div>
      `;
      
      reviewContainer.appendChild(reviewItem);
    });
  }

  addPinyin(chineseText, correctAnswer) {
    // Add pinyin for common characters - this is a simplified version
    const pinyinMap = {
      '你': 'nǐ',
      '好': 'hǎo', 
      '早': 'zǎo',
      '上': 'shàng',
      '谢': 'xiè',
      '再': 'zài',
      '见': 'jiàn',
      '要': 'yào',
      '菜': 'cài',
      '单': 'dān',
      '好吃': 'hǎo chī',
      '过敏': 'guò mǐn',
      '地铁': 'dì tiě',
      '前': 'qián',
      '右': 'yòu',
      '左': 'zuǒ',
      '走': 'zǒu'
    };
    
    let result = chineseText;
    
    // Replace the blank with the correct answer and add pinyin
    if (result.includes('___')) {
      const pinyin = pinyinMap[correctAnswer] || '';
      const replacement = pinyin ? `<span class="chinese-char">${correctAnswer}<span class="pinyin">${pinyin}</span></span>` : correctAnswer;
      result = result.replace('___', replacement);
    }
    
    // Add pinyin for other common characters
    Object.keys(pinyinMap).forEach(char => {
      if (result.includes(char) && char !== correctAnswer) {
        const regex = new RegExp(char, 'g');
        result = result.replace(regex, `<span class="chinese-char">${char}<span class="pinyin">${pinyinMap[char]}</span></span>`);
      }
    });
    
    return result;
  }
};

// Initialize Quiz Module when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  if (typeof window.quizModule === 'undefined') {
    window.quizModule = new QuizModule();
    console.log('Quiz Module initialized');
  }
});