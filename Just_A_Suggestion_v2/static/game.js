let gameState = {
    trust: 30,
    fear: 50,
    inventory: [],
    flags: {},
    history: [],
    turn: 0,
    is_over: false,
    ending: ""
};

const introSequence = [
    { text: "你在潮濕的冷空氣中醒來...", desc: "(你發現自己坐在一台閃爍著綠光的老舊終端機前)", img: "assets/intro_1.png" },
    { text: "螢幕上顯示著監視畫面：一個少年縮在冰冷的地下室角落。", desc: "(他看起來大約18歲，神情警覺而疲憊)", img: "assets/intro_boy_v8.png" },
    { text: "你是他唯一的『引導者』，但也許他根本不想要你的引導。", desc: "(試著跟他說點什麼，或者給他點建議)", img: "assets/intro_radio_v8.png" }
];

let introIndex = 0;

function startGame() {
    document.getElementById('overlay').classList.add('fading');
    setTimeout(() => {
        document.getElementById('overlay').style.display = 'none';
        document.getElementById('bgm').play();
        showNextIntro();
    }, 1000);
}

function showNextIntro() {
    if (introIndex < introSequence.length) {
        const item = introSequence[introIndex];
        updateUI({
            response_text: item.text,
            response_desc: item.desc,
            image_url: item.img
        });
        introIndex++;
    }
}

function updateUI(data) {
    document.getElementById('scene-image').style.opacity = "1";
    if (data.response_text) document.getElementById('text-content').innerText = data.response_text;
    if (data.response_desc) document.getElementById('desc-content').innerText = data.response_desc;
    
    if (data.image_b64) {
        document.getElementById('scene-image').src = "data:image/jpeg;base64," + data.image_b64;
    } else if (data.image_url) {
        // 為了展示方便，如果本地沒有圖片，先顯示一個預設占位符或嘗試加載
        document.getElementById('scene-image').src = data.image_url;
    }

    if (data.new_state) {
        gameState = data.new_state;
        updateBars();
        updateInventory();
    }
}

function updateBars() {
    document.getElementById('trust-bar').style.width = gameState.trust + "%";
    document.getElementById('fear-bar').style.width = gameState.fear + "%";
}

function updateInventory() {
    const list = gameState.inventory.length > 0 ? gameState.inventory.join(", ") : "無";
    document.getElementById('inventory-list').innerText = list;
}

async function sendSuggestion() {
    const input = document.getElementById('suggestion-input');
    const text = input.value.trim();
    if (!text) return;

    // 基於關鍵字獲取相關獨白
    function getRelatedMonologue(input) {
        const lowerInput = input.toLowerCase();
        if (lowerInput.includes("還好") || lowerInput.includes("沒事") || lowerInput.includes("舒服")) {
            return [
                "（他低下頭，避開了監視器的視角）",
                "「好不好... 對你有意義嗎？」",
                "他摸了摸冰冷的肩膀，眼神有些游移。"
            ];
        }
        if (lowerInput.includes("逃") || lowerInput.includes("走") || lowerInput.includes("牆") || lowerInput.includes("出口")) {
            return [
                "他屏住呼吸，聽著牆後的動靜。",
                "（他悄悄打量著那道緊閉的鋼門）",
                "「我試過了... 這裡根本沒有路。」"
            ];
        }
        if (lowerInput.includes("誰") || lowerInput.includes("名字") || lowerInput.includes("人類")) {
            return [
                "（他看著 terminal 上的文字，陷入了沈默）",
                "「你只是另一組程式碼... 對吧？」",
                "他試著回憶很久沒被叫過的那個名字。"
            ];
        }
        // 預設通用獨白
        return [
            "......他在終端機前猶豫著。",
            "（監視器傳來低沉的運作聲）",
            "「有人在那裡嗎？還是只有這台機器...」"
        ];
    }

    const currentMonologues = getRelatedMonologue(text);

    input.value = "";
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('scene-image').style.opacity = "0.5";
    
    // 等待期間：啟動動態點點點動畫
    let dotCount = 1;
    const thinkingText = "少年正在思考";
    document.getElementById('desc-content').innerText = "（他在思考你的建議...）";
    
    const dotsInterval = setInterval(() => {
        dotCount = (dotCount % 5) + 1; // 1 到 5 循環
        document.getElementById('text-content').innerText = thinkingText + ".".repeat(dotCount);
    }, 500);

    // 設置隨機獨白循環 (每 3 秒一次)
    const statusMessages = ["[SYNCING...]", "[ENCRYPTING...]", "[SIGNAL WEAK]", "[STABILIZING PATH]"];
    const monologueInterval = setInterval(() => {
        document.getElementById('desc-content').innerText = currentMonologues[Math.floor(Math.random() * currentMonologues.length)];
        document.getElementById('status-indicator').innerText = statusMessages[Math.floor(Math.random() * statusMessages.length)];
        document.getElementById('status-indicator').style.color = "#8b0000";
    }, 3000);

    try {
        const response = await fetch('/api/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ suggestion: text, state: gameState })
        });
        const data = await response.json();
        
        clearInterval(monologueInterval); // 停止獨白
        clearInterval(dotsInterval);      // 停止點點點
        document.getElementById('status-indicator').innerText = "[LINK ESTABLISHED]";
        document.getElementById('status-indicator').style.color = "#2f4f4f";
        
        if (data.error) {
            alert("Error: " + data.error);
        } else {
            updateUI(data);
            if (data.new_state.is_over) {
                setTimeout(() => {
                    alert("遊戲結束: " + data.new_state.ending);
                    location.reload();
                }, 1000);
            }
        }
    } catch (e) {
        console.error(e);
    } finally {
        document.getElementById('submit-btn').disabled = false;
        input.focus();
    }
}

// 綁定 Enter 鍵
document.getElementById('suggestion-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendSuggestion();
});

// 初始化 Bar
updateBars();
