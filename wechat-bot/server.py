import os
import yaml
import json
from fastapi import FastAPI, Request, HTTPException
from loguru import logger
from src.feishu_webhook import FeishuWebhookHandler
from src.feishu_bot import FeishuBot

# 加载配置
def load_config():
    config_path = './config/config.yaml'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        # 从环境变量加载（Zeabur 等云端推荐方式）
        return {
            'feishu': {
                'app_id': os.getenv('FEISHU_APP_ID'),
                'app_secret': os.getenv('FEISHU_APP_SECRET'),
                'receive_id': os.getenv('FEISHU_RECEIVE_ID')
            },
            'notion': {
                'token': os.getenv('NOTION_TOKEN'),
                'database_id': os.getenv('NOTION_DB_ID')
            },
            'ai': {
                'model': os.getenv('AI_MODEL', 'gpt-4.1-mini'),
                'high_score_threshold': int(os.getenv('HIGH_SCORE_THRESHOLD', 80))
            }
        }

config = load_config()

# 初始化 FastAPI 应用
app = FastAPI(title="WeChat News Bot Server")

# 初始化 Webhook 处理器
webhook_handler = FeishuWebhookHandler(
    app_id=config['feishu']['app_id'],
    app_secret=config['feishu']['app_secret'],
    notion_token=config['notion']['token'],
    notion_db_id=config['notion']['database_id'],
    high_score_threshold=config['ai']['high_score_threshold']
)

feishu_bot = FeishuBot(config['feishu']['app_id'], config['feishu']['app_secret'])

@app.post("/webhook/feishu")
async def feishu_webhook(request: Request):
    """
    飞书消息回调接口
    """
    try:
        # 1. 优先处理 URL 验证请求 (极速响应飞书 Challenge)
        body_bytes = await request.body()
        body = json.loads(body_bytes.decode())
        
        if body.get("type") == "url_verification":
            challenge = body.get("challenge")
            logger.info(f"收到 URL 验证请求，返回 challenge: {challenge}")
            return {"challenge": challenge}
        
        # 2. 验证请求合法性
        headers = request.headers
        timestamp = headers.get("X-Lark-Request-Timestamp")
        nonce = headers.get("X-Lark-Request-Nonce")
        signature = headers.get("X-Lark-Signature")
        
        if not webhook_handler.verify_request(body_bytes.decode(), timestamp, nonce, signature):
            logger.warning("请求验证失败")
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # 3. 处理消息事件回调
        if body.get("type") == "event_callback":
            event = body.get("event", {})
            message = event.get("message", {})
            
            # 处理新版 V2.0 消息事件
            if message:
                message_type = message.get("message_type")
                if message_type != "text":
                    return {"code": 0}
                
                content_json = json.loads(message.get("content", "{}"))
                text_content = content_json.get("text", "")
                chat_id = message.get("chat_id")
                sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id")
                
                logger.info(f"处理来自 {sender_id} 的消息: {text_content}")
                
                # 调用处理器
                result = webhook_handler.handle_message({"text": text_content}, sender_id)
                
                if result:
                    # 构建回复消息并发送
                    if isinstance(result, list):
                        for item in result:
                            if "error" in item:
                                feishu_bot.send_text_reply(chat_id, f"❌ {item['error']}")
                            else:
                                reply_text = f"📰 **{item['title']}**\n\n🎯 评分: {item['score']}分\n💡 理由: {item['reason']}\n📝 概要: {item['summary']}\n🏷️ 关键词: {', '.join(item['keywords'])}\n\n💬 回复\"存入\"可将此文章保存到 Notion"
                                feishu_bot.send_text_reply(chat_id, reply_text)
                    elif isinstance(result, dict):
                        reply_text = result.get("message", f"📰 {result.get('title')} 处理成功")
                        feishu_bot.send_text_reply(chat_id, reply_text)
            
            return {"code": 0}
        
        return {"code": 0}
    
    except Exception as e:
        logger.error(f"Webhook 处理失败: {e}")
        return {"code": 0} # 飞书要求非 200 响应会重试，通常返回 200 避免无限循环

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
