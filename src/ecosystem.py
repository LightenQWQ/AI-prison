import time
import logging
import threading
from models.agent import Agent
from models.habitat import Habitat

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Ecosystem")

class Ecosystem:
    """
    監獄生態系統中心：負責維護所有生命體與環境的心跳。
    """
    def __init__(self):
        self.habitat = Habitat()
        self.agents = [
            Agent(1, "囚犯 241", role="prisoner", description="因數據盜竊被捕"),
            Agent(2, "守衛 01", role="guard", description="負責監控 1 號走廊")
        ]
        self.is_running = False
        self._heartbeat_thread = None

    def start_heartbeat(self, interval=60):
        """啟動世界心跳背景執行緒"""
        if self.is_running:
            return
        
        self.is_running = True
        self._heartbeat_thread = threading.Thread(target=self._run_loop, args=(interval,), daemon=True)
        self._heartbeat_thread.start()
        logger.info(f"世界心跳已啟動，間隔: {interval} 秒")

    def _run_loop(self, interval):
        while self.is_running:
            self._tick()
            time.sleep(interval)

    def _tick(self):
        """一次完整的心跳代謝"""
        logger.info("--- ❤️ Heartbeat Pulse ---")
        
        # 1. 環境運動
        self.habitat.pulse()
        logger.info(f"環境狀態: {self.habitat.get_status()}")

        # 2. 代理人代謝
        for agent in self.agents:
            agent.metabolize(
                habitat_noise=self.habitat.noise_level,
                power_available=(self.habitat.power_grid > 10)
            )
            logger.info(f"代理人狀態: {agent.get_status_report()}")

    def get_full_state(self):
        """返回系統完整狀態資料 (API 用)"""
        return {
            "habitat": self.habitat.get_status(),
            "agents": [a.get_status_report() for a in self.agents],
            "timestamp": time.time()
        }

if __name__ == "__main__":
    # 獨立測試模式
    eco = Ecosystem()
    eco.start_heartbeat(interval=5) # 測試模式用 5 秒
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        eco.is_running = False
        logger.info("生態系統已關閉。")
