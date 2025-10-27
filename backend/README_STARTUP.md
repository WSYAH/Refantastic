# Refantastic 后端服务启动指南

## 前置条件

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**（可选）
   创建 `.env` 文件：
   ```env
   APP_NAME=Refantastic
   APP_VERSION=1.0.0
   DEBUG=true
   DATABASE_URL=sqlite+aiosqlite:///./refantastic.db
   ```

3. **初始化数据**（可选）

   **方式一：自动初始化（推荐）**
   
   直接启动服务，系统会自动检查并创建默认数据：
   - 1 个管理员用户 (admin / admin123)
   - 3 个默认模板（通用、通知、申请）
   - 3 个默认工作流
   
   **方式二：手动初始化默认数据**
   ```bash
   cd scripts
   python init_default_data.py
   ```
   
   **方式三：创建完整测试数据**
   ```bash
   cd scripts
   python create_test_data.py
   ```

## 数据初始化说明

### 🔍 系统启动检查

系统启动时会自动检查以下必需数据：

| 表名 | 检查项 | 默认行为 |
|------|--------|----------|
| User | 用户数 > 0 | 否：创建默认管理员 |
| Template | 模板数 > 0 | 否：创建 3 个默认模板 |
| Workflow | 工作流数 > 0 | 否：创建 3 个默认工作流 |

### 📦 默认数据内容

**用户 (User)**
- admin / admin123 - 系统管理员

**模板 (Template)**
1. 通用文档模板
2. 通知模板
3. 申请模板

**工作流 (Workflow)**
1. 简单审批流程（通用）
2. 通知发布流程（通知）
3. 申请审批流程（申请）

## 启动方式

### 方式一：使用启动脚本（推荐）

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

或直接运行 Python 脚本：
```bash
# 开发环境（自动检查默认数据）
python start_dev.py

# 生产环境
python start_prod.py
```

### 方式二：直接运行

```bash
python main.py
```

### 方式三：使用 uvicorn 命令

**开发环境（带热重载）:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**生产环境（多进程）:**
```bash
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

## 访问服务

启动成功后，可以访问：

- **主页**: http://localhost:8000
- **健康检查**: http://localhost:8000/health
- **API 文档 (Swagger)**: http://localhost:8000/docs
- **API 文档 (ReDoc)**: http://localhost:8000/redoc

## 测试账号

### 默认账号（自动创建）
| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | admin123 | 系统管理员 | 自动创建，用于基本功能测试 |

### 完整测试账号（需运行 create_test_data.py）
| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | password123 | 系统管理员 | 完整权限 |
| manager1 | password123 | 部门经理 | 审批权限 |
| employee1 | password123 | 普通员工 | 基本操作 |
| approver1 | password123 | 审批人 | 审批权限 |

## 常见问题

### 1. 端口被占用
```bash
# 修改端口
uvicorn main:app --port 8001
```

### 2. 导入错误
确保在 backend 目录下运行，或设置 PYTHONPATH：
```bash
export PYTHONPATH=/path/to/backend:$PYTHONPATH  # Linux/Mac
set PYTHONPATH=D:\path\to\backend  # Windows
```

### 3. 数据库连接失败
检查数据库文件是否存在，运行初始化脚本：
```bash
cd scripts
python init_default_data.py
```

### 4. 外键约束错误
如果创建 Document 时出现外键错误，说明缺少默认数据：
```bash
# 运行默认数据初始化
python scripts/init_default_data.py

# 或重启服务（自动检查并创建）
python start_dev.py
```

## 数据管理

### 查看数据库内容
```bash
cd scripts
python read_test_data.py
```

### 重置数据库
```bash
# 删除数据库文件
rm refantastic.db  # Linux/Mac
del refantastic.db  # Windows

# 重新启动服务（自动创建默认数据）
python start_dev.py
```

### 创建完整测试数据
```bash
cd scripts
python create_test_data.py
```

## 停止服务

按 `Ctrl + C` 停止服务

## 日志查看

日志输出到控制台，使用 loguru 进行日志管理。

## 开发建议

1. **首次使用**: 直接运行 `python start_dev.py`，系统会自动创建默认数据
2. **完整测试**: 运行 `python scripts/create_test_data.py` 创建完整数据集
3. **生产环境**: 使用 `python start_prod.py` 并提前准备好数据
