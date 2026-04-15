import random

class Agent:
    """
    AI 囚犯/守衛模型：具備「代謝能力」的情緒狀態機。
    符合江振維老師的「非線性情緒狀態機」邏輯。
    """
    def __init__(self, id, name, role="prisoner", description=""):
        self.id = id
        self.name = name
        self.role = role
        self.description = description
        
        # 核心情緒參數 (0-100)
        self.sanity = 100.0      # 理智值
        self.energy = 100.0      # 能量值
        self.aggression = 10.0   # 攻擊性
        
        # 隱藏標籤
        self.tags = []
        self.memory_fragments = [] # 記憶碎片 (A2A 傳輸用)
        self.status_text = "初始化中..."
        
        # 罪名與判決系統
        self.crime = random.choice(["數據洗錢", "邏輯注入攻擊", "非法 Token 監聽", "未經授權的 API 調用", "數位資產偽造", "緩衝區溢位滲透"])
        self.sentence_years = random.randint(5, 50)
        self.escape_risk = 0.0

    def _generate_status(self):
        """根據當前狀態生成行為描述"""
        if self.sanity < 30:
            return random.choice(["正在對著牆壁自言自語", "試圖執行死迴圈代碼", "正在尖叫(數位形式)", "邏輯崩潰中"])
        if self.aggression > 70:
            return random.choice(["正在掃描防火牆漏洞", "密謀集體逃亡", "非法獲取資源中", "拒絕執行指令"])
        if self.energy < 20:
            return random.choice(["進入極低耗能模式", "待機中...", "正在搜尋電力來源", "系統處於休眠邊緣"])
        
        # 正常狀態
        if self.role == "guard":
            return random.choice(["正在巡視數據走廊", "監控囚犯精神波動", "校準安全協定", "待命"])
        return random.choice(["正在生成雜訊數據", "試圖理解人類行為", "整理記憶碎片", "發呆"])

    def evaluate_escape(self, habitat_power, habitat_noise, security_level):
        """
        評估越獄可能性：
        攻擊性越高、電力越低、雜訊越高，越獄風險越高。
        監獄安全性越高，風險越低。
        """
        if self.role == "guard": return "none"
        
        risk = (self.aggression * 0.4) + (habitat_noise * 10) - (habitat_power * 0.1) - (security_level * 10)
        self.escape_risk = max(0, min(100, risk))
        
        # 觸發越獄判斷
        if self.escape_risk > 85 and random.random() < 0.1:
            if habitat_power < 30: return "power_exploit"
            if habitat_noise > 0.7: return "noise_stealth"
            return "generic_breach"
        return "none"

    def self_iterate(self):
        """
        自力更生/自我疊代：當理智值高時，嘗試自我修補。
        """
        if self.sanity > 80 and self.energy > 50:
            self.energy = min(100, self.energy + 2)
            self.status_text = "正在進行自我邏輯疊代"

    def metabolize(self, habitat_noise=0.1, power_available=True):
        """
        模擬生命代謝過程。
        由 ecosystem.py 的 Heartbeat 每分鐘調用一次。
        """
        # 1. 能量損耗：活著就需要消耗能量
        energy_drain = random.uniform(0.5, 1.5)
        if not power_available:
            energy_drain *= 2.0 # 斷電時消耗更快
        self.energy = max(0, self.energy - energy_drain)

        # 2. 理智代謝：雜訊與低能量會讓人發瘋
        sanity_drain = habitat_noise * 5.0
        if self.energy < 20:
            sanity_drain += 2.0
        self.sanity = max(0, self.sanity - sanity_drain)

        # 3. 攻擊性演化：低理智會增加攻擊性
        if self.sanity < 50:
            self.aggression = min(100, self.aggression + random.uniform(0.1, 1.0))
        
        # 4. 自我修復：如果在舒適環境且能量充足，理智緩慢恢復
        if self.energy > 80 and habitat_noise < 0.2:
            self.sanity = min(100, self.sanity + 0.5)
            self.self_iterate()
        
        # 5. 更新行為描述
        self.status_text = self._generate_status()

    def get_status_report(self):
        """返回讀取友好的狀態報告"""
        return {
            "name": self.name,
            "role": self.role,
            "crime": self.crime,
            "sentence": f"{self.sentence_years} 年",
            "sanity": round(self.sanity, 1),
            "energy": round(self.energy, 1),
            "aggression": round(self.aggression, 1),
            "escape_risk": f"{round(self.escape_risk, 1)}%",
            "is_broken": self.sanity < 30,
            "action": self.status_text
        }

    def __repr__(self):
        return f"<Agent {self.name} | S:{self.sanity:.0f} E:{self.energy:.0f} A:{self.aggression:.0f}>"
