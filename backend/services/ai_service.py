"""
AI服务模块

封装DeepSeek API的调用，提供行程生成和聊天功能。
"""
from openai import OpenAI
import httpx
from typing import List, Dict, Any, Optional
import logging
from config import Config

logger = logging.getLogger(__name__)


class AIService:
    """DeepSeek AI服务类"""

    def __init__(self, api_key: str = None, timeout: int = None):
        """
        初始化AI服务。

        Args:
            api_key: DeepSeek API密钥，默认从配置读取
            timeout: 请求超时时间（秒），默认从配置读取
        """
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.timeout = timeout or Config.DEEPSEEK_TIMEOUT
        self.model = Config.AI_CONFIG['model']
        self.temperature = Config.AI_CONFIG['temperature']

        self._client = None

        if not self.api_key or self.api_key == 'sk-d5826bdc14774b718b056a376bf894e0':
            logger.warning("DeepSeek API key not configured or using default key")

    @property
    def client(self) -> OpenAI:
        """
        获取DeepSeek客户端（懒加载）。

        Returns:
            OpenAI: DeepSeek客户端实例
        """
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        return self._client

    def is_available(self) -> bool:
        """
        检查AI服务是否可用。

        Returns:
            bool: 服务是否可用
        """
        return (
            self.api_key and
            self.api_key != ''
        )

    def generate_itinerary(
        self,
        prompt: str,
        days: int,
        max_tokens: int = None
    ) -> str:
        """
        生成旅游行程。

        Args:
            prompt: 行程生成提示词
            days: 行程天数
            max_tokens: 最大token数，默认根据天数计算

        Returns:
            str: AI生成的行程JSON字符串

        Raises:
            Exception: API调用失败时抛出
        """
        if not self.is_available():
            raise ValueError("AI service not available: API key not configured")

        # 计算max_tokens
        if max_tokens is None:
            tokens_per_day = Config.AI_CONFIG['tokens_per_day']
            base_tokens = Config.AI_CONFIG['base_tokens']
            max_tokens_limit = Config.AI_CONFIG['max_tokens']
            max_tokens = min(days * tokens_per_day + base_tokens, max_tokens_limit)

        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的旅游规划助手，帮助用户制定最佳的旅游路线和行程安排。"
                               "请以友好、专业的语气回答问题，并根据用户的兴趣、时间和预算提供建议。"
                               "必须严格按照指定的JSON格式返回结果。"
                               "**关键：必须确保返回完整的JSON结构，所有括号和引号都必须正确闭合。**"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                temperature=self.temperature,
                max_tokens=max_tokens
            )

            ai_response = response.choices[0].message.content
            logger.info(f"AI response received, length: {len(ai_response)}")

            return ai_response

        except Exception as e:
            logger.error(f"Error generating itinerary: {str(e)}")
            raise

    def chat(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        system_prompt: str = None,
        max_tokens: int = 10000
    ) -> str:
        """
        AI聊天对话。

        Args:
            message: 用户消息
            conversation_history: 对话历史
            system_prompt: 系统提示词
            max_tokens: 最大token数

        Returns:
            str: AI回复内容

        Raises:
            Exception: API调用失败时抛出
        """
        if not self.is_available():
            return "抱歉，AI助手当前不可用，因为未配置API密钥。请在后端设置DEEPSEEK_API_KEY环境变量。"

        try:
            # 构建消息列表
            messages = []

            # 添加系统提示词
            if system_prompt is None:
                system_prompt = "你是一个专业的旅游规划助手，帮助用户制定最佳的旅游路线和行程安排。" \
                               "请以友好、专业的语气回答问题，并根据用户的兴趣、时间和预算提供建议。"

            messages.append({"role": "system", "content": system_prompt})

            # 添加历史对话
            if conversation_history:
                for msg in conversation_history:
                    messages.append({"role": msg["role"], "content": msg["content"]})

            # 添加当前消息
            messages.append({"role": "user", "content": message})

            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                temperature=self.temperature,
                max_tokens=max_tokens
            )

            ai_response = response.choices[0].message.content
            return ai_response

        except Exception as e:
            logger.error(f"AI chat error: {str(e)}")
            raise

    def extract_json_from_response(self, response: str) -> str:
        """
        从AI响应中提取JSON部分。

        Args:
            response: AI返回的完整响应

        Returns:
            str: 提取的JSON字符串

        Note:
            该方法移到了utils/json_fixer.py，此处保留以便向后兼容
        """
        import re
        json_match = re.search(r'\{.*\}|\[.*\]', response, re.DOTALL)
        if json_match:
            return json_match.group()
        return response
