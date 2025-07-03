# config.py
# ⚙️ 配置文件 - 统一管理所有配置项

import os

class Config:
    """基础配置类"""
    
    # 🗄️ 数据库配置
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'xjpowerful'),
        'database': os.getenv('DB_NAME', 'gsminiapp'),
        'charset': 'utf8mb4'
    }
    
    # ⏱️ 会话配置
    SESSION_TIMEOUT = 1800  # 30分钟会话超时
    
    # 📊 分析配置
    MAX_QUERY_LIMIT = 5000  # 单次查询最大记录数
    MIN_CONVERSIONS_DEFAULT = 5  # 默认最小转化数
    
    # 🔍 页面路径配置
    EXCLUDED_PATHS = [
        'null', 'none', '', 'undefined',
        'localhost', '127.0.0.1'
    ]
    
    # 📈 事件映射配置
    EVENT_NAME_MAPPING = {
        # 小程序核心事件
        '$MPLaunch': '小程序启动',
        '$MPShow': '页面显示', 
        '$MPViewScreen': '页面浏览',
        '$MPPageLeave': '页面离开',
        '$MPHide': '小程序隐藏',
        '$MPEnd': '小程序结束',
        
        # 用户行为事件
        'click': '点击事件',
        'search': '搜索',
        'share': '分享',
        'add_to_cart': '添加购物车',
        'order_submit': '提交订单',
        'product_view': '商品浏览',
        'user_register': '用户注册',
        'user_login': '用户登录',
        'page_view': '页面访问',
        'button_click': '按钮点击',
        'form_submit': '表单提交',
        
        # 神策通用事件
        '$pageview': '页面浏览',
        '$WebClick': '网页点击',
        '$WebStay': '页面停留',
        '$SignUp': '注册',
        '$track_signup': '用户注册',
        '$identify': '用户识别',
        
        # 其他常见事件
        'track': '追踪事件',
        'identify': '用户识别',
        'page': '页面事件',
        'screen': '屏幕事件'
    }
    
    # 🌐 来源域名映射
    REFERRER_MAPPING = {
        'baidu': '百度搜索',
        'google': '谷歌搜索',
        'weixin': '微信',
        'wechat': '微信',
        'qq': 'QQ',
        'sina': '新浪微博',
        'zhihu': '知乎',
        'douyin': '抖音',
        'xiaohongshu': '小红书',
        'direct': '直接访问'
    }

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # 生产环境数据库配置
    DB_CONFIG = {
        'host': os.getenv('PROD_DB_HOST', 'localhost'),
        'user': os.getenv('PROD_DB_USER', 'root'),
        'password': os.getenv('PROD_DB_PASSWORD'),
        'database': os.getenv('PROD_DB_NAME', 'gsminiapp'),
        'charset': 'utf8mb4'
    }

# 📋 根据环境变量选择配置
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """获取当前环境配置"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])