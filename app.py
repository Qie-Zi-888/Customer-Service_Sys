# -*- coding: utf-8 -*-
# 指定文件编码为UTF-8，确保中文注释和字符串能正确处理
"""
智能客服助手 - Flask主应用

这是整个智能客服系统的核心文件，采用Flask框架构建Web应用。
本文件展示了如何将AI服务、数据存储、用户界面整合成一个完整的产品。

系统架构特点：
1. MVC架构：清晰的模型-视图-控制器分离
2. 服务化设计：AI服务和存储服务独立封装
3. RESTful API：标准的HTTP接口设计
4. 会话管理：基于Flask Session的用户状态管理
5. 错误处理：完整的异常捕获和用户友好提示

主要功能模块：
1. 客服对话页面 - 用户与AI进行实时对话的前端界面
2. 消息发送API - 处理用户消息并返回AI回复的核心接口
3. 管理后台页面 - 查看对话记录和系统配置的管理界面
4. 配置管理API - 动态管理系统设置的后台接口
5. 健康检查API - 监控系统运行状态的运维接口

产品思维体现：
- 用户体验：简洁的界面设计，快速的响应时间
- 数据驱动：完整的对话记录和统计分析
- 运营支持：管理后台和系统监控
- 可扩展性：模块化设计，便于功能扩展
"""

# 导入Flask核心组件
from flask import Flask, render_template, request, jsonify, session
# 导入UUID库，用于生成唯一标识符
import uuid
# 导入日志库，用于记录系统运行状态
import logging
# 导入日期时间处理库
from datetime import datetime

# 导入项目配置模块
from config import config
# 导入业务服务模块
from services import AIService, StorageService

# 配置应用日志系统
# 设置日志格式，包含时间、模块名、级别和消息内容
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# 创建当前模块的日志记录器
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    """
    应用工厂函数 - Flask应用的创建和配置中心
    
    这个函数采用工厂模式创建Flask应用，便于在不同环境下使用不同配置。
    工厂模式的优势：
    1. 便于单元测试：可以创建测试专用的应用实例
    2. 支持多环境：开发、测试、生产环境使用不同配置
    3. 延迟初始化：在需要时才创建应用实例
    4. 配置隔离：避免全局配置污染
    
    Args:
        config_name (str): 配置环境名称，支持 'development', 'production', 'default'
        
    Returns:
        Flask: 完全配置好的Flask应用实例
    """
    # 创建Flask应用实例
    # __name__参数帮助Flask确定应用的根路径，用于查找模板和静态文件
    app = Flask(__name__)
    
    # 从配置对象加载应用配置
    # 这种方式比直接设置配置项更安全和规范
    app.config.from_object(config[config_name])
    # 调用配置类的初始化方法，执行特定环境的初始化逻辑
    config[config_name].init_app(app)
    
    # 初始化AI服务实例
    # 从应用配置中获取API密钥和服务地址
    ai_service = AIService(
        api_key=app.config['SILICONFLOW_API_KEY'],  # 硅基流动API密钥
        base_url=app.config['SILICONFLOW_BASE_URL'],  # API服务地址
        trust_env=app.config['SILICONFLOW_TRUST_ENV']
    )
    
    # 初始化存储服务实例
    # 使用配置中指定的数据目录
    storage_service = StorageService(app.config['DATA_DIR'])
    
    # 记录应用初始化完成
    logger.info("🚀 智能客服助手应用初始化完成")
    
    # ==================== 路由定义 ====================
    
    @app.route('/')
    def index():
        """
        首页路由 - 客服对话页面
        
        这是用户访问系统的主要入口，提供与AI助手对话的界面。
        
        业务逻辑：
        1. 会话管理：为新用户创建唯一的对话ID
        2. 数据加载：获取系统配置和历史消息
        3. 页面渲染：将数据传递给前端模板
        
        用户体验考虑：
        - 自动会话创建：用户无需手动操作
        - 历史消息恢复：刷新页面不丢失对话
        - 错误友好处理：出错时显示友好提示
        
        Returns:
            str: 渲染的客服对话HTML页面
        """
        try:
            # 会话管理：为每个新访问者生成唯一的对话标识
            if 'conversation_id' not in session:
                # 生成格式：conv_xxxxxxxx（8位随机字符）
                session['conversation_id'] = f"conv_{uuid.uuid4().hex[:8]}"
                logger.info(f"👤 新会话创建: {session['conversation_id']}")
            
            # 获取系统配置数据
            # 包括欢迎语、快捷问题、AI参数等
            config_data = storage_service.get_config()
            
            # 获取当前对话的历史消息
            # 限制为20条，平衡用户体验和页面加载速度
            messages = storage_service.get_recent_messages(
                session['conversation_id'], 
                limit=20  # 显示最近20条消息，避免页面过长
            )
            
            # 渲染客服对话页面模板
            # 传递配置、消息历史和会话ID给前端
            return render_template('chat.html', 
                                 config=config_data,  # 系统配置
                                 messages=messages,    # 历史消息
                                 conversation_id=session['conversation_id'])  # 会话ID
                                 
        except Exception as e:
            # 记录详细错误信息，便于调试
            logger.error(f"❌ 首页加载失败: {str(e)}")
            # 返回用户友好的错误页面
            return render_template('error.html', 
                                 error_message="页面加载失败，请刷新重试"), 500
    
    @app.route('/send_message', methods=['POST'])
    def send_message():
        """
        发送消息API - 系统的核心业务接口
        
        这是整个智能客服系统最重要的接口，处理用户与AI的交互流程。
        
        业务流程：
        1. 请求验证：检查数据格式和内容有效性
        2. 会话管理：确保对话连续性
        3. 消息存储：保存用户输入到数据库
        4. 上下文构建：获取历史消息作为AI上下文
        5. AI调用：发送请求到AI服务获取回复
        6. 结果存储：保存AI回复到数据库
        7. 响应返回：将结果返回给前端
        
        请求格式:
        {
            "message": "用户输入的消息内容",
            "conversation_id": "对话ID（可选）"
        }
        
        响应格式:
        {
            "success": true,
            "data": {
                "ai_response": "AI的回复内容",
                "conversation_id": "对话ID",
                "timestamp": "时间戳"
            }
        }
        
        Returns:
            JSON: 包含AI回复和状态信息的响应
        """
        try:
            # 第一步：获取并验证请求数据
            data = request.get_json()
            
            # 检查请求数据的基本格式
            if not data or 'message' not in data:
                return jsonify({
                    'success': False,
                    'error': '请求数据格式错误，缺少message字段'
                }), 400
            
            # 清理和验证用户消息内容
            user_message = data['message'].strip()
            if not user_message:
                return jsonify({
                    'success': False,
                    'error': '消息内容不能为空'
                }), 400
            
            # 第二步：会话管理 - 获取或创建对话ID
            conversation_id = data.get('conversation_id') or session.get('conversation_id')
            if not conversation_id:
                # 如果没有对话ID，创建新的对话
                conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
                session['conversation_id'] = conversation_id
            
            # 记录消息处理开始（截取前50字符避免日志过长）
            logger.info(f"💬 处理消息: {conversation_id} - {user_message[:50]}...")
            
            # 第三步：保存用户消息到数据库
            user_msg_saved = storage_service.add_message_to_conversation(
                conversation_id, 
                {
                    'role': 'user',      # 标记为用户消息
                    'content': user_message  # 消息内容
                }
            )
            
            # 检查用户消息是否保存成功（非阻塞性检查）
            if not user_msg_saved:
                logger.error("⚠️  用户消息保存失败")
            
            # 第四步：构建AI上下文 - 获取对话历史
            recent_messages = storage_service.get_recent_messages(
                conversation_id, 
                limit=5  # 只发送最近5条消息给AI，平衡上下文和成本
            )
            
            # 转换消息格式为AI API需要的标准格式
            ai_messages = []
            for msg in recent_messages:
                ai_messages.append({
                    'role': msg['role'],        # 角色：user或assistant
                    'content': msg['content']   # 消息内容
                })
            
            # 第五步：获取系统配置，用于AI调用参数
            config_data = storage_service.get_config()
            
            # 第六步：调用AI服务获取智能回复
            ai_response = ai_service.get_chat_response(
                messages=ai_messages,  # 对话历史上下文
                model=config_data.get('ai_model', 'gpt-3.5-turbo'),  # AI模型
                temperature=config_data.get('temperature', 0.7),      # 创造性参数
                max_tokens=config_data.get('max_tokens', 150)         # 回复长度限制
            )

            if ai_service.has_error():
                logger.error(f"AI服务调用失败: {ai_service.last_error}")
                return jsonify({
                    'success': False,
                    'error': ai_service.last_error,
                    'data': {
                        'conversation_id': conversation_id,
                        'timestamp': datetime.now().isoformat()
                    }
                }), 503
            
            # 第七步：保存AI回复到数据库
            ai_msg_saved = storage_service.add_message_to_conversation(
                conversation_id,
                {
                    'role': 'assistant',  # 标记为AI助手消息
                    'content': ai_response   # AI回复内容
                }
            )
            
            # 检查AI消息是否保存成功（非阻塞性检查）
            if not ai_msg_saved:
                logger.error("⚠️  AI消息保存失败")
            
            # 第八步：返回成功响应给前端
            return jsonify({
                'success': True,
                'data': {
                    'ai_response': ai_response,           # AI的回复内容
                    'conversation_id': conversation_id,   # 对话ID
                    'timestamp': datetime.now().isoformat()  # 响应时间戳
                }
            })
            
        except Exception as e:
            # 捕获所有异常，记录详细错误信息
            logger.error(f"💥 发送消息失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': '服务器内部错误，请稍后再试'
            }), 500
    
    @app.route('/admin')
    def admin():
        """
        管理后台页面
        
        显示对话记录、系统配置和统计信息的管理界面。
        
        Returns:
            str: 渲染的管理后台HTML页面
        """
        try:
            # 获取对话统计信息
            stats = storage_service.get_conversation_stats()
            
            # 获取最近的对话记录
            conversations = storage_service.get_conversations()
            
            # 按更新时间倒序排列，显示最新的对话
            conversations.sort(
                key=lambda x: x.get('updated_at', ''), 
                reverse=True
            )
            
            # 只显示最近50个对话，避免页面过长
            recent_conversations = conversations[:50]
            
            # 获取系统配置
            config_data = storage_service.get_config()
            
            return render_template('admin.html',
                                 stats=stats,
                                 conversations=recent_conversations,
                                 config=config_data)
                                 
        except Exception as e:
            logger.error(f"管理后台加载失败: {str(e)}")
            return render_template('error.html',
                                 error_message="管理后台加载失败，请刷新重试"), 500
    
    @app.route('/admin/conversations', methods=['GET'])
    def get_conversations():
        """
        获取对话记录API
        
        返回所有对话记录的JSON数据，支持分页和筛选。
        
        查询参数:
        - page: 页码（默认1）
        - limit: 每页数量（默认20）
        - date: 日期筛选（YYYY-MM-DD格式）
        
        Returns:
            JSON: 对话记录列表和分页信息
        """
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 20))
            date_filter = request.args.get('date')
            
            # 获取所有对话
            conversations = storage_service.get_conversations()
            
            # 日期筛选
            if date_filter:
                filtered_conversations = []
                for conv in conversations:
                    created_date = conv.get('created_at', '')[:10]
                    if created_date == date_filter:
                        filtered_conversations.append(conv)
                conversations = filtered_conversations
            
            # 按时间倒序排列
            conversations.sort(
                key=lambda x: x.get('updated_at', ''),
                reverse=True
            )
            
            # 分页处理
            total = len(conversations)
            start = (page - 1) * limit
            end = start + limit
            page_conversations = conversations[start:end]
            
            return jsonify({
                'success': True,
                'data': {
                    'conversations': page_conversations,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total,
                        'pages': (total + limit - 1) // limit
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"获取对话记录失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': '获取对话记录失败'
            }), 500
    
    @app.route('/admin/config', methods=['GET', 'POST'])
    def manage_config():
        """
        系统配置管理API
        
        GET: 获取当前系统配置
        POST: 更新系统配置
        
        Returns:
            JSON: 配置数据或操作结果
        """
        if request.method == 'GET':
            try:
                config_data = storage_service.get_config()
                return jsonify({
                    'success': True,
                    'data': config_data
                })
            except Exception as e:
                logger.error(f"获取配置失败: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': '获取配置失败'
                }), 500
        
        elif request.method == 'POST':
            try:
                # 获取新配置数据
                new_config = request.get_json()
                
                if not new_config:
                    return jsonify({
                        'success': False,
                        'error': '配置数据不能为空'
                    }), 400
                
                # 验证必要字段
                required_fields = ['welcome_message', 'quick_questions']
                for field in required_fields:
                    if field not in new_config:
                        return jsonify({
                            'success': False,
                            'error': f'缺少必要字段: {field}'
                        }), 400
                
                # 保存配置
                success = storage_service.save_config(new_config)
                
                if success:
                    logger.info("系统配置更新成功")
                    return jsonify({
                        'success': True,
                        'message': '配置更新成功'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': '配置保存失败'
                    }), 500
                    
            except Exception as e:
                logger.error(f"更新配置失败: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': '更新配置失败'
                }), 500
    
    @app.route('/health')
    def health_check():
        """
        健康检查API
        
        用于检查应用和各个服务的运行状态。
        
        Returns:
            JSON: 系统健康状态信息
        """
        try:
            # 检查存储服务
            storage_status = True
            config_data = {}
            try:
                config_data = storage_service.get_config()
            except:
                storage_status = False

            # 检查AI服务连接
            ai_status = ai_service.test_connection(
                model=config_data.get('ai_model', app.config['AI_MODEL']),
                temperature=config_data.get('temperature', app.config['AI_TEMPERATURE']),
                max_tokens=min(config_data.get('max_tokens', app.config['AI_MAX_TOKENS']), 32)
            )
            
            return jsonify({
                'status': 'healthy' if ai_status and storage_status else 'degraded',
                'services': {
                    'ai_service': 'ok' if ai_status else 'error',
                    'storage_service': 'ok' if storage_status else 'error'
                },
                'details': {
                    'ai_service': None if ai_status else ai_service.last_error,
                    'storage_service': None if storage_status else 'storage service unavailable'
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # ==================== 错误处理 ====================
    
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return render_template('error.html', 
                             error_message="页面未找到"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        logger.error(f"服务器内部错误: {str(error)}")
        return render_template('error.html',
                             error_message="服务器内部错误"), 500
    
    return app

# ==================== 应用启动 ====================

if __name__ == '__main__':
    """
    应用启动入口
    
    当直接运行此文件时，启动Flask开发服务器。
    生产环境建议使用Gunicorn等WSGI服务器。
    """
    import os
    
    # 获取配置环境
    config_name = os.getenv('FLASK_ENV', 'development')
    
    # 创建应用实例
    app = create_app(config_name)
    
    # 启动开发服务器
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
