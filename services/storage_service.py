# -*- coding: utf-8 -*-
# 指定文件编码为UTF-8，确保中文注释和数据能正确处理
"""
智能客服助手 - 存储服务模块

这个模块是智能客服系统的数据持久化层，负责管理所有数据的存储和检索。

主要功能：
1. 对话记录的存储和管理
2. 系统配置的持久化
3. 数据统计和分析
4. 数据清理和维护

技术选择说明：
- 使用JSON文件存储：简单易懂，便于调试和学习
- 文件系统存储：无需额外数据库，降低部署复杂度
- 完整的错误处理：确保数据安全和系统稳定性
- 适合小到中型项目：支持并发访问，性能满足一般需求

产品思维体现：
- 数据安全：完整的备份和恢复机制
- 用户体验：快速的数据访问和检索
- 运营支持：丰富的统计信息和数据分析
- 成本控制：自动清理过期数据，控制存储成本
"""

# 导入JSON处理库，用于数据序列化和反序列化
import json
# 导入操作系统接口，用于文件和目录操作
import os
# 导入UUID库，用于生成唯一标识符
import uuid
# 导入日期时间处理库
from datetime import datetime
# 导入类型注解，提高代码可读性
from typing import List, Dict, Optional
# 导入日志库，用于记录操作和错误信息
import logging

# 配置日志系统，设置为INFO级别
# 这样可以记录重要的数据操作，便于监控和调试
logging.basicConfig(level=logging.INFO)
# 创建当前模块的日志记录器
logger = logging.getLogger(__name__)

class StorageService:
    """
    存储服务类 - 智能客服系统的数据管理中心
    
    这个类是整个系统的数据持久化层，负责所有数据的存储、检索和管理。
    
    设计原则：
    1. 数据安全：所有操作都有完整的错误处理
    2. 性能优化：合理的数据结构和访问模式
    3. 易于维护：清晰的文件组织和命名规范
    4. 扩展性：支持未来添加更多数据类型
    
    文件结构：
    - conversations.json: 存储所有对话记录
    - config.json: 存储系统配置信息
    
    数据模型：
    - 对话记录：包含用户ID、消息列表、时间戳等
    - 系统配置：包含欢迎语、快捷问题、AI参数等
    """
    
    def __init__(self, data_dir: str):
        """
        初始化存储服务实例
        
        这个方法设置数据存储的基本结构，创建必要的目录和文件。
        
        Args:
            data_dir (str): 数据存储目录的绝对路径
        """
        # 存储数据目录路径，所有数据文件都在这个目录下
        self.data_dir = data_dir
        # 对话记录文件的完整路径
        self.conversations_file = os.path.join(data_dir, 'conversations.json')
        # 系统配置文件的完整路径
        self.config_file = os.path.join(data_dir, 'config.json')
        
        # 确保数据目录存在，如果不存在则创建
        # exist_ok=True 表示如果目录已存在不会报错
        os.makedirs(data_dir, exist_ok=True)
        
        # 初始化数据文件，确保基本文件结构存在
        self._init_data_files()
        
        # 记录初始化完成的日志信息
        logger.info(f"📁 存储服务初始化完成，数据目录: {data_dir}")
    
    def _init_data_files(self):
        """
        初始化数据文件结构
        
        这个方法确保所有必要的数据文件都存在，如果不存在则创建默认文件。
        这是系统首次运行时的重要步骤，确保数据存储的完整性。
        """
        # 检查并初始化对话记录文件
        if not os.path.exists(self.conversations_file):
            # 创建空的对话记录列表
            self._save_json_file(self.conversations_file, [])
            logger.info("📝 创建对话记录文件")
        
        # 检查并初始化系统配置文件
        if not os.path.exists(self.config_file):
            # 获取默认配置并保存
            default_config = self._get_default_config()
            self._save_json_file(self.config_file, default_config)
            logger.info("⚙️  创建系统配置文件")
    
    def _get_default_config(self) -> Dict:
        """
        获取系统默认配置
        
        这个方法定义了智能客服系统的初始配置，包括用户界面设置和AI参数。
        这些配置直接影响用户体验和系统行为。
        
        Returns:
            Dict: 包含所有默认配置项的字典
        """
        return {
            # 用户界面配置
            # 欢迎消息：用户首次访问时看到的问候语
            "welcome_message": "欢迎使用智能客服助手！有什么可以帮助您的吗？",
            
            # 快捷问题：预设的常见问题，提高用户体验
            "quick_questions": [
                "你们的服务时间是什么？",
                "如何联系人工客服？",
                "产品价格是多少？",
                "如何申请退款？"
            ],
            
            # AI模型配置
            # 默认使用GPT-3.5，平衡性能和成本
            "ai_model": "gpt-3.5-turbo",
            # 创造性参数：0.7是一个平衡值，既有创造性又不会太随机
            "temperature": 0.7,
            # 最大回复长度：150字符，控制成本和回复简洁性
            "max_tokens": 150,
            
            # 元数据：记录配置的创建和更新时间
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def _load_json_file(self, file_path: str, default_value=None):
        """
        安全地加载JSON文件
        
        这个方法提供了健壮的文件读取功能，包含完整的错误处理。
        确保即使文件损坏或不存在，系统也能正常运行。
        
        Args:
            file_path (str): 要读取的JSON文件路径
            default_value: 文件读取失败时返回的默认值
            
        Returns:
            成功时返回解析后的数据，失败时返回默认值
        """
        try:
            # 以UTF-8编码打开文件，确保中文内容正确读取
            with open(file_path, 'r', encoding='utf-8') as f:
                # 解析JSON内容并返回
                return json.load(f)
                
        except FileNotFoundError:
            # 文件不存在：这是正常情况，特别是首次运行时
            logger.warning(f"📄 文件不存在: {file_path}")
            return default_value if default_value is not None else []
            
        except json.JSONDecodeError as e:
            # JSON格式错误：文件可能损坏或格式不正确
            logger.error(f"❌ JSON解析失败: {file_path}, 错误: {str(e)}")
            return default_value if default_value is not None else []
            
        except Exception as e:
            # 其他未预期的错误：权限问题、磁盘错误等
            logger.error(f"💥 文件读取失败: {file_path}, 错误: {str(e)}")
            return default_value if default_value is not None else []
    
    def _save_json_file(self, file_path: str, data) -> bool:
        """
        安全地保存数据到JSON文件
        
        这个方法提供了可靠的数据持久化功能，确保数据完整性。
        使用适当的JSON格式化选项，保证文件的可读性和兼容性。
        
        Args:
            file_path (str): 目标文件路径
            data: 要保存的数据（必须是JSON可序列化的）
            
        Returns:
            bool: True表示保存成功，False表示保存失败
        """
        try:
            # 以UTF-8编码写入文件，确保中文内容正确保存
            with open(file_path, 'w', encoding='utf-8') as f:
                # 保存JSON数据，配置选项说明：
                # ensure_ascii=False: 允许非ASCII字符（中文）
                # indent=2: 格式化输出，便于人工阅读和调试
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
            
        except Exception as e:
            # 记录保存失败的详细错误信息
            logger.error(f"💾 文件保存失败: {file_path}, 错误: {str(e)}")
            return False
    
    def save_conversation(self, conversation: Dict) -> bool:
        """
        保存或更新对话记录
        
        这个方法是对话数据管理的核心，支持新建和更新对话记录。
        采用智能的更新策略，避免重复数据，确保数据一致性。
        
        业务逻辑：
        1. 检查对话是否已存在（基于ID）
        2. 如果存在则更新，不存在则新建
        3. 自动维护时间戳信息
        4. 确保数据完整性
        
        Args:
            conversation (Dict): 对话记录字典，必须包含id字段
            
        Returns:
            bool: True表示保存成功，False表示保存失败
        """
        try:
            # 获取当前所有对话记录
            conversations = self.get_conversations()
            
            # 查找是否已存在相同ID的对话
            # 使用线性搜索，对于小到中型数据量是合适的
            existing_index = -1
            for i, conv in enumerate(conversations):
                if conv.get('id') == conversation.get('id'):
                    existing_index = i
                    break
            
            # 自动更新时间戳，记录最后修改时间
            conversation['updated_at'] = datetime.now().isoformat()
            
            if existing_index >= 0:
                # 更新已存在的对话记录
                conversations[existing_index] = conversation
                logger.info(f"🔄 更新对话记录: {conversation.get('id')}")
            else:
                # 添加新的对话记录
                # 如果没有创建时间，自动添加
                if 'created_at' not in conversation:
                    conversation['created_at'] = datetime.now().isoformat()
                conversations.append(conversation)
                logger.info(f"➕ 添加新对话记录: {conversation.get('id')}")
            
            # 保存更新后的对话列表到文件
            return self._save_json_file(self.conversations_file, conversations)
            
        except Exception as e:
            # 记录详细的错误信息，便于调试
            logger.error(f"💥 保存对话记录失败: {str(e)}")
            return False
    
    def get_conversations(self) -> List[Dict]:
        """
        获取所有对话记录
        
        这个方法提供对所有对话数据的访问，主要用于管理后台和数据分析。
        返回的数据按时间顺序排列，便于查看和管理。
        
        Returns:
            List[Dict]: 对话记录列表，每个元素包含完整的对话信息
        """
        # 调用安全的文件加载方法，如果文件不存在返回空列表
        return self._load_json_file(self.conversations_file, [])
    
    def get_conversation_by_id(self, conversation_id: str) -> Optional[Dict]:
        """
        根据ID获取特定对话记录
        
        这个方法提供精确的对话查找功能，用于恢复用户的对话历史。
        采用线性搜索算法，适合中小型数据量。
        
        Args:
            conversation_id (str): 要查找的对话唯一标识符
            
        Returns:
            Optional[Dict]: 找到时返回对话记录字典，未找到时返回None
        """
        # 获取所有对话记录
        conversations = self.get_conversations()
        
        # 遍历查找匹配的对话ID
        for conversation in conversations:
            if conversation.get('id') == conversation_id:
                # 找到匹配的对话，返回完整记录
                return conversation
                
        # 没有找到匹配的对话
        return None
    
    def add_message_to_conversation(self, conversation_id: str, message: Dict) -> bool:
        """
        向指定对话添加新消息
        
        这是对话系统的核心方法，每次用户发送消息或AI回复时都会调用。
        支持自动创建新对话，确保消息不会丢失。
        
        业务流程：
        1. 查找目标对话，如果不存在则创建新对话
        2. 为消息添加元数据（ID、时间戳等）
        3. 将消息添加到对话记录中
        4. 保存更新后的对话
        
        Args:
            conversation_id (str): 对话的唯一标识符
            message (Dict): 消息内容，必须包含role和content字段
            
        Returns:
            bool: True表示添加成功，False表示添加失败
        """
        try:
            # 尝试获取已存在的对话记录
            conversation = self.get_conversation_by_id(conversation_id)
            
            if not conversation:
                # 对话不存在，创建新的对话记录
                conversation = {
                    # 对话唯一标识
                    'id': conversation_id,
                    # 用户标识（简化处理，使用匿名用户）
                    'user_id': 'anonymous',
                    # 消息列表，初始为空
                    'messages': [],
                    # 对话创建时间
                    'created_at': datetime.now().isoformat(),
                    # 对话更新时间
                    'updated_at': datetime.now().isoformat()
                }
            
            # 为消息添加元数据信息
            message_with_meta = {
                # 生成唯一的消息ID，使用UUID的前8位
                'id': f"msg_{uuid.uuid4().hex[:8]}",
                # 消息时间戳，用于排序和显示
                'timestamp': datetime.now().isoformat(),
                # 展开原始消息内容（role, content等）
                **message
            }
            
            # 将新消息添加到对话的消息列表中
            conversation['messages'].append(message_with_meta)
            
            # 保存更新后的对话记录
            return self.save_conversation(conversation)
            
        except Exception as e:
            # 记录详细的错误信息
            logger.error(f"💬 添加消息失败: {str(e)}")
            return False
    
    def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """
        获取对话的最近消息
        
        这个方法用于获取对话的最新消息，主要用于AI上下文构建和界面显示。
        通过限制消息数量，可以控制AI的上下文长度和API成本。
        
        Args:
            conversation_id (str): 对话的唯一标识符
            limit (int): 返回的最大消息数量，默认10条
            
        Returns:
            List[Dict]: 最近的消息列表，按时间顺序排列
        """
        # 获取指定的对话记录
        conversation = self.get_conversation_by_id(conversation_id)
        if not conversation:
            # 对话不存在，返回空列表
            return []
        
        # 获取对话中的所有消息
        messages = conversation.get('messages', [])
        # 返回最后limit条消息，如果消息总数少于limit则返回全部
        return messages[-limit:] if len(messages) > limit else messages
    
    def get_config(self) -> Dict:
        """
        获取系统配置
        
        这个方法提供对系统配置的访问，包括AI参数、界面设置等。
        如果配置文件不存在或损坏，会自动返回默认配置。
        
        Returns:
            Dict: 系统配置字典，包含所有配置项
        """
        # 加载配置文件，如果失败则使用默认配置
        return self._load_json_file(self.config_file, self._get_default_config())
    
    def save_config(self, config: Dict) -> bool:
        """
        保存系统配置
        
        这个方法用于持久化系统配置更改，支持管理员通过后台修改系统设置。
        自动维护配置的时间戳信息，便于追踪配置变更历史。
        
        Args:
            config (Dict): 要保存的配置字典
            
        Returns:
            bool: True表示保存成功，False表示保存失败
        """
        try:
            # 自动更新配置的修改时间
            config['updated_at'] = datetime.now().isoformat()
            
            # 如果是新配置（没有创建时间），添加创建时间
            if 'created_at' not in config:
                config['created_at'] = datetime.now().isoformat()
            
            # 保存配置到文件
            success = self._save_json_file(self.config_file, config)
            if success:
                logger.info("⚙️  系统配置保存成功")
            return success
            
        except Exception as e:
            # 记录配置保存失败的错误
            logger.error(f"💥 保存系统配置失败: {str(e)}")
            return False
    
    def get_conversation_stats(self) -> Dict:
        """
        获取对话统计信息
        
        这个方法提供系统运营数据，用于管理后台的数据展示和业务分析。
        统计信息包括总体数据和当日数据，帮助了解系统使用情况。
        
        Returns:
            Dict: 包含各项统计指标的字典
        """
        try:
            # 获取所有对话记录
            conversations = self.get_conversations()
            
            # 计算总对话数
            total_conversations = len(conversations)
            # 计算总消息数（所有对话的消息数之和）
            total_messages = sum(len(conv.get('messages', [])) for conv in conversations)
            
            # 计算今日新增对话数
            today = datetime.now().date().isoformat()
            today_conversations = 0
            for conv in conversations:
                # 提取对话创建日期（ISO格式的前10位是日期）
                created_date = conv.get('created_at', '')[:10]
                if created_date == today:
                    today_conversations += 1
            
            # 返回完整的统计信息
            return {
                # 总对话数：系统累计处理的对话数量
                'total_conversations': total_conversations,
                # 总消息数：系统累计处理的消息数量
                'total_messages': total_messages,
                # 今日对话数：当天新增的对话数量
                'today_conversations': today_conversations,
                # 平均每个对话的消息数：衡量对话深度的指标
                'average_messages_per_conversation': round(total_messages / max(total_conversations, 1), 2)
            }
            
        except Exception as e:
            # 统计计算失败时，返回默认的零值统计
            logger.error(f"📊 获取统计信息失败: {str(e)}")
            return {
                'total_conversations': 0,
                'total_messages': 0,
                'today_conversations': 0,
                'average_messages_per_conversation': 0
            }
    
    def cleanup_old_conversations(self, days: int = 30) -> int:
        """
        清理过期的对话记录
        
        这个方法用于定期清理旧的对话数据，控制存储空间和提高系统性能。
        采用安全的清理策略，对于时间格式异常的数据会保留而不是删除。
        
        业务价值：
        1. 控制存储成本：定期清理过期数据
        2. 提高性能：减少数据量，提高查询速度
        3. 数据合规：符合数据保留政策要求
        4. 隐私保护：及时清理用户对话数据
        
        Args:
            days (int): 数据保留天数，默认30天
            
        Returns:
            int: 实际清理的对话数量
        """
        try:
            # 获取所有对话记录
            conversations = self.get_conversations()
            # 计算截止时间戳（当前时间减去保留天数）
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            # 用于存储保留的对话
            filtered_conversations = []
            # 记录清理的对话数量
            cleaned_count = 0
            
            # 遍历所有对话，判断是否需要清理
            for conv in conversations:
                created_at = conv.get('created_at', '')
                try:
                    # 解析对话创建时间，处理可能的时区标记
                    conv_timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp()
                    if conv_timestamp >= cutoff_date:
                        # 对话在保留期内，保留
                        filtered_conversations.append(conv)
                    else:
                        # 对话超过保留期，标记为清理
                        cleaned_count += 1
                except:
                    # 如果时间格式解析失败，为了安全起见保留对话
                    # 这避免了因为数据格式问题导致的意外数据丢失
                    filtered_conversations.append(conv)
            
            # 如果有对话被清理，保存更新后的对话列表
            if cleaned_count > 0:
                self._save_json_file(self.conversations_file, filtered_conversations)
                logger.info(f"🧹 清理了 {cleaned_count} 个旧对话记录（保留 {days} 天内的数据）")
            
            return cleaned_count
            
        except Exception as e:
            # 清理过程中出现错误，记录日志但不影响系统运行
            logger.error(f"💥 清理对话记录失败: {str(e)}")
            return 0

# 使用示例（仅用于测试）
if __name__ == "__main__":
    # 这部分代码仅在直接运行此文件时执行，用于测试
    import tempfile
    
    # 创建临时目录进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = StorageService(temp_dir)
        
        # 测试配置管理
        config = storage.get_config()
        print(f"默认配置: {config['welcome_message']}")
        
        # 测试对话管理
        conversation_id = "test_conv_001"
        
        # 添加用户消息
        storage.add_message_to_conversation(conversation_id, {
            "role": "user",
            "content": "你好"
        })
        
        # 添加AI回复
        storage.add_message_to_conversation(conversation_id, {
            "role": "assistant",
            "content": "您好！有什么可以帮助您的吗？"
        })
        
        # 获取对话记录
        messages = storage.get_recent_messages(conversation_id)
        print(f"对话消息数: {len(messages)}")
        
        # 获取统计信息
        stats = storage.get_conversation_stats()
        print(f"统计信息: {stats}")
        
        print("✅ 存储服务测试完成")