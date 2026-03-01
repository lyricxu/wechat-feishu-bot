from notion_client import Client
from loguru import logger

class NotionBot:
    def __init__(self, token, database_id):
        self.notion = Client(auth=token)
        self.database_id = database_id

    def add_article(self, title, summary, score, url, keywords, author):
        """
        向 Notion 数据库添加一篇文章记录
        数据库应包含：标题(Title)、概要(RichText)、分数(Number)、链接(Url)、标签(Multi-select)、作者(Select) 等字段
        """
        try:
            new_page = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "标题": {
                        "title": [{"text": {"content": title}}]
                    },
                    "概要": {
                        "rich_text": [{"text": {"content": summary}}]
                    },
                    "分数": {
                        "number": score
                    },
                    "链接": {
                        "url": url
                    },
                    "标签": {
                        "multi_select": [{"name": kw} for kw in keywords]
                    },
                    "作者": {
                        "select": {"name": author}
                    }
                }
            }
            response = self.notion.pages.create(**new_page)
            logger.info(f"Notion 记录添加成功: {title}")
            return response
        except Exception as e:
            logger.error(f"Notion 记录添加失败: {e}")
            return None

if __name__ == "__main__":
    # 测试代码
    # bot = NotionBot("test_token", "test_db_id")
    # bot.add_article("测试文章", "概要内容", 90, "https://mp.weixin.qq.com/s/test", ["AI"], "测试号")
    pass
