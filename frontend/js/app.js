let userId = 1;
let dueCards = [];
let currentCardIndex = 0;

// Khởi tạo
async function init() {
    await loadStats();
    setupTabs();
    await loadStudyCards();
}

function setupTabs() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.onclick = (e) => {
            let tab = link.dataset.tab;
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            if (tab === 'study') loadStudyCards();
        };
    });
}

async function loadStats() {
    let res = await fetch(`http://localhost:8000/api/users/${userId}/cards`);
    let cards = await res.json();
    document.getElementById('totalCards').innerText = cards.length;
    document.getElementById('userStats').innerText = `${cards.length} thẻ`;
    
    let dueRes = await fetch(`http://localhost:8000/api/users/${userId}/due-cards`);
    let dueCardsData = await dueRes.json();
    document.getElementById('dueCards').innerText = dueCardsData.length;
}

async function loadStudyCards() {
    let res = await fetch(`http://localhost:8000/api/users/${userId}/due-cards`);
    dueCards = await res.json();
    
    if (dueCards.length === 0) {
        document.getElementById('studyContent').innerHTML = '<div class="ai-box"><p>🎉 Chúc mừng! Hôm nay bạn đã học hết thẻ rồi!</p><button class="btn btn-primary" onclick="switchTab(\'ai\')">Tạo thêm thẻ mới</button></div>';
        return;
    }
    
    currentCardIndex = 0;
    showStudyCard();
}

function showStudyCard() {
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
                        <div class="card-text">🇬🇧 ${card.question}</div>
                        <button class="audio-btn" onclick="speakText('en', '${card.question.replace(/'/g, "\\'")}')">🔊 Nghe tiếng Anh</button>
                        <div style="margin-top: 20px; font-size: 12px;">👆 Chạm để xem đáp án</div>
                    </div>
                    <div class="flashcard-back">
                        <div class="card-text">🇻🇳 ${card.answer}</div>
                        <button class="audio-btn" onclick="speakText('vi', '${card.answer.replace(/'/g, "\\'")}')">🔊 Nghe tiếng Việt</button>
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
}

async function rateCard(quality) {
    let card = dueCards[currentCardIndex];
    
    await fetch('http://localhost:8000/api/study-sessions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            card_id: card.id,
            user_id: userId,
            quality: quality
        })
    });
    
    currentCardIndex++;
    if (currentCardIndex < dueCards.length) {
        showStudyCard();
    } else {
        showToast('🎉 Hoàn thành! Ngày mai quay lại nhé!');
        loadStudyCards();
    }
    loadStats();
}

window.createManualCard = async function() {
    let question = document.getElementById('newQuestion').value;
    let answer = document.getElementById('newAnswer').value;
    let topic = document.getElementById('newTopic').value;
    
    if (!question || !answer) {
        showToast('Vui lòng nhập đầy đủ câu hỏi và câu trả lời!');
        return;
    }
    
    let res = await fetch('http://localhost:8000/api/cards', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id: userId,
            question: question,
            answer: answer,
            topic: topic
        })
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
    
    showToast('🤖 AI đang sinh thẻ...');
    
    let res = await fetch(`http://localhost:8000/api/ai/generate-card?word=${encodeURIComponent(word)}`, {
        method: 'POST'
    });
    let data = await res.json();
    
    let html = `
        <div style="background:#e8f5e9; padding:1rem; border-radius:12px; margin:1rem 0;">
            <strong>🇬🇧 Câu hỏi:</strong> ${data.card.question}<br>
            <button class="audio-btn" onclick="speakText('en', '${data.card.question.replace(/'/g, "\\'")}')">🔊 Nghe</button>
        </div>
        <div style="background:#e3f2fd; padding:1rem; border-radius:12px; margin:1rem 0;">
            <strong>🇻🇳 Câu trả lời:</strong> ${data.card.answer}<br>
            <button class="audio-btn" onclick="speakText('vi', '${data.card.answer.replace(/'/g, "\\'")}')">🔊 Nghe</button>
        </div>
        ${data.card.examples_en ? `
        <div style="background:#fff3e0; padding:1rem; border-radius:12px;">
            <strong>📚 Ví dụ:</strong><br>
            🇬🇧 ${data.card.examples_en.join('<br>🇬🇧 ')}<br><br>
            🇻🇳 ${data.card.examples_vi.join('<br>🇻🇳 ')}
        </div>
        ` : ''}
        <button class="btn btn-primary" style="margin-top:1rem;" onclick="saveAICard('${data.card.question.replace(/'/g, "\\'")}', '${data.card.answer.replace(/'/g, "\\'")}')">
            💾 Lưu thẻ vào thư viện
        </button>
    `;
    document.getElementById('aiPreview').innerHTML = html;
};

window.saveAICard = async function(question, answer) {
    let res = await fetch('http://localhost:8000/api/cards', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id: userId,
            question: question,
            answer: answer,
            topic: 'AI Generated'
        })
    });
    
    if (res.ok) {
        showToast('✅ Đã lưu thẻ!');
        document.getElementById('aiWord').value = '';
        document.getElementById('aiPreview').innerHTML = '';
        loadStats();
    } else {
        showToast('❌ Lỗi lưu thẻ!');
    }
};

window.speakText = function(lang, text) {
    let utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === 'en' ? 'en-US' : 'vi-VN';
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
    
    for (let i = 0; i < words.length; i++) {
        let word = words[i];
        let percent = ((i + 1) / words.length) * 100;
        document.getElementById('progressFill').style.width = `${percent}%`;
        
        try {
            // Gọi AI sinh thẻ cho từng từ
            let aiRes = await fetch(`http://localhost:8000/api/ai/generate-card?word=${encodeURIComponent(word)}`, {
                method: 'POST'
            });
            let data = await aiRes.json();
            
            if (data && data.card) {
                // Lưu thẻ vào database
                let saveRes = await fetch('http://localhost:8000/api/cards', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user_id: userId,
                        question: data.card.question,
                        answer: data.card.answer,
                        topic: 'Batch Generated'
                    })
                });
                
                if (saveRes.ok) {
                    successCount++;
                    results.push(`✅ <strong>${word}</strong> - ${data.card.answer}`);
                } else {
                    failCount++;
                    results.push(`❌ <strong>${word}</strong> - Lỗi lưu`);
                }
            } else {
                failCount++;
                results.push(`❌ <strong>${word}</strong> - Lỗi sinh thẻ`);
            }
        } catch (error) {
            failCount++;
            results.push(`❌ <strong>${word}</strong> - ${error.message}`);
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
        
        // Delay 0.5s để tránh quá tải
        await new Promise(resolve => setTimeout(resolve, 500));
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
