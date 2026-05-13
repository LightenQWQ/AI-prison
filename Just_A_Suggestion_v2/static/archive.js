document.addEventListener('DOMContentLoaded', async () => {
    const listContainer = document.getElementById('archive-list');
    
    try {
        const response = await fetch('/api/archives');
        const archives = await response.json();
        
        if (!archives || archives.length === 0) {
            listContainer.innerHTML = '<div style="text-align:center; color:#666; margin-top:100px; letter-spacing:3px;">NO RECORDS FOUND.</div>';
            return;
        }

        listContainer.innerHTML = '';
        
        archives.forEach((record, index) => {
            const dateStr = new Date(record.timestamp).toLocaleString('zh-TW', {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute:'2-digit'
            });

            const itemDiv = document.createElement('div');
            itemDiv.className = 'archive-item';

            // 組合圖片
            let imgHtml = '';
            if (record.final_image_url) {
                imgHtml = `<img src="${record.final_image_url}" class="archive-img" alt="Ending Image">`;
            }

            // 組合回顧文字
            let retroHtml = '';
            if (record.ending_retrospective) {
                retroHtml = `<div class="archive-retro">${record.ending_retrospective}</div>`;
            }

            // 組合歷史對話
            let historyHtml = '<div class="history-content" id="hist-' + index + '">';
            if (record.history && record.history.length > 0) {
                record.history.forEach(turn => {
                    historyHtml += `
                        <div class="history-turn">
                            <div class="hist-user">${turn.user_suggestion || '...'}</div>
                            ${turn.dialogue ? `<div class="hist-dialogue">${turn.dialogue}</div>` : ''}
                            ${turn.narration ? `<div class="hist-narrative">${turn.narration}</div>` : ''}
                        </div>
                    `;
                });
            } else {
                historyHtml += '<div style="color:#666; text-align:center;">No history recorded.</div>';
            }
            historyHtml += '</div>';

            itemDiv.innerHTML = `
                ${imgHtml}
                <div class="archive-title">${record.ending_title || '【結局】'}</div>
                <div class="archive-date">${dateStr}</div>
                <div class="archive-narrative">${record.ending_narrative || ''}</div>
                ${retroHtml}
                <button class="history-toggle" onclick="toggleHistory(${index})">[ VIEW FULL STORY ]</button>
                ${historyHtml}
            `;

            listContainer.appendChild(itemDiv);
        });

    } catch (error) {
        console.error("Error fetching archives:", error);
        listContainer.innerHTML = '<div style="text-align:center; color:#ff4444; margin-top:100px; letter-spacing:3px;">ERROR LOADING RECORDS.</div>';
    }
});

function toggleHistory(index) {
    const histDiv = document.getElementById('hist-' + index);
    if (histDiv.style.display === 'block') {
        histDiv.style.display = 'none';
    } else {
        histDiv.style.display = 'block';
    }
}
