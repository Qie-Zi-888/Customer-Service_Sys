# -*- coding: utf-8 -*-
"""
智能客服助手 - 服务层模块

这个包包含了应用的核心业务逻辑服务：
- ai_service.py: AI API调用服务
- storage_service.py: 数据存储服务

服务层的设计遵循单一职责原则，每个服务类只负责一个特定的业务领域。
这样的设计便于测试、维护和扩展。
"""

# 导入核心服务类，便于外部使用
from .ai_service import AIService
from .storage_service import StorageService

# 定义包的公开接口
__all__ = ['AIService', 'StorageService']