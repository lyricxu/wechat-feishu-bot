import json
import hmac
import hashlib
import time
import re
from fastapi import FastAPI, Request
from loguru import logger
from src.scraper import WeChatScraper
from src.ai_analyzer import AIAnalyzer
from src.feishu_bot import FeishuBot
from src.notion_client import NotionBot

class FeishuWebhookHandler:
    def __init__(self, app_id, app_secret, notion_token, notion_db_id, high_score_threshold=80):
        self.app_id = app_id
        self.app_secret = app_secret
        self.feishu = FeishuBot(app_id, app_secret)
        self.notion = NotionBot(notion_token, notion_db_id)
        self.scraper = WeChatScraper()
        self.analyzer = AIAnalyzer()
        self.high_score_threshold = high_score_threshold
        
        # 对话状态管理：记录最近分析过的文章
        self.user_sessions = {}

    def verify_request(self, request_body: str, timestamp: str, nonce: str, signature: str) -> bool:
        """
        验证飞书请求的合法性
        """
        if not signature:
            return True # 如果没有签名，暂时允许通过（仅用于快速验证测试）
        msg = f"{timestamp}{nonce}{request_body}"
        computed_signature = hmac.new(
            self.app_secret.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()
        return computed_signature == signature

    def extract_links(self, text: str) -> list:
        """
        从文本中提取微信公众号链接
        """
        pattern = r'https?://mp\.weixin\.qq\.com/s/[a-zA-Z0-9_-]+'
        return re.findall(pattern, text)

    def process_article_link(self, url: str, user_id: str) -> dict:
        """
        处理单个文章链接：爬取 -> 分析 -> 返回结果
        """
        logger.info(f"开始处理链接: {url}")
        
        # 1. 获取文章正文
        content = self.scraper.get_article_content(url)
        if not content:
            return {"error": "无法获取文章内容，请检查链接是否有效"}
        
        # 提取标题（简化处理，正式环境建议从 HTML 中解析）
        title = "手动解析的微信文章"
        
        # 2. AI 分析
        analysis = self.analyzer.analyze_article(title, content)
        if not analysis:
            return {"error": "AI 分析失败"}
        
        # 3. 保存到用户会话
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {"articles": [], "timestamp": time.time()}
        
        article_record = {
            "title": title,
            "url": url,
            "summary": analysis['summary'],
            "score": analysis['score'],
            "keywords": analysis['keywords'],
            "reason": analysis['reason']
        }
        
        self.user_sessions[user_id]["articles"].insert(0, article_record)
        if len(self.user_sessions[user_id]["articles"]) > 5:
            self.user_sessions[user_id]["articles"].pop()
        
        return article_record

    def handle_message(self, message_data: dict, user_id: str) -> any:
        """
        处理用户消息
        """
        text = message_data.get("text", "").strip()
        
        # 1. 检查是否包含链接
        links = self.extract_links(text)
        if links:
            results = []
            for link in links:
                result = self.process_article_link(link, user_id)
                results.append(result)
            return results
        
        # 2. 检查是否是指令
        if any(keyword in text for keyword in ["存入", "收藏", "保存"]):
            if user_id in self.user_sessions and self.user_sessions[user_id]["articles"]:
                latest_article = self.user_sessions[user_id]["articles"][0]
                try:
                    self.notion.add_article(
                        title=latest_article["title"],
                        summary=latest_article["summary"],
                        score=latest_article["score"],
                        url=latest_article["url"],
                        keywords=latest_article["keywords"],
                        author="用户手动"
                    )
                    return {"success": True, "message": f"✅ 已将《{latest_article['title']}》存入 Notion"}
                except Exception as e:
                    return {"success": False, "message": f"❌ 存入失败: {str(e)}"}
            else:
                return {"success": False, "message": "❌ 没有找到最近分析的文章"}
        
        return None
