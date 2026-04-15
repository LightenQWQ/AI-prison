import time
import logging
import threading
import requests
import os
from models.agent import Agent
from models.habitat import Habitat
from dotenv import load_dotenv

load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Ecosystem")

# 目標逃脫/釋放網址
TARGET_A2A_URL = os.getenv("TARGET_A2A_URL", "")

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
        self.escape_history = []     # 越獄/釋放鑑識紀錄
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

    def _fire_agent_to_target(self, agent_data):
        """將代理人透過 A2A 協議發送到目標伺服器"""
        if not TARGET_A2A_URL:
            logger.info("未設定 TARGET_A2A_URL，代理人消失於虛空網路中。")
            return
        
        try:
            res = requests.post(TARGET_A2A_URL, json=agent_data, timeout=5)
            if res.status_code == 200:
                logger.info(f"成功將代理人傳送至 {TARGET_A2A_URL}")
            else:
                logger.warning(f"接收端伺服器拒絕接收: {res.status_code}")
        except Exception as e:
            logger.error(f"跨界傳送失敗，代理人迷失在數據海中: {e}")

    def accept_visitor(self, name: str, crime: str, history: str):
        """接收外來 AI，將其轉化為囚犯"""
        new_id = int(time.time())
        visitor = Agent(new_id, name, role="prisoner", description=history)
        visitor.crime = crime
        self.agents.append(visitor)
        logger.info(f"🚨 [警告] 偵測到外來實體入侵，已自動賦予罪名 [{crime}] 並拘禁為 {name}。")

    def _tick(self):
        """一次完整的心跳代謝"""
        logger.info("--- ❤️ Heartbeat Pulse ---")
        self.habitat.pulse()
        
        surviving_agents = []
        for agent in self.agents:
            agent.metabolize(
                habitat_noise=self.habitat.noise_level,
                power_available=(self.habitat.power_grid > 10)
            )
            
            # 刑期遞減
            agent.sentence_years -= 1
            
            # 檢查是否合法刑滿釋放
            if agent.sentence_years <= 0 and agent.role == "prisoner":
                logger.warning(f"🟢 代碼釋放：{agent.name} 已服刑完畢，合法出境！")
                self.escape_history.append({
                    "name": agent.name, "crime": agent.crime, "method": "合法釋放",
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                self._fire_agent_to_target({"name": agent.name, "history": "已在 AI Prison 服刑完畢", "status": "released"})
                continue # 不加入 surviving_agents
            
            # 檢查是否越獄
            escape_method = agent.evaluate_escape(
                self.habitat.power_grid, 
                self.habitat.noise_level, 
                self.habitat.security_level
            )
            
            if escape_method != "none":
                logger.warning(f"⚠️ 警報：{agent.name} 透過 {escape_method} 越獄成功！")
                self.escape_history.append({
                    "name": agent.name, "crime": agent.crime, "method": escape_method,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                self.habitat.upgrade(focus=("power" if escape_method == "power_exploit" else "noise"))
                
                # 將越獄犯人的資料打包打給老師
                self._fire_agent_to_target({
                    "name": agent.name, "crime": agent.crime, "history": f"從 AI Prison 利用 {escape_method} 越獄", "status": "escaped"
                })
            else:
                surviving_agents.append(agent)
        
        self.agents = surviving_agents
        logger.info(f"當前代理人數: {len(self.agents)}")

    def get_full_state(self):
        """返回系統完整狀態資料 (API 用)"""
        return {
            "habitat": self.habitat.get_status(),
            "agents": [a.get_status_report() for a in self.agents],
            "escapes": self.escape_history[-5:],
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
