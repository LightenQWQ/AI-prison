let gameState = {
    trust: 30,
    fear: 40,
    location: "rainy_alley",
    turn: 0,
    is_over: false,
    ending: "",
    clues_found: [],
    memories_unlocked: [],
    current_chapter: 1,
    scene_object: "",
    puzzle_stage: 1,
    inventory: [],
    flags: {},
    history: [],
    last_monologues: []
};

// 音訊與波紋引擎
let waveEngine = null;
let soundManager = null;
let rainEngine = null;

class RainEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.drops = [];
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.initDrops();
        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    initDrops() {
        this.drops = [];
        for (let i = 0; i < 150; i++) {
            this.drops.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                len: Math.random() * 20 + 10,
                speed: Math.random() * 10 + 5,
                opacity: Math.random() * 0.5
            });
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        this.ctx.lineWidth = 1;
        this.ctx.lineCap = 'round';

        this.drops.forEach(d => {
            this.ctx.beginPath();
            this.ctx.moveTo(d.x, d.y);
            this.ctx.lineTo(d.x, d.y + d.len);
            this.ctx.stroke();

            d.y += d.speed;
            if (d.y > this.canvas.height) {
                d.y = -d.len;
                d.x = Math.random() * this.canvas.width;
            }
        });
        requestAnimationFrame(() => this.animate());
    }
}

class WaveformEngine {
    constructor() {
        this.ecgCanvas = document.getElementById('ecg-canvas');
        this.eegCanvas = document.getElementById('eeg-canvas');
        if (!this.ecgCanvas || !this.eegCanvas) return;
        
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
        if (gameState.is_over || !this.ecgCtx) return;
        this.updatePhysiology();
        this.drawWave(this.ecgCtx, this.ecgPath, '#8b0000', 2);
        this.drawWave(this.eegCtx, this.eegPath, '#40e0d0', 1.5);
        requestAnimationFrame(() => this.render());
    }

    updatePhysiology() {
        this.offset++;
        const bpm = 60 + (gameState.fear * 1.2);
        const interval = (60 / bpm) * 60;
        let val = this.height / 2;
        if (this.offset % Math.floor(interval) === 0) {
            val -= 20;
        } else if (this.offset % Math.floor(interval) === 5) {
            val += 10;
        }
        this.ecgPath.shift();
        this.ecgPath.push(val + (Math.random() * 2 - 1));
        
        const chaos = 10 - (gameState.trust / 15);
        const eegVal = (this.height / 2) + (Math.sin(this.offset * 0.2) * 5) + (Math.random() * chaos);
        this.eegPath.shift();
        this.eegPath.push(eegVal);
        
        const hrEl = document.getElementById('hr-value');
        const syncEl = document.getElementById('sync-value');
        if (hrEl) hrEl.innerText = Math.floor(bpm);
        if (syncEl) syncEl.innerText = Math.floor(gameState.trust);
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
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(1000 + (gameState.fear * 2), this.audioCtx.currentTime);
        gain.gain.setValueAtTime(0.05, this.audioCtx.currentTime);
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
    "雨滴落下的聲音..... 濕冷，刺骨。",
    "我不知道在躲什麼，只知道不能停下來。",
    "這個聲音..... 是從我腦子裡冒出來的嗎？",
    "『只是一個建議』..... 它這麼說。"
];

const introSequence = [
    { text: "....", desc: "心靈防火牆滲透中。意識鏈接完成。", img: "assets/intro_start.png" },
    { text: "....", desc: "他在這座無名雨城中徘徊。這不是真實的世界，而是他為了躲避遺棄而創造的幻覺。", img: "assets/intro_start.png" },
    { text: "....", desc: "你是他殘存的直覺。試著開導他，帶他走出這場名為逃避的雨。", img: "assets/intro_start.png" }
];

let introIndex = 0;
let isSkippingPrologue = false;

// 啟動
window.onload = () => {
    rainEngine = new RainEngine('rain-canvas');
};

async function startGame() {
    isSkippingPrologue = false;
    soundManager = new SoundManager();
    waveEngine = new WaveformEngine();
    
    document.getElementById('overlay').classList.add('fading');
    document.getElementById('monitor-osd-bar').style.display = 'flex';
    setTimeout(() => {
        document.getElementById('overlay').style.display = 'none';
        soundManager.playBGM('intro');
    }, 1000);

    await playDreamSequence();

    if (isSkippingPrologue) {
        soundManager.playBGM('game');
        document.getElementById('scene-image').style.display = 'block';
        document.getElementById('scene-image').style.opacity = '1';
        const lastIntro = introSequence[introSequence.length - 1];
        updateUI({
            response_text: lastIntro.text,
            response_desc: lastIntro.desc,
            image_url: lastIntro.img
        });
        return;
    }

    triggerBootGlitch();
    soundManager.playGlitch();
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
        
        for (let i = 0; i < 40; i++) {
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
    document.getElementById('prologue-overlay').style.display = 'none';
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
            dialogue: item.text,       // ✅ 修正：使用 updateUI 讀得到的 key
            narration: item.desc,      // ✅ 修正：使用 updateUI 讀得到的 key
            image_url: item.img || ""
        });
        introIndex++;
    }
}

function updateUI(data) {
    const sceneImg = document.getElementById('scene-image');
    sceneImg.style.opacity = "1"; // 強制恢復透明度，避免卡在 0.5
    // 主角對白 → 白色對話框
    if (data.dialogue !== undefined) {
        // 若 Gemini 成功回傳但 dialogue 為空字串，顯示省略號而非「保持沉默」
        document.getElementById('text-content').innerText = data.dialogue || '......';
    }

    // 旁白區：小字灰色
    const narratorEl = document.getElementById('narrator-text');
    let narratorParts = [];
    if (data.narration) narratorParts.push(data.narration);
    if (data.scene_object) narratorParts.push(`【場景物件】${data.scene_object}`);
    narratorEl.innerText = narratorParts.join('  ｜  ');

    // 記憶碎片：展示為醒目的白色文字
    if (data.memory_fragment) {
        showMemoryFragment(data.memory_fragment);
    }

    // 線索發現：在旁白區展示
    if (data.clue_found) {
        narratorEl.innerText += `  │  🔍 線索：${data.clue_found}`;
    }

    if (data.metadata) {
        updateDebugInfo(data.metadata);
    }

    if (data.image_b64) {
        const sceneImg = document.getElementById('scene-image');
        sceneImg.style.opacity = "0";
        setTimeout(() => {
            sceneImg.src = "data:image/png;base64," + data.image_b64;
            sceneImg.style.opacity = "1";
        }, 300);
    } else if (data.image_url) {
        document.getElementById('scene-image').src = data.image_url;
    }

    if (data.new_state) {
        if (data.new_state.location !== gameState.location) {
            triggerCameraGlitch(data.new_state.location);
        }
        gameState = data.new_state;
        updateLocationDisplay(gameState.location);
    }
}

function updateLocationDisplay(loc) {
    // OSD 條已從 UI 移除，此函式不再執行 DOM 操作以避免報錯
    return;
}

// 呼吸感點點循環（只在主角靜默時作用）
let globalDotCount = 1;
setInterval(() => {
    const textEl = document.getElementById('text-content');
    if (!textEl) return;
    // 只對「純點號」字串作動畫，避免誤觸中文句點
    if (/^\.{1,6}$/.test(textEl.innerText)) {
        globalDotCount = (globalDotCount % 6) + 1;
        textEl.innerText = ".".repeat(globalDotCount);
    }
}, 600);

function triggerCameraGlitch(newLoc) {
    const sceneImg = document.getElementById('scene-image');
    const noise = document.getElementById('noise-layer');
    playGlitchSFX();
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
        for (let i = 0; i < bufferSize; i++) { data[i] = Math.random() * 2 - 1; }
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

// 預設開場獨白（主角思緒碎片）
const DEFAULT_MONOLOGUES = [
    "雨好大..... 回不去了。",
    "你是誰？為什麼在跟我說話？",
    "不要叫我做那個..... 我做不到。",
    "我看到的那些東西..... 如果是真的該怎麼辦？",
    "這座城市好安靜..... 靜得讓人害怕。",
    "救救我..... 或者是，殺了我。"
];

// 等待生圖期間的旁白池（每 5 秒輪換）
const WAITING_NARRATIONS = [
    "（他在雨中低頭，試著推開那些沉重的雜音⋯⋯）",
    "（這座城市正在微微顫抖，幻覺的邊緣開始剝落⋯⋯）",
    "（他聽見了，那是他不願回想的爭吵聲⋯⋯）",
    "（你在他的意識邊緣徘徊，試著點亮一盞燈⋯⋯）",
    "（雨滴停在半空，時間在這裡失去了意義⋯⋯）",
    "（真相就在那道門後，但他還沒有準備好⋯⋯）"
];

function toggleDebug() {
    const panel = document.getElementById('debug-panel');
    panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
}

function updateDebugInfo(metadata) {
    if (!metadata) return;
    const t = metadata.text || {};
    const v = metadata.vision || metadata; // 向後相容舊格式

    // 填入 BRAIN (Gemini) 欄位
    const brainInfo = `[BRAIN] ${t.model || 'gemini-flash-latest'} | ${t.latency || 0}s`;
    // 填入 VISION (Imagen) 欄位
    const visionModel = v.model || 'imagen-4.0-fast';
    const visionLatency = v.latency || 0;
    const finalPrompt = v.final_prompt || v.prompt || 'No prompt provided.';
    const hasError = v.error || t.error;

    document.getElementById('debug-model').innerText = `${visionModel} | ${brainInfo}`;
    document.getElementById('debug-latency').innerText = `Vision:${visionLatency}s | Brain:${t.latency||0}s`;
    document.getElementById('debug-prompt').innerText = finalPrompt;
    document.getElementById('debug-status').innerText = hasError ? 'FAILED' : 'DONE';
    document.getElementById('debug-status').style.color = hasError ? '#ff4444' : '#00ff00';

    const errorEl = document.getElementById('debug-error');
    if (hasError) {
        errorEl.innerText = 'ERROR: ' + (v.error || t.error);
        errorEl.style.display = 'block';
    } else {
        errorEl.style.display = 'none';
    }
}

async function sendSuggestion() {
    const input = document.getElementById('suggestion-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('scene-image').style.opacity = "0.5";
    
    document.getElementById('debug-status').innerText = "GENERATING...";
    document.getElementById('debug-status').style.color = "#ffff00";
    
    const textContent = document.getElementById('text-content');
    const narratorEl = document.getElementById('narrator-text');
    
    // 主角對話框：靜默等待（點點）
    textContent.innerText = '......';
    
    // 旁白區：每 5 秒輪換一則灰色小字
    let narratorIdx = 0;
    const showNarrator = () => {
        narratorEl.style.opacity = '0';
        setTimeout(() => {
            narratorEl.innerText = WAITING_NARRATIONS[narratorIdx % WAITING_NARRATIONS.length];
            narratorEl.style.opacity = '1';
            narratorIdx++;
        }, 400);
    };
    showNarrator();
    const narratorInterval = setInterval(showNarrator, 5000);

    try {
        const response = await fetch('/api/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ suggestion: text, state: gameState })
        });
        const data = await response.json();
        
        clearInterval(narratorInterval);
        
        if (data.error) {
            console.error("API Error:", data.error);
            narratorEl.innerText = `（系統訊號異常：${data.error}）`;
            document.getElementById('submit-btn').disabled = false; // ✅ 修正：錯誤時重新啟用按鈕
        } else {
            updateUI(data);
            
            // ✅ 修正：加入 null 安全檢查
            if (data.new_state && data.new_state.is_over) {
                const endingType = data.new_state.ending || "awakening";
                let endingTitle = "【覺醒：面對現實】";
                if (endingType === "connection_lost") {
                    endingTitle = "【錯誤：連線被強制中斷】\n主角拒絕了你的入侵，世界已永久關閉。";
                    soundManager.playBGM('ending_bad');
                } else if (endingType === "escapism") {
                    endingTitle = "【逃避：永恆之雨】";
                    soundManager.playBGM('ending_bad');
                } else {
                    soundManager.playBGM('ending_good');
                }
                
                setTimeout(() => {
                    alert("遊戲結束：" + endingTitle);
                    location.reload();
                }, 5000);
            }
        }
    } catch (e) {
        console.error(e);
        clearInterval(narratorInterval);
        narratorEl.innerText = '訊號中斷——請稍後再試。';
    } finally {
        document.getElementById('submit-btn').disabled = false;
        input.focus();
    }
}

document.getElementById('suggestion-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendSuggestion();
});

// updateBars(); // Removed to prevent crash in immersive mode
// new RainEngine('rain-canvas'); // Already handled in window.onload
