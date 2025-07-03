# 📊 数据分析仪表板 - 部署指南

## 🏗️ 项目结构

```
project/
├── app.py                 # 🚀 主应用入口
├── config.py             # ⚙️ 配置文件
├── database.py           # 🗄️ 数据库连接
├── requirements.txt      # 📦 项目依赖
├── api/                  # 📡 API路由模块
│   ├── __init__.py
│   ├── dashboard.py      # 📊 仪表板API
│   ├── analysis.py       # 🔍 分析选项API
│   └── user_path.py      # 🛤️ 用户路径分析API
├── utils/                # 🛠️ 工具函数模块
│   ├── __init__.py
│   ├── data_processor.py # 📈 数据处理工具
│   └── path_analyzer.py  # 🔄 路径分析工具
├── static/               # 🎨 静态资源
│   ├── css/
│   ├── js/
│   └── images/
└── templates/            # 🎭 HTML模板
    ├── index.html
    └── user-path.html
```

## 🚀 快速开始

### 1. 环境准备

```bash
# Python 3.8+ 
python --version

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置数据库

在 `config.py` 中修改数据库配置：

```python
DB_CONFIG = {
    'host': 'your_host',
    'user': 'your_user', 
    'password': 'your_password',
    'database': 'gsminiapp',
    'charset': 'utf8mb4'
}
```

或使用环境变量：

```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=gsminiapp
```

### 4. 测试数据库连接

```bash
flask test-db
```

### 5. 启动应用

```bash
# 开发环境
python app.py

# 或使用Flask命令
flask run --host=0.0.0.0 --port=80
```

### 6. 访问应用

- 仪表板: http://localhost/
- 用户路径分析: http://localhost/user-path.html
- API文档: http://localhost/api/debug

## 🔧 配置说明

### 环境配置

支持两种环境配置：

1. **开发环境** (`DevelopmentConfig`)
   - DEBUG=True
   - 详细错误信息
   - 自动重载

2. **生产环境** (`ProductionConfig`)
   - DEBUG=False
   - 安全优化
   - 性能优化

### 环境变量

```bash
# 运行环境
FLASK_ENV=development  # 或 production

# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=gsminiapp

# 生产环境数据库（可选）
PROD_DB_HOST=prod_host
PROD_DB_USER=prod_user
PROD_DB_PASSWORD=prod_password
PROD_DB_NAME=gsminiapp

# 应用配置
FLASK_HOST=0.0.0.0
FLASK_PORT=80
FLASK_DEBUG=True
```

## 📡 API接口

### 仪表板相关

- `GET /api/dashboard` - 获取仪表板数据
- `GET /api/debug` - 调试信息
- `GET /api/health` - 健康检查

### 分析选项

- `GET /api/analysis-options` - 获取所有分析选项
- `GET /api/events` - 获取事件类型（兼容旧版）
- `GET /api/pages` - 获取页面路径（兼容旧版）

### 用户路径分析

- `GET /api/user-path-analysis` - 用户路径分析
- `GET /api/user-path-analysis/mock` - 模拟数据（测试用）

## 🛠️ 开发工具

### Flask CLI 命令

```bash
# 测试数据库连接
flask test-db

# 显示所有路由
flask show-routes

# 显示当前配置
flask show-config
```

### 调试技巧

1. **启用调试模式**
   ```bash
   export FLASK_DEBUG=True
   flask run
   ```

2. **查看日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **使用调试接口**
   ```bash
   curl http://localhost/api/debug
   ```

## 🚀 生产环境部署

### 1. 使用 Gunicorn

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:80 app:app
```

### 2. 使用 Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 80
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "app:app"]
```

### 3. 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 安全建议

1. **生产环境配置**
   - 设置 `FLASK_ENV=production`
   - 使用强密码和加密连接
   - 配置防火墙和访问控制

2. **数据库安全**
   - 使用专用数据库用户
   - 限制数据库权限
   - 启用SSL连接

3. **应用安全**
   - 定期更新依赖包
   - 使用HTTPS
   - 配置请求限流

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查配置
   flask test-db
   
   # 检查网络连接
   ping your_db_host
   ```

2. **依赖包冲突**
   ```bash
   # 重新创建虚拟环境
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **端口占用**
   ```bash
   # 查看端口占用
   lsof -i :80
   
   # 使用其他端口
   flask run --port=8080
   ```

### 日志查看

```python
# 在 app.py 中添加详细日志
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

## 📈 性能优化

### 数据库优化

1. **添加索引**
   ```sql
   CREATE INDEX idx_created_at ON summit(created_at);
   CREATE INDEX idx_distinct_id_time ON summit(distinct_id, created_at);
   CREATE INDEX idx_event_time ON summit(event, created_at);
   ```

2. **查询优化**
   - 使用分页查询
   - 添加查询缓存
   - 优化复杂JSON查询

### 应用优化

1. **使用缓存**
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   
   @cache.cached(timeout=300)
   def get_dashboard_data():
       # 缓存仪表板数据
   ```

2. **异步处理**
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   # 并行处理多个查询
   with ThreadPoolExecutor() as executor:
       futures = [executor.submit(query_func, params) for params in param_list]
   ```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 发起 Pull Request

## 📞 技术支持

如有问题请：
1. 查看 [故障排除](#故障排除) 部分
2. 使用 `/api/debug` 接口检查系统状态
3. 查看应用日志
4. 提交 Issue 或联系开发团队

---

## 🎉 部署完成！

现在你的数据分析仪表板已经成功部署，可以开始进行用户路径分析了！