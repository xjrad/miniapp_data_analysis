# app.py
# 🚀 主应用入口文件

import os
import logging
from flask import Flask, render_template, jsonify
from config import get_config
from api import register_blueprints

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_app():
    """
    应用工厂函数
    
    Returns:
        Flask: 配置好的Flask应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    config = get_config()
    app.config.from_object(config)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册路由
    register_routes(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册请求处理器
    register_request_handlers(app)
    
    return app

def register_routes(app):
    """
    注册主要路由
    
    Args:
        app: Flask应用实例
    """
    
    @app.route('/')
    def index():
        """仪表板首页"""
        return render_template('index.html')

    @app.route('/user-path.html')
    def user_path():
        """用户路径分析页面"""
        return render_template('user-path.html')
    
    @app.route('/event-analysis.html')
    def event_analysis():
        """事件分析页面（占位）"""
        return jsonify({
            'message': '事件分析页面正在开发中',
            'status': 'coming_soon'
        })
    
    @app.route('/funnel-analysis.html')
    def funnel_analysis():
        """漏斗分析页面（占位）"""
        return jsonify({
            'message': '漏斗分析页面正在开发中',
            'status': 'coming_soon'
        })
    
    @app.route('/retention-analysis.html')
    def retention_analysis():
        """留存分析页面（占位）"""
        return jsonify({
            'message': '留存分析页面正在开发中',
            'status': 'coming_soon'
        })

def register_error_handlers(app):
    """
    注册错误处理器
    
    Args:
        app: Flask应用实例
    """
    
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return jsonify({
            'error': 'API endpoint not found',
            'message': '请求的资源不存在',
            'status_code': 404
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        logging.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal server error',
            'message': '服务器内部错误，请稍后重试',
            'status_code': 500
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        """400错误处理"""
        return jsonify({
            'error': 'Bad request',
            'message': '请求参数错误',
            'status_code': 400
        }), 400

def register_request_handlers(app):
    """
    注册请求处理器
    
    Args:
        app: Flask应用实例
    """
    
    @app.before_request
    def before_request():
        """请求前处理"""
        # 可以在这里添加认证、日志记录等
        pass
    
    @app.after_request
    def after_request(response):
        """请求后处理"""
        # 添加CORS头
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        # 添加安全头
        response.headers.add('X-Content-Type-Options', 'nosniff')
        response.headers.add('X-Frame-Options', 'DENY')
        response.headers.add('X-XSS-Protection', '1; mode=block')
        
        return response

# 创建应用实例
app = create_app()

# 添加一些有用的命令行工具
@app.cli.command()
def test_db():
    """测试数据库连接"""
    from database import test_connection
    result = test_connection()
    if result['success']:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['message']}")

@app.cli.command()
def show_routes():
    """显示所有路由"""
    print("\n📍 注册的路由:")
    print("-" * 50)
    for rule in app.url_map.iter_rules():
        methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{rule.endpoint:30} {methods:15} {rule.rule}")

@app.cli.command()
def show_config():
    """显示当前配置"""
    config = get_config()
    print(f"\n⚙️  当前配置: {config.__name__}")
    print("-" * 50)
    print(f"DEBUG: {config.DEBUG}")
    print(f"数据库主机: {config.DB_CONFIG['host']}")
    print(f"数据库名称: {config.DB_CONFIG['database']}")
    print(f"会话超时: {config.SESSION_TIMEOUT}秒")

if __name__ == '__main__':
    # 从环境变量获取运行参数
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 80))
    
    # 启动应用
    app.run(
        debug=debug,
        host=host,
        port=port,
        threaded=True  # 启用多线程支持
    )