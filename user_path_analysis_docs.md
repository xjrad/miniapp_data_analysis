# 用户路径分析系统 - 指标查询逻辑文档

## 1. 系统概述

该系统基于神策数据SDK收集的小程序用户行为数据，提供用户路径分析、事件流转分析和行为时间轴分析功能。

### 技术栈
- **后端**: Python Flask + PyMySQL
- **前端**: HTML + JavaScript + ECharts
- **数据库**: MySQL (神策数据格式)

## 2. 数据表结构

### 2.1 主表 `summit` 
存储所有用户行为事件数据

**关键字段**:
- `distinct_id`: 用户唯一标识
- `event`: 事件类型
- `created_at`: 事件时间戳
- `all_json`: 完整事件数据(JSON格式)

**重要事件类型**:
- `$MPLaunch`: 小程序启动
- `$MPShow`: 页面显示  
- `$MPViewScreen`: 页面浏览
- `$MPPageLeave`: 页面离开
- `$MPHide`: 小程序隐藏

### 2.2 用户表 `summit_user`
存储用户基本信息和映射关系

### 2.3 设备表 `summit_device` 
存储设备信息、地理位置等维度数据

## 3. 核心指标查询逻辑

### 3.1 基础数据查询

```sql
SELECT 
    distinct_id,
    event,
    created_at,
    all_json,
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url"')) AS url,
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url_path"')) AS url_path,
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$title"')) AS page_title,
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties.event_duration')) AS event_duration
FROM summit
WHERE event IN ('$MPLaunch', '$MPShow', '$MPViewScreen', '$MPPageLeave', '$MPHide')
AND created_at BETWEEN {start_timestamp} AND {end_timestamp}
ORDER BY distinct_id, created_at
```

**字段说明**:
- 使用JSON_EXTRACT提取嵌套属性
- url_path优先级高于url
- event_duration用于计算页面停留时间

### 3.2 时间范围处理

```python
def get_time_condition(time_range):
    now = datetime.now()
    
    if time_range == 'today':
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'yesterday':
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'last7days':
        start_time = now - timedelta(days=7)
    elif time_range == 'last30days':
        start_time = now - timedelta(days=30)
    
    return f"AND created_at BETWEEN {start_timestamp} AND {end_timestamp}"
```

## 4. 关键指标计算

### 4.1 用户数量指标

```python
# 总用户数
total_users = df['distinct_id'].nunique()

# 活跃用户（有实际操作的用户）
active_users = df[df['event'].isin(['$MPViewScreen', '$MPLaunch'])]['distinct_id'].nunique()
```

### 4.2 会话分析

**会话划分逻辑**:
```python
# 按用户和时间排序
df = df.sort_values(['distinct_id', 'timestamp'])

# 计算时间间隔，超过30分钟视为新会话
df['time_diff'] = df.groupby('distinct_id')['timestamp'].diff()
df['new_session'] = (df['time_diff'].isna() | 
                    (df['time_diff'] > pd.Timedelta(minutes=30)))

# 生成会话ID
df['session_id'] = df.groupby('distinct_id')['new_session'].cumsum()
df['session_global'] = df['distinct_id'].astype(str) + '-session-' + df['session_id'].astype(str)
```

**会话指标**:
```python
# 总会话数
total_sessions = df['session_global'].nunique()

# 平均会话时长
session_durations = df.groupby('session_global')['timestamp'].agg(['min', 'max'])
session_durations['duration'] = (session_durations['max'] - session_durations['min']).dt.total_seconds()
avg_duration = session_durations['duration'].mean()

# 跳出率（只有一个事件的会话占比）
events_per_session = df.groupby('session_global').size()
bounce_rate = (events_per_session == 1).sum() / len(events_per_session) * 100
```

### 4.3 页面路径分析

**路径清理逻辑**:
```python
def clean_page_path(path):
    if pd.isna(path) or str(path).lower() in ['null', 'none', '']:
        return 'unknown'
    
    path_str = str(path)
    
    # 处理完整路径：pages/tabBar/home/home -> home
    if path_str.startswith('pages/'):
        path_str = path_str.replace('pages/', '')
        path_str = path_str.replace('tabBar/', '')
        if '/' in path_str:
            path_str = path_str.split('/')[-1]
    
    return path_str if path_str and path_str != '/' else 'unknown'
```

**路径序列构建**:
```python
# 按会话分组获取页面访问序列
for session_id, session_df in df.groupby('session_global'):
    session_df = session_df.sort_values('timestamp')
    pages = session_df['clean_path'].tolist()
    
    # 去重相邻重复页面
    unique_pages = []
    for page in pages:
        if not unique_pages or page != unique_pages[-1]:
            unique_pages.append(page)
    
    if len(unique_pages) >= 2:
        path = ' → '.join(unique_pages)
        path_stats[path] = path_stats.get(path, 0) + 1
```

### 4.4 页面转换分析（桑基图）

**转换关系提取**:
```python
# 构建页面转换对
transitions = []
for session_id, session_df in view_events.groupby('session_global'):
    session_df = session_df.sort_values('timestamp')
    pages = session_df['clean_path'].tolist()
    
    # 生成相邻页面转换
    for i in range(len(pages) - 1):
        current_page = pages[i]
        next_page = pages[i + 1]
        if current_page != next_page:  # 只记录不同页面转换
            transitions.append((current_page, next_page))

# 统计转换频次
from collections import Counter
transition_counts = Counter(transitions)
```

**无循环桑基图构建**:
```python
def build_layered_sankey(transition_counts):
    # 页面位置分析
    page_positions = analyze_page_positions(transition_counts)
    
    # 分层处理避免循环
    layers = {}
    for page, avg_position in page_positions.items():
        layer = int(avg_position)
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(page)
    
    # 只允许从低层到高层的连接
    for (src, tgt), count in transition_counts.items():
        src_layer = get_page_layer(src, page_positions)
        tgt_layer = get_page_layer(tgt, page_positions)
        if src_layer <= tgt_layer:  # 防止循环
            # 添加连接
```

## 5. 事件时间轴分析

```python
def build_timeline_data(df):
    timeline_data = []
    timeline_df = df[['distinct_id', 'event', 'timestamp', 'page_path', 'event_duration']].copy()
    
    for _, row in timeline_df.iterrows():
        timeline_data.append({
            'distinct_id': str(row['distinct_id']),
            'event': str(row['event']),
            'time': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'url_path': str(row['page_path']),
            'duration': float(row['event_duration']) if pd.notna(row['event_duration']) else 0.0
        })
    
    return timeline_data
```

## 6. 前端图表渲染

### 6.1 桑基图 (ECharts)
```javascript
const option = {
    series: [{
        type: 'sankey',
        data: nodes,  // [{name: "页面名"}]
        links: links, // [{source: 0, target: 1, value: 转换次数}]
        emphasis: { focus: 'adjacency' },
        lineStyle: { color: 'gradient', curveness: 0.5 }
    }]
};
```

### 6.2 时间轴散点图
```javascript
const option = {
    xAxis: { type: 'time' },
    yAxis: { type: 'category', data: users },
    series: [{
        type: 'scatter',
        data: [[时间戳, 用户索引, 事件类型, 持续时间]],
        symbolSize: function(val) { return val[3] * 2; } // 根据持续时间调整点大小
    }]
};
```

## 7. 性能优化策略

### 7.1 数据量控制
- 单次查询限制1000条记录
- 时间轴最多显示50条最新数据
- 用户数限制在10个以内

### 7.2 查询优化
- 在created_at字段添加索引
- 使用JSON_EXTRACT优化JSON字段查询
- 按distinct_id分区提高查询效率

### 7.3 前端优化
- 图表懒加载和resize自适应
- 错误处理和降级方案
- 数据验证防止渲染异常

## 8. 异常处理

### 8.1 数据异常
- 空数据处理：返回默认空结果
- 循环检测：自动修复桑基图循环问题
- 字段缺失：使用默认值填充

### 8.2 系统异常
- 数据库连接失败处理
- JSON解析异常处理
- 图表渲染失败降级

## 9. 扩展方向

### 9.1 高级分析
- 漏斗分析
- 留存分析  
- 转化率分析
- A/B测试分析

### 9.2 实时性优化
- 数据流式处理
- 增量计算
- 缓存策略

### 9.3 可视化增强
- 3D路径图
- 热力图
- 自定义仪表板