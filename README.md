# Shopping Site Pro - 电商平台

一个具备用户行为数据采集、离线数据分析、商品推荐系统的电商平台。

## 功能特性

- 用户注册/登录/注销（JWT认证）
- 商品展示与管理
- 购物车
- 订单确认机制（邮件确认链接 → 前端公开页面确认）
- 用户行为日志（浏览记录）
- 商品推荐系统（共现推荐 + 协同过滤）
- 数据分析（用户画像、销售趋势预测、异常检测）
- 反爬虫安全防护
- **后台分离**：管理员后台 `/admin` + 销售后台 `/sales`

## 技术栈

- **后端**: FastAPI + SQLAlchemy
- **数据库**: MySQL 8.0+
- **前端**: Vue3
- **Python**: 3.8+

## 快速开始

### 1. 环境要求

```bash
# 检查Python版本
python --version  # 需要 Python 3.8+
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库配置

修改 `config.yaml` 中的数据库连接信息：

```yaml
database:
  host: localhost      # MySQL主机
  port: 3306         # 端口
  username: root     # 用户名
  password: your_password  # 密码
  name: shopping_site   # 数据库名
```

### 4. 初始化数据库

```bash
# 确保MySQL服务已启动
python scripts/init_db.py
```

### 5. 启动服务

```bash
# 方式1：直接运行
python app/main.py

# 方式2：使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问API文档

- Swagger文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

## 项目结构

```
shopping_site_pro/
├── app/
│   ├── main.py                # FastAPI入口
│   ├── config.py             # 配置加载
│   ├── dependencies.py       # 认证依赖
│   ├── router/              # 路由层
│   │   ├── auth.py          # 认证接口
│   │   ├── product.py       # 商品接口
│   │   ├── cart.py         # 购物车接口
│   │   ├── order.py       # 订单接口
│   │   ├── recommend.py  # 推荐接口
│   │   ├── admin.py      # 管理接口
│   │   └── log.py       # 日志接口
│   ├── service/            # 服务层
│   ├── model/             # 数据模型
│   └── middleware/        # 中间件
├── scripts/
│   ├── init_db.py        # 数据库初始化
│   ├── recommend.py      # 推荐系统
│   └── analysis.py      # 数据分析
├── docs/                 # 文档
├── config.yaml           # 配置文件
└── requirements.txt    # 依赖列表
```

## API接口

### 认证接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/logout` | POST | 用户注销 |
| `/api/auth/me` | GET | 当前用户 |

### 商品接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/product` | GET | 商品列表 |
| `/api/product/{id}` | GET | 商品详情 |
| `/api/product` | POST | 创建商品（需Sales权限）|
| `/api/product/{id}` | PUT | 更新商品 |
| `/api/product/{id}` | DELETE | 删除商品 |

### 购物车接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/cart` | GET | 购物车列表 |
| `/api/cart` | POST | 添加商品 |
| `/api/cart/{id}` | PUT | 更新数量 |
| `/api/cart/{id}` | DELETE | 删除商品 |

### 订单接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/order` | POST | 创建订单 |
| `/api/order` | GET | 订单列表 |
| `/api/order/{id}` | GET | 订单详情 |
| `/api/order/confirm` | GET | 确认订单 |
| `/api/order/{id}/cancel` | POST | 取消订单 |

### 推荐接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/recommend/product/{id}` | GET | 商品相关推荐（共现推荐） |
| `/api/recommend/bought-also/{id}` | GET | 浏览过此商品的用户也买了 |
| `/api/recommend/user/me` | GET | 个性化推荐（需登录） |

### 管理接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/stats` | GET | 销售统计 |
| `/api/admin/orders` | GET | 订单列表 |
| `/api/admin/order/{order_id}` | GET | 订单详情 |
| `/api/admin/order/{order_id}/status` | PUT | 修改订单状态 |
| `/api/admin/order/{order_id}` | DELETE | 删除订单 |
| `/api/admin/users` | GET | 用户列表 |
| `/api/admin/logs` | GET | 操作日志 |
| `/api/admin/logs/browse` | GET | 用户行为日志 |
| `/api/admin/recommend/trigger` | POST | 触发推荐 |

## 角色权限

| 角色 | 权限 |
|------|------|
| customer | 浏览、下单、个人中心 |
| sales | 订单管理（查看/修改状态）、销售数据 |
| admin | 订单管理（查看/修改状态/删除）、用户管理、日志查看、手动触发推荐系统 |

## 定时任务

### 推荐系统（每日凌晨2点）

```bash
# 方式1：通过API触发（需要admin权限）
curl -X POST http://localhost:8000/api/admin/recommend/trigger \
  -H "Authorization: Bearer <your-token>"

# 方式2：直接运行脚本
python scripts/recommend.py

# 或设置定时任务
0 2 * * * python /path/to/scripts/recommend.py
```

### 数据分析（每日凌晨3点）

```bash
python scripts/analysis.py
```

## 部署指南

### 开发环境

```bash
# 1. 克隆项目
git clone <repository-url>
cd shopping_site_pro

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置数据库
# 修改config.yaml中的数据库配置

# 5. 初始化数据库
python scripts/init_db.py

# 6. 启动服务
python app/main.py
```

### 生产环境

#### 1. 服务器要求

- CPU: 2核+
- 内存: 4GB+
- 磁盘: 20GB+
- OS: Ubuntu 20.04+ / Windows Server 2019+

#### 2. 安装MySQL

**Ubuntu**:
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql
```

**配置MySQL**:
```bash
sudo mysql_secure_installation
sudo mysql -u root -p
CREATE USER 'shopuser'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON shopping_site.* TO 'shopuser'@'localhost';
FLUSH PRIVILEGES;
```

#### 3. 安装Python依赖

```bash
sudo apt install python3.10 python3-pip
pip install -r requirements.txt
```

#### 4. 配置生产环境

修改 `config.yaml`:

```yaml
app:
  host: 0.0.0.0
  port: 8000
  debug: false  # 关闭调试

jwt:
  secret: your-production-secret  # 更复杂的密钥
  expire_minutes: 60  # 缩短过期时间

security:
  ip_limit_per_minute: 30  # 更严格的限流
  max_login_attempts: 3
  block_duration_minutes: 60
```

#### 5. 使用Systemd（Ubuntu）

创建服务文件 `/etc/systemd/system/shopping_site.service`:

```ini
[Unit]
Description=Shopping Site Pro
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/shopping_site_pro
ExecStart=/usr/bin/python3 /var/www/shopping_site_pro/app/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务:
```bash
sudo systemctl daemon-reload
sudo systemctl start shopping_site
sudo systemctl enable shopping_site
```

#### 6. 使用Nginx反向代理

安装Nginx:
```bash
sudo apt install nginx
```

配置 `/etc/nginx/sites-available/shopping_site`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /var/www/shopping_site_pro/static;
    }
}
```

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/shopping_site /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl reload nginx
```

### Docker部署（可选）

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行:

```bash
docker build -t shopping_site_pro .
docker run -d -p 8000:8000 --name shopping_site shopping_site_pro
```

### Windows IIS部署

1. 安装IIS和URL Rewrite模块
2. 安装Python并配置为处理程序
3. 创建web.config:

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python Handler" path="*" verb="*" 
           modules="FastCGIModule" 
           scriptProcessor="C:\Python311\python.exe|C:\Python311\python.exe|D:\VS Code\python code\shopping_site_pro\app\main.py"
           resourceType="Unspecified" requireAccess="Script"/>
    </handlers>
  </system.webServer>
</configuration>
```

## 常见问题

### Q1: 连接MySQL失败

```bash
# 检查MySQL服务状态
systemctl status mysql  # Ubuntu
services.msc           # Windows
```

### Q2: ImportError

```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### Q3: 端口被占用

```bash
# 查找占用8000端口的进程
netstat -ano | findstr :8000
# 或
lsof -i :8000
```

### Q4: 中文乱码

确保数据库使用utf8mb4字符集，建表SQL已配置。

## 目录权限

```bash
# Ubuntu设置权限
sudo chown -R www-data:www-data /var/www/shopping_site_pro
sudo chmod -R 755 /var/www/shopping_site_pro
sudo chmod -R 775 /var/www/shopping_site_pro/logs
```

## 监控

### 检查服务状态

```bash
# 查看运行日志
journalctl -u shopping_site -f

# 或
docker logs shopping_site
```

### 健康检查

```bash
curl http://localhost:8000/health
```

## 备份

### 数据库备份

```bash
mysqldump -u root -p shopping_site > backup_$(date +%Y%m%d).sql
```

### 恢复

```bash
mysql -u root -p shopping_site < backup_20240101.sql
```

## SSL/HTTPS

使用Let's Encrypt免费SSL:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 联系支持

- 问题反馈: https://github.com/anomalyco/opencode/issues
- 文档更新: 定期检查项目仓库

---

**版本**: 1.0.0  
**最后更新**: 2024-01-01