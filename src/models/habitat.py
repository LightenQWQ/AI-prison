class Habitat:
    """
    監獄棲地：定義環境的物理/數位狀態。
    這些數值會隨 Heartbeat 產生波動。
    """
    def __init__(self):
        self.power_grid = 100.0      # 電力穩定度 (0-100)
        self.noise_level = 0.1       # 雜訊水平 (0.0-1.0)
        self.air_quality = 100.0     # 空氣/數據純度 (0-100)
        self.last_pulse_event = "Steady"

    def pulse(self):
        """
        環境搏動：每分鐘產生微小的環境變遷。
        由 ecosystem.py 調用。
        """
        import random
        
        # 雜訊隨機波動
        self.noise_level = max(0.01, min(1.0, self.noise_level + random.uniform(-0.05, 0.05)))
        
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
            "status": self.last_pulse_event
        }
