let currentFear = 75;
let currentTrust = 30;
let inventory = [];
let flags = {};
let isWaiting = false;
let introStep = 0;

const fearBar = document.getElementById('fear-bar');
const trustBar = document.getElementById('trust-bar');
const npcText = document.getElementById('npc-text');
const sceneImage = document.getElementById('scene-image');
const inputField = document.getElementById('suggestion-input');
const submitBtn = document.getElementById('submit-btn');
const inventoryItemsContainer = document.getElementById('inventory-items');
const gameContainer = document.getElementById('game-container');
const usernameDisplay = document.getElementById('username-display');

const bgmPlayer = document.getElementById('bgm-player');

function updateBars() {
    fearBar.style.width = currentFear + '%';
    trustBar.style.width = currentTrust + '%';
    
    // 依據恐懼值調整畫面濾鏡與雜訊
    if (currentFear > 80) {
        sceneImage.style.filter = 'sepia(80%) grayscale(20%) contrast(250%) brightness(0.4)';
        document.getElementById('noise-overlay').style.opacity = '0.5';
    } else if (currentFear < 40) {
        sceneImage.style.filter = 'sepia(30%) grayscale(70%) contrast(120%) brightness(0.9)';
        document.getElementById('noise-overlay').style.opacity = '0.03';
    } else {
        sceneImage.style.filter = 'sepia(50%) grayscale(50%) contrast(180%) brightness(0.6)';
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

function advanceIntro() {
    introStep++;
    
    // 嘗試播法音樂 (瀏覽器限制：需在點擊後觸發)
    if (bgmPlayer && bgmPlayer.paused) {
        bgmPlayer.play().catch(e => console.log("Audio waiting for stronger interaction:", e));
    }

    if (introStep === 1) {
        // 第一幕：訊號建立 (顯示器視角)
        sceneImage.style.opacity = '0.2';
        setTimeout(() => {
            sceneImage.src = 'assets/intro_tv_v8.png';
            sceneImage.style.opacity = '1';
            usernameDisplay.textContent = "OBSERVATION LOG";
            typeWriterEffect("", "[ 嗡鳴聲 ] 螢幕點亮的瞬間，我看見了地底下的噩夢。光影在地窖牆面上扭曲，我看見了他。");
        }, 500);
    } 
    else if (introStep === 2) {
        // 第二幕：連結 (少年特寫)
        sceneImage.style.opacity = '0.2';
        setTimeout(() => {
            sceneImage.src = 'assets/intro_boy_v8.png';
            sceneImage.style.opacity = '1';
            usernameDisplay.textContent = "SYNC ESTABLISHED";
            typeWriterEffect("", "他還活著，但靈魂被困在深淵。這台機器是我唯一的介入點... 我該如何喚醒這個靈魂？");
            submitBtn.textContent = "啟動核心";
        }, 500);
    }
    else if (introStep === 3) {
        triggerSignalSync();
    }
}

function triggerSignalSync() {
    isWaiting = true;
    submitBtn.disabled = true;
    
    // 建立系統日誌滾屏效果
    npcText.innerHTML = '<span class="desc" style="color: #00ff00; font-family: monospace;">> EXECUTING CORE_SYNC_v12.3...<br>> CALCULATING NEURAL DYNAMIC...<br>> BYPASSING FIREWALL... DONE.<br>> ESTABLISHING VOICE CHANNEL...</span>';

    const syncLabel = document.createElement('div');
    syncLabel.className = 'sync-label';
    syncLabel.textContent = '[ BOOTING / 系統啟動 ]';
    gameContainer.appendChild(syncLabel);
    
    sceneImage.classList.add('syncing-zoom', 'glitch-flash');
    
    setTimeout(() => {
        syncLabel.remove();
        sceneImage.classList.remove('syncing-zoom', 'glitch-flash');
        gameContainer.classList.remove('intro-mode');
        submitBtn.textContent = "傳達";
        submitBtn.disabled = false;
        isWaiting = false;
        
        usernameDisplay.textContent = "連線已建立";
        sendSuggestion(""); // 第一回合：觸發 main.py 的 "......"
    }, 2500);
}


async function sendSuggestion(forcedSuggestion = null) {
    if (isWaiting && forcedSuggestion === null) return;
    
    const suggestion = forcedSuggestion !== null ? forcedSuggestion : inputField.value.trim();
    if (suggestion === "" && forcedSuggestion === null) return;
    
    if (forcedSuggestion === null) {
        inputField.value = '';
    }

    isWaiting = true;
    submitBtn.disabled = true;
    
    // --- 動態等待訊息邏輯 ---
    const loadingMessagePool = {
        search: [
            "[ 正在對環境進行掃描... ]",
            "[ 少年走向房間陰暗角落... ]",
            "[ 這邊找不到，換另一邊看看... ]",
            "[ 撥開廢墟，揚起一堆灰塵... ]",
            "[ 似乎在霉味中聞到了什麼... ]"
        ],
        dig: [
            "[ 正在持續施加壓力... ]",
            "[ 指尖嵌入牆縫，碎石掉落... ]",
            "[ 指甲有些斷裂，但他沒有停下... ]",
            "[ 牆壁底座傳來空心的回音... ]",
            "[ 汗水滴落在冰冷的水泥地上... ]"
        ],
        general: [
            "[ 正在解碼量子意識訊號... ]",
            "[ 少年正在過濾指令... ]",
            "[ 神經元路徑同步中... ]",
            "[ 影像引擎正在構建深淵圖景... ]",
            "[ 終端機負載過高，螢幕閃爍中... ]"
        ]
    };

    // 根據指令選擇分類
    let category = "general";
    const lowerSuggestion = suggestion.toLowerCase();
    if (["找", "看", "查", "find", "look", "search", "探索"].some(k => lowerSuggestion.includes(k))) category = "search";
    if (["挖", "摳", "壁", "牆", "dig", "wall"].some(k => lowerSuggestion.includes(k))) category = "dig";

    let messageIndex = 0;
    const currentMessages = loadingMessagePool[category];
    
    // 立即顯示第一條
    npcText.innerHTML = `<span class="desc" style="color: #666; font-family: monospace;">> DECODING SIGNAL...<br>${currentMessages[0]}</span>`;

    const waitingInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % currentMessages.length;
        npcText.innerHTML = `<span class="desc" style="color: #666; font-family: monospace;">> DECODING SIGNAL...<br>${currentMessages[messageIndex]}</span>`;
    }, 3000);
    // -----------------------

    sceneImage.style.opacity = '0.4';
    
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
        clearInterval(waitingInterval);
        
        currentFear = data.new_fear;
        currentTrust = data.new_trust;
        if (data.new_inventory) inventory = data.new_inventory;
        if (data.new_flags) flags = data.new_flags;
        
        updateBars();
        updateInventoryUI();
        
        if (data.image_b64) {
            sceneImage.src = "data:image/jpeg;base64," + data.image_b64;
        } else if (data.image_url) {
            sceneImage.src = data.image_url;
        }
        sceneImage.style.opacity = '1';
        
        // 切換為少年名稱
        usernameDisplay.textContent = "少年";
        typeWriterEffect(data.response_text, data.response_desc);
        
    } catch (e) {
        clearInterval(waitingInterval);
        npcText.innerHTML = "系統離線，訊號遺失...";
        console.error(e);
    }
    
    isWaiting = false;
    submitBtn.disabled = false;
    if (gameContainer.classList.contains('intro-mode') === false) {
        inputField.focus();
    }
}

function typeWriterEffect(text, desc) {
    npcText.innerHTML = '';
    let i = 0;
    
    // 如果沒有主標題文字，隱藏使用者標籤以創造純描述感
    if (text === "") {
        usernameDisplay.style.display = 'none';
    } else {
        usernameDisplay.style.display = 'block';
    }
    
    function typeMain() {
        if (i < text.length) {
            npcText.innerHTML += text.charAt(i);
            i++;
            setTimeout(typeMain, 25);
        } else if (desc) {
            // 主要文字打完後，開始打描述文字
            const descSpan = document.createElement('span');
            descSpan.className = 'desc';
            if (text !== "") npcText.appendChild(document.createElement('br')); // 如果有主文字才換行
            npcText.appendChild(descSpan);
            
            let j = 0;
            function typeDesc() {
                if (j < desc.length) {
                    descSpan.innerHTML += desc.charAt(j);
                    j++;
                    setTimeout(typeDesc, 18); // 描述文字打快一點
                }
            }
            typeDesc();
        }
    }
    typeMain();
}

submitBtn.addEventListener('click', () => {
    if (gameContainer.classList.contains('intro-mode')) {
        advanceIntro();
    } else {
        sendSuggestion();
    }
});

inputField.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !gameContainer.classList.contains('intro-mode')) {
        sendSuggestion();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    updateBars();
    updateInventoryUI();
    
    // 初始化 Act 0：發現老舊對白
    submitBtn.textContent = "NEXT";
    sceneImage.src = 'assets/intro_radio_v8.png';
    typeWriterEffect("", "我在廢墟的桌底下發現了它。它還在跳動，帶著某種不屬於這時代的訊號。");
});
