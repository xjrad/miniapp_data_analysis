# utils/data_processor.py
# 📈 数据处理工具模块

import pandas as pd
import re
from urllib.parse import urlparse
from datetime import datetime, timedelta
from config import get_config

# 获取配置
config = get_config()

def format_event_name(event):
    """
    格式化事件显示名称
    
    Args:
        event (str): 原始事件名称
        
    Returns:
        str: 格式化后的事件名称
    """
    if not event:
        return "未知事件"
        
    # 从配置中获取映射
    formatted_name = config.EVENT_NAME_MAPPING.get(event, event)
    
    # 如果没有找到映射，进行基本格式化
    if formatted_name == event:
        formatted_name = event.replace('$MP', '').replace('$', '').replace('_', ' ').title()
        if not formatted_name:
            formatted_name = event
    
    return formatted_name

def clean_page_path(path):
    """
    清理页面路径
    
    Args:
        path (str): 原始页面路径
        
    Returns:
        str: 清理后的页面路径
    """
    if pd.isna(path) or str(path).lower() in config.EXCLUDED_PATHS:
        return 'unknown'
    
    path_str = str(path)
    
    # 如果是完整的pages路径，提取页面名称
    if path_str.startswith('pages/'):
        path_str = path_str.replace('pages/', '')
        path_str = path_str.replace('tabBar/', '')
        if '/' in path_str:
            path_str = path_str.split('/')[-1]
    
    # 移除查询参数
    if '?' in path_str:
        path_str = path_str.split('?')[0]
    
    # 移除文件扩展名
    if '.' in path_str:
        name, ext = path_str.rsplit('.', 1)
        if ext in ['html', 'htm', 'php', 'jsp', 'asp']:
            path_str = name
    
    # 如果路径为空或只有斜杠，返回unknown
    if not path_str or path_str in ['/', '']:
        return 'unknown'
    
    return path_str

def extract_domain_from_url(url):
    """
    从URL中提取域名
    
    Args:
        url (str): 完整URL
        
    Returns:
        str: 域名
    """
    if not url or url.strip() == '':
        return 'direct'
        
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if not domain:
            return 'direct'
            
        # 移除www前缀
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
        
    except Exception:
        return 'unknown'

def categorize_referrer(referrer):
    """
    分类来源渠道
    
    Args:
        referrer (str): 来源URL
        
    Returns:
        tuple: (分类, 显示名称)
    """
    if not referrer or referrer.strip() == '':
        return 'direct', '直接访问'
        
    domain = extract_domain_from_url(referrer)
    
    # 从配置中匹配已知来源
    for key, name in config.REFERRER_MAPPING.items():
        if key in domain.lower():
            return key, name
    
    return domain, f"来源: {domain}"

def get_time_condition(time_range):
    """
    根据时间范围生成查询条件
    
    Args:
        time_range (str): 时间范围标识
        
    Returns:
        str: SQL时间条件语句
    """
    now = datetime.now()
    
    if time_range == 'today':
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now
    elif time_range == 'yesterday':
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'last7days':
        start_time = now - timedelta(days=7)
        end_time = now
    elif time_range == 'last30days':
        start_time = now - timedelta(days=30)
        end_time = now
    else:
        return ""
    
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())
    
    return f"AND created_at BETWEEN {start_timestamp} AND {end_timestamp}"

def extract_json_property(all_json, property_path, default=None):
    """
    从JSON字段中提取属性值
    
    Args:
        all_json (str): JSON字符串
        property_path (str): 属性路径，如 '$.properties."$url_path"'
        default: 默认值
        
    Returns:
        any: 提取的值或默认值
    """
    try:
        if not all_json:
            return default
            
        import json
        data = json.loads(all_json)
        
        # 简单的路径解析
        if property_path.startswith('$.properties.'):
            prop_name = property_path.replace('$.properties.', '').strip('"')
            properties = data.get('properties', {})
            return properties.get(prop_name, default)
        elif property_path.startswith('$.'):
            prop_name = property_path.replace('$.', '').strip('"')
            return data.get(prop_name, default)
        else:
            return default
            
    except Exception:
        return default

def build_comprehensive_step_identifier(row):
    """
    构建综合步骤标识符
    
    Args:
        row (pandas.Series): 数据行
        
    Returns:
        str: 步骤标识符
    """
    event = row.get('event', '')
    clean_path = row.get('clean_path', '')
    page_title = row.get('page_title', '')
    url = row.get('url', '')
    referrer = row.get('referrer', '')
    screen_name = row.get('screen_name', '')
    element_content = row.get('element_content', '')
    
    # 格式化事件名称
    formatted_event = format_event_name(event)
    
    # 构建步骤标识符 - 优先级：页面标题 > 屏幕名称 > 页面路径 > URL路径 > 元素内容
    identifier_parts = [formatted_event]
    
    if page_title and len(str(page_title).strip()) > 0:
        identifier_parts.append(f"({str(page_title)[:20]})")
    elif screen_name and len(str(screen_name).strip()) > 0:
        identifier_parts.append(f"({str(screen_name)[:20]})")
    elif clean_path and clean_path != 'unknown':
        identifier_parts.append(f"({clean_path})")
    elif url and len(str(url).strip()) > 0:
        try:
            parsed = urlparse(str(url))
            path = parsed.path if parsed.path and parsed.path != '/' else parsed.netloc
            if path:
                clean_url_path = clean_page_path(path)
                if clean_url_path != 'unknown':
                    identifier_parts.append(f"({clean_url_path})")
        except:
            pass
    elif element_content and len(str(element_content).strip()) > 0:
        content = str(element_content).strip()[:15]
        identifier_parts.append(f"[{content}]")
    
    return "".join(identifier_parts)

def apply_path_length_filter(path_sequence, path_length):
    """
    应用路径长度筛选
    
    Args:
        path_sequence (list): 路径序列
        path_length (str): 路径长度条件
        
    Returns:
        bool: 是否符合条件
    """
    length = len(path_sequence)
    
    if path_length == 'all':
        return True
    elif path_length == '2-3':
        return 2 <= length <= 3
    elif path_length == '4-5':
        return 4 <= length <= 5
    elif path_length == '6-8':
        return 6 <= length <= 8
    elif path_length == '9+':
        return length >= 9
    
    return True

def preprocess_dataframe(df):
    """
    预处理DataFrame
    
    Args:
        df (pandas.DataFrame): 原始数据
        
    Returns:
        pandas.DataFrame: 预处理后的数据
    """
    if df.empty:
        return df
    
    # 数据预处理
    df['timestamp'] = pd.to_datetime(df['created_at'], unit='s')
    df['clean_path'] = df['url_path'].apply(clean_page_path)
    df['event_duration'] = pd.to_numeric(df.get('event_duration', 0), errors='coerce').fillna(0)
    
    # 构建步骤标识（综合多个维度）
    df['step_identifier'] = df.apply(lambda row: build_comprehensive_step_identifier(row), axis=1)
    
    return df

def generate_mock_trend_data(time_range):
    """
    生成模拟趋势数据
    
    Args:
        time_range (str): 时间范围
        
    Returns:
        dict: 趋势数据
    """
    if time_range == 'today':
        dates = [(datetime.now() - timedelta(hours=i)).strftime('%H:00') for i in range(23, -1, -1)]
        uv = [max(10, 50 + i * 2 + (i % 3) * 10) for i in range(24)]
        pv = [max(20, int(uv[i] * (2 + (i % 4) * 0.5))) for i in range(24)]
    else:
        days = {'yesterday': 1, 'last7days': 7, 'last30days': 30}.get(time_range, 7)
        dates = [(datetime.now() - timedelta(days=i)).strftime('%m-%d') for i in range(days-1, -1, -1)]
        uv = [max(50, 200 + i * 10 + (i % 5) * 20) for i in range(days)]
        pv = [max(100, int(uv[i] * (3 + (i % 3) * 0.8))) for i in range(days)]
    
    return {'dates': dates, 'uv': uv, 'pv': pv}

def generate_mock_hourly_data():
    """
    生成24小时热力图模拟数据
    
    Returns:
        dict: 小时数据
    """
    hourly_data = []
    for hour in range(24):
        for day in range(7):
            if 9 <= hour <= 18:
                activity = max(50, 100 + (hour - 12) ** 2 * 5 + day * 10)
            elif 19 <= hour <= 23:
                activity = max(30, 80 - (hour - 21) ** 2 * 3 + day * 5)
            else:
                activity = max(5, 20 - hour + day * 2)
            
            hourly_data.append([hour, day, int(activity)])
    
    return {'hourlyData': hourly_data}