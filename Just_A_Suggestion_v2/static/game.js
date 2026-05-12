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
        // 固定心跳與腦波節奏，不再隨 fear/trust 變動，僅作為純視覺裝飾
        const bpm = 72; 
        const interval = (60 / bpm) * 60;
        let val = this.height / 2;
        if (this.offset % Math.floor(interval) === 0) {
            val -= 20;
        } else if (this.offset % Math.floor(interval) === 5) {
            val += 10;
        }
        this.ecgPath.shift();
        this.ecgPath.push(val + (Math.random() * 2 - 1));
        
        const eegVal = (this.height / 2) + (Math.sin(this.offset * 0.2) * 5) + (Math.random() * 5);
        this.eegPath.shift();
        this.eegPath.push(eegVal);
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
        this.bgm.volume = 0; // 初始音量0，準備淡入
        
        // 統一全程使用 custom_bgm.mp3
        this.tracks = {
            intro: "assets/custom_bgm.mp3",
            game: "assets/custom_bgm.mp3",
            ending_good: "https://cdn.pixabay.com/download/audio/2022/10/25/audio_2267b2d556.mp3?filename=sad-piano-ambient-123473.mp3",
            ending_bad: "https://cdn.pixabay.com/download/audio/2021/08/04/audio_031bb29e05.mp3?filename=scary-ambient-horror-12398.mp3"
        };

        this.rainNode = null;
        this.isMuted = false;
    }

    // 淡入淡出 BGM 播放
    playBGM(type) {
        if (this.isMuted) return;
        const targetSrc = this.tracks[type];
        if (!targetSrc) return;

        // 如果目前已經在播放同一個檔案，就不要中斷重放，保持流暢
        if (this.bgm.src.includes(targetSrc) && !this.bgm.paused) {
            console.log(`BGM ${type} is already playing, skipping reset.`);
            return;
        }

        if (this.bgm.src) {
            // 淡出淡入邏輯
            let vol = this.bgm.volume;
            const fadeOut = setInterval(() => {
                vol = Math.max(0, vol - 0.05);
                this.bgm.volume = vol;
                if (vol <= 0) {
                    clearInterval(fadeOut);
                    this.bgm.src = targetSrc;
                    this.bgm.play().then(() => {
                        const fadeIn = setInterval(() => {
                            vol = Math.min(this.bgmVolume, vol + 0.02);
                            this.bgm.volume = vol;
                            if (vol >= this.bgmVolume) clearInterval(fadeIn);
                        }, 100);
                    }).catch(e => console.log("Audio play blocked", e));
                }
            }, 100);
        } else {
            // 第一次播放
            this.bgm.src = targetSrc;
            this.bgm.play().then(() => {
                this.bgm.volume = this.bgmVolume;
            }).catch(e => console.log("Audio play blocked", e));
        }
    }

    // 常駐背景雨聲 - 直接播放使用者提供的 rain_bgm.mp3
    startRain() {
        if (this.rainAudio) return; // 避免重複啟動
        this.rainAudio = new Audio('assets/rain_bgm.mp3');
        this.rainAudio.loop = true;
        this.rainAudio.volume = 0.5; // 調高預設雨聲，營造下大雨的感覺
        this.rainAudio.play().catch(e => console.log('Rain audio blocked:', e));
        // rainNode 保留供靜音控制用
        this.rainNode = { _isFile: true };
    }

    // 模擬紙張翻頁的音效 (Web Audio API)
    playPageTurn() {
        if(this.isMuted || this.audioCtx.state === 'suspended') return;
        
        const bufferSize = this.audioCtx.sampleRate * 0.4; // 0.4秒長度
        const noiseBuffer = this.audioCtx.createBuffer(1, bufferSize, this.audioCtx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1;
        }

        const whiteNoise = this.audioCtx.createBufferSource();
        whiteNoise.buffer = noiseBuffer;

        // 帶通濾波器：保留紙張摩擦的頻段 (約 1000Hz - 2000Hz)
        const filter = this.audioCtx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.value = 1500;
        
        // 音量包絡線 (Envelope)：模擬「唰」一聲的動態
        const gain = this.audioCtx.createGain();
        gain.gain.setValueAtTime(0, this.audioCtx.currentTime);
        gain.gain.linearRampToValueAtTime(0.6, this.audioCtx.currentTime + 0.05); // 快速達到最大聲
        gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.3); // 慢慢滑落

        whiteNoise.connect(filter);
        filter.connect(gain);
        gain.connect(this.audioCtx.destination);
        
        whiteNoise.start();
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
        if (this.isMuted) return;
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
    "冰冷的雨水不斷落在屋簷上，濺起細小的水花。",
    "生鏽的排水管發出沉悶的低鳴，迴盪在無人的巷弄裡。",
    "霓虹燈的倒影在積水中破碎，又隨著水滴重新匯聚。",
    "就在這片寂靜的雨聲中，我聽見了一個聲音。"
];

const introSequence = [
    { text: "....", desc: "一位少年，孤身佇立在深夜的巷道盡頭。路燈的光暈在濕地上暈開，像一個沒人回答的問題。", img: "assets/cover_v3.png" },
    { text: "....", desc: "他不知道自己在等什麼。雨滴打在他的肩膀上，他沒有躲避，就這樣站著。", img: "assets/cover_v3.png" },
    { text: "....", desc: "你感覺到了他。他的某一部分，正在向外呼喊——儘管他自己還沒有察覺。", img: "assets/cover_v3.png" }
];

let introIndex = 0;
let isSkippingPrologue = false;

function skipPrologue() {
    isSkippingPrologue = true;
    const overlay = document.getElementById('prologue-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.display = 'none';
        }, 500);
    }
}

// 啟動
window.onload = () => {
    rainEngine = new RainEngine('rain-canvas');
};

async function quickStart() {
    console.log("DEBUG: Quick starting game...");
    const entry = document.getElementById('pre-entry');
    const overlay = document.getElementById('overlay');
    const gameContainer = document.getElementById('game-container');
    
    entry.style.display = 'none';
    overlay.style.display = 'none';
    gameContainer.style.setProperty('display', 'flex', 'important');
    
    if (!window.soundManager) window.soundManager = new SoundManager();
    soundManager = window.soundManager;
    if (soundManager.audioCtx.state === 'suspended') soundManager.audioCtx.resume();
    
    soundManager.startRain();
    soundManager.playBGM('game');
    
    waveEngine = new WaveformEngine();
    document.getElementById('scene-image').style.display = 'block';
    document.getElementById('scene-image').style.opacity = '1';
    
    updateUI({
        dialogue: "......",
        narration: "（你直接跳入了這場永恆的雨夜。）",
        image_url: "assets/cover_v3.png"
    });
}

async function startGame() {
    isSkippingPrologue = false;
    
    // 如果全域已經有 soundManager (來自 index.html 啟動)，則沿用，避免重複播放
    if (!window.soundManager) {
        window.soundManager = new SoundManager();
    }
    soundManager = window.soundManager; 
    
    waveEngine = new WaveformEngine();
    
    document.getElementById('overlay').classList.add('fading');
    
    // 序章期間保持背景純淨，暫時不顯示遊戲介面
    setTimeout(() => {
        // 僅移除舊的顯示邏輯
    }, 100);
    setTimeout(() => {
        document.getElementById('overlay').style.display = 'none';
        
        // 為了確保 AudioContext 解鎖，必須在 user click 之後恢復
        if (soundManager.audioCtx.state === 'suspended') {
            soundManager.audioCtx.resume();
        }
        
        soundManager.startRain(); // 啟動全代碼生成的暴雨聲
        soundManager.playBGM('intro');
    }, 1000);

    await playDreamSequence();

    if (isSkippingPrologue) {
        // 跳過時也必須顯現遊戲介面
        document.getElementById('game-container').style.setProperty('display', 'flex', 'important');
        document.getElementById('monitor-osd-bar').style.display = 'flex';

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

    // 序章結束，正式顯示遊戲介面與儀表板
    document.getElementById('game-container').style.setProperty('display', 'flex', 'important');
    document.getElementById('monitor-osd-bar').style.display = 'flex';
    
    triggerBootGlitch();
    // 已依照要求移除監視器啟動音效 (playGlitch)
    soundManager.playBGM('game');
    showNextIntro();
}

async function playDreamSequence() {
    const overlay = document.getElementById('prologue-overlay');
    overlay.style.display = 'flex';
    // 將 SKIP 按鈕只建立一次
    overlay.innerHTML = '<div id="skip-btn" onclick="skipPrologue()">SKIP >></div>';
    
    for (let text of dreamSequence) {
        if (isSkippingPrologue) break;
        
        // 每次只保留一個 p 標籤，避免水平或垂直堆疊造成位移
        const oldP = overlay.querySelector('.dream-text');
        if (oldP) oldP.remove();

        const p = document.createElement('p');
        p.className = 'dream-text';
        p.innerText = text;
        overlay.appendChild(p);
        
        // 已依照要求移除翻頁音效
        
        for (let i = 0; i < 40; i++) {
            if (isSkippingPrologue) break;
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
    
    if (!isSkippingPrologue) {
        overlay.style.transition = 'opacity 2s ease';
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
        const text = data.dialogue || '......';
        document.getElementById('text-content').innerText = text;
        
        // 移除每回合的翻頁音效呼叫
        /*
        if(soundManager) {
            soundManager.playPageTurn();
        }
        */
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
        sceneImg.style.filter = "contrast(1.1) grayscale(1) brightness(0.85) blur(20px)"; // 轉場開始：模糊
        
        setTimeout(() => {
            sceneImg.src = "data:image/png;base64," + data.image_b64;
            sceneImg.classList.add("cinematic-animation");
            sceneImg.style.opacity = "1";
            sceneImg.style.filter = "contrast(1.1) grayscale(1) brightness(0.85) blur(0px)"; // 轉場結束：清晰
        }, 300);
    } else if (data.image_url) {
        const sceneImg = document.getElementById('scene-image');
        sceneImg.style.opacity = "0";
        sceneImg.style.filter = "contrast(1.1) grayscale(1) brightness(0.85) blur(20px)";
        
        setTimeout(() => {
            sceneImg.src = data.image_url;
            sceneImg.classList.add("cinematic-animation");
            sceneImg.style.opacity = "1";
            sceneImg.style.filter = "contrast(1.1) grayscale(1) brightness(0.85) blur(0px)";
        }, 100);
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
    "這條路..... 我每天都走，可今晚感覺走不完。",
    "不想回家..... 家裡也沒有人在等。",
    "雨聲把什麼都蓋掉了..... 挺好的。",
    "為什麼要跟我說話？你是誰？",
    "我沒事..... 不，我說謊了。",
    "就算我一直站在這裡，也不會有人發現吧。"
];

// 等待生圖期間的旁白池（每 5 秒輪換）
const WAITING_NARRATIONS = [
    "（他的視線停在積水的地面，路燈的倒影在水中顫抖⋯⋯）",
    "（他握緊了口袋裡的手，那裡什麼都沒有，卻很安心⋯⋯）",
    "（他閉上眼，試著讓雨聲蓋過腦子裡那些旋轉的問題⋯⋯）",
    "（他想起一個人，但馬上把那個名字推開了⋯⋯）",
    "（他知道你在那裡。他假裝不知道⋯⋯）",
    "（他深吸一口氣，雨水的氣味混著鐵鏽，讓他清醒了一秒⋯⋯）"
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

    // 更新進度與事件資訊 (Debug Panel)
    const stageMap = {
        0: "情感接觸",
        1: "尋找電話亭",
        2: "回憶號碼",
        3: "撥通電話",
        4: "前往公寓",
        5: "開啟信箱",
        6: "家門之前"
    };
    
    if (gameState) {
        document.getElementById('debug-progress').innerText = `${gameState.turn} 回合 | Stage ${gameState.puzzle_stage}`;
        document.getElementById('debug-chapter').innerText = stageMap[gameState.puzzle_stage] || "未知";
    }

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
            
            if (data.new_state && data.new_state.is_over) {
                // 播放結局音樂
                const endingType = data.new_state.ending || "awakening";
                if (endingType === "connection_lost" || endingType === "escapism") {
                    soundManager.playBGM('ending_bad');
                } else {
                    soundManager.playBGM('ending_good');
                }
                
                // 顯示全螢幕結局畫面（4秒後切入，讓玩家先看最後一張圖）
                setTimeout(() => {
                    const endScreen = document.getElementById('ending-screen');
                    const titleEl = document.getElementById('ending-title-display');
                    const narrativeEl = document.getElementById('ending-narrative-display');
                    const retroWrap = document.getElementById('ending-retrospective-wrap');
                    const retroDivider = document.getElementById('retro-divider');
                    const retroEl = document.getElementById('ending-retrospective-display');
                    
                    titleEl.innerText = data.ending_title || '【結局】';
                    narrativeEl.innerText = data.ending_narrative || '雨不停歇。這座城市將再次歸於沉默。';
                    
                    endScreen.style.display = 'flex';
                    setTimeout(() => endScreen.style.opacity = '1', 50);

                    // 心境回顧：打字機效果，延遲出現
                    const retroText = data.ending_retrospective || '';
                    if (retroText) {
                        setTimeout(() => {
                            retroDivider.style.display = 'flex';
                            retroWrap.style.display = 'block';
                            retroEl.innerText = '';
                            let i = 0;
                            const typeInterval = setInterval(() => {
                                if (i < retroText.length) {
                                    retroEl.innerText += retroText[i];
                                    i++;
                                } else {
                                    clearInterval(typeInterval);
                                }
                            }, 40);
                        }, 3500); // 結局文字顯示3.5秒後才出現內心獨白
                    }
                }, 4000); // 讓玩家先看最後一張圖 4 秒再切入結局
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

// ============================================================
// 音效控制面板
// ============================================================

let audioPanelOpen = false;

function toggleAudioPanel() {
    audioPanelOpen = !audioPanelOpen;
    const panel = document.getElementById('audio-controls-panel');
    panel.style.display = audioPanelOpen ? 'block' : 'none';
}

function toggleAudio() {
    // 如果尚未初始化，則進行初始化
    if (!window.soundManager) {
        window.soundManager = new SoundManager();
        soundManager = window.soundManager;
    }
    
    soundManager.isMuted = !soundManager.isMuted;

    const btn = document.getElementById('mute-btn');
    if (soundManager.isMuted) {
        btn.innerText = 'OFF';
        btn.style.color = '#ff6666';
        btn.style.borderColor = 'rgba(255,102,102,0.4)';
        soundManager.bgm.pause();
        if (soundManager.rainAudio) soundManager.rainAudio.pause();
    } else {
        btn.innerText = 'ON';
        btn.style.color = '#88cc88';
        btn.style.borderColor = 'rgba(136,204,136,0.4)';
        
        // 解鎖音訊環境
        if (soundManager.audioCtx && soundManager.audioCtx.state === 'suspended') {
            soundManager.audioCtx.resume();
        }

        // 恢復播放
        if (soundManager.bgm.src) {
            soundManager.bgm.play().catch(e => {});
        } else {
            soundManager.playBGM('intro');
        }

        if (soundManager.rainAudio) {
            soundManager.rainAudio.play().catch(e => {});
        } else {
            soundManager.startRain();
        }
    }
}

function setBgmVolume(val) {
    document.getElementById('bgm-vol-label').innerText = val + '%';
    if (!window.soundManager) {
        window.soundManager = new SoundManager();
        soundManager = window.soundManager;
    }
    if (soundManager && soundManager.bgm) {
        soundManager.bgmVolume = val / 100;
        soundManager.bgm.volume = val / 100;
    }
}

function setRainVolume(val) {
    document.getElementById('rain-vol-label').innerText = val + '%';
    if (!window.soundManager) {
        window.soundManager = new SoundManager();
        soundManager = window.soundManager;
    }
    if (soundManager && soundManager.rainAudio) {
        soundManager.rainAudio.volume = val / 100;
    }
}

document.getElementById('suggestion-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendSuggestion();
});

// updateBars(); // Removed to prevent crash in immersive mode
// new RainEngine('rain-canvas'); // Already handled in window.onload
