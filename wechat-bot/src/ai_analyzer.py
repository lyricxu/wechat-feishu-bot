import os
import json
from openai import OpenAI
from loguru import logger

class AIAnalyzer:
    def __init__(self, model="gpt-4.1-mini"):
        # 系统会自动从环境变量读取 OPENAI_API_KEY
        self.client = OpenAI()
        self.model = model

    def analyze_article(self, title, content):
        """
        AI 自动阅读文章并给出概要与评分
        """
        if not content or len(content) < 100:
            logger.warning(f"文章内容太短，跳过分析: {title}")
            return None

        prompt = f"""
        你是一位专业的资讯分析师。请阅读以下文章，并按要求输出分析结果。

        文章标题：{title}
        文章正文：{content[:3000]} # 限制长度防止超限

        请按以下 JSON 格式输出：
        {{
            "summary": "150字以内的文章核心概要",
            "score": 0-100的整数（基于信息密度、逻辑严密性和行业相关度综合评分）,
            "reason": "评分的简要理由",
            "keywords": ["关键词1", "关键词2", "关键词3"]
        }}
        注意：仅输出 JSON，不要有任何其他文字。
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的资讯分析助手，擅长精炼内容并客观评分。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI 分析完成: {title}, 得分: {result.get('score')}")
            return result
        except Exception as e:
            logger.error(f"AI 分析失败: {e}")
            return None

if __name__ == "__main__":
    analyzer = AIAnalyzer()
    # 简单测试
    test_title = "测试文章"
    test_content = "这是一篇关于人工智能未来发展的文章，探讨了通用人工智能的可能性..."
    # result = analyzer.analyze_article(test_title, test_content)
    # print(result)
