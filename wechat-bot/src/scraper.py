import requests
from bs4 import BeautifulSoup
from loguru import logger
import time
from playwright.sync_api import sync_playwright

class WeChatScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def search_articles(self, account_name):
        """
        搜索指定公众号的最新文章
        由于搜狗等接口的不稳定性，这里采用模拟搜索或特定聚合页面的逻辑
        实际开发中建议使用稳定的 API 接口
        """
        logger.info(f"正在搜索公众号: {account_name} 的最新文章...")
        # 示例：通过搜狗微信搜索（需处理验证码）
        search_url = f"https://weixin.sogou.com/weixin?type=1&query={account_name}&ie=utf8"
        
        # 这里仅作为逻辑占位，实际环境可能需要 Playwright 绕过限制
        return []

    def get_article_content(self, url):
        """
        获取微信文章正文内容
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                content_div = soup.find('div', id='js_content')
                if content_div:
                    # 提取文本并清洗
                    text = content_div.get_text(separator='\n', strip=True)
                    return text
            return None
        except Exception as e:
            logger.error(f"获取文章内容失败: {url}, 错误: {e}")
            return None

    def fetch_latest_by_browser(self, account_name):
        """
        使用 Playwright 模拟浏览器获取公众号文章列表（更稳定但速度慢）
        """
        articles = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                # 模拟在搜狗微信搜索公众号
                page.goto(f"https://weixin.sogou.com/weixin?type=1&query={account_name}&ie=utf8")
                # 点击搜索结果中的第一个公众号
                page.click(".tit a")
                
                # 微信公众号历史页通常需要扫码或特定 Token，这里演示获取当前可见的文章
                # 实际场景中，可以通过监控搜狗的“最新文章”列表
                page.wait_for_selector(".news-box")
                links = page.query_selector_all(".news-box li h3 a")
                for link in links[:3]: # 获取前3篇
                    articles.append({
                        "title": link.inner_text(),
                        "url": "https://weixin.sogou.com" + link.get_attribute("href")
                    })
            except Exception as e:
                logger.error(f"浏览器爬取失败: {e}")
            finally:
                browser.close()
        return articles

if __name__ == "__main__":
    scraper = WeChatScraper()
    # 测试获取单篇文章内容
    test_url = "https://mp.weixin.qq.com/s/example" # 替换为真实链接测试
    # content = scraper.get_article_content(test_url)
    # print(content[:200] if content else "None")
