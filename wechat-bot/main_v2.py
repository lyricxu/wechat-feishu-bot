import os
import yaml
import time
import threading
import uvicorn
from loguru import logger
from main import NewsBotManager
from server import app

def run_scheduler(config_path):
    """
    运行定时爬取任务
    """
    try:
        manager = NewsBotManager(config_path)
        # 启动定时调度
        import schedule
        # 每 4 小时执行一次
        schedule.every(4).hours.do(manager.run_task)
        
        logger.info("定时任务调度器已启动，每 4 小时执行一次")
        while True:
            schedule.run_pending()
            time.sleep(60)
    except Exception as e:
        logger.error(f"定时任务调度器启动失败: {e}")

def run_webhook_server():
    """
    运行 Webhook 服务
    """
    port = int(os.getenv("PORT", 8000))
    logger.info(f"启动飞书 Webhook 服务，监听端口: {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    config_path = './config/config.yaml'
    
    # 1. 启动定时任务线程
    scheduler_thread = threading.Thread(target=run_scheduler, args=(config_path,), daemon=True)
    scheduler_thread.start()
    
    # 2. 启动 Webhook 服务（主线程运行）
    run_webhook_server()
