# 项目启动步骤

本文档详细介绍如何启动电商平台的前后端服务。

## 环境要求

### 前端环境
- Node.js 16+
- npm 8+

### 后端环境
- Python 3.8+
- MySQL 8.0+

---

## 第一步：启动后端服务

### 1.1 配置数据库

编辑 `config.yaml` 文件，确保数据库配置正确：

```yaml
database:
  host: localhost
  port: 3306
  username: root
  password: your_password
  name: shopping_site
```

### 1.2 初始化数据库

```bash
# 确保 MySQL 服务已启动
python scripts/init_db.py
```

### 1.3 启动后端服务

```bash
# 方式1：直接运行
python app/main.py

# 方式2：使用 uvicorn（推荐，支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动成功后，访问：
- API 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

---

## 第二步：启动前端服务

### 2.1 进入前端目录

```bash
cd vue
```

### 2.2 安装依赖

```bash
npm install
```

### 2.3 启动开发服务器

```bash
npm run dev
```

前端启动成功后，访问：http://localhost:3000

---

## 第三步：验证系统

### 3.1 访问前端页面

打开浏览器访问 http://localhost:3000 ，应该能看到商城首页。

### 3.2 测试 API 连接

在前端页面进行以下操作：
1. 注册新用户
2. 登录系统
3. 浏览商品
4. 添加购物车

如果以上操作正常，说明前后端连接成功。

---

## 常见问题

### Q1: 前端无法连接后端 API

检查后端服务是否启动，确保后端运行在 localhost:8000

### Q2: 数据库连接失败

```bash
# 检查 MySQL 服务状态
# Windows
services.msc

# Linux
systemctl status mysql
```

### Q3: 端口被占用

```bash
# 查找占用 8000 端口的进程
netstat -ano | findstr :8000

# 查找占用 3000 端口的进程
netstat -ano | findstr :3000
```

### Q4: 前端 SCSS 编译错误

确保已正确配置 vite.config.ts 中的 SCSS 预处理器选项。

---

## 项目结构

```
shopping_site_pro/
├── app/                    # 后端代码
│   ├── main.py            # FastAPI 入口
│   ├── router/           # API 路由
│   ├── service/          # 业务逻辑
│   ├── model/            # 数据模型
│   └── middleware/       # 中间件
├── vue/                   # 前端代码
│   ├── src/
│   │   ├── api/          # API 封装
│   │   ├── components/   # 组件
│   │   ├── views/        # 页面
│   │   ├── stores/       # 状态管理
│   │   └── router/       # 路由配置
│   └── package.json
├── config.yaml           # 配置文件
└── scripts/              # 脚本工具
```

---

## 生产环境部署（可选）

### 后端部署

使用 Nginx + uvicorn 部署后端，参考 README.md 中的部署指南。

### 前端构建

```bash
cd vue
npm run build
```

构建产物在 `vue/dist` 目录，可部署到任何静态服务器。