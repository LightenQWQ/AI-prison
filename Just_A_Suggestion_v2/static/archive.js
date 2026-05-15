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
    const modal = document.getElementById('modal-overlay');
    const body = document.getElementById('modal-body');

    // 格式化對話歷史
    let historyHtml = '';
    if (record.history && record.history.length > 0) {
        record.history.forEach(turn => {
            historyHtml += `
                <div class="modal-turn">
                    <div class="modal-turn-user">>> ${turn.user_suggestion || '...'}</div>
                    ${turn.dialogue ? `<div class="modal-turn-dialogue">「${turn.dialogue}」</div>` : ''}
                    ${turn.narration ? `<div class="modal-turn-narrative">${turn.narration}</div>` : ''}
                </div>
            `;
        });
    }

    body.innerHTML = `
        <img src="${record.final_image_url || ''}" class="modal-img" alt="Final Shot">
        <h2 class="modal-title">${record.ending_title || '【未命名結局】'}</h2>
        <p class="modal-narrative">${record.ending_narrative || ''}</p>
        
        <div class="modal-retro-title">Protagonist's Inner Perspective</div>
        <div class="modal-retro">${record.ending_retrospective || '在那場雨中，我什麼也沒留下。'}</div>

        <div class="modal-history-title">THE FULL STORY ARC</div>
        <div class="modal-history-list">
            ${historyHtml}
        </div>
    `;

    modal.style.display = 'flex';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 10);
    document.body.style.overflow = 'hidden';
}

function closeDetail(event) {
    const modal = document.getElementById('modal-overlay');
    modal.style.opacity = '0';
    setTimeout(() => {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }, 400);
}
