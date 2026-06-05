let currentArchives = [];

document.addEventListener('DOMContentLoaded', async () => {
    const listContainer = document.getElementById('archive-list');
    
    try {
        const response = await fetch('/api/archives');
        currentArchives = await response.json();
        
        if (!currentArchives || currentArchives.length === 0) {
            listContainer.innerHTML = '<div style="text-align:center; color:#666; margin-top:100px; letter-spacing:3px;">NO RECORDS FOUND.</div>';
            return;
        }

        listContainer.innerHTML = '';
        
        currentArchives.forEach((record, index) => {
            const dateStr = new Date(record.timestamp).toLocaleString('zh-TW', {
                year: 'numeric', month: '2-digit', day: '2-digit'
            });

            const itemDiv = document.createElement('div');
            itemDiv.className = 'archive-item';
            itemDiv.onclick = () => openDetail(index);

            // 簡短摘要 (取前 60 字)
            const summary = record.ending_narrative ? record.ending_narrative.substring(0, 60) + '...' : '一段未知的回憶...';

            itemDiv.innerHTML = `
                <div class="archive-thumb-wrap">
                    <img src="${record.final_image_url || ''}" class="archive-thumb" alt="Ending">
                </div>
                <div class="archive-info">
                    <div class="archive-title">${record.ending_title || '【未命名結局】'}</div>
                    <div class="archive-meta">RECORDED ON ${dateStr}</div>
                    <div class="archive-summary">${summary}</div>
                </div>
            `;

            listContainer.appendChild(itemDiv);
        });

    } catch (error) {
        console.error("Error fetching archives:", error);
        listContainer.innerHTML = '<div style="text-align:center; color:#ff4444; margin-top:100px; letter-spacing:3px;">ERROR LOADING RECORDS.</div>';
    }
});

function openDetail(index) {
    const record = currentArchives[index];
    const listContainer = document.getElementById('archive-list');
    const detailView = document.getElementById('detail-view');
    const detailBody = document.getElementById('detail-body');
    const detailTitle = document.getElementById('detail-title');
    const detailSubtitle = document.getElementById('detail-subtitle');

    // 隱藏清單，顯示詳細視圖
    listContainer.style.display = 'none';
    document.querySelector('.header').style.display = 'none'; // 隱藏主頁標題
    
    // 設定標題
    detailTitle.textContent = record.ending_title || '【未命名結局】';
    const dateStr = new Date(record.timestamp).toLocaleString('zh-TW');
    detailSubtitle.textContent = `RECORDED ON ${dateStr}`;

    let html = '';

    // 遍歷歷史紀錄生成卡片
    if (record.history && record.history.length > 0) {
        record.history.forEach(turn => {
            const fear = turn.fear_level || 'N/A';
            // 從 text_metadata 取出資訊，如果沒有則給預設值
            const cd = (turn.text_metadata && turn.text_metadata.cooldown !== undefined) ? turn.text_metadata.cooldown : 'N/A';
            const stage = (turn.text_metadata && turn.text_metadata.puzzle_stage !== undefined) ? turn.text_metadata.puzzle_stage : 'N/A';
            
            html += `
            <div class="report-card">
                <div class="turn-header">Turn ${turn.turn}</div>
                <div class="player-msg">>> 玩家: ${turn.user_suggestion || '...'}</div>
                ${turn.dialogue ? `<div class="ai-dialogue">主角: 「${turn.dialogue}」</div>` : ''}
                ${turn.narration ? `<div class="ai-narration">旁白: ${turn.narration}</div>` : ''}
                <div class="meta-info">
                    🧩 Puzzle Stage: ${stage} | ⏳ Cooldown: ${cd} | 😨 Fear: ${fear}
                </div>
                ${turn.image_url ? `<div><img src="${turn.image_url}" class="game-image"></div>` : ''}
            </div>
            `;
        });
    }

    // 生成結局專屬卡片
    html += `
    <div class="report-card ending-card">
        <div class="turn-header" style="color: #ffaa44;">[ ENDING REACHED ]</div>
        <div class="ai-narration" style="color: #ddd;">${record.ending_narrative || ''}</div>
        <div class="retro-text">
            <strong>主角的回顧：</strong><br>
            ${record.ending_retrospective || '在那場雨中，我什麼也沒留下。'}
        </div>
        ${record.final_image_url ? `<div><img src="${record.final_image_url}" class="game-image" style="border-color:#ff4444;"></div>` : ''}
    </div>
    `;

    detailBody.innerHTML = html;
    
    detailView.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function closeDetail() {
    document.getElementById('detail-view').style.display = 'none';
    document.querySelector('.header').style.display = 'block';
    document.getElementById('archive-list').style.display = 'flex';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
