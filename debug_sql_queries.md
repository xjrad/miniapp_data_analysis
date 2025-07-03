-- 📊 用户路径分析 - 数据调试SQL查询
-- 请依次执行这些查询来验证数据结构和内容

-- 1. 📈 事件类型统计 (验证事件数据)
SELECT 
    event, 
    COUNT(*) as count,
    COUNT(DISTINCT distinct_id) as unique_users,
    MIN(created_at) as first_seen,
    MAX(created_at) as last_seen
FROM summit 
WHERE event IS NOT NULL AND event != ''
GROUP BY event 
ORDER BY count DESC 
LIMIT 20;

-- 2. 📄 页面路径统计 (从JSON中提取)
SELECT 
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url_path"')) AS url_path,
    COUNT(*) as count,
    COUNT(DISTINCT distinct_id) as unique_users
FROM summit 
WHERE JSON_EXTRACT(all_json, '$.properties."$url_path"') IS NOT NULL
    AND JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url_path"')) NOT IN ('null', '', 'undefined')
    AND CHAR_LENGTH(JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url_path"'))) > 0
GROUP BY url_path 
ORDER BY count DESC 
LIMIT 15;

-- 3. 🏷️ 页面标题统计
SELECT 
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$title"')) AS page_title,
    COUNT(*) as count,
    COUNT(DISTINCT distinct_id) as unique_users
FROM summit 
WHERE JSON_EXTRACT(all_json, '$.properties."$title"') IS NOT NULL
    AND JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$title"')) NOT IN ('null', '', 'undefined')
    AND CHAR_LENGTH(JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$title"'))) > 0
GROUP BY page_title 
ORDER BY count DESC 
LIMIT 10;

-- 4. 🔗 URL路径统计 (从url字段)
SELECT 
    url,
    COUNT(*) as count,
    COUNT(DISTINCT distinct_id) as unique_users
FROM summit 
WHERE url IS NOT NULL 
    AND url != '' 
    AND url NOT LIKE '%localhost%'
    AND url NOT LIKE '%127.0.0.1%'
GROUP BY url 
ORDER BY count DESC 
LIMIT 10;

-- 5. 🌐 来源渠道统计
SELECT 
    CASE 
        WHEN referrer IS NULL OR referrer = '' THEN 'direct'
        WHEN referrer LIKE '%baidu%' THEN 'baidu'
        WHEN referrer LIKE '%google%' THEN 'google'
        WHEN referrer LIKE '%weixin%' OR referrer LIKE '%wechat%' THEN 'wechat'
        ELSE SUBSTRING_INDEX(SUBSTRING_INDEX(referrer, '/', 3), '/', -1)
    END as referrer_domain,
    COUNT(*) as count,
    COUNT(DISTINCT distinct_id) as unique_users
FROM summit 
GROUP BY referrer_domain
ORDER BY count DESC 
LIMIT 10;

-- 6. 📊 JSON结构分析 (查看all_json字段的键)
-- 注意：这个查询可能比较慢，建议限制行数
SELECT 
    JSON_KEYS(all_json) as json_keys,
    COUNT(*) as count
FROM summit 
WHERE all_json IS NOT NULL
    AND JSON_VALID(all_json) = 1
GROUP BY json_keys
ORDER BY count DESC
LIMIT 5;

-- 7. 🔍 properties字段内容分析
SELECT 
    JSON_KEYS(JSON_EXTRACT(all_json, '$.properties')) as property_keys,
    COUNT(*) as count
FROM summit 
WHERE JSON_EXTRACT(all_json, '$.properties') IS NOT NULL
    AND JSON_VALID(all_json) = 1
GROUP BY property_keys
ORDER BY count DESC
LIMIT 5;

-- 8. 📝 样本数据查看 (查看完整记录结构)
SELECT 
    distinct_id,
    event,
    created_at,
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$url_path"')) AS url_path,
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$title"')) AS title,
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$screen_name"')) AS screen_name,
    JSON_UNQUOTE(JSON_EXTRACT(all_json, '$.properties."$element_content"')) AS element_content,
    url,
    referrer,
    all_json
FROM summit 
ORDER BY created_at DESC
LIMIT 3;

-- 9. 📈 时间范围数据量检查
SELECT 
    DATE(FROM_UNIXTIME(created_at)) as date,
    COUNT(*) as total_events,
    COUNT(DISTINCT distinct_id) as unique_users,
    COUNT(DISTINCT event) as unique_events
FROM summit 
WHERE created_at >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
GROUP BY DATE(FROM_UNIXTIME(created_at))
ORDER BY date DESC;

-- 10. 👥 用户会话分析 (检查用户活动)
SELECT 
    distinct_id,
    COUNT(*) as event_count,
    MIN(created_at) as first_event,
    MAX(created_at) as last_event,
    MAX(created_at) - MIN(created_at) as session_duration_seconds
FROM summit 
WHERE created_at >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 1 DAY))
GROUP BY distinct_id
HAVING event_count >= 3
ORDER BY event_count DESC
LIMIT 10;

-- 💡 使用建议：
-- 1. 依次执行查询1-5来验证基础数据
-- 2. 查询6-7帮助了解JSON结构
-- 3. 查询8查看具体的数据样本
-- 4. 查询9-10验证数据的时间分布和用户活动情况

-- 🔧 如果某些查询返回空结果，可能的原因：
-- 1. JSON字段中的键名不同（如$url_path可能是url_path）
-- 2. 数据格式不同（需要调整清洗逻辑）
-- 3. 时间范围内没有数据（调整时间条件）