let currentArchives = [];
let translatedArchives = {}; // index -> translated record dict
let translatedListItems = null; // array of translated items {index, ending_title, ending_narrative}
let currentDetailIndex = null; // tracks which archive index is currently open in detail view (null if list view)
let isTranslatingList = false;
let isTranslatingDetail = false;

window.currentLang = localStorage.getItem('game_lang') || 'zh';

const TRANSLATIONS = {
    zh: {
        'back-to-home': '<< 返回',
        'archive-header-title': '檔案館',
        'archive-header-sub': '雨夜紀錄',
        'lang-toggle-btn': 'English',
        'loading-text': '紀錄讀取中...',
        'no-records-text': '未找到任何紀錄。',
        'error-text': '載入紀錄失敗。',
        'back-to-archives': '<< 返回檔案清單',
        'unnamed-ending': '【未命名結局】',
        'recorded-on': '紀錄於 ',
        'turn-label': '第 ',
        'turn-suffix': ' 回合',
        'player-prefix': '>> 玩家: ',
        'speaker-boy': '主角: 「',
        'speaker-boy-suffix': '」',
        'narrator-prefix': '旁白: ',
        'ending-reached-label': '[ 達成結局 ]',
        'retrospective-label': '主角的回顧：',
        'retrospective-default': '在那場雨中，我什麼也沒留下。',
        'unknown-memory': '一段未知的回憶...',
        'translating-text': '翻譯中...'
    },
    en: {
        'back-to-home': '<< RETURN',
        'archive-header-title': 'THE ARCHIVES',
        'archive-header-sub': 'RECORDS OF THE RAIN',
        'lang-toggle-btn': '中文',
        'loading-text': 'LOADING RECORDS...',
        'no-records-text': 'NO RECORDS FOUND.',
        'error-text': 'ERROR LOADING RECORDS.',
        'back-to-archives': '<< BACK TO ARCHIVES',
        'unnamed-ending': '[Unnamed Ending]',
        'recorded-on': 'RECORDED ON ',
        'turn-label': 'Turn ',
        'turn-suffix': '',
        'player-prefix': '>> Player: ',
        'speaker-boy': 'The Boy: "',
        'speaker-boy-suffix': '"',
        'narrator-prefix': 'Narrator: ',
        'ending-reached-label': '[ ENDING REACHED ]',
        'retrospective-label': "The Boy's Retrospective:",
        'retrospective-default': 'In that rain, I left nothing behind.',
        'unknown-memory': 'An unknown memory...',
        'translating-text': 'Translating...'
    }
};

function applyLangFont(lang) {
    const headerTitle = document.getElementById('archive-header-title');
    const headerSub = document.getElementById('archive-header-sub');
    const langBtn = document.getElementById('lang-toggle-btn');
    const backBtn = document.getElementById('back-to-home');
    const detailTitle = document.getElementById('detail-title');
    const detailSubtitle = document.getElementById('detail-subtitle');
    const detailBackBtns = document.querySelectorAll('.detail-back-btn');

    if (lang === 'en') {
        document.body.style.fontFamily = "'Crimson Pro', 'EB Garamond', 'Noto Sans TC', serif";
        if (headerTitle) headerTitle.style.fontFamily = "'Special Elite', 'Courier New', monospace";
        if (langBtn) langBtn.style.fontFamily = "'Special Elite', 'Courier New', monospace";
        if (backBtn) backBtn.style.fontFamily = "'Special Elite', 'Courier New', monospace";
        if (detailTitle) detailTitle.style.fontFamily = "'Special Elite', 'Courier New', monospace";
        detailBackBtns.forEach(btn => btn.style.fontFamily = "'Special Elite', 'Courier New', monospace");
    } else {
        document.body.style.fontFamily = "";
        if (headerTitle) headerTitle.style.fontFamily = "";
        if (langBtn) langBtn.style.fontFamily = "";
        if (backBtn) backBtn.style.fontFamily = "";
        if (detailTitle) detailTitle.style.fontFamily = "";
        detailBackBtns.forEach(btn => btn.style.fontFamily = "");
    }
}

function applyUIStaticTranslations() {
    const lang = window.currentLang;
    const t = TRANSLATIONS[lang];
    
    document.documentElement.lang = lang === 'en' ? 'en' : 'zh-TW';
    
    const backBtn = document.getElementById('back-to-home');
    if (backBtn) backBtn.textContent = t['back-to-home'];
    
    const langBtn = document.getElementById('lang-toggle-btn');
    if (langBtn) langBtn.textContent = t['lang-toggle-btn'];
    
    const headerTitle = document.getElementById('archive-header-title');
    if (headerTitle) headerTitle.textContent = t['archive-header-title'];
    
    const headerSub = document.getElementById('archive-header-sub');
    if (headerSub) headerSub.textContent = t['archive-header-sub'];
    
    const detailBackBtns = document.querySelectorAll('.detail-back-btn');
    detailBackBtns.forEach(btn => btn.textContent = t['back-to-archives']);
    
    applyLangFont(lang);
}

async function translateListIfNeeded() {
    if (window.currentLang === 'zh') return;
    if (translatedListItems) return; // already translated
    if (isTranslatingList) return;
    
    isTranslatingList = true;
    try {
        const itemsToTranslate = currentArchives.map((record, index) => ({
            index: index,
            ending_title: record.ending_title || '【未命名結局】',
            ending_narrative: record.ending_narrative || ''
        }));
        
        const response = await fetch('/api/translate_archive_list', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: itemsToTranslate, target_lang: 'en' })
        });
        const result = await response.json();
        translatedListItems = result.items;
    } catch (error) {
        console.error("Error translating archive list:", error);
    } finally {
        isTranslatingList = false;
    }
}

async function translateDetailIfNeeded(index) {
    if (window.currentLang === 'zh') return currentArchives[index];
    if (translatedArchives[index]) return translatedArchives[index]; // already translated
    
    isTranslatingDetail = true;
    renderLoadingDetail();
    
    try {
        const response = await fetch('/api/translate_archive_detail', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ record: currentArchives[index], target_lang: 'en' })
        });
        const translatedRecord = await response.json();
        translatedArchives[index] = translatedRecord;
        return translatedRecord;
    } catch (error) {
        console.error("Error translating archive detail:", error);
        return currentArchives[index];
    } finally {
        isTranslatingDetail = false;
    }
}

function renderLoadingDetail() {
    const detailBody = document.getElementById('detail-body');
    const t = TRANSLATIONS[window.currentLang];
    if (detailBody) {
        detailBody.innerHTML = `
            <div style="text-align:center; color:#666; margin-top:50px; letter-spacing:3px; font-style:italic;">
                ${t['translating-text']}
            </div>
        `;
    }
}

function renderArchiveList() {
    const listContainer = document.getElementById('archive-list');
    if (!listContainer) return;
    
    const lang = window.currentLang;
    const t = TRANSLATIONS[lang];
    
    if (!currentArchives || currentArchives.length === 0) {
        listContainer.innerHTML = `<div style="text-align:center; color:#666; margin-top:100px; letter-spacing:3px;">${t['no-records-text']}</div>`;
        return;
    }
    
    listContainer.innerHTML = '';
    
    currentArchives.forEach((record, index) => {
        const dateLocale = lang === 'en' ? 'en-US' : 'zh-TW';
        const dateStr = new Date(record.timestamp).toLocaleString(dateLocale, {
            year: 'numeric', month: '2-digit', day: '2-digit'
        });
        
        let title = record.ending_title || t['unnamed-ending'];
        let rawNarrative = record.ending_narrative || '';
        
        if (lang === 'en' && translatedListItems) {
            const trItem = translatedListItems.find(item => item.index === index);
            if (trItem) {
                title = trItem.ending_title || t['unnamed-ending'];
                rawNarrative = trItem.ending_narrative || '';
            }
        }
        
        const summary = rawNarrative ? rawNarrative.substring(0, 60) + '...' : t['unknown-memory'];
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'archive-item';
        itemDiv.onclick = () => openDetail(index);
        
        itemDiv.innerHTML = `
            <div class="archive-thumb-wrap">
                <img src="${record.final_image_url || ''}" class="archive-thumb" alt="Ending">
            </div>
            <div class="archive-info">
                <div class="archive-title">${title}</div>
                <div class="archive-meta">${t['recorded-on']}${dateStr}</div>
                <div class="archive-summary">${summary}</div>
            </div>
        `;
        listContainer.appendChild(itemDiv);
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    applyUIStaticTranslations();
    
    const listContainer = document.getElementById('archive-list');
    const t = TRANSLATIONS[window.currentLang];
    
    try {
        const response = await fetch('/api/archives');
        currentArchives = await response.json();
        
        if (window.currentLang === 'en') {
            listContainer.innerHTML = `
                <div style="text-align:center; color:#666; margin-top:100px; letter-spacing:3px; font-style:italic;">
                    ${t['translating-text']}
                </div>
            `;
            await translateListIfNeeded();
        }
        
        renderArchiveList();
    } catch (error) {
        console.error("Error fetching archives:", error);
        if (listContainer) {
            listContainer.innerHTML = `<div style="text-align:center; color:#ff4444; margin-top:100px; letter-spacing:3px;">${t['error-text']}</div>`;
        }
    }
});

async function openDetail(index) {
    currentDetailIndex = index;
    const listContainer = document.getElementById('archive-list');
    const detailView = document.getElementById('detail-view');
    const detailTitle = document.getElementById('detail-title');
    const detailSubtitle = document.getElementById('detail-subtitle');
    const t = TRANSLATIONS[window.currentLang];
    
    listContainer.style.display = 'none';
    document.querySelector('.header').style.display = 'none';
    
    detailTitle.textContent = t['translating-text'];
    detailSubtitle.textContent = '';
    renderLoadingDetail();
    detailView.style.display = 'block';
    
    const record = await translateDetailIfNeeded(index);
    
    detailTitle.textContent = record.ending_title || t['unnamed-ending'];
    
    const dateLocale = window.currentLang === 'en' ? 'en-US' : 'zh-TW';
    const dateStr = new Date(record.timestamp).toLocaleString(dateLocale);
    detailSubtitle.textContent = `${t['recorded-on']}${dateStr}`;
    
    let html = '';
    
    if (record.history && record.history.length > 0) {
        record.history.forEach(turn => {
            const fear = turn.fear_level !== undefined ? turn.fear_level : 'N/A';
            const cd = (turn.text_metadata && turn.text_metadata.cooldown !== undefined) ? turn.text_metadata.cooldown : 'N/A';
            const stage = (turn.text_metadata && turn.text_metadata.puzzle_stage !== undefined) ? turn.text_metadata.puzzle_stage : 'N/A';
            
            html += `
            <div class="report-card">
                <div class="turn-header">${t['turn-label']}${turn.turn}${t['turn-suffix']}</div>
                <div class="player-msg">${t['player-prefix']}${turn.user_suggestion || '...'}</div>
                ${turn.dialogue ? `<div class="ai-dialogue">${t['speaker-boy']}${turn.dialogue}${t['speaker-boy-suffix']}</div>` : ''}
                ${turn.narration ? `<div class="ai-narration">${t['narrator-prefix']}${turn.narration}</div>` : ''}
                <div class="meta-info">
                    🧩 Puzzle Stage: ${stage} | ⏳ Cooldown: ${cd} | 😨 Fear: ${fear}
                </div>
                ${turn.image_url ? `<div><img src="${turn.image_url}" class="game-image"></div>` : ''}
            </div>
            `;
        });
    }
    
    html += `
    <div class="report-card ending-card">
        <div class="turn-header" style="color: #ffaa44;">${t['ending-reached-label']}</div>
        <div class="ai-narration" style="color: #ddd;">${record.ending_narrative || ''}</div>
        <div class="retro-text">
            <strong>${t['retrospective-label']}</strong><br>
            ${record.ending_retrospective || t['retrospective-default']}
        </div>
        ${record.final_image_url ? `<div><img src="${record.final_image_url}" class="game-image" style="border-color:#ff4444;"></div>` : ''}
    </div>
    `;
    
    document.getElementById('detail-body').innerHTML = html;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function closeDetail() {
    currentDetailIndex = null;
    document.getElementById('detail-view').style.display = 'none';
    document.querySelector('.header').style.display = 'block';
    document.getElementById('archive-list').style.display = 'flex';
    
    renderArchiveList();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function toggleLanguage() {
    const newLang = window.currentLang === 'zh' ? 'en' : 'zh';
    window.currentLang = newLang;
    localStorage.setItem('game_lang', newLang);
    
    applyUIStaticTranslations();
    
    if (currentDetailIndex !== null) {
        await openDetail(currentDetailIndex);
    } else {
        if (newLang === 'en' && !translatedListItems) {
            const listContainer = document.getElementById('archive-list');
            if (listContainer) {
                listContainer.innerHTML = `
                    <div style="text-align:center; color:#666; margin-top:100px; letter-spacing:3px; font-style:italic;">
                        ${TRANSLATIONS['en']['translating-text']}
                    </div>
                `;
            }
            await translateListIfNeeded();
        }
        renderArchiveList();
    }
}
