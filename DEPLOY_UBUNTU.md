# Shopping Site Pro — Ubuntu 24.04 部署指南

## 架构概览

```
浏览器 ─── http://<公网IP>:80 ─── Nginx
                                      ├── /            → /var/www/shopping_site/  (Vue dist)
                                      ├── /api/*       → proxy → FastAPI :8000
                                      ├── /uploads/*   → proxy → FastAPI :8000
                                      ├── /docs        → proxy → FastAPI :8000
                                      └── /health      → proxy → FastAPI :8000
                                                              │
                                                              ▼
                                              FastAPI (uvicorn, systemd, :8000)
                                                              │
                                                              ▼
                                                          MySQL 8.0
```

---

## 一、服务器准备

### 1.1 阿里云 ECS 选购

| 项目 | 建议值 |
|------|--------|
| 实例规格 | 2 vCPU / 2 GiB（ecs.c7.large 或 ecs.e 系列） |
| 操作系统 | **Ubuntu 24.04 LTS** |
| 系统盘 | 40 GiB ESSD Entry |
| 公网带宽 | 按流量计费（小站推荐）或 1-3 Mbps 固定 |

### 1.2 安全组规则

> 阿里云控制台 → 云服务器 ECS → 安全组 → 配置规则

| 方向 | 端口 | 协议 | 来源 | 说明 |
|------|------|------|------|------|
| 入方向 | 22 | TCP | `0.0.0.0/0` | SSH 登录 + Git |
| 入方向 | 80 | TCP | `0.0.0.0/0` | HTTP 访问 |

> **8000 端口不需要开放**：FastAPI 只监听 127.0.0.1，由 Nginx 统一代理。

### 1.3 SSH 登录

```bash
ssh root@<你的公网IP>
```

---

## 二、本地准备（Windows）

### 2.1 初始化 Git 仓库并创建 .gitignore

在项目根目录执行：

```powershell
cd "D:\VS Code\python code\shopping_site_pro"
git init
```

创建 `.gitignore`：

```powershell
# 在项目根目录创建 .gitignore，内容如下：
```

```
# .gitignore
config.yaml
*.pyc
__pycache__/
*.egg-info/
.env
.venv/
venv/
node_modules/
vue/dist/
uploads/
*.log
.vscode/

# IDE
.idea/
*.swp
*.swo

# OS
Thumbs.db
.DS_Store
```

```powershell
# 首次提交
git add .
git commit -m "init: initial project commit"
```

> **重要：** `config.yaml` 已加入 .gitignore，包含敏感信息（数据库密码、JWT 密钥、SMTP 凭证）不会被提交。部署时在服务器手动创建。

### 2.2 设置 Git 远程仓库

两种方案任选其一：

**方案 A：推送到服务器裸仓库**（推荐，无需第三方平台）

```powershell
# 先在服务器上创建裸仓库（SSH 到服务器执行）
ssh root@<公网IP> "git init --bare /opt/shopping_site_pro.git"

# 返回本地，添加远程仓库并推送
git remote add origin ssh://root@<公网IP>/opt/shopping_site_pro.git
git push -u origin master
```

**方案 B：使用 GitHub / Gitee 私有仓库**

先在 GitHub/Gitee 上创建私有仓库，然后：

```powershell
git remote add origin git@github.com:<用户名>/shopping_site_pro.git
# 或 Gitee: git remote add origin git@gitee.com:<用户名>/shopping_site_pro.git
git push -u origin master
```

> 国内服务器推荐 Gitee（码云），访问速度更快。

---

## 三、系统环境安装

SSH 到服务器后执行：

### 3.1 更新系统

```bash
apt update && apt upgrade -y
```

### 3.2 安装必要工具

```bash
apt install -y curl wget vim git unzip build-essential
```

### 3.3 Python 环境

Ubuntu 24.04 自带 Python 3.12：

```bash
python3 --version        # 应显示 Python 3.12.x
apt install -y python3-pip python3-venv python3-dev
```

### 3.4 安装 MySQL 8.0

```bash
apt install -y mysql-server

systemctl enable mysql
systemctl start mysql
```

#### MySQL 安全初始化

```bash
mysql_secure_installation
```

交互步骤选择：

```
Enter password for user root: 直接回车（首次无密码）
VALIDATE PASSWORD COMPONENT: N          # 不启用密码强度验证
Remove anonymous users? Y
Disallow root login remotely? Y
Remove test database and access to it? Y
Reload privilege tables now? Y
```

#### 设置 root 密码（如安全脚本未设置）

```bash
mysql -u root
```

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '你的root密码';
FLUSH PRIVILEGES;
```

#### 创建项目数据库和专用用户

```sql
CREATE DATABASE shopping_site CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'shop_user'@'localhost' IDENTIFIED BY '你的项目数据库密码';
GRANT ALL PRIVILEGES ON shopping_site.* TO 'shop_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 优化低配服务器 MySQL（2C2G）

```bash
vim /etc/mysql/mysql.conf.d/mysqld.cnf
```

在 `[mysqld]` 段添加：

```ini
innodb_buffer_pool_size = 256M
innodb_log_file_size   = 64M
max_connections        = 150
table_open_cache       = 256
performance_schema     = OFF
```

```bash
systemctl restart mysql
```

### 3.5 安装 Nginx

```bash
apt install -y nginx
systemctl enable nginx
```

---

## 四、拉取项目代码

### 4.1 克隆仓库

```bash
# 如果是方案 A（服务器裸仓库）
git clone /opt/shopping_site_pro.git /opt/shopping_site_pro

# 如果是方案 B（GitHub/Gitee）
git clone <你的仓库地址> /opt/shopping_site_pro
```

### 4.2 创建生产配置文件

```bash
cd /opt/shopping_site_pro
vim config.yaml
```

**config.yaml 内容（根据你的实际情况填写）：**

```yaml
database:
  host: localhost
  port: 3306
  username: shop_user                  # ← 第 3.4 节创建的用户
  password: "你的项目数据库密码"         # ← 第 3.4 节设置的密码
  name: shopping_site

app:
  host: 0.0.0.0
  port: 8000
  debug: false
  frontend_url: http://<你的公网IP>     # ← 用于订单邮件中的链接

jwt:
  secret: <运行下方命令生成的随机字符串>  # ← 部署前必须更换
  algorithm: HS256
  expire_minutes: 1440     # 24小时

security:
  ip_limit_per_minute: 60
  max_login_attempts: 5
  block_duration_minutes: 30

smtp:
  host: smtp.qq.com
  port: 587
  username: ""              # ← 如需邮件功能，填入 QQ 邮箱
  password: ""              # ← 填入 QQ 邮箱授权码（非密码）
  use_tls: true
```

> **生成 JWT 密钥：**
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```
> 把输出粘贴到 `secret:` 后面。

```bash
# 保护配置文件
chmod 600 /opt/shopping_site_pro/config.yaml
```

### 4.3 创建上传目录

```bash
mkdir -p /opt/shopping_site_pro/app/uploads
chmod 755 /opt/shopping_site_pro/app/uploads
```

---

## 五、构建前端

### 5.1 安装 Node.js

> Ubuntu 24.04 仓库中的 Node.js 较旧，建议使用 NodeSource 安装 LTS 版本。

```bash
# 安装 Node.js 20.x LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 验证
node --version     # v20.x.x
npm --version      # 10.x.x
```

### 5.2 构建

```bash
cd /opt/shopping_site_pro/vue
npm install
npm run build

# 部署到 Nginx 目录
mkdir -p /var/www/shopping_site
cp -r dist/* /var/www/shopping_site/
```

> **如果 npm run build 内存不足 OOM**，增加 swap：
> ```bash
> fallocate -l 2G /swapfile
> chmod 600 /swapfile
> mkswap /swapfile
> swapon /swapfile
> ```
> 或者采用备用方案：本地 Windows 构建 dist，然后 scp 上传：
> ```powershell
> scp -r "D:\VS Code\python code\shopping_site_pro\vue\dist\*" root@<公网IP>:/var/www/shopping_site/
> ```

---

## 六、安装 Python 依赖与初始化数据库

### 6.1 创建虚拟环境并安装依赖

```bash
cd /opt/shopping_site_pro
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> 如果 `mysql-connector-python==9.6.0` 构建失败：
> ```bash
> pip install mysql-connector-python==8.0.33
> ```

### 6.2 初始化数据库

```bash
cd /opt/shopping_site_pro
source venv/bin/activate
python3 scripts/init_db.py
```

期望输出：

```
Database 'shopping_site' already exists
Creating database tables...
Default roles created
Default admin user created: username=123456, password=123456
Database tables created successfully!
Done!
```

> **默认管理员：** 用户名 `123456`，密码 `123456`。**部署后立即登录修改密码。**

---

## 七、已修复：生产环境关键配置

以下两项已在代码层面修复，无需手动操作：

| 问题 | 之前 | 修复后 |
|------|------|--------|
| **Nginx 反向代理下真实 IP 丢失** | `request.client.host` 始终返回 `127.0.0.1`，导致所有用户共用限流计数器、误封会使全站 403 | uvicorn 启动参数加 `--proxy-headers`（见第八节），安全中间件现在能正确获取真实客户端 IP |
| **HTTP 环境下发送 HSTS 头** | `security.py` 无条件发送 `Strict-Transport-Security`，虽浏览器忽略但属不良实践 | 已注释 `app/middleware/security.py` 第 161 行 |

你可以在 GitHub/Gitee 上这样查看已合并的修复：

```bash
git log --oneline
# 或者检查这些文件的改动
git diff HEAD~1 app/middleware/security.py
```

---

## 八、创建 systemd 服务

```bash
vim /etc/systemd/system/shopping_site.service
```

内容：

```ini
[Unit]
Description=Shopping Site Pro Backend API
After=network.target mysql.service
Requires=mysql.service

[Service]
User=root
Group=root
WorkingDirectory=/opt/shopping_site_pro
ExecStart=/opt/shopping_site_pro/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

> **关键参数说明：**
> - `--host 127.0.0.1`：只监听本地回环，不暴露到公网（由 Nginx 代理）
> - `--proxy-headers`：信任 Nginx 传入的 `X-Forwarded-*` 头，限流中间件借此拿到真实 IP
> - `Requires=mysql.service`：确保 MySQL 先启动

```bash
systemctl daemon-reload
systemctl enable shopping_site
systemctl start shopping_site

systemctl status shopping_site
```

---

## 九、配置 Nginx

```bash
vim /etc/nginx/sites-available/shopping_site
```

内容：

```nginx
server {
    listen 80 default_server;
    server_name _;    # 匹配所有请求（无域名）

    access_log /var/log/nginx/shopping_site_access.log;
    error_log  /var/log/nginx/shopping_site_error.log;

    # 上传文件大小限制（与后端 MAX_FILE_SIZE=5MB 对齐）
    client_max_body_size 10m;

    # Vue 前端静态文件
    root /var/www/shopping_site;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;   # SPA history 模式回退
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # 上传文件（StaticFiles 挂载）
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    # API 文档（可选，生产环境建议删除或加 IP 限制）
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

启用站点：

```bash
# 删除默认站点
rm -f /etc/nginx/sites-enabled/default

# 启用
ln -s /etc/nginx/sites-available/shopping_site /etc/nginx/sites-enabled/

# 测试 + 重载
nginx -t
systemctl reload nginx
```

---

## 十、验证部署

### 在服务器上自检

```bash
# 健康检查（直连 FastAPI）
curl http://127.0.0.1:8000/health
# → {"status":"healthy"}

# 健康检查（通过 Nginx）
curl http://127.0.0.1/health
# → {"status":"healthy"}

# 静态文件
curl -s http://127.0.0.1/ | head -5
# → 返回 <!DOCTYPE html>

# API
curl http://127.0.0.1/api/product/list
# → {"success": true, "data": [...]}
```

### 在浏览器中验证

| URL | 预期效果 |
|-----|---------|
| `http://<公网IP>` | 商城首页 |
| `http://<公网IP>/health` | `{"status":"healthy"}` |
| `http://<公网IP>/docs` | Swagger API 文档 |

### 登录验证

用默认管理员账号 `123456 / 123456` 登录，验证：

- 商品浏览与搜索
- 购物车加购
- 提交订单（邮件功能未配置时，订单仍会创建但不会发确认邮件）
- 管理后台：`http://<公网IP>/admin`
- 销售后台：`http://<公网IP>/sales`

---

## 十一、设置定时任务

```bash
crontab -e
```

添加：

```
# 每天凌晨 2:00 运行推荐引擎
0 2 * * * cd /opt/shopping_site_pro && /opt/shopping_site_pro/venv/bin/python scripts/recommend.py >> /var/log/recommend.log 2>&1

# 每天凌晨 3:00 运行数据分析
0 3 * * * cd /opt/shopping_site_pro && /opt/shopping_site_pro/venv/bin/python scripts/analysis.py >> /var/log/analysis.log 2>&1
```

---

## 十二、日常更新流程

代码修改后，通过 Git 同步到服务器：

### 本地操作

```powershell
cd "D:\VS Code\python code\shopping_site_pro"

# 如果修改了前端代码，重新构建
cd vue
npm run build
cd ..

# 提交并推送（注意：config.yaml 和 vue/dist 在 .gitignore 中）
git add .
git commit -m "fix: 修复 xxx 问题"
git push origin master
```

### 服务器操作

```bash
cd /opt/shopping_site_pro

# 拉取最新代码
git pull origin master

# 如果 requirements.txt 有变更，安装新依赖
source venv/bin/activate
pip install -r requirements.txt

# 如果前端代码有变更，重新构建
cd vue
npm install
npm run build
cp -r dist/* /var/www/shopping_site/
cd ..

# 重启后端服务
systemctl restart shopping_site
```

> **快速重启脚本**（保存为 `/opt/update.sh`）：
> ```bash
> #!/bin/bash
> set -e
> cd /opt/shopping_site_pro
> echo "Pulling latest code..."
> git pull origin master
> source venv/bin/activate
> pip install -r requirements.txt -q 2>/dev/null
> echo "Restarting service..."
> systemctl restart shopping_site
> echo "Done! Status:"
> systemctl status shopping_site --no-pager | head -5
> ```
> ```bash
> chmod +x /opt/update.sh
> ```

---

## 十三、安全检查清单

| # | 检查项 | 操作 |
|---|--------|------|
| 1 | JWT 密钥 | 已更换为随机生成的 64 位十六进制字符串 |
| 2 | 数据库密码 | 已使用专用强密码而非 `123456` |
| 3 | 默认管理员密码 | 部署后立刻通过网页登录并修改 |
| 4 | SMTP 凭证 | 已填入 QQ 邮箱和授权码（如需邮件功能） |
| 5 | `/docs` 页面 | 考虑加 IP 白名单或删除 Nginx 中的 location 块 |
| 6 | MySQL root 密码 | 已设置强密码 |
| 7 | `config.yaml` 权限 | `chmod 600`（`ls -la /opt/shopping_site_pro/config.yaml` 确认） |
| 8 | `.gitignore` | 确认 `config.yaml` 不在 Git 仓库中 |
| 9 | 服务器安全 | 非必要端口不开放、定期 `apt update` |

---

## 十四、故障排查

### API 502 Bad Gateway

```bash
systemctl status shopping_site
journalctl -u shopping_site -n 50 --no-pager
```

常见原因：`config.yaml` 格式错误（检查缩进使用空格而非 Tab）、数据库连接失败。

### Nginx 403 Forbidden

```bash
chmod -R 755 /var/www/shopping_site
chown -R root:root /var/www/shopping_site
```

### 首页能访问但 API 请求全部 404

检查 `vue/.env` 中 `VITE_API_BASE_URL` 是否为 `/api`，并确保已重新构建前端。

### Python 依赖安装失败

- `bcrypt` 失败 → `apt install -y build-essential python3-dev`
- `mysql-connector-python` 版本问题 → `pip install mysql-connector-python==8.0.33`

### 内存不足 OOM

```bash
free -h
# 如果 MySQL 占用过多，进一步降低缓冲池：
# vim /etc/mysql/mysql.conf.d/mysqld.cnf
# innodb_buffer_pool_size = 128M
# systemctl restart mysql
```

### Git push 被拒绝（服务器裸仓库权限问题）

```bash
# 在服务器上
chown -R root:root /opt/shopping_site_pro.git
chmod -R 755 /opt/shopping_site_pro.git
```

---

## 附录：一键部署脚本

> **使用前确保：** 项目已推送到 Git 仓库，且已在服务器上 `git clone` 到 `/opt/shopping_site_pro`。config.yaml 已手动创建。

将以下内容保存为 `/opt/setup.sh`：

```bash
#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "用法: bash setup.sh <公网IP>"
    echo "示例: bash setup.sh 47.96.123.45"
    exit 1
fi

PUBLIC_IP="$1"

echo "=== Shopping Site Pro 环境安装 ==="
echo "前置条件: 项目已 git clone 到 /opt/shopping_site_pro"
echo "          /opt/shopping_site_pro/config.yaml 已配置"
echo ""
read -p "确认继续? (y/n): " confirm
if [ "$confirm" != "y" ]; then exit 0; fi

# 1. 安装系统依赖
echo "[1/6] 安装系统依赖..."
apt update
apt install -y mysql-server nginx python3-pip python3-venv python3-dev build-essential git curl

# 2. 配置 MySQL
echo "[2/6] 配置 MySQL..."
systemctl start mysql
systemctl enable mysql

# 3. 安装 Node.js 并构建前端
echo "[3/6] 构建前端..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
fi
cd /opt/shopping_site_pro/vue
npm install
npm run build
mkdir -p /var/www/shopping_site
cp -r dist/* /var/www/shopping_site/

# 4. Python 依赖 + 数据库初始化
echo "[4/6] 安装 Python 依赖并初始化数据库..."
cd /opt/shopping_site_pro
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || pip install mysql-connector-python==8.0.33
mkdir -p app/uploads
chmod 755 app/uploads
python3 scripts/init_db.py

# 5. systemd 服务
echo "[5/6] 配置 systemd 服务..."
cat > /etc/systemd/system/shopping_site.service <<'UNIT'
[Unit]
Description=Shopping Site Pro Backend API
After=network.target mysql.service
Requires=mysql.service

[Service]
User=root
Group=root
WorkingDirectory=/opt/shopping_site_pro
ExecStart=/opt/shopping_site_pro/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable shopping_site
systemctl start shopping_site

# 6. Nginx
echo "[6/6] 配置 Nginx..."
cat > /etc/nginx/sites-available/shopping_site <<'NGINX'
server {
    listen 80 default_server;
    server_name _;

    access_log /var/log/nginx/shopping_site_access.log;
    error_log  /var/log/nginx/shopping_site_error.log;

    client_max_body_size 10m;

    root /var/www/shopping_site;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
NGINX

rm -f /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/shopping_site /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo ""
echo "========================================"
echo "  环境安装完成!"
echo "========================================"
echo ""
echo "  访问地址: http://${PUBLIC_IP}"
echo "  API 文档: http://${PUBLIC_IP}/docs"
echo ""
echo "  管理员: 123456 / 123456 (请立即修改)"
echo ""
```

> **使用方法：** 在服务器上执行 `bash /opt/setup.sh <公网IP>`
>
> 注意：此脚本不包含 MySQL 数据库和用户的创建步骤（需提前手动执行 3.4 节），也不生成 config.yaml（需提前手动创建 4.2 节）。

---

## 十五、日志检查

```bash
journalctl -u shopping_site -f               # 应用日志
tail -f /var/log/nginx/shopping_site_access.log   # Nginx 访问日志
tail -f /var/log/nginx/shopping_site_error.log    # Nginx 错误日志
tail -f /var/log/mysql/error.log             # MySQL 错误日志
```
