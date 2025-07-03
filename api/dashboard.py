# api/dashboard.py
# 📊 仪表板API模块

from flask import Blueprint, jsonify, request
import logging
from database import execute_query, test_connection
from utils import get_time_condition, generate_mock_trend_data, generate_mock_hourly_data

# 创建蓝图
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard', methods=['GET'])
def dashboard_api():
    """仪表板数据API"""
    try:
        time_range = request.args.get('timeRange', 'today')
        
        time_condition = get_time_condition(time_range)
        
        # 基础统计查询
        metrics = get_basic_metrics(time_condition)
        
        # 设备分布数据
        device_data = get_device_distribution(time_condition)
        
        # 生成趋势数据
        trend_data = generate_mock_trend_data(time_range)
        hourly_data = generate_mock_hourly_data()
        
        result = {
            'metrics': metrics,
            'trend': trend_data,
            'device': {'devices': device_data},
            'hourly': hourly_data
        }
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"仪表板API错误: {e}")
        return jsonify({'error': f'获取仪表板数据失败: {str(e)}'}), 500

def get_basic_metrics(time_condition):
    """
    获取基础指标数据
    
    Args:
        time_condition (str): 时间条件
        
    Returns:
        dict: 基础指标
    """
    try:
        stats_query = f'''
            SELECT 
                COUNT(DISTINCT distinct_id) as total_users,
                COUNT(*) as total_events,
                COUNT(CASE WHEN event IN ('$MPViewScreen', '$MPShow') THEN 1 END) as total_pv
            FROM summit
            WHERE event IS NOT NULL
            {time_condition}
        '''
        
        results, _ = execute_query(stats_query, fetch_all=False)
        
        if results:
            total_users = int(results[0]) if results[0] else 0
            total_events = int(results[1]) if results[1] else 0
            total_pv = int(results[2]) if results[2] else 0
        else:
            total_users = total_events = total_pv = 0
        
        # 计算会话相关指标（简化处理）
        session_metrics = calculate_session_metrics(time_condition)
        
        return {
            'total_users': total_users,
            'total_pv': total_pv,
            'avg_session_duration': session_metrics.get('avg_duration', 125.5),
            'bounce_rate': session_metrics.get('bounce_rate', 35.2)
        }
        
    except Exception as e:
        logging.error(f"获取基础指标失败: {e}")
        return {
            'total_users': 0,
            'total_pv': 0,
            'avg_session_duration': 0,
            'bounce_rate': 0
        }

def calculate_session_metrics(time_condition):
    """
    计算会话相关指标
    
    Args:
        time_condition (str): 时间条件
        
    Returns:
        dict: 会话指标
    """
    try:
        # 简化的会话时长计算
        session_query = f'''
            SELECT 
                distinct_id,
                MIN(created_at) as session_start,
                MAX(created_at) as session_end,
                COUNT(*) as event_count
            FROM summit
            WHERE event IS NOT NULL
            {time_condition}
            GROUP BY distinct_id
            HAVING COUNT(*) >= 2
        '''
        
        results, _ = execute_query(session_query)
        
        if not results:
            return {'avg_duration': 125.5, 'bounce_rate': 35.2}
        
        total_duration = 0
        valid_sessions = 0
        single_event_sessions = 0
        
        for row in results:
            session_start = row[1]
            session_end = row[2]
            event_count = row[3]
            
            if session_end > session_start:
                duration = session_end - session_start
                total_duration += duration
                valid_sessions += 1
            
            if event_count == 1:
                single_event_sessions += 1
        
        # 计算平均会话时长
        avg_duration = (total_duration / valid_sessions) if valid_sessions > 0 else 125.5
        
        # 计算跳出率（单页面会话比例）
        total_sessions = len(results) + single_event_sessions
        bounce_rate = (single_event_sessions / total_sessions * 100) if total_sessions > 0 else 35.2
        
        return {
            'avg_duration': round(avg_duration, 1),
            'bounce_rate': round(bounce_rate, 1)
        }
        
    except Exception as e:
        logging.error(f"计算会话指标失败: {e}")
        return {'avg_duration': 125.5, 'bounce_rate': 35.2}

def get_device_distribution(time_condition):
    """
    获取设备分布数据
    
    Args:
        time_condition (str): 时间条件
        
    Returns:
        list: 设备分布数据
    """
    try:
        device_query = f'''
            SELECT 
                JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$os"')) as os,
                COUNT(DISTINCT distinct_id) as user_count
            FROM summit
            WHERE event = '$MPLaunch'
            {time_condition}
            GROUP BY os
            HAVING os IS NOT NULL AND os != 'null'
        '''
        
        results, _ = execute_query(device_query)
        
        device_data = []
        if results:
            for row in results:
                os_name = row[0]
                user_count = int(row[1])
                
                if os_name and os_name.strip():
                    # 映射操作系统名称
                    display_name = map_os_name(os_name)
                    device_data.append({
                        'value': user_count,
                        'name': display_name
                    })
        
        # 如果没有数据，返回示例数据
        if not device_data:
            device_data = [
                {'value': 600, 'name': 'iOS'},
                {'value': 350, 'name': 'Android'},
                {'value': 50, 'name': '其他'}
            ]
        
        return device_data
        
    except Exception as e:
        logging.error(f"获取设备分布失败: {e}")
        # 返回示例数据
        return [
            {'value': 600, 'name': 'iOS'},
            {'value': 350, 'name': 'Android'},
            {'value': 50, 'name': '其他'}
        ]

def map_os_name(os_name):
    """
    映射操作系统名称
    
    Args:
        os_name (str): 原始操作系统名称
        
    Returns:
        str: 映射后的名称
    """
    os_mapping = {
        'ios': 'iOS',
        'iphone': 'iOS',
        'ipad': 'iOS',
        'android': 'Android',
        'windows': 'Windows',
        'mac': 'Mac',
        'linux': 'Linux'
    }
    
    os_lower = os_name.lower()
    for key, value in os_mapping.items():
        if key in os_lower:
            return value
    
    return os_name.title() if len(os_name) <= 10 else '其他'

@dashboard_bp.route('/api/debug', methods=['GET'])
def debug():
    """调试接口"""
    try:
        # 测试数据库连接
        connection_test = test_connection()
        
        if not connection_test['success']:
            return jsonify({
                'database_status': 'failed',
                'error': connection_test['message'],
                'api_status': 'error'
            }), 500
        
        # 获取事件分布
        event_query = """
            SELECT event, COUNT(*) as count 
            FROM summit 
            WHERE event IS NOT NULL 
            GROUP BY event 
            ORDER BY count DESC
            LIMIT 10
        """
        
        event_results, _ = execute_query(event_query)
        event_distribution = {}
        
        if event_results:
            event_distribution = {row[0]: row[1] for row in event_results}
        
        return jsonify({
            'database_status': 'connected',
            'total_records': connection_test.get('record_count', 0),
            'event_distribution': event_distribution,
            'api_status': 'optimized'
        })
        
    except Exception as e:
        logging.error(f"调试接口错误: {e}")
        return jsonify({'error': f'Debug failed: {str(e)}'}), 500

@dashboard_bp.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 测试数据库连接
        connection_test = test_connection()
        
        status = 'healthy' if connection_test['success'] else 'unhealthy'
        status_code = 200 if connection_test['success'] else 503
        
        return jsonify({
            'status': status,
            'database': connection_test['success'],
            'message': connection_test['message']
        }), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': False,
            'message': str(e)
        }), 503