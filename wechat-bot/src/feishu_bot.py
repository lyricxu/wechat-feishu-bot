import requests
import json
from loguru import logger

class FeishuBot:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = self._get_access_token()

    def _get_access_token(self):
        """
        获取飞书应用的 tenant_access_token
        """
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    return result.get("tenant_access_token")
            logger.error(f"获取飞书 Access Token 失败: {response.text}")
            return None
        except Exception as e:
            logger.error(f"获取飞书 Access Token 异常: {e}")
            return None

    def send_rich_text(self, receive_id, title, summary, score, url, keywords, reason):
        """
        发送富文本消息给指定用户
        """
        if not self.access_token:
            self.access_token = self._get_access_token()
        
        send_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # 飞书富文本消息格式
        content = {
            "zh_cn": {
                "title": f"📰 资讯简报: {title}",
                "content": [
                    [{"tag": "text", "text": f"🎯 评分: {score}分\n"}],
                    [{"tag": "text", "text": f"💡 理由: {reason}\n"}],
                    [{"tag": "text", "text": f"📝 概要: {summary}\n"}],
                    [{"tag": "text", "text": f"🏷️ 关键词: {', '.join(keywords)}\n"}],
                    [{"tag": "a", "text": "🔗 点击阅读全文", "href": url}]
                ]
            }
        }
        
        payload = {
            "receive_id": receive_id,
            "msg_type": "post",
            "content": json.dumps(content)
        }
        
        try:
            response = requests.post(send_url, headers=headers, json=payload)
            if response.status_code == 200:
                logger.info(f"飞书消息发送成功: {title}")
                return True
            logger.error(f"飞书消息发送失败: {response.text}")
            return False
        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}")
            return False

if __name__ == "__main__":
    # 测试代码
    bot = FeishuBot("test_id", "test_secret")
    # bot.send_rich_text("test_open_id", "测试标题", "这是一段测试概要", 85, "https://mp.weixin.qq.com/s/test", ["AI", "测试"], "内容详实")
