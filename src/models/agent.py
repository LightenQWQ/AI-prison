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

    def get_status_report(self):
        """返回讀取友好的狀態報告"""
        return {
            "name": self.name,
            "role": self.role,
            "sanity": round(self.sanity, 1),
            "energy": round(self.energy, 1),
            "aggression": round(self.aggression, 1),
            "is_broken": self.sanity < 30
        }

    def __repr__(self):
        return f"<Agent {self.name} | S:{self.sanity:.0f} E:{self.energy:.0f} A:{self.aggression:.0f}>"
