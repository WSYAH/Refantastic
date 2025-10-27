# Refantastic 测试文档

## 目录
- [快速开始](#快速开始)
- [测试环境配置](#测试环境配置)
- [系统启动步骤](#系统启动步骤)
- [API 测试步骤](#api-测试步骤)
- [数据库测试数据](#数据库测试数据)
- [向量存储测试](#向量存储测试)
- [文档生成测试](#文档生成测试)
- [集成测试场景](#集成测试场景)

## 快速开始

### 前置要求
- Python 3.9+
- Node.js 16+
- Docker (用于 ChromaDB)
- Git

### 一键启动测试
```bash
# 克隆项目
git clone <repository-url>
cd Refantastic

# 安装依赖
cd backend
pip install -r requirements.txt

# 初始化测试数据
python scripts/init_test_db.py

# 运行测试
pytest tests/ -v

# 启动服务
python scripts/start_server.py
```

## 测试环境配置

### 环境变量
```bash
DEBUG=True
DATABASE_URL=sqlite+aiosqlite:///./test.db
VECTOR_STORE_TYPE=chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001
OPENAI_API_KEY=your_test_api_key
```

### 测试数据库初始化
```bash
# 创建测试数据库
python scripts/init_test_db.py

# 清理测试数据
python scripts/clean_test_db.py
```

### 1. 创建虚拟环境
```bash
# Windows
cd backend
python -m venv venv
venv\Scripts\activate

# Linux/Mac
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：
```bash
# 在 backend 目录下创建 .env 文件
cd backend
touch .env  # Linux/Mac
type nul > .env  # Windows
```

编辑 `.env` 文件：
```bash
# 应用配置
APP_NAME=Refantastic
APP_VERSION=0.1.0
DEBUG=True

# 数据库配置
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite+aiosqlite:///./refantastic.db

# 向量存储配置
VECTOR_STORE_TYPE=chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION_NAME=documents

# AI 配置 (可选)
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

### 4. 启动 ChromaDB (可选)

如果需要使用向量存储功能：
```bash
# 使用 Docker 启动 ChromaDB
docker run -d \
  --name chroma \
  -p 8001:8000 \
  -v chroma-data:/chroma/chroma \
  chromadb/chroma:latest

# 验证 ChromaDB 是否运行
curl http://localhost:8001/api/v1/heartbeat
```

## 系统启动步骤

### 方式 1: 使用启动脚本（推荐）

```bash
# 进入后端目录
cd backend

# 启动服务
python scripts/start_server.py
```

**预期输出：**
```
==================================================
启动 Refantastic v0.1.0
环境: 开发
数据库: sqlite
向量存储: chroma
==================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 方式 2: 直接运行 main.py

```bash
cd backend
python main.py
```

### 方式 3: 使用 uvicorn 命令

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 验证服务启动成功

打开浏览器访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

或使用 curl：
```bash
curl http://localhost:8000/
```

**预期响应：**
```json
{
  "name": "Refantastic",
  "version": "0.1.0",
  "status": "running"
}
```

## API 测试步骤

### 步骤 1: 健康检查测试

#### 1.1 测试根路径
```bash
curl http://localhost:8000/
```

**预期结果：** 返回状态码 200 和基本信息

#### 1.2 测试详细健康检查
```bash
curl http://localhost:8000/health
```

**预期结果：**
```json
{
  "status": "healthy",
  "database": "connected",
  "vector_store": "initialized"
}
```

### 步骤 2: 模板管理测试

#### 2.1 创建模板
```bash
curl -X POST http://localhost:8000/api/v1/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "请示报告",
    "category": "请示",
    "content": "{{title}}\n\n{{department}}:\n\n{{content}}\n\n特此请示。\n\n{{date}}",
    "variables": ["title", "department", "content", "date"],
    "description": "标准请示报告模板"
  }'
```

**预期结果：** 返回创建的模板，包含 id 字段

**保存返回的模板 ID：**
```bash
# 假设返回的 ID 为 1
TEMPLATE_ID=1
```

#### 2.2 查询所有模板
```bash
curl http://localhost:8000/api/v1/templates
```

**预期结果：** 返回模板列表数组

#### 2.3 查询单个模板
```bash
curl http://localhost:8000/api/v1/templates/1
```

**预期结果：** 返回指定 ID 的模板详情

#### 2.4 更新模板
```bash
curl -X PUT http://localhost:8000/api/v1/templates/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "请示报告(更新版)",
    "category": "请示",
    "content": "{{title}}\n\n{{department}}:\n\n{{content}}\n\n特此请示。\n\n{{date}}",
    "variables": ["title", "department", "content", "date"],
    "description": "更新后的请示报告模板"
  }'
```

#### 2.5 删除模板
```bash
curl -X DELETE http://localhost:8000/api/v1/templates/1
```

### 步骤 3: 文档生成测试

#### 3.1 基于模板生成文档
```bash
curl -X POST http://localhost:8000/api/v1/documents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "variables": {
      "title": "关于采购办公设备的请示",
      "department": "行政部",
      "content": "因业务发展需要，拟采购联想品牌电脑10台，单价约5000元，总预算5万元。采购后将提高工作效率，降低设备故障率。",
      "date": "2024年1月20日"
    }
  }'
```

**预期结果：** 返回生成的文档内容

**检查要点：**
- 变量是否正确替换
- 文档格式是否正确
- 内容是否完整

#### 3.2 查询生成的文档列表
```bash
curl http://localhost:8000/api/v1/documents
```

#### 3.3 查询单个文档
```bash
curl http://localhost:8000/api/v1/documents/1
```

### 步骤 4: 知识库功能测试

#### 4.1 上传参考文档

首先准备测试文件：
```bash
# 创建测试文档
echo "这是一份测试文档内容" > test_document.txt
```

上传文档：
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/upload \
  -F "file=@test_document.txt" \
  -F "category=测试文档" \
  -F "tags=测试,样例"
```

**预期结果：** 返回上传成功信息和文档 ID

#### 4.2 搜索相似文档
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试文档",
    "top_k": 5
  }'
```

**预期结果：** 返回相似度最高的文档列表

#### 4.3 获取知识库统计
```bash
curl http://localhost:8000/api/v1/knowledge/stats
```

### 步骤 5: AI 辅助生成测试（需要配置 API Key）

```bash
curl -X POST http://localhost:8000/api/v1/documents/ai-generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "写一份关于加强网络安全管理的通知，要求所有员工定期修改密码，不得使用简单密码",
    "document_type": "通知",
    "style": "正式",
    "max_length": 500
  }'
```

**预期结果：** 返回 AI 生成的文档内容

## 数据库测试数据

### 用户数据
```json
[
  {
    "id": 1,
    "username": "test_user1",
    "email": "test1@example.com",
    "department": "行政部",
    "role": "user"
  },
  {
    "id": 2,
    "username": "test_admin",
    "email": "admin@example.com",
    "department": "管理层",
    "role": "admin"
  }
]
```

### 文档模板数据
```json
[
  {
    "id": 1,
    "name": "请示报告",
    "category": "请示",
    "content": "{{title}}\n\n{{department}}:\n\n{{content}}\n\n特此请示。",
    "variables": ["title", "department", "content"],
    "is_active": true
  },
  {
    "id": 2,
    "name": "会议通知",
    "category": "通知",
    "content": "关于{{meeting_topic}}的通知\n\n各部门:\n\n定于{{meeting_time}}召开{{meeting_topic}}会议。",
    "variables": ["meeting_topic", "meeting_time"],
    "is_active": true
  },
  {
    "id": 3,
    "name": "工作总结",
    "category": "总结",
    "content": "{{period}}工作总结\n\n一、工作回顾\n{{review}}\n\n二、存在问题\n{{problems}}\n\n三、下步计划\n{{plans}}",
    "variables": ["period", "review", "problems", "plans"],
    "is_active": true
  }
]
```

### 生成的文档数据
```json
[
  {
    "id": 1,
    "title": "关于采购办公设备的请示",
    "content": "关于采购办公设备的请示...",
    "template_id": 1,
    "user_id": 1,
    "status": "draft"
  },
  {
    "id": 2,
    "title": "2024年第一季度工作总结",
    "content": "2024年第一季度工作总结...",
    "template_id": 3,
    "user_id": 1,
    "status": "published"
  }
]
```

## 向量存储测试

### 测试文档集
```python
test_documents = [
    {
        "id": "doc1",
        "content": "公司年度财务报表显示，营业收入同比增长15%，净利润增长12%。",
        "doc_metadata": {"type": "财务报告", "year": "2023"}  # 使用 doc_metadata
    },
    {
        "id": "doc2",
        "content": "关于规范公务接待流程的通知：严格执行公务接待标准，控制接待费用。",
        "doc_metadata": {"type": "制度文件", "category": "行政管理"}
    },
    {
        "id": "doc3",
        "content": "员工培训计划：本季度将开展职业技能培训、安全生产培训等课程。",
        "doc_metadata": {"type": "培训文件", "quarter": "Q1"}
    }
]
```

### 相似度搜索测试用例
```python
search_queries = [
    {
        "query": "财务收入情况",
        "expected_doc": "doc1",
        "min_similarity": 0.7
    },
    {
        "query": "公务接待规定",
        "expected_doc": "doc2",
        "min_similarity": 0.7
    },
    {
        "query": "员工培训",
        "expected_doc": "doc3",
        "min_similarity": 0.7
    }
]
```

### 问题 1: 服务启动失败

**症状：** 运行启动脚本后报错

**常见错误：**

#### 错误 1: "Attribute name 'metadata' is reserved"
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved 
when using the Declarative API.
```

**解决方案：**
- 这是因为模型中使用了 SQLAlchemy 保留字 `metadata`
- 已修复为使用 `doc_metadata` 字段
- 如果仍然出现此错误，请确保所有模型都已更新

#### 错误 2: 端口被占用
```bash
# Windows
netstat -ano | findstr :8000
# 找到进程 PID 后
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
# 找到进程后
kill -9 <PID>
```

#### 错误 3: 数据库迁移失败
```bash
# 1. 检查 Python 版本
python --version

# 2. 检查依赖是否安装
pip list

# 3. 重新初始化数据库
python scripts/clean_test_db.py
python scripts/init_test_db.py

# 4. 查看详细错误日志
python scripts/start_server.py 2>&1 | tee server.log
```

## 文档生成测试

### 测试场景 1: 请示报告生成
```json
{
  "scenario": "采购申请",
  "input": {
    "template_id": 1,
    "variables": {
      "title": "关于采购办公电脑的请示",
      "department": "信息技术部",
      "content": "为满足日常办公需求，拟采购联想品牌台式电脑20台，单价约5000元，总预算10万元。采购后将提高工作效率，降低设备故障率。",
      "date": "2024年1月20日"
    }
  },
  "expected_output": {
    "contains": ["采购", "电脑", "预算", "请示"],
    "format": "标准公文格式",
    "length_min": 100
  }
}
```

### 测试场景 2: 会议通知生成
```json
{
  "scenario": "会议通知",
  "input": {
    "template_id": 2,
    "variables": {
      "meeting_topic": "年度工作总结大会",
      "meeting_time": "2024年1月25日上午9:00",
      "meeting_location": "公司大会议室",
      "participants": "全体员工"
    }
  },
  "expected_output": {
    "contains": ["通知", "会议", "时间", "地点"],
    "format": "通知格式",
    "length_min": 80
  }
}
```

### 测试场景 3: AI 智能生成
```json
{
  "scenario": "AI辅助写作",
  "input": {
    "prompt": "写一份关于加强网络安全管理的通知，要求所有员工定期修改密码，不得使用简单密码",
    "document_type": "通知",
    "style": "正式",
    "context": "近期发现多起密码泄露事件"
  },
  "expected_output": {
    "contains": ["网络安全", "密码", "通知"],
    "tone": "严肃、正式",
    "length_range": [200, 500]
  }
}
```

## 集成测试场景

### 场景 1: 完整文档生成流程
```
1. 用户登录
2. 浏览模板列表
3. 选择"请示报告"模板
4. 填写变量信息
5. 生成文档
6. 保存草稿
7. 查看历史记录
```

### 场景 2: 基于知识库的智能生成
```
1. 上传参考文档到知识库
2. 搜索相关历史文档
3. 使用 AI 生成新文档
4. 参考相似文档进行优化
5. 发布文档
```

### 场景 3: 模板管理流程
```
1. 管理员创建新模板
2. 设置模板变量
3. 测试模板生成效果
4. 激活模板供用户使用
5. 用户使用模板生成文档
```

## 性能测试指标

### 响应时间要求
- API 健康检查: < 100ms
- 模板列表查询: < 200ms
- 文档生成(模板): < 500ms
- AI 文档生成: < 3000ms
- 向量搜索: < 1000ms

### 并发测试
```bash
# 使用 Apache Bench 进行并发测试
ab -n 1000 -c 10 http://localhost:8000/api/v1/templates

# 使用 Locust 进行负载测试
locust -f tests/load_test.py --host=http://localhost:8000
```

### 数据量测试
- 模板数量: 100+
- 历史文档: 10000+
- 知识库文档: 1000+
- 并发用户: 50+

## 测试清单

- [ ] 所有 API 端点正常响应
- [ ] 数据库 CRUD 操作正常
- [ ] 向量存储读写正常
- [ ] 模板变量替换正确
- [ ] AI 生成内容质量达标
- [ ] 文件上传下载功能正常
- [ ] 权限控制有效
- [ ] 错误处理完善
- [ ] 日志记录完整
- [ ] 性能指标达标

## 常见问题排查

### 问题 1: 向量存储连接失败
```bash
# 检查 ChromaDB 服务
docker ps | grep chroma

# 重启服务
docker restart chroma
```

### 问题 2: 数据库迁移失败
```bash
# 查看迁移状态
alembic current

# 重新迁移
alembic downgrade -1
alembic upgrade head
```

### 问题 3: AI 生成超时
```bash
# 检查 API 配置
echo $OPENAI_API_KEY

# 增加超时时间
export API_TIMEOUT=60
```

## 测试报告模板

```markdown
# 测试报告 - [日期]

## 测试概述
- 测试时间: 
- 测试人员: 
- 测试环境: 

## 测试结果
- 通过用例: X/Y
- 失败用例: 
- 阻塞问题: 

## 详细结果
| 用例编号 | 用例名称 | 测试结果 | 备注 |
|---------|---------|---------|------|
| TC001   | 健康检查 | ✅ Pass | |
| TC002   | 模板创建 | ❌ Fail | 变量验证失败 |

## 问题列表
1. [BUG-001] 模板变量验证逻辑错误
2. [BUG-002] AI 生成偶尔超时

## 建议
- 优化向量搜索性能
- 增加更多错误处理
- 完善文档说明
```
