let token = localStorage.getItem("token");
let currentUser = null;
let dueCards = [];
let currentCardIndex = 0;

// Khởi tạo

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
        window.currentQuestionsCount = questions.length;
        window.solvedQuestionsCount = 0;
        let html = '';
        questions.forEach(q => {
            let text = q.cloze_text.replace('_____', `<input type="text" class="exercise-input" id="ex-${q.vocab_id}" onkeypress="if(event.key === 'Enter') checkExercise(${q.vocab_id})">`);
            html += `
                <div class="exercise-card" id="ex-card-${q.vocab_id}">
                    <div class="exercise-text">${text}</div>
                    <div class="exercise-vi">${q.example_vi}</div>
                    <button class="btn btn-primary" onclick="checkExercise(${q.vocab_id})">Kiểm tra</button>
                    <div id="ex-res-${q.vocab_id}" class="exercise-result"></div>
                </div>
            `;
        });
        if(questions.length === 0) html = '<div style="text-align:center; padding:2rem;">Bạn chưa có từ vựng nào để làm bài tập!</div>';
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
            if (!resDiv.classList.contains('correct')) {
                window.solvedQuestionsCount++;
            }
            resDiv.innerHTML = '✅ Chính xác! Giỏi lắm bé ơi! 🌟';
            resDiv.className = 'exercise-result correct';
            
            // Nếu đã làm xong hết
            if (window.solvedQuestionsCount >= window.currentQuestionsCount) {
                // Phát nhạc thiếu nhi
                const audio = new Audio('https://www.fesliyanstudios.com/play-mp3/4383');
                audio.volume = 0.5;
                audio.play();
                
                showToast('🎊 CHÚC MỪNG BÉ ĐÃ HOÀN THÀNH TẤT CẢ BÀI TẬP! 🎊');
                confetti({
                    particleCount: 200,
                    spread: 120,
                    origin: { y: 0.6 }
                });
            }
        } else {
            resDiv.innerHTML = `❌ Sai rồi! Đáp án đúng: <strong>${data.correct_answer}</strong>`;
            resDiv.className = 'exercise-result incorrect';
        }
    } catch (e) {
        console.log(e);
    }
}

async function init() {
    if (!token) {
        document.getElementById("loginOverlay").classList.add("active");
        return;
    } else {
        document.getElementById("loginOverlay").classList.remove("active");
    }

    await loadStats();
    setupTabs();
    await loadStudyCards();
}

window.showTab = function(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    
    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.add('active');
    
    const navLink = document.querySelector(`.nav-link[data-tab="${tabId}"]`);
    if (navLink) navLink.classList.add('active');

    if (tabId === 'study') loadStudyCards();
    if (tabId === 'exercises') loadExercises();
};

function setupTabs() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.onclick = (e) => {
            showTab(link.dataset.tab);
        };
    });
}

async function loadStats() {
    try {
        let res = await apiFetch(`/stats/dashboard`);
        let data = await res.json();
        document.getElementById('totalCards').innerText = data.progress.total;
        document.getElementById('userStats').innerText = `${data.progress.total} thẻ`;
        document.getElementById('dueCards').innerText = data.today_review_words;
        document.getElementById('streak').innerText = data.streak;
    } catch(e){}
}


async function loadStudyCards() {
    try {
        let res = await apiFetch(`/words/today`);
        let data = await res.json();
        dueCards = data.words || [];
        
        if (dueCards.length === 0) {
            document.getElementById('studyContent').innerHTML = '<div class="ai-box"><p>🎉 Chúc mừng! Hôm nay bạn đã học hết thẻ rồi!</p><button class="btn btn-primary" onclick="switchTab(\'ai\')">Tạo thêm thẻ mới</button></div>';
            return;
        }
        
        currentCardIndex = 0;
        showStudyCard();
    } catch(e){}
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
    
    // Sử dụng Pollinations AI với prompt dành riêng cho trẻ em để đảm bảo ảnh đúng nội dung và kute
    let wordClean = card.word.trim().toLowerCase().replace(/[^\w\s]/gi, '');
    let seed = Math.floor(Math.random() * 1000);
    let imgUrl = `https://image.pollinations.ai/prompt/cute%20cartoon%20illustration%20of%20a%20${encodeURIComponent(wordClean)}%20for%20kids,%20sticker%20style,%20white%20background?width=400&height=400&nologo=true&seed=${seed}`;

    let html = `
        <div class="flashcard-container">
            <div class="flashcard" id="studyFlashcard" style="height: 520px;">
                <div class="flashcard-inner">
                    <div class="flashcard-front">
                        <img src="${imgUrl}" class="flashcard-image" alt="Kid-friendly illustration" 
                             onerror="this.onerror=null; this.src='https://img.icons8.com/color/200/${wordClean}.png';">
                        <div class="card-text" style="color: #000; font-weight: bold; font-size: 1.5rem;">${flag} ${card.word}</div>
                        <div style="font-size: 1rem; color: #333; margin-bottom: 5px;">${card.pronunciation}</div>
                        <div style="font-size: 1rem; color: #555; font-style: italic; margin-bottom: 15px; padding: 0 10px; display: flex; align-items: center; justify-content: center; gap: 8px;">
                            "${card.example}"
                            <span style="cursor: pointer; font-size: 1.2rem;" onclick="speakText('${langCode}', '${card.example.replace(/'/g, "\\'")}')">🔊</span>
                        </div>
                        <button class="audio-btn" style="background: #f3f4f6; color: #4b5563;" onclick="speakText('${langCode}', '${card.word.replace(/'/g, "\\'")}')">${audioText}</button>
                        
                        <div class="mcq-container">
                            ${card.options && card.options.length > 0 ? card.options.map(opt => `
                                <button class="mcq-btn" onclick="checkAnswer(this, '${opt.replace(/'/g, "\\'")}', '${card.primary_meaning.replace(/'/g, "\\'")}')">${opt}</button>
                            `).join('') : '<div style="margin-top: 20px; font-size: 12px; grid-column: span 2;">👆 Chạm vào thẻ để lật</div>'}
                        </div>
                    </div>
                    <div class="flashcard-back">
                        <div class="card-text" style="color: #000; font-weight: bold;">🇻🇳 ${card.meaning}</div>
                        <div style="font-size: 1rem; color: #333; font-style: italic; margin-top: 10px; display: flex; align-items: center; justify-content: center; gap: 8px;">
                            "${card.example}"
                            <span style="cursor: pointer; font-size: 1.2rem;" onclick="speakText('${langCode}', '${card.example.replace(/'/g, "\\'")}')">🔊</span>
                        </div>
                        <div style="font-size: 1rem; color: #666; margin-bottom: 15px;">${card.example_vi}</div>
                        <button class="audio-btn" onclick="speakText('vi', '${card.meaning.replace(/'/g, "\'")}')">🔊 Nghe tiếng Việt</button>
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
            // Cho phép lật thủ công nếu thẻ không có đáp án trắc nghiệm
            if (!card.options || card.options.length === 0) {
                if (!e.target.classList.contains('audio-btn') && !e.target.classList.contains('rating-btn') && !e.target.classList.contains('mcq-btn')) {
                    flashcard.classList.toggle('flipped');
                }
            }
        };
    }
}

window.checkAnswer = function(btn, selected, correct) {
    if (btn.classList.contains('correct') || btn.classList.contains('incorrect')) return;
    
    if (selected === correct) {
        btn.classList.add('correct');
        // Hiệu ứng tung hoa
        if (typeof confetti === 'function') {
            confetti({
                particleCount: 150,
                spread: 100,
                origin: { y: 0.6 }
            });
        }
        
        // Tặng quà ngẫu nhiên
        setTimeout(() => {
            showRandomGift();
        }, 500);
        
        // Tự động lật thẻ sau một lúc
        setTimeout(() => {
            let flashcard = document.getElementById('studyFlashcard');
            if (flashcard) flashcard.classList.add('flipped');
        }, 2000);
        
    } else {
        btn.classList.add('incorrect');
        btn.classList.add('shake');
        setTimeout(() => btn.classList.remove('shake'), 400);
    }
};

const gifts = [
    { name: "Một gói Bim Bim khổng lồ! 🍟", icon: "🍟" },
    { name: "Một cây Xúc xích nướng thơm phức! 🌭", icon: "🌭" },
    { name: "Siêu phẩm iPhone 15 Pro Max! 📱", icon: "📱" },
    { name: "Một chiếc Siêu xe Lamborghini! 🏎️", icon: "🏎️" },
    { name: "Một cây Kem ốc quế mát lạnh! 🍦", icon: "🍦" },
    { name: "Một chiếc Pizza full topping! 🍕", icon: "🍕" },
    { name: "Một cây Kẹo mút cầu vồng! 🍭", icon: "🍭" },
    { name: "Laptop Gaming cực khủng! 💻", icon: "💻" },
    { name: "Một chuyến du lịch vòng quanh thế giới! ✈️", icon: "✈️" },
    { name: "Một hũ Kim cương lấp lánh! 💎", icon: "💎" }
];

function showRandomGift() {
    const gift = gifts[Math.floor(Math.random() * gifts.length)];
    document.getElementById('giftIcon').innerText = gift.icon;
    document.getElementById('giftName').innerText = gift.name;
    document.getElementById('giftOverlay').classList.add('active');
}

window.closeGift = function() {
    document.getElementById('giftOverlay').classList.remove('active');
}

async function rateCard(quality) {
    let card = dueCards[currentCardIndex];
    let is_correct = quality > 0;
    
    await apiFetch(`/words/learn?vocab_id=${card.id}&is_correct=${is_correct}`, {
        method: 'POST'
    });
    
    currentCardIndex++;
    if (currentCardIndex < dueCards.length) {
        showStudyCard();
    } else {
        showToast('🎉 Hoàn thành! Tự động chuyển sang bài tập điền từ...');
        setTimeout(() => {
            showTab('exercises');
            loadExercises();
        }, 1500);
    }
    loadStats();
}

window.createManualCard = async function() {
    let question = document.getElementById('newQuestion').value;
    if (!question) {
        showToast('Vui lòng nhập từ tiếng Anh!');
        return;
    }
    
    let lang = document.getElementById('globalLangSelect').value;
    showToast('⏳ Đang nhờ AI dịch và tạo thẻ...');
    let res = await apiFetch('/words/batch-ai', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ words: [question], language: lang })
    });
    
    if (res.ok) {
        showToast('✅ Đã tạo thẻ thành công!');
        document.getElementById('newQuestion').value = '';
        document.getElementById('newAnswer').value = '';
        document.getElementById('newTopic').value = '';
        loadStats();
    } else {
        showToast('❌ Lỗi tạo thẻ!');
    }
};

window.generateAICard = async function() {
    let word = document.getElementById('aiWord').value;
    if (!word) {
        showToast('Nhập từ cần học!');
        return;
    }
    
    showToast('🤖 AI đang sinh và lưu thẻ...');
    document.getElementById('aiPreview').innerHTML = '⏳ Đang tạo bài tập, ví dụ và dịch nghĩa...';
    let lang = document.getElementById('globalLangSelect').value;
    
    let res = await apiFetch('/words/batch-ai', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ words: [word], language: lang })
    });
    
    if (res.ok) {
        let data = await res.json();
        let meaning = data.words[0]?.meaning || "Đã lưu";
        let flag = lang === 'zh' ? '🇨🇳' : '🇬🇧';
        let html = `
            <div style="background:#e8f5e9; padding:1rem; border-radius:12px; margin:1rem 0;">
                <strong>✅ Đã tạo và lưu thành công!</strong><br>
                ${flag} ${word}<br>
                🇻🇳 ${meaning}<br>
                <em>(AI đã tự động tạo câu ví dụ và bài tập điền từ cho thẻ này)</em>
            </div>
        `;
        document.getElementById('aiPreview').innerHTML = html;
        document.getElementById('aiWord').value = '';
        loadStats();
        showToast('✅ Đã lưu thẻ vào thư viện!');
    } else {
        document.getElementById('aiPreview').innerHTML = '';
        showToast('❌ Lỗi sinh thẻ!');
    }
};

window.speakText = function(lang, text) {
    let utterance = new SpeechSynthesisUtterance(text);
    if (lang === 'zh') {
        utterance.lang = 'zh-CN';
    } else {
        utterance.lang = lang === 'en' ? 'en-US' : 'vi-VN';
    }
    utterance.rate = 0.9;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
};

window.sendChat = async function() {
    let input = document.getElementById('chatInput');
    let question = input.value;
    if (!question) return;
    
    let messagesDiv = document.getElementById('chatMessages');
    messagesDiv.innerHTML += `<div class="message user"><strong>Bạn:</strong> ${question}</div>`;
    input.value = '';
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    messagesDiv.innerHTML += `<div class="message ai"><strong>🤖 AI:</strong> Cảm ơn bạn đã hỏi! Tôi đang học để trả lời tốt hơn. Hãy thử tạo thẻ mới với từ "${question.split(' ')[0]}" nhé!</div>`;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
};

function showToast(msg) {
    let toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

window.switchTab = function(tab) {
    document.querySelector(`.nav-link[data-tab="${tab}"]`).click();
};

init();

// Tạo nhiều thẻ cùng lúc
window.generateBatchCards = async function() {
    let textarea = document.getElementById('batchWords');
    let wordsText = textarea.value;
    
    // Tách từ (theo dòng hoặc dấu phẩy)
    let words = wordsText.split(/[,\n]+/).map(w => w.trim().toLowerCase()).filter(w => w && w.length > 0);
    words = [...new Set(words)]; // Loại bỏ trùng lặp
    
    if (words.length === 0) {
        showToast('⚠️ Vui lòng nhập ít nhất 1 từ!');
        return;
    }
    
    if (words.length > 20) {
        if (!confirm(`Bạn đang tạo ${words.length} thẻ. Quá trình này có thể mất vài phút. Tiếp tục?`)) {
            return;
        }
    }
    
    showToast(`🚀 Đang tạo ${words.length} thẻ... Vui lòng chờ!`);
    
    let progressDiv = document.getElementById('batchProgress');
    let resultDiv = document.getElementById('batchResult');
    
    progressDiv.innerHTML = `<div style="background:#e5e7eb; border-radius:10px; height:20px; overflow:hidden;"><div id="progressFill" style="width:0%; background:#10b981; height:100%; transition:width 0.3s;"></div></div>`;
    resultDiv.innerHTML = '<div style="text-align:center;">⏳ Đang xử lý...</div>';
    
    let successCount = 0;
    let failCount = 0;
    let results = [];
    
    let lang = document.getElementById('globalLangSelect').value;

    for (let i = 0; i < words.length; i++) {
        let word = words[i];
        let percent = ((i + 1) / words.length) * 100;
        document.getElementById('progressFill').style.width = `${percent}%`;
        
        try {
            // Gọi AI sinh thẻ
            let res = await apiFetch('/words/batch-ai', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ words: [word], language: lang })
            });
            
            if (res.ok) {
                let data = await res.json();
                successCount++;
                results.push(`✅ <strong>${word}</strong> - ${data.words[0]?.meaning || 'OK'}`);
            } else {
                failCount++;
                results.push(`❌ <strong>${word}</strong> - Lỗi lưu`);
            }
        } catch (error) {
            failCount++;
            results.push(`❌ <strong>${word}</strong> - Lỗi mạng`);
        }
        
        // Cập nhật kết quả tạm thời
        resultDiv.innerHTML = `
            <div style="margin-bottom:1rem; padding:1rem; background:#f0fdf4; border-radius:12px;">
                <strong>📊 Tiến độ:</strong> ${i+1}/${words.length}<br>
                ✅ Thành công: ${successCount}<br>
                ❌ Thất bại: ${failCount}
            </div>
            <div style="max-height: 300px; overflow-y: auto;">
                ${results.slice(-10).map(r => `<div style="padding:5px; margin:2px 0; background:#f9fafb; border-radius:5px;">${r}</div>`).join('')}
            </div>
        `;
    }
    
    // Kết quả cuối cùng
    resultDiv.innerHTML = `
        <div style="margin-bottom:1rem; padding:1rem; background:#f0fdf4; border-radius:12px;">
            <strong>📊 KẾT QUẢ HOÀN TẤT:</strong><br>
            ✅ Thành công: ${successCount}<br>
            ❌ Thất bại: ${failCount}<br>
            📚 Tổng số: ${words.length}
        </div>
        <div style="max-height: 400px; overflow-y: auto;">
            ${results.map(r => `<div style="padding:8px; margin:4px 0; background:#f9fafb; border-radius:8px; border-left:4px solid ${r.includes('✅') ? '#10b981' : '#ef4444'};">${r}</div>`).join('')}
        </div>
        <button class="btn btn-primary" style="margin-top:1rem;" onclick="location.reload()">🔄 Làm mới</button>
    `;
    
    showToast(`✅ Hoàn tất! Thành công: ${successCount}/${words.length} thẻ!`);
    await loadStats();
};
