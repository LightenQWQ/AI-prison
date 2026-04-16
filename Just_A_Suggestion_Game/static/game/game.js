let currentFear = 75;
let currentTrust = 30;
let inventory = [];
let flags = {};
let isWaiting = false;

const fearBar = document.getElementById('fear-bar');
const trustBar = document.getElementById('trust-bar');
const npcText = document.getElementById('npc-text');
const sceneImage = document.getElementById('scene-image');
const inputField = document.getElementById('suggestion-input');
const submitBtn = document.getElementById('submit-btn');
const inventoryItemsContainer = document.getElementById('inventory-items');

function updateBars() {
    fearBar.style.width = currentFear + '%';
    trustBar.style.width = currentTrust + '%';
    
    // Fear effect on screen (visual feedback of psychological state)
    if (currentFear > 80) {
        sceneImage.style.filter = 'grayscale(100%) contrast(220%) brightness(0.5)';
        document.getElementById('noise-overlay').style.opacity = '0.4';
    } else if (currentFear < 40) {
        sceneImage.style.filter = 'grayscale(100%) contrast(140%) brightness(0.9)';
        document.getElementById('noise-overlay').style.opacity = '0.05';
    } else {
        sceneImage.style.filter = 'grayscale(100%) contrast(180%) brightness(0.6)';
        document.getElementById('noise-overlay').style.opacity = '0.15';
    }
}

function updateInventoryUI() {
    inventoryItemsContainer.innerHTML = '';
    if (inventory.length === 0) {
        inventoryItemsContainer.innerHTML = '<span class="empty-inventory">無</span>';
        return;
    }
    
    inventory.forEach(item => {
        const itemSpan = document.createElement('span');
        itemSpan.className = 'inventory-item';
        itemSpan.textContent = item;
        inventoryItemsContainer.appendChild(itemSpan);
    });
}

async function sendSuggestion() {
    if (isWaiting) return;
    
    const suggestion = inputField.value.trim();
    if (!suggestion) return;
    
    // User feedback while waiting
    inputField.value = '';
    npcText.innerHTML = `<span class="desc">（正在推敲你的語氣與建議...）</span>`;
    isWaiting = true;
    submitBtn.disabled = true;

    // 降低透明度表示思考中
    sceneImage.style.opacity = '0.3';
    
    try {
        const response = await fetch('/api/game/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                suggestion: suggestion,
                current_fear: currentFear,
                current_trust: currentTrust,
                inventory: inventory,
                flags: flags
            })
        });
        
        const data = await response.json();
        
        // Update variables
        currentFear = data.new_fear;
        currentTrust = data.new_trust;
        
        if (data.new_inventory) inventory = data.new_inventory;
        if (data.new_flags) flags = data.new_flags;
        
        updateBars();
        updateInventoryUI();
        
        // 接收並顯示 Base64 格式的圖片或是後端提供的預設 fallback 圖片
        if (data.image_b64) {
            sceneImage.src = "data:image/jpeg;base64," + data.image_b64;
        } else if (data.image_url) {
            sceneImage.src = data.image_url;
        } else {
            sceneImage.src = "intro_panel.png";
        }
        sceneImage.style.opacity = '1';

        // Typewriter effect for dialogue
        typeWriterEffect(data.response_text, data.response_desc);
        
    } catch (e) {
        npcText.innerHTML = "系統離線，靈魂連接中斷...";
        console.error(e);
    }
    
    isWaiting = false;
    submitBtn.disabled = false;
    inputField.focus();
}

function typeWriterEffect(text, desc) {
    npcText.innerHTML = '';
    let i = 0;
    function type() {
        if (i < text.length) {
            npcText.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, 30); // text pace
        } else {
            if (desc) {
                npcText.innerHTML += `<br><span class="desc">${desc}</span>`;
            }
        }
    }
    type();
}

submitBtn.addEventListener('click', sendSuggestion);
inputField.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendSuggestion();
});

// Initial logic
document.addEventListener('DOMContentLoaded', () => {
    updateBars();
    updateInventoryUI();
    inputField.focus();
});
