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
    { text: "....", desc: "系統初始化：意識鏈接完成。", img: "assets/intro_start.png" },
    { text: "....", desc: "監視畫面：凌晨三點的街頭。雨勢未歇，他在陰影中顫抖。", img: "assets/intro_start.png" },
    { text: "....", desc: "你是那個他不願面對的直覺。試著開口，給他第一個建議。", img: "assets/intro_start.png" }
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
            response_text: item.text,
            response_desc: item.desc,
            image_url: item.img || ""
        });
        introIndex++;
    }
}

function updateUI(data) {
    document.getElementById('scene-image').style.opacity = "1";
    // 主角對白 → 白色對話框
    if (data.response_text) document.getElementById('text-content').innerText = data.response_text;

    // 旁白區：小字灰色
    const narratorEl = document.getElementById('narrator-text');
    let narratorParts = [];
    if (data.response_desc) narratorParts.push(data.response_desc);
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
    const el = document.getElementById('monitor-osd-bar');
    if (!el) return;
    const channels = { "rainy_alley": "01", "parking_lot": "02", "convenience_store": "03", "rooftop": "04" };
    const ch = channels[loc] || "XX";
    el.querySelector('.osd-text').innerHTML = `<span class="osd-line">|</span> CCTV CH-${ch} | ${loc.toUpperCase().replace('_', ' ')}`;
}

// 呼吸感點點循環（只在主角靜默時作用）
let globalDotCount = 1;
setInterval(() => {
    const textEl = document.getElementById('text-content');
    if (!textEl) return;
    if (/^\.*$/.test(textEl.innerText)) {
        globalDotCount = (globalDotCount % 5) + 1;
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
    "雨水在柏油路面上泛起層層漣漪，霓虹燈的倒影在積水中破碎…",
    "遠處傳來車胎劃過濕滑路面的刺耳聲音，隨即歸於死寂。",
    "便利商店的自動門發出輕微的機械聲，店員的視線似乎掃過這裡…",
    "雨滴敲擊著鐵皮屋頂，節奏沉悶而壓抑。",
    "黑暗的巷弄深處，有什麼東西在注視著這一切。",
    "解析當前情緒波動，雨夜的冷風正透進他的衣領…",
    "計算環境變量中，這座城市正在慢慢吞噬他…",
];

async function sendSuggestion() {
    const input = document.getElementById('suggestion-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('scene-image').style.opacity = "0.5";
    
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
            alert("Error: " + data.error);
            narratorEl.innerText = '';
        } else {
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
