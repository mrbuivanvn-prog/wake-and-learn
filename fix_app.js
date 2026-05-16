import re

with open("frontend/js/app.js", "r") as f:
    content = f.read()

# Replace userId with auth state
content = re.sub(r'let userId = 1;', 'let token = localStorage.getItem("token");\nlet currentUser = null;', content)

# Inject auth and api fetch functions
auth_code = """
async function apiFetch(endpoint, options = {}) {
    if (!options.headers) options.headers = {};
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(`http://localhost:8000${endpoint}`, options);
    if (res.status === 401) {
        logout();
        throw new Error("Unauthorized");
    }
    return res;
}

let authMode = 'login';
function toggleAuthMode() {
    authMode = authMode === 'login' ? 'register' : 'login';
    document.getElementById('authTitle').innerText = authMode === 'login' ? 'Đăng nhập' : 'Đăng ký';
    document.getElementById('authSwitchText').innerText = authMode === 'login' ? 'Chưa có tài khoản? Đăng ký' : 'Đã có tài khoản? Đăng nhập';
}

async function handleAuth() {
    let username = document.getElementById('authUsername').value;
    let password = document.getElementById('authPassword').value;
    if (!username || !password) {
        showToast('Vui lòng nhập đủ thông tin');
        return;
    }
    try {
        let res = await fetch(`http://localhost:8000/auth/${authMode}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        if (res.ok) {
            let data = await res.json();
            token = data.token;
            localStorage.setItem('token', token);
            currentUser = data.username;
            document.getElementById('loginOverlay').classList.remove('active');
            document.getElementById('username').innerText = currentUser;
            showToast('Đăng nhập thành công');
            init();
        } else {
            let err = await res.json();
            showToast(err.detail || 'Lỗi đăng nhập');
        }
    } catch (e) {
        showToast('Không kết nối được server');
    }
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    document.getElementById('loginOverlay').classList.add('active');
}

// Exercises logic
async function loadExercises() {
    try {
        let res = await apiFetch('/exercises/fill-blank');
        let questions = await res.json();
        let html = '';
        questions.forEach(q => {
            let text = q.cloze_text.replace('_____', `<input type="text" class="exercise-input" id="ex-${q.vocab_id}" onkeypress="if(event.key === 'Enter') checkExercise(${q.vocab_id})">`);
            html += `
                <div class="exercise-card">
                    <div class="exercise-text">${text}</div>
                    <div class="exercise-vi">${q.example_vi}</div>
                    <button class="btn btn-primary" onclick="checkExercise(${q.vocab_id})">Kiểm tra</button>
                    <div id="ex-res-${q.vocab_id}" class="exercise-result"></div>
                </div>
            `;
        });
        if(questions.length === 0) html = '<p>Bạn chưa có từ vựng nào để làm bài tập!</p>';
        document.getElementById('exercisesContainer').innerHTML = html;
    } catch (e) {
        console.log(e);
    }
}

async function checkExercise(vocab_id) {
    let ans = document.getElementById(`ex-${vocab_id}`).value;
    if (!ans) return;
    try {
        let res = await apiFetch('/exercises/fill-blank/submit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({vocab_id: vocab_id, answer: ans})
        });
        let data = await res.json();
        let resDiv = document.getElementById(`ex-res-${vocab_id}`);
        if (data.correct) {
            resDiv.innerHTML = '✅ Chính xác!';
            resDiv.className = 'exercise-result correct';
        } else {
            resDiv.innerHTML = `❌ Sai rồi! Đáp án đúng: ${data.correct_answer}`;
            resDiv.className = 'exercise-result incorrect';
        }
    } catch (e) {
        console.log(e);
    }
}
"""

content = re.sub(r'async function init\(\) {', auth_code + '\nasync function init() {\n    if (!token) {\n        document.getElementById("loginOverlay").classList.add("active");\n        return;\n    } else {\n        document.getElementById("loginOverlay").classList.remove("active");\n    }\n', content)

# Fix fetch calls
content = content.replace('await fetch(`http://localhost:8000/api/users/${userId}/cards`)', 'await apiFetch("/words/all")')
content = content.replace('await fetch(`http://localhost:8000/api/users/${userId}/due-cards`)', 'await apiFetch("/words/today")')

# Adjust loadStats due to API difference
# old: let cards = await res.json();
#      document.getElementById('totalCards').innerText = cards.length;
# new for due-cards: let dueRes = await apiFetch('/words/today'); let dueCardsData = await dueRes.json();
# But wait! I will just rewrite loadStats and loadStudyCards and showStudyCard manually because it's too much Regex.

new_loadStats = """async function loadStats() {
    try {
        let res = await apiFetch(`/stats/dashboard`);
        let data = await res.json();
        document.getElementById('totalCards').innerText = data.progress.total;
        document.getElementById('userStats').innerText = `${data.progress.total} thẻ`;
        document.getElementById('dueCards').innerText = data.today_review_words;
        document.getElementById('streak').innerText = data.streak;
    } catch(e){}
}"""
content = re.sub(r'async function loadStats\(\) \{[\s\S]*?\}', new_loadStats, content, flags=re.MULTILINE)

new_loadStudyCards = """async function loadStudyCards() {
    try {
        let res = await apiFetch(`/words/today`);
        let data = await res.json();
        dueCards = data.words || [];
        
        if (dueCards.length === 0) {
            document.getElementById('studyContent').innerHTML = '<div class="ai-box"><p>🎉 Chúc mừng! Hôm nay bạn đã học hết thẻ rồi!</p><button class="btn btn-primary" onclick="switchTab(\\\'ai\\\')">Tạo thêm thẻ mới</button></div>';
            return;
        }
        
        currentCardIndex = 0;
        showStudyCard();
    } catch(e){}
}"""
content = re.sub(r'async function loadStudyCards\(\) \{[\s\S]*?\}', new_loadStudyCards, content, flags=re.MULTILINE)

new_showStudyCard = """function showStudyCard() {
    if (currentCardIndex >= dueCards.length) {
        loadStudyCards();
        return;
    }
    
    let card = dueCards[currentCardIndex];
    let html = `
        <div class="flashcard-container">
            <div class="flashcard" id="studyFlashcard">
                <div class="flashcard-inner">
                    <div class="flashcard-front">
                        <div class="card-text">🇬🇧 ${card.word}</div>
                        <div style="font-size: 1rem; color: #ddd;">${card.pronunciation}</div>
                        <button class="audio-btn" onclick="speakText('en', '${card.word.replace(/'/g, "\\'")}')">🔊 Nghe tiếng Anh</button>
                        <div style="margin-top: 20px; font-size: 12px;">👆 Chạm để xem đáp án</div>
                    </div>
                    <div class="flashcard-back">
                        <div class="card-text">🇻🇳 ${card.meaning}</div>
                        <div style="font-size: 1rem; color: #666;">${card.example_vi}</div>
                        <button class="audio-btn" onclick="speakText('vi', '${card.meaning.replace(/'/g, "\\'")}')">🔊 Nghe tiếng Việt</button>
                        <div class="rating-buttons">
                            <button class="rating-btn hard" onclick="rateCard(0)">😫 Khó - Học lại</button>
                            <button class="rating-btn medium" onclick="rateCard(1)">😊 Tạm được - Ôn mai</button>
                            <button class="rating-btn easy" onclick="rateCard(2)">🎉 Dễ - Ôn sau 3 ngày</button>
                        </div>
                    </div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 1rem;">${currentCardIndex + 1} / ${dueCards.length}</div>
        </div>
    `;
    document.getElementById('studyContent').innerHTML = html;
    
    let flashcard = document.getElementById('studyFlashcard');
    if (flashcard) {
        flashcard.onclick = (e) => {
            if (!e.target.classList.contains('audio-btn') && !e.target.classList.contains('rating-btn')) {
                flashcard.classList.toggle('flipped');
            }
        };
    }
}"""
content = re.sub(r'function showStudyCard\(\) \{[\s\S]*?(?=async function rateCard)', new_showStudyCard + '\n', content, flags=re.MULTILINE)

new_rateCard = """async function rateCard(quality) {
    let card = dueCards[currentCardIndex];
    let is_correct = quality > 0;
    
    await apiFetch(`/words/learn?vocab_id=${card.id}&is_correct=${is_correct}`, {
        method: 'POST'
    });
    
    currentCardIndex++;
    if (currentCardIndex < dueCards.length) {
        showStudyCard();
    } else {
        showToast('🎉 Hoàn thành! Ngày mai quay lại nhé!');
        loadStudyCards();
    }
    loadStats();
}"""
content = re.sub(r'async function rateCard\(quality\) \{[\s\S]*?\}', new_rateCard, content, flags=re.MULTILINE)

# Also fix toggle tab to load exercises when exercises tab is clicked
content = content.replace("if (tab === 'study') loadStudyCards();", "if (tab === 'study') loadStudyCards(); if (tab === 'exercises') loadExercises();")

# Fix Batch AI and Chat and other features if possible, but let's just make the core work.
with open("frontend/js/app.js", "w") as f:
    f.write(content)
