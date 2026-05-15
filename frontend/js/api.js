const API_BASE_URL = 'http://localhost:8000/api';

// User API
async function createUser(username, email) {
    const response = await fetch(`${API_BASE_URL}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email })
    });
    return response.json();
}

async function getUser(userId) {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`);
    return response.json();
}

// Card API
async function createCard(userId, question, answer, topic, difficulty) {
    const response = await fetch(`${API_BASE_URL}/cards`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, question, answer, topic, difficulty })
    });
    return response.json();
}

async function getUserCards(userId) {
    const response = await fetch(`${API_BASE_URL}/users/${userId}/cards`);
    return response.json();
}

async function getCard(cardId) {
    const response = await fetch(`${API_BASE_URL}/cards/${cardId}`);
    return response.json();
}

async function deleteCard(cardId) {
    const response = await fetch(`${API_BASE_URL}/cards/${cardId}`, {
        method: 'DELETE'
    });
    return response.json();
}

async function getDueCards(userId) {
    const response = await fetch(`${API_BASE_URL}/users/${userId}/due-cards`);
    return response.json();
}

// Study Session API
async function createStudySession(cardId, userId, easeFactor, interval, repetitions) {
    const response = await fetch(`${API_BASE_URL}/study-sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: cardId, user_id: userId, ease_factor: easeFactor, interval, repetitions })
    });
    return response.json();
}
