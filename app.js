// Firebase Configuration
const firebaseConfig = {
  apiKey: "AIzaSyDnmZ7YoQlfbJ8oTvmlnhBOLZ5vem1XhmI",
  authDomain: "ai-interviewer-6b475.firebaseapp.com",
  databaseURL: "https://ai-interviewer-6b475-default-rtdb.firebaseio.com",
  projectId: "ai-interviewer-6b475",
  storageBucket: "ai-interviewer-6b475.firebasestorage.app",
  messagingSenderId: "308796780282",
  appId: "1:308796780282:web:d2995ee8ddd38d2d61a343"
};


// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const database = firebase.database();

// Global State
let currentScreen = 'setup';
let selectedCompany = '';
let interviewQuestions = [];
let currentQuestionIndex = 0;
let answers = [];
let mediaRecorder = null;
let recordedChunks = [];
let videoStream = null;
let recognition = null;
let isListening = false;

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;
} else {
    alert('Speech recognition is not supported in this browser. Please use Chrome.');
}

// DOM Elements
const setupScreen = document.getElementById('setupScreen');
const adminScreen = document.getElementById('adminScreen');
const interviewScreen = document.getElementById('interviewScreen');
const resultsScreen = document.getElementById('resultsScreen');

const companySelect = document.getElementById('companySelect');
const startButton = document.getElementById('startButton');
const companyInfo = document.getElementById('companyInfo');
const questionCount = document.getElementById('questionCount');

const manageQuestionsLink = document.getElementById('manageQuestionsLink');
const backToHome = document.getElementById('backToHome');
const adminCompany = document.getElementById('adminCompany');
const adminQuestion = document.getElementById('adminQuestion');
const addQuestionBtn = document.getElementById('addQuestionBtn');
const filterCompany = document.getElementById('filterCompany');
const questionsList = document.getElementById('questionsList');

const userVideo = document.getElementById('userVideo');
const aiBall = document.getElementById('aiBall');
const aiStatus = document.getElementById('aiStatus');
const soundWave = document.getElementById('soundWave');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const questionText = document.getElementById('questionText');
const answerText = document.getElementById('answerText');
const listenBtn = document.getElementById('listenBtn');
const typeBtn = document.getElementById('typeBtn');
const nextBtn = document.getElementById('nextBtn');
const finishBtn = document.getElementById('finishBtn');
const statusMessage = document.getElementById('statusMessage');

const resultCompany = document.getElementById('resultCompany');
const resultAnswered = document.getElementById('resultAnswered');
const resultDate = document.getElementById('resultDate');
const responsesList = document.getElementById('responsesList');
const downloadBtn = document.getElementById('downloadBtn');
const downloadVideoBtn = document.getElementById('downloadVideoBtn');
const newInterviewBtn = document.getElementById('newInterviewBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCompanies();
    setupEventListeners();
});

// Load Companies from Firebase
function loadCompanies() {
    database.ref('questions').once('value', (snapshot) => {
        const data = snapshot.val();
        const companies = new Set();
        
        if (data) {
            Object.values(data).forEach(question => {
                companies.add(question.company);
            });
        }
        
        // Populate company select
        companySelect.innerHTML = '<option value="">Select a company</option>';
        filterCompany.innerHTML = '<option value="">All Companies</option>';
        
        companies.forEach(company => {
            const option = document.createElement('option');
            option.value = company;
            option.textContent = company;
            companySelect.appendChild(option);
            
            const filterOption = document.createElement('option');
            filterOption.value = company;
            filterOption.textContent = company;
            filterCompany.appendChild(filterOption);
        });
        
        if (companies.size === 0) {
            companySelect.innerHTML = '<option value="">No companies available - Add questions first</option>';
        }
    });
}

// Event Listeners
function setupEventListeners() {
    companySelect.addEventListener('change', handleCompanyChange);
    startButton.addEventListener('click', startInterview);
    manageQuestionsLink.addEventListener('click', (e) => {
        e.preventDefault();
        showScreen('admin');
        loadAllQuestions();
    });
    backToHome.addEventListener('click', () => showScreen('setup'));
    addQuestionBtn.addEventListener('click', addQuestion);
    filterCompany.addEventListener('change', loadAllQuestions);
    
    listenBtn.addEventListener('click', toggleListening);
    typeBtn.addEventListener('click', typeAnswer);
    nextBtn.addEventListener('click', nextQuestion);
    finishBtn.addEventListener('click', finishInterview);
    
    downloadBtn.addEventListener('click', downloadResults);
    downloadVideoBtn.addEventListener('click', downloadVideo);
    newInterviewBtn.addEventListener('click', () => {
        location.reload();
    });
}

// Handle Company Change
function handleCompanyChange() {
    selectedCompany = companySelect.value;
    
    if (selectedCompany) {
        // Count questions for this company
        database.ref('questions').orderByChild('company').equalTo(selectedCompany).once('value', (snapshot) => {
            const count = snapshot.numChildren();
            questionCount.textContent = count;
            companyInfo.style.display = 'block';
            startButton.disabled = count < 5;
            
            if (count < 5) {
                alert(`This company only has ${count} questions. Please add at least 5 questions to start an interview.`);
            }
        });
    } else {
        companyInfo.style.display = 'none';
        startButton.disabled = true;
    }
}

// Add Question
function addQuestion() {
    const company = adminCompany.value.trim();
    const question = adminQuestion.value.trim();
    
    if (!company || !question) {
        alert('Please enter both company name and question');
        return;
    }
    
    const questionId = Date.now().toString();
    
    database.ref('questions/' + questionId).set({
        company: company,
        question: question,
        id: questionId,
        createdAt: new Date().toISOString()
    }).then(() => {
        alert('Question added successfully!');
        adminCompany.value = '';
        adminQuestion.value = '';
        loadCompanies();
        loadAllQuestions();
    }).catch((error) => {
        alert('Error adding question: ' + error.message);
    });
}

// Load All Questions
function loadAllQuestions() {
    const filter = filterCompany.value;
    
    let query = database.ref('questions');
    if (filter) {
        query = query.orderByChild('company').equalTo(filter);
    }
    
    query.once('value', (snapshot) => {
        const data = snapshot.val();
        questionsList.innerHTML = '';
        
        if (!data) {
            questionsList.innerHTML = '<p class="loading">No questions found</p>';
            return;
        }
        
        Object.values(data).forEach(q => {
            const div = document.createElement('div');
            div.className = 'question-item';
            div.innerHTML = `
                <div class="question-content">
                    <div class="question-company">${q.company}</div>
                    <div class="question-text-item">${q.question}</div>
                </div>
                <button class="delete-btn" onclick="deleteQuestion('${q.id}')">Delete</button>
            `;
            questionsList.appendChild(div);
        });
    });
}

// Delete Question
function deleteQuestion(id) {
    if (confirm('Are you sure you want to delete this question?')) {
        database.ref('questions/' + id).remove().then(() => {
            alert('Question deleted successfully!');
            loadCompanies();
            loadAllQuestions();
        }).catch((error) => {
            alert('Error deleting question: ' + error.message);
        });
    }
}

// Start Interview
async function startInterview() {
    // Load questions for selected company
    const snapshot = await database.ref('questions').orderByChild('company').equalTo(selectedCompany).once('value');
    const allQuestions = Object.values(snapshot.val());
    
    // Select 5 random questions
    interviewQuestions = getRandomQuestions(allQuestions, 5);
    currentQuestionIndex = 0;
    answers = [];
    
    // Initialize video
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: true 
        });
        userVideo.srcObject = videoStream;
        
        // Setup MediaRecorder
        recordedChunks = [];
        mediaRecorder = new MediaRecorder(videoStream, {
            mimeType: 'video/webm;codecs=vp9'
        });
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.start();
        
        // Show interview screen
        showScreen('interview');
        
        // Small delay then ask first question
        setTimeout(() => {
            askCurrentQuestion();
        }, 500);
        
    } catch (error) {
        alert('Error accessing camera/microphone: ' + error.message);
    }
}

// Get Random Questions
function getRandomQuestions(array, count) {
    const shuffled = array.sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
}

// Ask Current Question
function askCurrentQuestion() {
    const question = interviewQuestions[currentQuestionIndex];
    questionText.textContent = question.question;
    answerText.innerHTML = '<p class="placeholder">Your transcribed answer will appear here...</p>';
    
    // Update progress
    const progress = ((currentQuestionIndex + 1) / interviewQuestions.length) * 100;
    progressFill.style.width = progress + '%';
    progressText.textContent = `Question ${currentQuestionIndex + 1} of ${interviewQuestions.length}`;
    
    // Reset buttons
    nextBtn.disabled = true;
    listenBtn.disabled = true; // Disable while AI is speaking
    typeBtn.disabled = true;
    
    // Automatically speak question with animation
    speakQuestion(`Question ${currentQuestionIndex + 1}. ${question.question}`);
}

// Speak Question with Animation
function speakQuestion(text) {
    // Start animation
    aiBall.classList.add('speaking');
    aiStatus.textContent = 'Speaking...';
    soundWave.classList.add('active'); // Show sound wave
    statusMessage.textContent = '🎙️ AI is asking the question... Please listen';
    statusMessage.style.background = 'linear-gradient(135deg, #f093fb22 0%, #f5576c22 100%)';
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    utterance.onstart = () => {
        console.log('AI started speaking');
    };
    
    utterance.onend = () => {
        // Stop animation
        aiBall.classList.remove('speaking');
        soundWave.classList.remove('active'); // Hide sound wave
        aiStatus.textContent = 'Ready to listen';
        statusMessage.textContent = '🎯 AI finished asking. Now record your answer!';
        statusMessage.style.background = 'linear-gradient(135deg, #667eea22 0%, #764ba222 100%)';
        
        // Enable buttons after speaking
        listenBtn.disabled = false;
        typeBtn.disabled = false;
        
        console.log('AI finished speaking');
    };
    
    utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        // Stop animation even on error
        aiBall.classList.remove('speaking');
        soundWave.classList.remove('active');
        aiStatus.textContent = 'Ready';
        statusMessage.textContent = '⚠️ Could not speak question, but you can see it above';
        
        // Enable buttons anyway
        listenBtn.disabled = false;
        typeBtn.disabled = false;
    };
    
    // Cancel any ongoing speech and start new one
    speechSynthesis.cancel();
    speechSynthesis.speak(utterance);
}

// Speak Text (for confirmations, not questions)
function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    speechSynthesis.speak(utterance);
}

// Toggle Listening
function toggleListening() {
    if (isListening) {
        stopListening();
    } else {
        startListening();
    }
}

// Start Listening
function startListening() {
    if (!recognition) {
        alert('Speech recognition not supported in this browser. Please use Chrome and ensure internet connection.');
        return;
    }
    
    isListening = true;
    aiBall.classList.add('listening');
    aiStatus.textContent = 'Listening...';
    listenBtn.classList.add('listening');
    listenBtn.innerHTML = '<span>🎤</span><span>Listening...</span>';
    statusMessage.textContent = '🎤 Speak now... (speak clearly and naturally)';
    
    let finalTranscript = '';
    let interimTranscript = '';
    
    recognition.onstart = () => {
        console.log('Speech recognition started');
    };
    
    recognition.onresult = (event) => {
        interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Show interim results in real-time
        const displayText = finalTranscript + interimTranscript;
        if (displayText.trim()) {
            answerText.innerHTML = `<p>${displayText}</p>`;
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        
        let errorMessage = '';
        switch(event.error) {
            case 'network':
                errorMessage = '❌ Network error. Please check your internet connection and try again.';
                // Offer text input as fallback
                offerTextInput();
                break;
            case 'not-allowed':
                errorMessage = '❌ Microphone access denied. Please allow microphone permissions.';
                break;
            case 'no-speech':
                errorMessage = '⚠️ No speech detected. Please try again and speak clearly.';
                break;
            case 'aborted':
                errorMessage = '⚠️ Recognition aborted. Click the button to try again.';
                break;
            default:
                errorMessage = '❌ Error: ' + event.error + '. Try again or use text input.';
                offerTextInput();
        }
        
        statusMessage.textContent = errorMessage;
        stopListening();
    };
    
    recognition.onend = () => {
        console.log('Speech recognition ended');
        
        if (isListening) {
            // If we got a transcript, save it
            if (finalTranscript.trim()) {
                displayAnswer(finalTranscript.trim());
            }
            stopListening();
        }
    };
    
    try {
        recognition.start();
    } catch (error) {
        console.error('Error starting recognition:', error);
        statusMessage.textContent = '❌ Could not start speech recognition. Please check microphone permissions.';
        stopListening();
    }
}

// Stop Listening
function stopListening() {
    isListening = false;
    aiBall.classList.remove('listening');
    aiStatus.textContent = 'Ready';
    listenBtn.classList.remove('listening');
    listenBtn.innerHTML = '<span>🎤</span><span>Listen to Answer</span>';
    
    if (recognition) {
        recognition.stop();
    }
}

// Display Answer
function displayAnswer(answer) {
    answerText.innerHTML = `<p>${answer}</p>`;
    
    // Save answer
    answers.push({
        question: interviewQuestions[currentQuestionIndex].question,
        answer: answer,
        timestamp: new Date().toISOString()
    });
    
    nextBtn.disabled = false;
    statusMessage.textContent = '✅ Answer recorded! Click "Next Question" to continue';
    
    // Speak confirmation
    speakText("Thank you. I've recorded your answer.");
}

// Type Answer (Manual Input)
function typeAnswer() {
    const answer = prompt('Type your answer to the question:');
    
    if (answer && answer.trim()) {
        displayAnswer(answer.trim());
    }
}

// Offer Text Input Fallback
function offerTextInput() {
    const useTextInput = confirm(
        'Speech recognition is having issues.\n\n' +
        'Would you like to type your answer instead?'
    );
    
    if (useTextInput) {
        const textAnswer = prompt('Please type your answer:');
        if (textAnswer && textAnswer.trim()) {
            displayAnswer(textAnswer.trim());
        }
    }
}

// Next Question
function nextQuestion() {
    currentQuestionIndex++;
    
    if (currentQuestionIndex < interviewQuestions.length) {
        askCurrentQuestion();
    } else {
        finishInterview();
    }
}

// Finish Interview
function finishInterview() {
    if (answers.length === 0) {
        alert('No answers recorded yet!');
        return;
    }
    
    // Stop recording
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    
    // Stop video stream
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
    }
    
    // Show results
    showResults();
}

// Show Results
function showResults() {
    resultCompany.textContent = selectedCompany;
    resultAnswered.textContent = `${answers.length}/${interviewQuestions.length}`;
    resultDate.textContent = new Date().toLocaleDateString();
    
    // Display responses
    responsesList.innerHTML = '';
    answers.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'response-item';
        div.innerHTML = `
            <div class="response-question">Q${index + 1}: ${item.question}</div>
            <div class="response-answer">${item.answer}</div>
        `;
        responsesList.appendChild(div);
    });
    
    showScreen('results');
    
    // Speak completion
    speakText('Interview completed. Great job!');
}

// Download Results
function downloadResults() {
    const results = {
        company: selectedCompany,
        date: new Date().toISOString(),
        totalQuestions: interviewQuestions.length,
        answeredQuestions: answers.length,
        responses: answers
    };
    
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview_${selectedCompany}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// Download Video
function downloadVideo() {
    if (recordedChunks.length === 0) {
        alert('No video recorded');
        return;
    }
    
    const blob = new Blob(recordedChunks, { type: 'video/webm' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview_${selectedCompany}_${Date.now()}.webm`;
    a.click();
    URL.revokeObjectURL(url);
}

// Show Screen
function showScreen(screen) {
    setupScreen.classList.remove('active');
    adminScreen.classList.remove('active');
    interviewScreen.classList.remove('active');
    resultsScreen.classList.remove('active');
    
    switch(screen) {
        case 'setup':
            setupScreen.classList.add('active');
            break;
        case 'admin':
            adminScreen.classList.add('active');
            break;
        case 'interview':
            interviewScreen.classList.add('active');
            break;
        case 'results':
            resultsScreen.classList.add('active');
            break;
    }
    
    currentScreen = screen;
}
