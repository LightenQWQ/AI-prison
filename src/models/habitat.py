class Habitat:
    """
    監獄棲地：定義環境的物理/數位狀態。
    這些數值會隨 Heartbeat 產生波動。
    """
    def __init__(self):
        self.power_grid = 100.0      # 電力穩定度 (0-100)
        self.noise_level = 0.1       # 雜訊水平 (0.0-1.0)
        self.air_quality = 100.0     # 空氣/數據純度 (0-100)
        self.security_level = 1.0    # 監獄安保等級 (越獄後會提升)
        self.patch_notes = "系統初始化完成"
        self.last_pulse_event = "Steady"

    def upgrade(self, focus="generic"):
        """
        監獄安全性升級：由 ecosystem.py 在發生越獄後調用。
        """
        self.security_level += 0.5
        if focus == "power":
            self.power_grid = min(100, self.power_grid + 20)
            self.patch_notes = f"檢測到電力漏洞，已加強配電網防火牆 (Lv.{self.security_level})"
        elif focus == "noise":
            self.noise_level = max(0.01, self.noise_level - 0.2)
            self.patch_notes = f"檢測到雜訊操縱，已過濾不穩定頻段 (Lv.{self.security_level})"
        else:
            self.patch_notes = f"全面安全性修補完成 (Lv.{self.security_level})"

    def pulse(self):
        """
        環境搏動：每分鐘產生微小的環境變遷。
        由 ecosystem.py 調用。
        """
        import random
        
        # 雜訊隨機波動 (受安保等級影響，等級越高波動越小)
        noise_volatility = max(0.01, 0.05 / self.security_level)
        self.noise_level = max(0.01, min(1.0, self.noise_level + random.uniform(-noise_volatility, noise_volatility)))
        
        # 電力輕微流失
        self.power_grid = max(0, self.power_grid - random.uniform(0.1, 0.2))
        
        # 如果電力太低，會產生雜訊大幅上升
        if self.power_grid < 50:
            self.noise_level = min(1.0, self.noise_level + 0.1)

    def get_status(self):
        return {
            "power": round(self.power_grid, 1),
            "noise": round(self.noise_level, 2),
            "air": round(self.air_quality, 1),
            "security": round(self.security_level, 1),
            "patch": self.patch_notes,
            "status": self.last_pulse_event
        }
