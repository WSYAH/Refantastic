"""LLM 客户端"""
from typing import Dict, Any, Optional, List
from loguru import logger
import httpx
from openai import AsyncOpenAI

from config import get_settings


class LLMClient:
    """LLM 客户端 - 支持多种大语言模型"""
    
    def __init__(self):
        self.settings = get_settings()
        self.config = self.settings.config
        
        llm_config = self.config.get("version_config", {}).get("llm_config", {})
        
        # DeepSeek 配置
        self.llm_type = llm_config.get("llm_type", "openai").lower()
        self.deepseek_url = llm_config.get("llm_url", "")
        self.deepseek_key = llm_config.get("llm_key", "")
        self.model_name = llm_config.get("llm_model_name", "default")
        
        # 初始化客户端
        self._init_client()
        
        logger.info(f"LLM客户端初始化完成: {self.llm_type}")
    
    def _init_client(self):
        if self.llm_type == "deepseek":
            self.client = AsyncOpenAI(
                api_key=self.deepseek_key,
                base_url=self.deepseek_url,
                timeout=60.0
            )
        else:
            # 默认使用 OpenAI 兼容接口
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                timeout=60.0
            )
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        model: Optional[str] = None,
        system_message: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        生成文本
        
        Args:
            prompt: 提示词
            max_tokens: 最大生成长度
            temperature: 温度参数 (0-2)
            model: 模型名称
            system_message: 系统消息
            stream: 是否流式输出
        
        Returns:
            {
                "content": str,  # 生成的内容
                "model": str,  # 使用的模型
                "usage": {  # token使用情况
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int
                }
            }
        """
        try:
            # 构建消息
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # 选择模型
            if model is None:
                if self.llm_type == "deepseek":
                    model = self.model_name
                else:
                    model = "gpt-3.5-turbo"
            
            logger.info(f"调用LLM生成: model={model}, max_tokens={max_tokens}, temperature={temperature}")
            # 调用API
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream
            )
            
            if stream:
                # 流式输出
                return response
            else:
                # 非流式输出
                content = response.choices[0].message.content
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                logger.info(f"生成完成: tokens={usage['total_tokens']}")
                
                return {
                    "content": content,
                    "model": response.model,
                    "usage": usage
                }
        
        except Exception as e:
            logger.error(f"LLM生成失败: {str(e)}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        model: Optional[str] = None,
        system_message: Optional[str] = None
    ):
        """
        流式生成文本
        
        Yields:
            str: 生成的文本片段
        """
        try:
            # 构建消息
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # 选择模型
            if model is None:
                if self.llm_type == "deepseek":
                    model = self.model_name
                else:
                    model = "gpt-3.5-turbo"
            
            logger.info(f"调用LLM流式生成: model={model}")
            
            # 调用API
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"LLM流式生成失败: {str(e)}")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        多轮对话
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            max_tokens: 最大生成长度
            temperature: 温度参数
            model: 模型名称
        """
        try:
            # 选择模型
            if model is None:
                if self.llm_type == "deepseek":
                    model = self.model_name
                else:
                    model = "gpt-3.5-turbo"
            
            logger.info(f"调用LLM对话: model={model}, messages={len(messages)}")
            
            # 调用API
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return {
                "content": content,
                "model": response.model,
                "usage": usage
            }
        
        except Exception as e:
            logger.error(f"LLM对话失败: {str(e)}")
            raise
    
    async def embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        文本嵌入
        
        Args:
            text: 输入文本
            model: 嵌入模型名称
        
        Returns:
            向量列表
        """
        try:
            if model is None:
                model = "text-embedding-ada-002"
            
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"文本嵌入失败: {str(e)}")
            raise
    
    async def batch_embedding(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        批量文本嵌入
        
        Args:
            texts: 文本列表
            model: 嵌入模型
            batch_size: 批次大小
        """
        try:
            if model is None:
                model = "text-embedding-ada-002"
            
            embeddings = []
            
            # 分批处理
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = await self.client.embeddings.create(
                    model=model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
                logger.info(f"已处理 {len(embeddings)}/{len(texts)} 个文本")
            
            return embeddings
        
        except Exception as e:
            logger.error(f"批量文本嵌入失败: {str(e)}")
            raise
    
    async def get_models(self) -> List[str]:
        """获取可用的模型列表"""
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"获取模型列表失败: {str(e)}")
            return []


# 单例
_llm_client = None


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
