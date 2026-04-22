let gameState = {
    trust: 30,
    fear: 50,
    inventory: [],
    flags: {},
    history: [],
    turn: 0,
    is_over: false,
    ending: "",
    last_monologues: []
};

// 音訊與波紋引擎
let waveEngine = null;
let soundManager = null;

class WaveformEngine {
    constructor() {
        this.ecgCanvas = document.getElementById('ecg-canvas');
        this.eegCanvas = document.getElementById('eeg-canvas');
        this.ecgCtx = this.ecgCanvas.getContext('2d');
        this.eegCtx = this.eegCanvas.getContext('2d');
        
        this.width = this.ecgCanvas.offsetWidth;
        this.height = this.ecgCanvas.offsetHeight;
        this.ecgCanvas.width = this.width;
        this.ecgCanvas.height = this.height;
        this.eegCanvas.width = this.width;
        this.eegCanvas.height = this.height;

        this.ecgPath = new Array(this.width).fill(this.height / 2);
        this.eegPath = new Array(this.width).fill(this.height / 2);
        this.offset = 0;
        
        this.render();
    }

    render() {
        if (gameState.is_over) return;
        
        this.updatePhysiology();
        this.drawWave(this.ecgCtx, this.ecgPath, '#8b0000', 2);
        this.drawWave(this.eegCtx, this.eegPath, '#40e0d0', 1.5);
        
        requestAnimationFrame(() => this.render());
    }

    updatePhysiology() {
        this.offset++;
        
        // ECG (Heart) Logic: R-wave peaks based on fear
        const bpm = 60 + (gameState.fear * 1.2);
        const interval = (60 / bpm) * 60; // frames
        let val = this.height / 2;
        if (this.offset % Math.floor(interval) === 0) {
            val -= 20; // Pulse peak
            // 已移除嗶音，保持安靜
        } else if (this.offset % Math.floor(interval) === 5) {
            val += 10;
        }
        
        this.ecgPath.shift();
        this.ecgPath.push(val + (Math.random() * 2 - 1));
        
        // EEG (Brain) Logic
        const chaos = 10 - (gameState.trust / 15);
        const eegVal = (this.height / 2) + (Math.sin(this.offset * 0.2) * 5) + (Math.random() * chaos);
        this.eegPath.shift();
        this.eegPath.push(eegVal);
        
        document.getElementById('hr-value').innerText = Math.floor(bpm);
        document.getElementById('sync-value').innerText = Math.floor(gameState.trust);
    }

    drawWave(ctx, path, color, width) {
        ctx.clearRect(0, 0, this.width, this.height);
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.lineJoin = 'round';
        
        for (let i = 0; i < path.length; i++) {
            ctx.lineTo(i, path[i]);
        }
        ctx.stroke();
    }
}

class SoundManager {
    constructor() {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        this.bgm = new Audio();
        this.bgm.loop = true;
        this.bgmVolume = 0.3;
        this.bgm.volume = this.bgmVolume;
        
        this.tracks = {
            intro: "https://assets.mixkit.co/music/preview/mixkit-ethereal-dreams-442.mp3",
            game: "https://assets.mixkit.co/music/preview/mixkit-horror-ambient-94.mp3",
            ending_good: "https://assets.mixkit.co/music/preview/mixkit-sad-piano-reflections-564.mp3",
            ending_bad: "https://assets.mixkit.co/music/preview/mixkit-suspense-horror-piano-557.mp3"
        };
    }

    playBGM(type) {
        if (this.tracks[type]) {
            this.bgm.src = this.tracks[type];
            this.bgm.play().catch(e => console.log("Audio play blocked", e));
        }
    }

    playBeep() {
        // 合成心跳嗶音 - 音量調低如用戶所求
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        
        osc.type = 'sine';
        osc.frequency.setValueAtTime(1000 + (gameState.fear * 2), this.audioCtx.currentTime);
        
        gain.gain.setValueAtTime(0.05, this.audioCtx.currentTime); // 基礎音量極低
        gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.1);
        
        osc.connect(gain);
        gain.connect(this.audioCtx.destination);
        
        osc.start();
        osc.stop(this.audioCtx.currentTime + 0.1);
    }

    playGlitch() {
        const bufferSize = this.audioCtx.sampleRate * 0.2;
        const buffer = this.audioCtx.createBuffer(1, bufferSize, this.audioCtx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) { data[i] = Math.random() * 2 - 1; }
        
        const noise = this.audioCtx.createBufferSource();
        noise.buffer = buffer;
        const filter = this.audioCtx.createBiquadFilter();
        filter.type = 'highpass';
        filter.frequency.value = 2000;
        
        const gain = this.audioCtx.createGain();
        gain.gain.setValueAtTime(0.1, this.audioCtx.currentTime);
        gain.gain.linearRampToValueAtTime(0, this.audioCtx.currentTime + 0.2);
        
        noise.connect(filter);
        filter.connect(gain);
        gain.connect(this.audioCtx.destination);
        noise.start();
    }
}

const dreamSequence = [
    "額頭好痛..... 像是被重物擊中過。",
    "為什麼我在這裡？腦子裡空蕩蕩的... 什麼也想不起來。",
    "但我感覺得到... 他在那裡。在那個螢幕後面。",
    "我只記得一件事..... 我必須看著他。"
];

const introSequence = [
    { text: "....", desc: "訊號同步中：連線成功。", img: "assets/intro_start.png" },
    { text: "....", desc: "畫面啟動：一個少年縮在神祕解謎空間的角落，陷入深沉的睡眠。", img: "assets/intro_start.png" },
    { text: "....", desc: "監視器運轉聲中，他的氣息平穩。試著發出訊號，引導他的潛意識。", img: "assets/intro_start.png" }
];

let introIndex = 0;
let isSkippingPrologue = false;

async function startGame() {
    isSkippingPrologue = false;
    // 初始化聲音與引擎
    soundManager = new SoundManager();
    waveEngine = new WaveformEngine();
    
    // 1. 隱藏主遮罩
    document.getElementById('overlay').classList.add('fading');
    document.getElementById('monitor-osd-bar').style.display = 'flex';
    setTimeout(() => {
        document.getElementById('overlay').style.display = 'none';
        soundManager.playBGM('intro');
    }, 1000);

    // 2. 播放夢境序章
    await playDreamSequence();

    if (isSkippingPrologue) {
        // 極速模式：直接跳過所有過場特效，顯示最後一幕的文字與圖片
        soundManager.playBGM('game');
        document.getElementById('scene-image').style.display = 'block';
        document.getElementById('scene-image').style.opacity = '1';
        const lastIntro = introSequence[introSequence.length - 1];
        updateUI({
            response_text: lastIntro.text,
            response_desc: lastIntro.desc,
            image_url: lastIntro.img
        });
        return; // 結束啟動流程，直接可遊玩
    }

    // 3. 監視器啟動故障 (Glitch)
    triggerBootGlitch();
    soundManager.playGlitch();

    // 4. 開始正式介紹
    soundManager.playBGM('game');
    showNextIntro();
}

async function playDreamSequence() {
    const overlay = document.getElementById('prologue-overlay');
    overlay.style.display = 'flex';
    
    for (let text of dreamSequence) {
        if (isSkippingPrologue) break;
        const p = document.createElement('p');
        p.className = 'dream-text';
        p.innerText = text;
        overlay.innerHTML = '<div id="skip-btn" onclick="skipPrologue()">SKIP >></div>';
        overlay.appendChild(p);
        
        // 分段等待，以便在 4 秒內隨時可以被跳過中斷
        for(let i=0; i<40; i++) {
            if (isSkippingPrologue) break;
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
    
    if (!isSkippingPrologue) {
        overlay.style.transition = 'opacity 0.5s';
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
            overlay.style.opacity = '1';
        }, 500);
    }
}

function skipPrologue() {
    isSkippingPrologue = true;
    const overlay = document.getElementById('prologue-overlay');
    // 瞬間消失，不播動畫
    overlay.style.display = 'none';
}

function triggerBootGlitch() {
    const container = document.getElementById('game-container');
    container.classList.add('power-on-glitch');
    setTimeout(() => {
        container.classList.remove('power-on-glitch');
        container.style.opacity = '1';
    }, 1000);
}

function showNextIntro() {
    if (introIndex < introSequence.length) {
        const item = introSequence[introIndex];
        document.getElementById('scene-image').style.display = 'block';
        document.getElementById('scene-image').style.opacity = '0';
        setTimeout(() => { document.getElementById('scene-image').style.opacity = '1'; }, 100);

        updateUI({
            response_text: item.text,
            response_desc: item.desc,
            image_url: item.img || ""
        });
        introIndex++;
    }
}

function updateUI(data) {
    document.getElementById('scene-image').style.opacity = "1";
    if (data.response_text) document.getElementById('text-content').innerText = data.response_text;
    if (data.response_desc) document.getElementById('desc-content').innerText = data.response_desc;
    
    if (data.image_b64) {
        console.log("Received new image, length:", data.image_b64.length);
        const sceneImg = document.getElementById('scene-image');
        sceneImg.style.opacity = "0"; // 先隱藏
        setTimeout(() => {
            sceneImg.src = "data:image/png;base64," + data.image_b64; // 改為 PNG
            sceneImg.style.opacity = "1"; // 再顯現
        }, 300);
    } else if (data.image_url) {
        document.getElementById('scene-image').src = data.image_url;
    }

    if (data.new_state) {
        // 檢查地點是否改變，觸發雜訊轉場
        if (data.new_state.location !== gameState.location) {
            triggerCameraGlitch(data.new_state.location);
        }
        gameState = data.new_state;
        updateLocationDisplay(gameState.location);
    }

    if (data.memory_fragment) {
        showMemoryFragment(data.memory_fragment);
    }
}

function updateLocationDisplay(loc) {
    const el = document.getElementById('location-display');
    if (!el) return;
    const channels = { "puzzle_room": "01", "hallway": "02", "storage": "03", "locked_room": "04" };
    const ch = channels[loc] || "XX";
    el.innerText = `CCTV CH-${ch} | ${loc.replace('_', ' ')}`;
}

// 呼吸感點點循環引擎 (V15.5)
let globalDotCount = 1;
setInterval(() => {
    const textEl = document.getElementById('text-content');
    if (!textEl) return;
    
    // 只有當內容全是點點時（代表少年沈睡或思考中），才觸發循環
    if (/^\.*$/.test(textEl.innerText)) {
        globalDotCount = (globalDotCount % 5) + 1;
        textEl.innerText = ".".repeat(globalDotCount);
    }
}, 600);

function triggerCameraGlitch(newLoc) {
    const sceneImg = document.getElementById('scene-image');
    const noise = document.getElementById('noise-layer');
    
    // 播放斷訊音效
    playGlitchSFX();
    
    // 強烈隨機雜訊
    noise.style.opacity = "0.8";
    sceneImg.style.filter = "contrast(200%) brightness(150%) hue-rotate(90deg)";
    
    setTimeout(() => {
        noise.style.opacity = "0.05";
        sceneImg.style.filter = "none";
    }, 500);
}

function playGlitchSFX() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const bufferSize = audioCtx.sampleRate * 0.4;
        const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        const gain = audioCtx.createGain();
        gain.gain.setValueAtTime(0.03, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
        source.connect(gain);
        gain.connect(audioCtx.destination);
        source.start();
    } catch(e) { console.error("Audio error", e); }
}

function showMemoryFragment(text) {
    const el = document.getElementById('memory-fragment');
    el.innerText = text;
    el.classList.remove('fragment-glitch');
    void el.offsetWidth;
    el.classList.add('fragment-glitch');
}

// 預設開場獨白 (主角的思緒碎片)
const DEFAULT_MONOLOGUES = [
    "誰在那裡.....",
    "不要靠近我.....",
    "這台機器為什麼在動.....",
    "是我在看著他嗎？還是他在看著我.....",
    "這冷氣好重，壓得我喘不過氣.....",
    "救救我..... 不，我是來救他的..... 應該是這樣。"
];

async function sendSuggestion() {
    const input = document.getElementById('suggestion-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('scene-image').style.opacity = "0.5";
    
    // 1. 獨白重定向至中央敘事框
    const textContent = document.getElementById('text-content');
    textContent.classList.add('monologue-style'); // 加上斜體發光樣式
    
    let monologuePool = gameState.last_monologues && gameState.last_monologues.length > 0 
                     ? gameState.last_monologues 
                     : DEFAULT_MONOLOGUES;
    let monologueIdx = 0;
    let dotCount = 1;
    
    const rotateMonologue = () => {
        const rawText = monologuePool[monologueIdx % monologuePool.length];
        const dots = ".".repeat(dotCount);
        textContent.innerText = rawText + dots;
        
        dotCount++;
        if (dotCount > 5) {
            dotCount = 1;
            monologueIdx++;
        }
    };
    
    rotateMonologue();
    const monologueInterval = setInterval(rotateMonologue, 600); // 600ms * 5 dots = 3 seconds per cycle

    try {
        const response = await fetch('/api/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ suggestion: text, state: gameState })
        });
        const data = await response.json();
        
        clearInterval(monologueInterval);
        textContent.classList.remove('monologue-style'); // 恢復正常樣式
        
        if (data.error) {
            alert("Error: " + data.error);
        } else {
            // 更新狀態與最後收到的獨白池
            gameState.last_monologues = data.monologues || DEFAULT_MONOLOGUES;
            updateUI(data);
            
            if (data.new_state.is_over) {
                soundManager.playBGM(data.new_state.suspicion >= 80 ? 'ending_bad' : 'ending_good');
                setTimeout(() => {
                    alert("遊戲結束: " + data.new_state.ending);
                    location.reload();
                }, 5000);
            }
        }
    } catch (e) {
        console.error(e);
        clearInterval(monologueInterval);
        textContent.classList.remove('monologue-style');
    } finally {
        document.getElementById('submit-btn').disabled = false;
        input.focus();
    }
}

document.getElementById('suggestion-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendSuggestion();
});

document.getElementById('suggestion-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendSuggestion();
});

updateBars();
