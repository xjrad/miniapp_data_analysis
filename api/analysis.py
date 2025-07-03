# api/analysis.py
# 🔍 分析选项API模块

from flask import Blueprint, jsonify
from urllib.parse import urlparse
import logging
from database import execute_query
from utils import format_event_name, clean_page_path, categorize_referrer
from config import get_config

# 创建蓝图
analysis_bp = Blueprint('analysis', __name__)
config = get_config()

@analysis_bp.route('/api/analysis-options', methods=['GET'])
def get_analysis_options():
    """获取所有可用的分析选项（事件+页面路径+URL+其他属性）"""
    try:
        # 获取所有事件类型
        events = get_event_options()
        
        # 获取页面路径（从all_json中提取）
        pages = get_page_options()
        
        # 获取URL路径（从url字段）
        urls = get_url_options()
        
        # 获取页面标题
        titles = get_title_options()
        
        # 获取来源渠道
        referrers = get_referrer_options()
        
        # 合并所有选项
        all_options = events + pages + urls + titles + referrers
        
        # 按类别分组
        grouped_options = {
            'events': events,
            'pages': pages,
            'urls': urls,
            'titles': titles,
            'referrers': referrers,
            'all': all_options
        }
        
        logging.info(f"返回分析选项: 事件{len(events)}个, 页面{len(pages)}个, URL{len(urls)}个, 标题{len(titles)}个, 来源{len(referrers)}个")
        return jsonify({'options': grouped_options})
        
    except Exception as e:
        logging.error(f"获取分析选项失败: {e}")
        return jsonify({'error': f'获取分析选项失败: {str(e)}'}), 500

def get_event_options():
    """获取事件类型选项"""
    try:
        events_query = '''
            SELECT event, COUNT(*) as count 
            FROM summit 
            WHERE event IS NOT NULL AND event != ''
            GROUP BY event 
            ORDER BY count DESC
            LIMIT 50
        '''
        results, _ = execute_query(events_query)
        
        events = []
        if results:
            for row in results:
                event_name = row[0]
                count = row[1]
                
                events.append({
                    'type': 'event',
                    'key': f"event_{event_name}",
                    'value': event_name,
                    'count': count,
                    'display_name': format_event_name(event_name),
                    'category': '事件类型'
                })
        
        return events
        
    except Exception as e:
        logging.error(f"获取事件选项失败: {e}")
        return []

def get_page_options():
    """获取页面路径选项"""
    try:
        pages_query = '''
            SELECT 
                JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url_path"')) AS url_path,
                COUNT(*) as count
            FROM summit 
            WHERE JSON_EXTRACT(all_json, '$.properties."$url_path"') IS NOT NULL
                AND JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url_path"')) NOT IN ('null', '', 'undefined')
                AND CHAR_LENGTH(JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url_path"'))) > 0
            GROUP BY url_path 
            ORDER BY count DESC
            LIMIT 50
        '''
        results, _ = execute_query(pages_query)
        
        pages = []
        if results:
            for row in results:
                original_path = row[0]
                count = row[1]
                
                if original_path and original_path.strip():
                    clean_path = clean_page_path(original_path)
                    if clean_path != 'unknown':
                        pages.append({
                            'type': 'page',
                            'key': f"page_{clean_path}",
                            'value': original_path,
                            'count': count,
                            'display_name': f"页面: {clean_path}",
                            'category': '页面路径'
                        })
        
        return pages
        
    except Exception as e:
        logging.error(f"获取页面选项失败: {e}")
        return []

def get_url_options():
    """获取URL路径选项"""
    try:
        url_query = '''
            SELECT 
                url,
                COUNT(*) as count
            FROM summit 
            WHERE url IS NOT NULL 
                AND url != '' 
                AND url NOT LIKE '%localhost%'
                AND url NOT LIKE '%127.0.0.1%'
            GROUP BY url 
            ORDER BY count DESC
            LIMIT 30
        '''
        results, _ = execute_query(url_query)
        
        urls = []
        if results:
            for row in results:
                url = row[0]
                count = row[1]
                
                if url and url.strip():
                    # 提取URL路径部分
                    try:
                        parsed = urlparse(url)
                        path = parsed.path if parsed.path else url
                        if path and path != '/':
                            clean_url = clean_page_path(path)
                            if clean_url != 'unknown':
                                urls.append({
                                    'type': 'url',
                                    'key': f"url_{clean_url}",
                                    'value': url,
                                    'count': count,
                                    'display_name': f"URL: {clean_url}",
                                    'category': 'URL路径'
                                })
                    except:
                        pass
        
        return urls
        
    except Exception as e:
        logging.error(f"获取URL选项失败: {e}")
        return []

def get_title_options():
    """获取页面标题选项"""
    try:
        title_query = '''
            SELECT 
                JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$title"')) AS page_title,
                COUNT(*) as count
            FROM summit 
            WHERE JSON_EXTRACT(all_json, '$.properties."$title"') IS NOT NULL
                AND JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$title"')) NOT IN ('null', '', 'undefined')
                AND CHAR_LENGTH(JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$title"'))) > 0
            GROUP BY page_title 
            ORDER BY count DESC
            LIMIT 30
        '''
        results, _ = execute_query(title_query)
        
        titles = []
        if results:
            for row in results:
                title = row[0]
                count = row[1]
                
                if title and len(title.strip()) > 0:
                    titles.append({
                        'type': 'title',
                        'key': f"title_{title}",
                        'value': title,
                        'count': count,
                        'display_name': f"标题: {title[:30]}{'...' if len(title) > 30 else ''}",
                        'category': '页面标题'
                    })
        
        return titles
        
    except Exception as e:
        logging.error(f"获取标题选项失败: {e}")
        return []

def get_referrer_options():
    """获取来源渠道选项"""
    try:
        referrer_query = '''
            SELECT 
                referrer,
                COUNT(*) as count
            FROM summit 
            WHERE referrer IS NOT NULL 
                AND referrer != '' 
                AND referrer NOT LIKE '%localhost%'
            GROUP BY referrer 
            ORDER BY count DESC
            LIMIT 20
        '''
        results, _ = execute_query(referrer_query)
        
        referrers = []
        if results:
            for row in results:
                referrer = row[0]
                count = row[1]
                
                if referrer and referrer.strip():
                    category, display_name = categorize_referrer(referrer)
                    referrers.append({
                        'type': 'referrer',
                        'key': f"referrer_{category}",
                        'value': referrer,
                        'count': count,
                        'display_name': display_name,
                        'category': '来源渠道'
                    })
        
        return referrers
        
    except Exception as e:
        logging.error(f"获取来源选项失败: {e}")
        return []

@analysis_bp.route('/api/events', methods=['GET'])
def get_available_events():
    """获取所有可用的事件类型（兼容旧接口）"""
    try:
        events = get_event_options()
        # 转换为旧格式
        old_format_events = []
        for event in events:
            old_format_events.append({
                'event': event['value'],
                'count': event['count'],
                'display_name': event['display_name']
            })
        
        return jsonify({'events': old_format_events})
        
    except Exception as e:
        logging.error(f"获取事件数据失败: {e}")
        return jsonify({'error': f'获取事件数据失败: {str(e)}'}), 500

@analysis_bp.route('/api/pages', methods=['GET'])
def get_available_pages():
    """获取所有可用的页面路径（兼容旧接口）"""
    try:
        pages = get_page_options()
        # 转换为旧格式
        old_format_pages = []
        for page in pages:
            old_format_pages.append({
                'original_path': page['value'],
                'clean_path': page['key'].replace('page_', ''),
                'count': page['count']
            })
        
        return jsonify({'pages': old_format_pages})
        
    except Exception as e:
        logging.error(f"获取页面数据失败: {e}")
        return jsonify({'error': f'获取页面数据失败: {str(e)}'}), 500