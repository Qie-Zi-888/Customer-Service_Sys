# -*- coding: utf-8 -*-
# 指定文件编码为UTF-8，确保中文注释能正确显示
"""
智能客服助手 - AI服务模块

这个模块是整个智能客服系统的核心，负责与硅基流动AI API进行交互。
主要功能包括：
1. 封装AI API调用逻辑
2. 处理网络异常和超时
3. 管理对话上下文
4. 提供友好的错误处理

设计原则：
- 简单易懂：适合初学者学习API调用
- 健壮性：完整的错误处理机制
- 可扩展：便于添加新的AI服务提供商
- 成本控制：合理的参数设置控制API调用成本
"""

# 导入HTTP请求库，用于调用外部API
import requests
# 导入JSON处理库，用于解析API响应
import json
# 导入日志库，用于记录运行状态和错误信息
import logging
# 导入类型注解，提高代码可读性和IDE支持
from typing import List, Dict, Optional

# 配置日志系统，设置日志级别为INFO
# 这样可以看到重要的运行信息，但不会过于冗余
logging.basicConfig(level=logging.INFO)
# 创建当前模块的日志记录器
logger = logging.getLogger(__name__)

class AIService:
    """
    AI服务类 - 智能客服系统的大脑
    
    这个类封装了所有与AI API交互的逻辑，是整个系统的核心组件。
    
    主要职责：
    1. 管理API连接和认证
    2. 构建和发送API请求
    3. 解析和处理API响应
    4. 提供错误恢复机制
    5. 记录操作日志便于监控
    
    设计特点：
    - 单一职责：只负责AI API相关操作
    - 错误友好：所有异常都有友好的用户提示
    - 可配置：支持不同的模型和参数
    - 可测试：提供连接测试功能
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.siliconflow.cn/v1",
        trust_env: bool = False,
    ):
        """
        初始化AI服务实例
        
        这个方法设置API连接的基本参数，包括认证信息和服务地址。
        
        Args:
            api_key (str): 硅基流动API密钥，用于身份验证和计费
            base_url (str): API服务的基础URL地址，默认使用官方地址
        """
        # 存储API密钥，用于后续的身份验证
        self.api_key = api_key
        # 存储API基础URL，支持使用不同的服务端点
        self.base_url = base_url
        self.last_error = None
        self.session = requests.Session()
        self.session.trust_env = trust_env
        # 构建HTTP请求头，包含认证和内容类型信息
        self.headers = {
            # Bearer Token是API认证的标准方式
            "Authorization": f"Bearer {api_key}",
            # 指定请求内容为JSON格式
            "Content-Type": "application/json"
        }
        
        # 验证API密钥是否已正确配置
        # 这是一个重要的安全检查，避免使用默认值导致的问题
        if not api_key or api_key == "your-api-key-here":
            logger.warning("⚠️  AI服务初始化警告: API密钥未正确配置，请检查.env文件")
    
    def get_chat_response(self, messages: List[Dict], model: str = "gpt-3.5-turbo", 
                         temperature: float = 0.7, max_tokens: int = 150) -> str:
        """
        获取AI聊天回复 - 核心业务方法
        
        这是整个AI服务的核心方法，负责与AI API交互获取智能回复。
        
        参数说明：
        - messages: 对话历史，AI会基于这些信息生成回复
        - model: AI模型选择，影响回复质量和成本
        - temperature: 创造性参数，0=保守，1=创新
        - max_tokens: 回复长度限制，直接影响API成本
        
        Args:
            messages (List[Dict]): 对话消息列表，格式为 [{"role": "user", "content": "消息内容"}]
            model (str): 使用的AI模型名称，如gpt-3.5-turbo
            temperature (float): 控制回复的随机性，0-1之间，值越高越随机
            max_tokens (int): 最大回复长度，控制成本和回复详细程度
            
        Returns:
            str: AI的回复内容，如果出错则返回友好的错误提示
        """
        self.last_error = None

        try:
            # 构建符合API规范的请求数据结构
            request_data = {
                # 指定使用的AI模型
                "model": model,
                # 添加系统提示后的完整消息列表
                "messages": self._build_messages_with_system_prompt(messages),
                # 控制回复的创造性程度
                "temperature": temperature,
                # 限制回复的最大长度（成本控制）
                "max_tokens": max_tokens
            }
            
            # 记录API调用信息，便于监控和调试
            logger.info(f"🤖 发送AI请求: {len(messages)}条消息, 模型: {model}")
            
            # 发送HTTP POST请求到AI API
            response = self.session.post(
                # 拼接完整的API端点URL
                f"{self.base_url}/chat/completions",
                # 传递认证和内容类型头
                headers=self.headers,
                # 将请求数据序列化为JSON
                json=request_data,
                # 设置30秒超时，避免长时间等待影响用户体验
                timeout=30
            )
            
            # 检查HTTP响应状态码
            # 200表示请求成功，其他状态码表示出现错误
            if response.status_code != 200:
                logger.error(f"❌ API请求失败: HTTP {response.status_code}")
                logger.error(f"📄 响应内容: {response.text}")
                return self._fail(f"API请求失败 (状态码: {response.status_code})")
            
            # 解析API返回的JSON响应数据
            response_data = response.json()
            
            # 从响应中提取AI生成的回复内容
            # API响应格式: {"choices": [{"message": {"content": "回复内容"}}]}
            if "choices" in response_data and len(response_data["choices"]) > 0:
                # 获取第一个选择项中的消息内容
                ai_message = response_data["choices"][0]["message"]["content"]
                logger.info("✅ AI回复获取成功")
                # 去除回复内容前后的空白字符
                return ai_message.strip()
            else:
                # API响应格式不符合预期，记录错误并返回友好提示
                logger.error("❌ API响应格式异常: 缺少choices字段")
                return self._fail("API响应格式异常")
                
        # 处理各种可能的异常情况，确保系统稳定运行
        except requests.exceptions.Timeout as e:
            # 请求超时异常：API服务响应太慢
            logger.error(f"⏰ API请求超时: {str(e)}")
            return self._fail("请求超时，请稍后再试")
            
        except requests.exceptions.ConnectionError as e:
            # 连接错误异常：网络问题或API服务不可用
            logger.error(f"🌐 API连接失败: {str(e)}")
            return self._fail("网络连接失败，请检查网络")
            
        except json.JSONDecodeError:
            # JSON解析错误：API返回的不是有效的JSON格式
            logger.error("📝 API响应JSON解析失败")
            return self._fail("服务器响应格式错误")
            
        except Exception as e:
            # 捕获所有其他未预期的异常
            logger.error(f"💥 AI服务异常: {str(e)}")
            return self._fail("服务暂时不可用，请稍后再试")
    
    def _build_messages_with_system_prompt(self, messages: List[Dict]) -> List[Dict]:
        """
        构建包含系统提示的完整消息列表
        
        系统提示（System Prompt）是AI对话的关键，它定义了AI的角色、行为准则和回复风格。
        这个方法将系统提示与用户对话历史合并，形成完整的上下文。
        
        Args:
            messages (List[Dict]): 用户对话消息列表，不包含系统提示
            
        Returns:
            List[Dict]: 包含系统提示的完整消息列表，系统提示在最前面
        """
        # 定义AI助手的角色和行为准则
        # 这是整个客服系统服务质量的核心定义
        system_message = {
            # 角色标识：system表示这是系统级别的指令
            "role": "system",
            # 详细的行为准则和服务标准
            "content": (
                "你是一个专业友好的智能客服助手。请严格遵循以下服务准则：\n"
                "1. 用简洁明了的语言回答用户问题，避免冗长复杂的表述\n"
                "2. 始终保持礼貌和专业的态度，体现优质的服务品质\n"
                "3. 如果不确定答案，诚实地告知用户，不要编造信息\n"
                "4. 主动提供有用的建议和解决方案，展现主动服务精神\n"
                "5. 回复长度控制在150字以内，确保信息简洁有效\n"
                "6. 遇到复杂问题时，建议用户联系人工客服获得更好的帮助"
            )
        }
        
        # 将系统提示放在消息列表的最前面
        # 这样AI会首先读取角色定义，然后基于这个角色回复用户
        return [system_message] + messages
    
    def _get_error_response(self, error_message: str) -> str:
        """
        生成用户友好的错误回复
        
        当AI服务出现任何异常时，这个方法将技术错误转换为用户能理解的友好提示。
        这是用户体验设计的重要组成部分，确保即使出错也能保持专业形象。
        
        设计原则：
        1. 承认问题但不推卸责任
        2. 提供明确的后续行动建议
        3. 保持品牌的专业形象
        4. 避免暴露技术细节给用户
        
        Args:
            error_message (str): 内部错误信息，用于日志记录
            
        Returns:
            str: 面向用户的友好错误回复
        """
        # 构建专业而友好的错误回复
        # 包含道歉、问题说明、解决建议三个要素
        return f"😔 抱歉，我现在遇到了一些技术问题：{error_message}。\n\n" \
               f"🔄 请您稍后再试，或者联系我们的人工客服获得immediate帮助。\n" \
               f"📞 我们会尽快解决这个问题，感谢您的耐心理解！"

    def _fail(self, error_message: str) -> str:
        self.last_error = error_message
        return self._get_error_response(error_message)

    def has_error(self) -> bool:
        return self.last_error is not None
    
    def test_connection(
        self,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 32,
    ) -> bool:
        """
        测试AI API连接是否正常
        
        这个方法用于系统启动时或健康检查时验证AI服务是否可用。
        通过发送一个简单的测试消息来验证整个调用链路。
        
        测试逻辑：
        1. 发送简单的问候消息
        2. 检查是否收到正常回复
        3. 如果回复以"抱歉"开头，说明出现了错误
        
        Returns:
            bool: True表示连接正常，False表示连接失败
        """
        try:
            # 构建简单的测试消息
            test_messages = [{"role": "user", "content": "你好"}]
            # 调用AI服务获取回复
            self.get_chat_response(
                test_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            is_healthy = not self.has_error()
            
            if is_healthy:
                logger.info("✅ AI服务连接测试通过")
            else:
                logger.warning(f"⚠️  AI服务连接测试失败：{self.last_error}")
                
            return is_healthy
            
        except Exception as e:
            # 捕获测试过程中的任何异常
            logger.error(f"❌ API连接测试失败: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict:
        """
        获取AI模型的基本信息
        
        这个方法返回当前支持的AI模型信息，包括默认模型、支持的模型列表等。
        主要用于系统配置和用户界面显示。
        
        注意：这是一个静态信息方法，实际的模型支持情况可能需要
        根据硅基流动API的最新文档进行更新。
        
        Returns:
            Dict: 包含模型信息的字典
                - default_model: 默认使用的模型
                - supported_models: 支持的模型列表
                - max_tokens: 最大token限制
                - cost_info: 成本相关信息
        """
        # 返回模型配置信息
        # 这些信息可以用于系统配置界面和成本估算
        return {
            # 默认模型：平衡性能和成本的选择
            "default_model": "gpt-3.5-turbo",
            # 支持的模型列表：根据实际API支持情况配置
            "supported_models": ["gpt-3.5-turbo", "gpt-4"],
            # 最大token限制：影响单次对话的长度
            "max_tokens": 4096,
            # 成本信息：帮助用户了解使用成本
            "cost_info": {
                "gpt-3.5-turbo": "经济型选择，适合大多数客服场景",
                "gpt-4": "高质量选择，适合复杂问题处理"
            }
        }

# 使用示例（仅用于测试）
if __name__ == "__main__":
    # 这部分代码仅在直接运行此文件时执行，用于测试
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 创建AI服务实例
    ai_service = AIService(
        api_key=os.getenv("SILICONFLOW_API_KEY", "your-api-key-here")
    )
    
    # 测试API连接
    if ai_service.test_connection():
        print("✅ AI服务连接正常")
        
        # 测试对话
        test_messages = [
            {"role": "user", "content": "你好，我想了解你们的服务"}
        ]
        
        response = ai_service.get_chat_response(test_messages)
        print(f"AI回复: {response}")
    else:
        print("❌ AI服务连接失败，请检查API密钥配置")
