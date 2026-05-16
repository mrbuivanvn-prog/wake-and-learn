const API_BASE_URL = 'http://localhost:8000/api';

let currentUser = null;

async function initUser() {
    let saved = localStorage.getItem('wake_user');
    if (saved) {
        currentUser = JSON.parse(saved);
        let nameEl = document.getElementById('username');
        if (nameEl) nameEl.innerText = currentUser.username;
        return currentUser;
    }
    
    let username = prompt('👋 Nhập tên của bạn:', 'demo');
    let email = prompt('📧 Email:', `${username}@example.com`);
    
    if (username) {
        try {
            let res = await fetch(`${API_BASE_URL}/users`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ username, email })
            });
            currentUser = await res.json();
            localStorage.setItem('wake_user', JSON.stringify(currentUser));
            let nameEl = document.getElementById('username');
            if (nameEl) nameEl.innerText = currentUser.username;
            return currentUser;
        } catch (error) {
            console.error('Init user error:', error);
            currentUser = { id: 1, username: username };
            localStorage.setItem('wake_user', JSON.stringify(currentUser));
            return currentUser;
        }
    }
    return null;
}

async function getCards() {
    if (!currentUser) return [];
    try {
        let res = await fetch(`${API_BASE_URL}/users/${currentUser.id}/cards`);
        return res.json();
    } catch (error) {
        return [];
    }
}

async function getDueCards() {
    if (!currentUser) return [];
    try {
        let res = await fetch(`${API_BASE_URL}/users/${currentUser.id}/due-cards`);
        return res.json();
    } catch (error) {
        return [];
    }
}

async function saveCard(question, answer, topic, difficulty) {
    if (!currentUser) return null;
    try {
        console.log("Saving card to:", `${API_BASE_URL}/cards`);
        let res = await fetch(`${API_BASE_URL}/cards`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: currentUser.id,
                question: question,
                answer: answer,
                topic: topic || 'General',
                difficulty: difficulty || 'medium'
            })
        });
        if (!res.ok) {
            console.error("Save card failed:", res.status);
            return null;
        }
        return res.json();
    } catch (error) {
        console.error('Save card error:', error);
        return null;
    }
}

async function saveStudySession(cardId, easeFactor, interval, repetitions) {
    if (!currentUser) return;
    try {
        await fetch(`${API_BASE_URL}/study-sessions`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                card_id: cardId,
                user_id: currentUser.id,
                ease_factor: easeFactor,
                interval: interval,
                repetitions: repetitions
            })
        });
    } catch (error) {
        console.error('Save study session error:', error);
    }
}

async function generateAICard(word) {
    try {
        let res = await fetch(`${API_BASE_URL}/ai/generate-bilingual-card?word=${encodeURIComponent(word)}`, { 
            method: 'POST' 
        });
        if (!res.ok) {
            throw new Error('API error');
        }
        return res.json();
    } catch (error) {
        console.error('Generate AI card error:', error);
        return {
            card: {
                id: Date.now(),
                question: word,
                answer: `nghĩa của ${word}`,
                topic: 'Vocabulary',
                difficulty: 'medium'
            },
            examples_en: [`Example with ${word}`],
            examples_vn: [`Ví dụ với ${word}`]
        };
    }
}

async function chatWithAI(question) {
    try {
        let res = await fetch(`${API_BASE_URL}/ai/chat?question=${encodeURIComponent(question)}`, { 
            method: 'POST' 
        });
        let data = await res.json();
        return data.response;
    } catch (error) {
        return `Xin lỗi, lỗi: ${error.message}`;
    }
}
