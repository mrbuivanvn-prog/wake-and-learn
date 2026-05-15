// State
let currentUser = null;
let currentCards = [];
let currentDueCards = [];
let currentCardIndex = 0;
let studyChart = null;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    loadUser();
    setupEventListeners();
    switchTab('home');
});

function loadUser() {
    const savedUser = localStorage.getItem('wakeandlearn_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        document.getElementById('userName').textContent = currentUser.username;
        loadDashboard();
    } else {
        showLoginPrompt();
    }
}

function showLoginPrompt() {
    const username = prompt('Welcome! Enter your username to start learning:');
    const email = prompt('Enter your email:');
    if (username && email) {
        createUser(username, email).then(user => {
            currentUser = user;
            localStorage.setItem('wakeandlearn_user', JSON.stringify(user));
            document.getElementById('userName').textContent = user.username;
            loadDashboard();
            showNotification(`Welcome ${username}! 🎉`, 'success');
        });
    }
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const tab = item.dataset.tab;
            switchTab(tab);
        });
    });
    
    // Create card form
    document.getElementById('createCardForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleCreateCard();
    });
    
    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.removeItem('wakeandlearn_user');
        currentUser = null;
        showLoginPrompt();
    });
    
    // Flashcard click
    document.getElementById('flashcard').addEventListener('click', (e) => {
        if (!e.target.classList.contains('rating-btn')) {
            document.getElementById('flashcard').classList.toggle('flipped');
            if (document.getElementById('flashcard').classList.contains('flipped')) {
                document.getElementById('ratingButtons').style.display = 'flex';
            }
        }
    });
    
    // Rating buttons
    document.querySelectorAll('.rating-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const quality = parseInt(btn.dataset.quality);
            await handleRating(quality);
        });
    });
}

function switchTab(tabName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.tab === tabName);
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}Tab`);
    });
    
    // Load data for tab
    if (tabName === 'home') loadDashboard();
    if (tabName === 'study') loadStudySession();
    if (tabName === 'stats') loadStats();
}

async function loadDashboard() {
    if (!currentUser) return;
    
    try {
        const cards = await getUserCards(currentUser.id);
        const dueCards = await getDueCards(currentUser.id);
        
        document.getElementById('totalCards').textContent = cards.length;
        document.getElementById('dueCards').textContent = dueCards.length;
        
        // Count studied today
        const studiedToday = cards.filter(card => {
            const lastStudied = new Date(card.updated_at);
            const today = new Date();
            return lastStudied.toDateString() === today.toDateString();
        }).length;
        document.getElementById('studiedToday').textContent = studiedToday;
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadStudySession() {
    if (!currentUser) return;
    
    try {
        currentDueCards = await getDueCards(currentUser.id);
        
        if (currentDueCards.length === 0) {
            document.getElementById('flashcard').style.display = 'none';
            document.getElementById('noCardsMessage').style.display = 'block';
            return;
        }
        
        document.getElementById('flashcard').style.display = 'block';
        document.getElementById('noCardsMessage').style.display = 'none';
        currentCardIndex = 0;
        displayCurrentCard();
        updateStudyProgress();
    } catch (error) {
        console.error('Error loading study session:', error);
    }
}

function displayCurrentCard() {
    if (currentCardIndex >= currentDueCards.length) {
        completeStudySession();
        return;
    }
    
    const card = currentDueCards[currentCardIndex];
    document.getElementById('cardTopic').textContent = card.topic || 'General';
    document.getElementById('cardQuestion').textContent = card.question;
    document.getElementById('cardAnswer').textContent = card.answer;
    
    // Reset flashcard
    const flashcard = document.getElementById('flashcard');
    flashcard.classList.remove('flipped');
    document.getElementById('ratingButtons').style.display = 'none';
}

function updateStudyProgress() {
    const studied = currentCardIndex;
    const total = currentDueCards.length;
    const percentage = (studied / total) * 100;
    
    document.getElementById('cardCounter').textContent = `Card ${studied + 1} / ${total}`;
    document.getElementById('studyProgress').style.width = `${percentage}%`;
}

async function handleRating(quality) {
    const card = currentDueCards[currentCardIndex];
    
    // Simple spaced repetition calculation
    let easeFactor = 2.5;
    let interval = 1;
    let repetitions = 0;
    
    if (quality === 2) { // Easy
        interval = Math.ceil(interval * easeFactor);
        repetitions++;
    } else if (quality === 1) { // Good
        interval = Math.ceil(interval * easeFactor * 0.8);
        repetitions++;
    } else { // Hard
        interval = 1;
        repetitions = 0;
        easeFactor = Math.max(1.3, easeFactor - 0.2);
    }
    
    try {
        await createStudySession(card.id, currentUser.id, easeFactor, interval, repetitions);
        showNotification('Great job! Card recorded! 📝', 'success');
        
        currentCardIndex++;
        updateStudyProgress();
        
        if (currentCardIndex < currentDueCards.length) {
            displayCurrentCard();
        } else {
            completeStudySession();
        }
        
        loadDashboard();
    } catch (error) {
        console.error('Error recording study session:', error);
        showNotification('Error saving progress', 'error');
    }
}

function completeStudySession() {
    showNotification('🎉 Congratulations! You completed all due cards!', 'success');
    switchTab('home');
    loadStudySession();
}

async function handleCreateCard() {
    const topic = document.getElementById('topic').value;
    const question = document.getElementById('question').value;
    const answer = document.getElementById('answer').value;
    const difficulty = document.getElementById('difficulty').value;
    
    try {
        await createCard(currentUser.id, question, answer, topic, difficulty);
        showNotification('Card created successfully! 📚', 'success');
        
        // Clear form
        document.getElementById('createCardForm').reset();
        loadDashboard();
        
        // Optional: ask to create another
        setTimeout(() => {
            if (confirm('Create another card?')) {
                document.getElementById('topic').focus();
            }
        }, 500);
    } catch (error) {
        console.error('Error creating card:', error);
        showNotification('Error creating card', 'error');
    }
}

async function loadStats() {
    if (!currentUser) return;
    
    try {
        const cards = await getUserCards(currentUser.id);
        
        // Prepare chart data
        const topics = {};
        cards.forEach(card => {
            const topic = card.topic || 'General';
            topics[topic] = (topics[topic] || 0) + 1;
        });
        
        const ctx = document.getElementById('studyChart').getContext('2d');
        if (studyChart) studyChart.destroy();
        
        studyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(topics),
                datasets: [{
                    label: 'Cards per Topic',
                    data: Object.values(topics),
                    backgroundColor: 'rgba(102, 126, 234, 0.5)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.style.background = type === 'success' ? '#4caf50' : '#f44336';
    notification.style.color = 'white';
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}
