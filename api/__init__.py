# api/__init__.py
# 📡 API模块初始化文件

from .analysis import analysis_bp
from .user_path import user_path_bp
from .dashboard import dashboard_bp

def register_blueprints(app):
    """
    注册所有蓝图到Flask应用
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(analysis_bp)
    app.register_blueprint(user_path_bp)
    app.register_blueprint(dashboard_bp)

__all__ = [
    'analysis_bp',
    'user_path_bp', 
    'dashboard_bp',
    'register_blueprints'
]