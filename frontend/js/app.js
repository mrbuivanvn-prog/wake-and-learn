let token = localStorage.getItem("token");
let currentUser = null;
let dueCards = [];
let currentCardIndex = 0;

function escapeJS(str) {
    if (!str) return "";
    return str.toString().replace(/'/g, "\\'").replace(/"/g, "&quot;").replace(/\n/g, " ");
}

async function apiFetch(endpoint, options = {}) {
    if (!options.headers) options.headers = {};
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    if (options.body && !options.headers['Content-Type']) {
        options.headers['Content-Type'] = 'application/json';
    }
    let timeout = options.timeout || 10000;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    options.signal = controller.signal;
    try {
        const res = await fetch(`${location.protocol}//${location.hostname}:8000${endpoint}`, options);
        clearTimeout(timeoutId);
        if (res.status === 401) {
            logout();
            throw new Error("Unauthorized");
        }
        return res;
    } catch (e) {
        clearTimeout(timeoutId);
        throw e;
    }
}

let authMode = 'login';
window.toggleAuthMode = function() {
    authMode = authMode === 'login' ? 'register' : 'login';
    document.getElementById('authTitle').innerText = authMode === 'login' ? 'Đăng nhập' : 'Đăng ký';
    document.getElementById('authSwitchText').innerText = authMode === 'login' ? 'Chưa có tài khoản? Đăng ký' : 'Đã có tài khoản? Đăng nhập';
}

window.handleAuth = async function() {
    let username = document.getElementById('authUsername').value;
    let password = document.getElementById('authPassword').value;
    if (!username || !password) {
        showToast('Vui lòng nhập đủ thông tin');
        return;
    }
    try {
        let res = await fetch(`${location.protocol}//${location.hostname}:8000/auth/${authMode}`, {
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

window.logout = function() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    document.getElementById('loginOverlay').classList.add('active');
}

async function init() {
    if (!token) {
        document.getElementById('loginOverlay').classList.add('active');
        return;
    }
    try {
        let res = await apiFetch('/auth/me');
        let data = await res.json();
        currentUser = data.username;
        document.getElementById('username').innerText = currentUser;
        
        await loadSettings();
        await loadStats();
        await loadStudyCards();
        setupTabs();
    } catch (e) {
        logout();
    }
}

window.loadSettings = async function() {
    try {
        let res = await apiFetch('/settings');
        let data = await res.json();
        if (data.settings) {
            document.getElementById('settingDailyGoal').value = data.settings.daily_goal;
            document.getElementById('settingProfession').value = data.settings.profession || 'Tổng quát';
            document.getElementById('settingLang').value = data.settings.learning_language || 'en';
            
            let lang = data.settings.learning_language || 'en';
            let prof = data.settings.profession || 'Tổng quát';
            let langText = lang === 'trilingual' ? '🌍 3 Ngôn ngữ' : (lang === 'zh' ? '🇨🇳 Tiếng Trung' : '🇬🇧 Tiếng Anh');
            
            document.getElementById('activeGoalDisplay').innerText = langText;
            document.getElementById('aiStatusDisplay').innerText = `💼 Ngành: ${prof}`;
        }
    } catch (e) { console.log(e); }
}

window.saveUserSettings = async function() {
    let goal = document.getElementById('settingDailyGoal').value;
    let prof = document.getElementById('settingProfession').value;
    let lang = document.getElementById('settingLang').value;
    
    let res = await apiFetch('/settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ daily_goal: goal, profession: prof, learning_language: lang })
    });
    
    if (res.ok) {
        showToast('✅ Đã lưu cấu hình học tập!');
        init();
    }
}

window.loadStats = async function() {
    try {
        let res = await apiFetch(`/stats/dashboard`);
        let data = await res.json();
        document.getElementById('totalCards').innerText = data.progress.total;
        document.getElementById('countEN').innerText = data.counts.en;
        document.getElementById('countZH').innerText = data.counts.zh;
        document.getElementById('countTRI').innerText = data.counts.trilingual;
        document.getElementById('userStats').innerText = `${data.progress.total} thẻ`;
        
        let modeText = data.settings.learning_language === 'trilingual' ? '3 Ngôn ngữ' : (data.settings.learning_language === 'zh' ? 'Tiếng Trung' : 'Tiếng Anh');
        let profession = data.settings.profession || 'Tổng quát';
        
        document.getElementById('activeGoalDisplay').innerText = modeText;
        document.getElementById('aiStatusDisplay').innerText = `💼 Ngành: ${profession}`;
    } catch(e){}
}

window.showTab = function(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.add('active');
    const navLink = document.querySelector(`.nav-link[data-tab="${tabId}"]`);
    if (navLink) navLink.classList.add('active');
    if (tabId === 'study') loadStudyCards();
    if (tabId === 'manage') renderManageCards();
    if (tabId === 'exercises') loadExercises();
};

function setupTabs() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.onclick = (e) => {
            showTab(link.dataset.tab);
        };
    });
}

window.loadStudyCards = async function() {
    try {
        let res = await apiFetch(`/words/today`);
        if (!res.ok) throw new Error("Error");
        let data = await res.json();
        dueCards = data.words || [];
        
        if (dueCards.length === 0) {
            document.getElementById('studyContent').innerHTML = `
                <div class="ai-box" style="text-align: center; padding: 2rem;">
                    <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">🎉 Hiện không có thẻ nào khớp với mục tiêu học của bạn. <br>Hãy tạo thẻ mới hoặc đổi lại <strong>Cấu hình</strong>!</p>
                    <button class="btn btn-primary" onclick="showTab('create')">➕ Tạo thẻ mới</button>
                </div>
            `;
            return;
        }
        currentCardIndex = 0;
        showStudyCard();
    } catch(e){
        document.getElementById('studyContent').innerHTML = `<div class="ai-box">Không có thẻ nào hôm nay.</div>`;
    }
}

function showStudyCard() {
    if (currentCardIndex >= dueCards.length) {
        loadStudyCards();
        return;
    }
    let card = dueCards[currentCardIndex];
    let langCode = card.language || 'en';
    let flag = langCode === 'zh' ? '🇨🇳' : '🇬🇧';
    let audioText = langCode === 'zh' ? '🔊 Nghe tiếng Trung' : '🔊 Nghe tiếng Anh';
    let imgKeyword = card.word_en || card.word;
    let wordClean = imgKeyword ? imgKeyword.trim().toLowerCase().replace(/[^\\w\\s]/gi, '') : "object";
    let prof = document.getElementById('settingProfession').value || 'general';
    let seed = Math.floor(Math.random() * 1000);
    let imgUrl = `https://image.pollinations.ai/prompt/professional%20clean%203D%20render%20of%20${encodeURIComponent(wordClean)}%20related%20to%20${encodeURIComponent(prof)},%20modern%20style,%20white%20background?width=400&height=400&seed=${seed}`;

    let html = `
        <div class="flashcard-container">
            <div class="flashcard" id="studyFlashcard" style="height: 520px;">
                <div class="flashcard-inner">
                    <div class="flashcard-front">
                        <img src="${imgUrl}" class="flashcard-image" alt="Visual" onerror="this.onerror=null; this.src='https://img.icons8.com/color/200/${wordClean}.png';">
                        <div class="card-text" style="color: #000; font-weight: bold; font-size: 1.5rem;">
                            ${card.word_en && card.word_zh ? `<span>🇬🇧 ${card.word_en}</span><br><span>🇨🇳 ${card.word_zh}</span>` : `${flag} ${card.word}`}
                        </div>
                        <div style="font-size: 1rem; color: #333; margin-bottom: 5px;">${card.pinyin || card.pronunciation}</div>
                        <div style="font-size: 1rem; color: #555; font-style: italic; margin-bottom: 15px; padding: 0 10px;">
                            "${card.example || ""}"
                            <span style="cursor: pointer;" onclick="speakText('${langCode}', '${escapeJS(card.example)}')">🔊</span>
                        </div>
                        <button class="audio-btn" onclick="speakText('${langCode}', '${escapeJS(card.word)}')">${audioText}</button>
                        <div class="rating-buttons">
                            <button class="rating-btn hard" onclick="rateCard(0)">😫 Khó</button>
                            <button class="rating-btn medium" onclick="rateCard(1)">😊 Tạm</button>
                            <button class="rating-btn easy" onclick="rateCard(2)">🎉 Dễ</button>
                        </div>
                    </div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 1rem;">${currentCardIndex + 1} / ${dueCards.length}</div>
        </div>
    `;
    document.getElementById('studyContent').innerHTML = html;
}

async function rateCard(mastery) {
    let card = dueCards[currentCardIndex];
    let isCorrect = mastery > 0;
    try {
        await apiFetch(`/words/learn?vocab_id=${card.id}&is_correct=${isCorrect}`, {
            method: 'POST'
        });
        currentCardIndex++;
        showStudyCard();
        loadStats();
    } catch(e){}
}

window.createManualCard = async function() {
    let word = document.getElementById('newQuestion').value;
    let meaning = document.getElementById('newAnswer').value;
    if (!word || !meaning) {
        showToast('Vui lòng nhập đủ từ và nghĩa');
        return;
    }
    try {
        let res = await apiFetch('/words', {
            method: 'POST',
            body: JSON.stringify({ word: word, meaning: meaning })
        });
        if (res.ok) {
            showToast('✅ Đã tạo thẻ thành công!');
            document.getElementById('newQuestion').value = '';
            document.getElementById('newAnswer').value = '';
            document.getElementById('newTopic').value = '';
            loadStats();
        } else {
            showToast('Lỗi khi tạo thẻ');
        }
    } catch(e) {
        showToast('Không kết nối được server');
    }
}

window.deleteCurrentCard = async function() {
    if (currentCardIndex >= dueCards.length) return;
    let card = dueCards[currentCardIndex];
    if (!confirm('Xoá thẻ này?')) return;
    try {
        let res = await apiFetch(`/words/${card.id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('✅ Đã xoá');
            dueCards.splice(currentCardIndex, 1);
            showStudyCard();
            loadStats();
        }
    } catch(e) {}
}

window.generateAICard = async function() {
    let word = document.getElementById('aiWord').value;
    if (!word) { showToast('Nhập từ!'); return; }
    showLoading();
    try {
        let lang = document.getElementById('settingLang').value;
        let res = await apiFetch('/words/batch-ai', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ words: [word], language: lang })
        });
        if (res.ok) {
            showToast('✅ Đã tạo thẻ!');
            loadStats();
            showTab('study');
        }
    } catch(e){}
    hideLoading();
}

window.generateBatchCards = async function() {
    let text = document.getElementById('batchWords').value;
    let words = text.split(/[\\n,]+/).map(w => w.trim()).filter(w => w);
    if (words.length === 0) return;
    document.getElementById('batchProgress').innerHTML = '⏳ Đang tạo hàng loạt...';
    let lang = document.getElementById('settingLang').value;
    for (let word of words) {
        try {
            await apiFetch('/words/batch-ai', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ words: [word], language: lang }),
                timeout: 60000
            });
        } catch(e){}
    }
    showToast('✅ Đã tạo xong!');
    loadStats();
    showTab('manage');
}

window.renderManageCards = async function() {
    try {
        let res = await apiFetch('/words/today'); 
        let data = await res.json();
        let cards = data.words || [];
        let searchTerm = document.getElementById('manageSearch').value.toLowerCase();
        let container = document.getElementById('manageCardsContainer');
        container.innerHTML = '';
        let filtered = cards.filter(c => c.word.toLowerCase().includes(searchTerm) || (c.word_en && c.word_en.toLowerCase().includes(searchTerm)));
        filtered.forEach(c => {
            let cardDiv = document.createElement('div');
            cardDiv.className = 'ai-box';
            cardDiv.style.position = 'relative';
            let badgeClass = `badge badge-${c.mode || 'en'}`;
            let modeText = c.mode === 'trilingual' ? '3 Ngôn ngữ' : (c.mode === 'zh' ? 'Tiếng Trung' : 'Tiếng Anh');
            cardDiv.innerHTML = `
                <div class="${badgeClass}">${modeText}</div>
                <div style="font-weight: 700; color: #1e293b; margin-bottom: 5px;">${c.word_en ? '🇬🇧 '+c.word_en : c.word}</div>
                <div style="color: #64748b; font-size: 12px; margin-bottom: 8px;">${c.word_zh ? '🇨🇳 '+c.word_zh : ''}</div>
                <div style="color: #475569; font-size: 13px;">🇻🇳 ${c.meaning}</div>
                <button onclick="deleteCardDirect(${c.id})" style="position: absolute; top: 10px; right: 10px; background: none; border: none; cursor: pointer; color: #ef4444; font-size: 1.1rem;">🗑️</button>
            `;
            container.appendChild(cardDiv);
        });
    } catch(e) {}
}

window.deleteCardDirect = async function(id) {
    if (!confirm('Xoá thẻ này?')) return;
    try {
        let res = await apiFetch(`/words/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('✅ Đã xoá');
            renderManageCards();
            loadStats();
        }
    } catch(e) {}
}

window.deleteAllCards = async function() {
    if (!confirm('Xoá TẤT CẢ thẻ?')) return;
    try {
        let res = await apiFetch('/words/all', { method: 'DELETE' });
        if (res.ok) {
            showToast('✅ Đã xoá sạch');
            renderManageCards();
            loadStats();
        }
    } catch(e) {}
}

window.sendChat = async function() {
    let input = document.getElementById('chatInput');
    let question = input.value;
    if (!question) return;
    let messagesDiv = document.getElementById('chatMessages');
    messagesDiv.innerHTML += `<div class="message user"><strong>Bạn:</strong> ${question}</div>`;
    input.value = '';
    let res = await apiFetch('/ai/chat', { method: 'POST', body: JSON.stringify({ prompt: question }) });
    let data = await res.json();
    messagesDiv.innerHTML += `<div class="message ai"><strong>🤖 AI:</strong> ${data.response}</div>`;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

window.speakText = function(lang, text) {
    let utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === 'zh' ? 'zh-CN' : 'en-US';
    window.speechSynthesis.speak(utterance);
}

function showToast(msg) {
    let toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

window.showLoading = function() { document.getElementById('loadingOverlay').style.display = 'flex'; }
window.hideLoading = function() { document.getElementById('loadingOverlay').style.display = 'none'; }

document.addEventListener('DOMContentLoaded', init);

window.loadExercises = async function() {
    try {
        let res = await apiFetch('/exercises/fill-blank');
        let questions = await res.json();
        let container = document.getElementById('exercisesContainer');
        container.innerHTML = '';
        
        if (questions.length === 0) {
            container.innerHTML = '<p style="text-align:center; padding:20px;">Bạn chưa có từ vựng nào có câu ví dụ để làm bài tập!</p>';
            return;
        }
        
        questions.forEach(q => {
            let div = document.createElement('div');
            div.className = 'exercise-card';
            div.style.background = '#f8fafc';
            div.style.padding = '15px';
            div.style.borderRadius = '12px';
            div.style.marginBottom = '15px';
            
            let text = q.cloze_text.replace('_____', `<input type="text" id="ex-in-${q.vocab_id}" style="border:none; border-bottom: 2px solid #6366f1; width: 100px; text-align: center; outline: none; background: transparent;">`);
            
            div.innerHTML = `
                <div style="font-size: 1.1rem; margin-bottom: 10px;">${text}</div>
                <div style="color: #64748b; font-size: 0.9rem; margin-bottom: 10px;">🇻🇳 ${q.example_vi}</div>
                <button class="btn btn-primary btn-sm" onclick="checkExercise(${q.vocab_id})">Kiểm tra</button>
                <div id="ex-res-${q.vocab_id}" style="margin-top: 10px; font-weight: bold;"></div>
            `;
            container.appendChild(div);
        });
    } catch(e) {}
}

window.checkExercise = async function(vocab_id) {
    let input = document.getElementById(`ex-in-${vocab_id}`);
    let answer = input.value.trim();
    if (!answer) return;
    
    try {
        let res = await apiFetch('/exercises/fill-blank/submit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ vocab_id: vocab_id, answer: answer })
        });
        let data = await res.json();
        let resDiv = document.getElementById(`ex-res-${vocab_id}`);
        if (data.correct) {
            resDiv.innerHTML = '✅ Chính xác!';
            resDiv.style.color = '#16a34a';
            input.style.borderColor = '#16a34a';
        } else {
            resDiv.innerHTML = `❌ Sai rồi! Đáp án: ${data.correct_answer}`;
            resDiv.style.color = '#dc2626';
            input.style.borderColor = '#dc2626';
        }
        loadStats();
    } catch(e) {}
}
