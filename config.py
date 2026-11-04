# -*- coding: utf-8 -*-
# 指定文件编码为UTF-8，确保中文注释能正确显示
"""
智能客服助手 - 配置文件

这个文件包含了应用的所有配置信息，包括API密钥、数据库路径等。
适合初学者学习的简单配置管理方案。

主要功能：
1. 管理Flask应用的基础配置
2. 管理AI API的连接配置
3. 管理数据存储路径配置
4. 支持不同环境的配置切换
"""

# 导入操作系统接口模块，用于读取环境变量和文件路径操作
import os
# 导入python-dotenv库，用于从.env文件加载环境变量
from dotenv import load_dotenv

# 加载.env文件中的环境变量到系统环境变量中
# 这样可以将敏感信息（如API密钥）从代码中分离出来
load_dotenv()

class Config:
    """
    应用配置基类
    
    这个类包含了应用运行所需的所有配置项。
    使用类的方式组织配置，便于管理和扩展。
    
    配置项说明：
    - Flask基础配置：SECRET_KEY, DEBUG等
    - AI服务配置：API密钥、模型参数等
    - 数据存储配置：文件路径、目录等
    - 网络配置：主机地址、端口等
    """
    
    # ==================== Flask应用基础配置 ====================
    
    # Flask会话加密密钥，用于保护用户会话数据的安全
    # 优先从环境变量读取，如果没有则使用默认值（生产环境必须更改）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 调试模式开关，开发时开启便于调试，生产时必须关闭
    # 从环境变量FLASK_DEBUG读取，默认为True，转换为布尔值
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # ==================== 硅基流动AI服务配置 ====================
    
    # 硅基流动API密钥，用于身份验证和API调用计费
    # 必须从环境变量获取，避免在代码中暴露敏感信息
    SILICONFLOW_API_KEY = os.environ.get('SILICONFLOW_API_KEY') or 'your-api-key-here'
    
    # 硅基流动API的基础URL地址
    # 默认使用官方API地址，可通过环境变量自定义（如使用代理）
    SILICONFLOW_BASE_URL = os.environ.get('SILICONFLOW_BASE_URL') or 'https://api.siliconflow.cn/v1'
    SILICONFLOW_TRUST_ENV = os.environ.get('SILICONFLOW_TRUST_ENV', 'False').lower() == 'true'
    
    # ==================== AI模型参数配置 ====================
    
    # 使用的AI模型名称，默认使用Qwen/Qwen2.5-7B-Instruct（免费模型）
    # 可选：Qwen/Qwen2.5-7B-Instruct, Qwen/Qwen2.5-72B-Instruct等，根据需求选择
    AI_MODEL = os.environ.get('AI_MODEL') or 'Qwen/Qwen2.5-7B-Instruct'
    
    # AI回复的创造性参数，范围0-1
    # 0表示回复更保守一致，1表示更有创造性和随机性
    # 0.7是一个平衡值，适合客服场景
    AI_TEMPERATURE = float(os.environ.get('AI_TEMPERATURE', '0.7'))
    
    # AI回复的最大token数量，直接影响API调用成本
    # 150个token大约对应100-200个中文字符，适合简洁回复
    AI_MAX_TOKENS = int(os.environ.get('AI_MAX_TOKENS', '150'))
    
    # ==================== 数据存储配置 ====================
    
    # 数据存储目录，位于项目根目录下的data文件夹
    # os.path.dirname(os.path.abspath(__file__))获取当前文件所在目录
    # 然后拼接'data'子目录作为数据存储路径
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    # 对话记录存储文件路径，使用JSON格式存储所有用户对话
    # 包含用户消息、AI回复、时间戳等完整对话信息
    CONVERSATIONS_FILE = os.path.join(DATA_DIR, 'conversations.json')
    
    # 系统配置文件路径，存储可动态调整的系统参数
    # 如欢迎语、快捷问题、AI参数等运营配置
    CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
    
    # ==================== 网络服务配置 ====================
    
    # Flask应用监听的主机地址
    # 127.0.0.1只允许本地访问，0.0.0.0允许外部访问
    HOST = os.environ.get('HOST', '127.0.0.1')
    
    # Flask应用监听的端口号
    # 5000是Flask的默认端口，生产环境通常使用80或443
    PORT = int(os.environ.get('PORT', '5000'))
    
    @staticmethod
    def init_app(app):
        """
        初始化应用配置
        
        这个方法在Flask应用启动时调用，用于执行一些初始化操作：
        1. 创建必要的目录结构
        2. 验证关键配置项
        3. 输出配置警告信息
        
        Args:
            app: Flask应用实例
        """
        # 创建数据存储目录，如果目录不存在则创建
        # exist_ok=True表示目录已存在时不会报错
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        
        # 检查API密钥是否已正确配置
        # 如果仍使用默认值，则输出警告信息提醒用户配置
        if Config.SILICONFLOW_API_KEY == 'your-api-key-here':
            print("⚠️  警告: 请在.env文件中配置SILICONFLOW_API_KEY")
            print("📝 示例: SILICONFLOW_API_KEY=sk-your-actual-api-key")
            print("🔗 获取API密钥: https://siliconflow.cn/")

# ==================== 环境特定配置类 ====================

class DevelopmentConfig(Config):
    """
    开发环境配置类
    
    继承基础配置类，重写或添加开发环境特有的配置项。
    开发环境特点：
    - 开启调试模式，便于开发调试
    - 详细的错误信息输出
    - 热重载功能
    """
    # 强制开启调试模式，覆盖父类的配置
    DEBUG = True
    
class ProductionConfig(Config):
    """
    生产环境配置类
    
    继承基础配置类，重写或添加生产环境特有的配置项。
    生产环境特点：
    - 关闭调试模式，提高安全性和性能
    - 错误信息不暴露给用户
    - 优化的性能配置
    """
    # 强制关闭调试模式，确保生产环境安全
    DEBUG = False

# ==================== 配置选择字典 ====================

# 配置映射字典，根据环境变量FLASK_ENV的值选择对应的配置类
# 使用方式：config[os.getenv('FLASK_ENV', 'default')]
config = {
    'development': DevelopmentConfig,  # 开发环境配置
    'production': ProductionConfig,    # 生产环境配置
    'default': DevelopmentConfig       # 默认使用开发环境配置
}
