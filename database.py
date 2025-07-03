# database.py
# 🗄️ 数据库连接管理

import pymysql
import logging
from config import get_config

# 获取配置
config = get_config()

def get_db_connection():
    """
    获取数据库连接
    
    Returns:
        connection: 数据库连接对象，失败时返回None
    """
    try:
        conn = pymysql.connect(**config.DB_CONFIG)
        return conn
    except Exception as e:
        logging.error(f"数据库连接失败: {e}")
        return None

def execute_query(query, params=None, fetch_all=True):
    """
    执行查询并返回结果
    
    Args:
        query (str): SQL查询语句
        params (tuple): 查询参数
        fetch_all (bool): 是否获取所有结果
        
    Returns:
        tuple: (结果数据, 列名列表) 或 (None, None)
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        if not conn:
            return None, None
            
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # 获取数据
        if fetch_all:
            results = cursor.fetchall()
        else:
            results = cursor.fetchone()
            
        return results, columns
        
    except Exception as e:
        logging.error(f"查询执行失败: {e}")
        return None, None
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_insert(query, params=None):
    """
    执行插入操作
    
    Args:
        query (str): SQL插入语句
        params (tuple): 插入参数
        
    Returns:
        int: 影响的行数，失败时返回0
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        if not conn:
            return 0
            
        cursor = conn.cursor()
        
        if params:
            result = cursor.execute(query, params)
        else:
            result = cursor.execute(query)
            
        conn.commit()
        return result
        
    except Exception as e:
        logging.error(f"插入操作失败: {e}")
        if conn:
            conn.rollback()
        return 0
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def test_connection():
    """
    测试数据库连接
    
    Returns:
        dict: 连接测试结果
    """
    try:
        conn = get_db_connection()
        if not conn:
            return {
                'success': False,
                'message': '无法建立数据库连接'
            }
            
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM summit")
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'数据库连接成功，共有 {count} 条记录',
            'record_count': count
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'数据库连接测试失败: {str(e)}'
        }

def get_table_info():
    """
    获取表结构信息
    
    Returns:
        dict: 表结构信息
    """
    try:
        # 获取表结构
        structure_query = "DESCRIBE summit"
        structure_results, structure_columns = execute_query(structure_query)
        
        # 获取索引信息
        index_query = "SHOW INDEX FROM summit"
        index_results, index_columns = execute_query(index_query)
        
        # 获取表状态
        status_query = "SHOW TABLE STATUS LIKE 'summit'"
        status_results, status_columns = execute_query(status_query, fetch_all=False)
        
        return {
            'structure': {
                'columns': structure_columns,
                'data': structure_results
            },
            'indexes': {
                'columns': index_columns,
                'data': index_results
            },
            'status': {
                'columns': status_columns,
                'data': status_results
            }
        }
        
    except Exception as e:
        logging.error(f"获取表信息失败: {e}")
        return None