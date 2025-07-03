# api/user_path.py
# 🛤️ 用户路径分析API模块

from flask import Blueprint, jsonify, request
import pandas as pd
import logging
from database import execute_query
from utils import (
    get_time_condition, preprocess_dataframe, build_enhanced_user_paths,
    build_enhanced_sankey_data, analyze_step_distribution, 
    analyze_path_conversion, calculate_enhanced_path_stats
)
from config import get_config

# 创建蓝图
user_path_bp = Blueprint('user_path', __name__)
config = get_config()

@user_path_bp.route('/api/user-path-analysis', methods=['GET'])
def user_path_analysis_api():
    """优化后的用户路径分析API - 支持事件、页面、URL、标题、来源混合分析"""
    try:
        # 获取筛选参数
        selected_options = request.args.get('selectedOptions', '').split(',') if request.args.get('selectedOptions') else []
        path_type = request.args.get('pathType', 'start')
        start_option = request.args.get('startOption', '') if path_type == 'start' else ''
        end_option = request.args.get('endOption', '') if path_type == 'end' else ''
        path_length = request.args.get('pathLength', 'all')
        min_conversions = int(request.args.get('minConversions', config.MIN_CONVERSIONS_DEFAULT))
        time_range = request.args.get('timeRange', 'last7days')
        page_filter = request.args.get('pageFilter', '')
        
        logging.info(f"用户路径分析参数:")
        logging.info(f"  选择的选项: {selected_options}")
        logging.info(f"  路径类型: {path_type}")
        logging.info(f"  起始选项: {start_option}")
        logging.info(f"  结束选项: {end_option}")
        
        # 参数验证
        if not selected_options or selected_options == ['']:
            return jsonify({'error': '请至少选择一个分析选项'}), 400
        
        # 构建查询条件
        where_conditions, query_params = build_query_conditions(selected_options)
        
        if not where_conditions:
            return jsonify({'error': '无效的选择选项'}), 400
        
        time_condition = get_time_condition(time_range)
        options_condition = f"AND ({' OR '.join(where_conditions)})"
        
        # 查询用户路径数据
        df = query_user_path_data(time_condition, options_condition, query_params)
        
        if df.empty:
            return get_empty_result()
        
        # 数据预处理
        df = preprocess_dataframe(df)
        
        # 关键词筛选
        if page_filter:
            df = df[df['step_identifier'].str.contains(page_filter, case=False, na=False)]
        
        # 会话划分和路径构建
        user_paths = build_enhanced_user_paths(df, path_type, start_option, end_option, path_length)
        
        # 筛选满足最小转化数的路径
        filtered_paths = {path: count for path, count in user_paths.items() if count >= min_conversions}
        
        if not filtered_paths:
            return get_empty_result()
        
        # 生成分析结果
        result = generate_analysis_result(df, filtered_paths)
        
        logging.info(f"分析完成: 找到 {len(filtered_paths)} 条有效路径")
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"用户路径分析API错误: {e}")
        return jsonify({'error': f'用户路径分析失败: {str(e)}'}), 500

def build_query_conditions(selected_options):
    """
    构建查询条件
    
    Args:
        selected_options (list): 选择的选项列表
        
    Returns:
        tuple: (条件列表, 参数列表)
    """
    where_conditions = []
    query_params = []
    
    for option in selected_options:
        if option.startswith('event_'):
            event_name = option.replace('event_', '')
            where_conditions.append("event = %s")
            query_params.append(event_name)
        elif option.startswith('page_'):
            page_path = option.replace('page_', '')
            where_conditions.append('JSON_UNQUOTE(JSON_EXTRACT(all_json, \'$.properties."$url_path"\')) LIKE %s')
            query_params.append(f'%{page_path}%')
        elif option.startswith('url_'):
            url_path = option.replace('url_', '')
            where_conditions.append('url LIKE %s')
            query_params.append(f'%{url_path}%')
        elif option.startswith('title_'):
            title = option.replace('title_', '')
            where_conditions.append('JSON_UNQUOTE(JSON_EXTRACT(all_json, \'$.properties."$title"\')) = %s')
            query_params.append(title)
        elif option.startswith('referrer_'):
            referrer_domain = option.replace('referrer_', '')
            where_conditions.append('referrer LIKE %s')
            query_params.append(f'%{referrer_domain}%')
    
    return where_conditions, query_params

def query_user_path_data(time_condition, options_condition, query_params):
    """
    查询用户路径数据
    
    Args:
        time_condition (str): 时间条件
        options_condition (str): 选项条件
        query_params (list): 查询参数
        
    Returns:
        pandas.DataFrame: 查询结果
    """
    path_query = f'''
        SELECT 
            distinct_id,
            event,
            created_at,
            JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url_path"')) AS url_path,
            JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties.event_duration')) AS event_duration,
            JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$title"')) AS page_title,
            url,
            referrer,
            JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$screen_name"')) AS screen_name,
            JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$element_content"')) AS element_content
        FROM summit
        WHERE 1=1
        {time_condition}
        {options_condition}
        ORDER BY distinct_id, created_at
        LIMIT {config.MAX_QUERY_LIMIT}
    '''
    
    results, columns = execute_query(path_query, query_params)
    
    if results and columns:
        return pd.DataFrame(results, columns=columns)
    else:
        return pd.DataFrame()

def get_empty_result():
    """返回空结果"""
    return jsonify({
        'sankey': {'nodes': [], 'links': []},
        'stepDistribution': {'steps': []},
        'pathConversion': {'funnelData': []},
        'pathStats': {}
    })

def generate_analysis_result(df, filtered_paths):
    """
    生成分析结果
    
    Args:
        df (pandas.DataFrame): 原始数据
        filtered_paths (dict): 过滤后的路径数据
        
    Returns:
        dict: 分析结果
    """
    sankey_data = build_enhanced_sankey_data(filtered_paths)
    step_distribution = analyze_step_distribution(filtered_paths)
    path_conversion = analyze_path_conversion(df, filtered_paths)
    path_stats = calculate_enhanced_path_stats(df, filtered_paths)
    
    return {
        'sankey': sankey_data,
        'stepDistribution': step_distribution,
        'pathConversion': path_conversion,
        'pathStats': path_stats
    }

# 提供一些示例数据生成函数，用于测试和演示
def generate_mock_path_data():
    """生成模拟路径数据"""
    return {
        'sankey': {
            'nodes': [
                {'name': '启动应用'},
                {'name': '首页浏览'},
                {'name': '商品搜索'},
                {'name': '商品详情'},
                {'name': '添加购物车'},
                {'name': '提交订单'}
            ],
            'links': [
                {'source': 0, 'target': 1, 'value': 1000, 'sourceName': '启动应用', 'targetName': '首页浏览'},
                {'source': 1, 'target': 2, 'value': 600, 'sourceName': '首页浏览', 'targetName': '商品搜索'},
                {'source': 1, 'target': 3, 'value': 300, 'sourceName': '首页浏览', 'targetName': '商品详情'},
                {'source': 2, 'target': 3, 'value': 400, 'sourceName': '商品搜索', 'targetName': '商品详情'},
                {'source': 3, 'target': 4, 'value': 200, 'sourceName': '商品详情', 'targetName': '添加购物车'},
                {'source': 4, 'target': 5, 'value': 80, 'sourceName': '添加购物车', 'targetName': '提交订单'}
            ]
        },
        'stepDistribution': {
            'steps': [
                {'value': 35, 'name': '2-3步路径'},
                {'value': 30, 'name': '4-5步路径'},
                {'value': 25, 'name': '6-8步路径'},
                {'value': 10, 'name': '9步以上'}
            ]
        },
        'pathConversion': {
            'totalUsers': 1000,
            'funnelData': [
                {'value': 1000, 'name': '启动应用'},
                {'value': 850, 'name': '浏览首页'},
                {'value': 600, 'name': '搜索商品'},
                {'value': 350, 'name': '查看详情'},
                {'value': 200, 'name': '添加购物车'},
                {'value': 80, 'name': '提交订单'}
            ]
        },
        'pathStats': {
            '启动应用 → 首页浏览 → 商品搜索': {'count': 450, 'conversionRate': '75%', 'avgDuration': '85s'},
            '启动应用 → 首页浏览 → 商品详情': {'count': 280, 'conversionRate': '68%', 'avgDuration': '120s'},
            '商品搜索 → 商品详情 → 添加购物车': {'count': 180, 'conversionRate': '45%', 'avgDuration': '150s'},
            '商品详情 → 添加购物车 → 提交订单': {'count': 75, 'conversionRate': '38%', 'avgDuration': '200s'}
        }
    }

@user_path_bp.route('/api/user-path-analysis/mock', methods=['GET'])
def get_mock_path_data():
    """获取模拟路径数据（用于测试）"""
    return jsonify(generate_mock_path_data())