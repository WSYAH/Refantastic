## 测试执行流程详解

当你运行 `pytest tests/test_document_service.py::TestDocumentService::test_create_document` 时：

### 1. Pytest 解析测试函数

```python
async def test_create_document(self, db_session, sample_document_data, sample_user_id):
    service = DocumentService(db_session)
    # ...
```

Pytest 发现测试函数需要 3 个 fixture：
- `db_session`
- `sample_document_data`
- `sample_user_id`

### 2. 构建依赖树

```
test_create_document
├── db_session (需要 engine)
│   └── engine
├── sample_document_data
└── sample_user_id
```

### 3. 按依赖顺序执行 Fixture

#### 步骤 1: 执行 engine fixture
```python
@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(...)  # 创建引擎
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # 创建表
    yield engine  # 🎯 返回 engine
    # 等待测试完成...
```

#### 步骤 2: 执行 db_session fixture
```python
@pytest_asyncio.fixture
async def db_session(engine):  # ⬅️ 接收上面的 engine
    async_session = async_sessionmaker(engine, ...)
    async with async_session() as session:
        async with session.begin():
            yield session  # 🎯 返回 session
            # 等待测试完成...
```

#### 步骤 3: 执行简单的 fixture
```python
@pytest.fixture
def sample_document_data():
    return {
        "title": "测试文档",
        # ...
    }  # 🎯 直接返回字典

@pytest.fixture
def sample_user_id():
    return "test-user-123"  # 🎯 直接返回字符串
```

#### 步骤 4: 执行测试函数
```python
async def test_create_document(
    self, 
    db_session,           # ⬅️ 接收 AsyncSession 对象
    sample_document_data, # ⬅️ 接收字典
    sample_user_id        # ⬅️ 接收字符串
):
    # 使用注入的值
    service = DocumentService(db_session)
    document = await service.create_document(**sample_document_data)
    assert document.creator_id == sample_user_id
```

#### 步骤 5: 清理（Teardown）
```python
# db_session fixture 的 teardown
await session.rollback()  # 回滚事务

# engine fixture 的 teardown
await engine.dispose()  # 关闭引擎
```

### 4. 关键点总结

1. **参数名匹配**: 测试函数的参数名必须与 fixture 名称完全匹配
   ```python
   # ✅ 正确
   def test_something(db_session):  # 参数名 = fixture 名
   
   # ❌ 错误
   def test_something(session):     # 找不到名为 session 的 fixture
   ```

2. **自动依赖注入**: pytest 会自动解析依赖关系
   ```python
   db_session 依赖 engine
   → pytest 先执行 engine
   → 再执行 db_session
   → 最后执行测试
   ```

3. **作用域隔离**: 每个测试都有独立的 session
   ```python
   @pytest_asyncio.fixture
   async def db_session(engine):
       # 每个测试都创建新的 session
       async with async_session() as session:
           yield session
           await session.rollback()  # 回滚保证数据隔离
   ```

4. **Yield 的作用**:
   ```python
   @pytest.fixture
   def my_fixture():
       # Setup: yield 之前的代码
       resource = create_resource()
       
       yield resource  # 传递给测试函数
       
       # Teardown: yield 之后的代码
       cleanup_resource(resource)
   ```

### 5. 完整示例对比

#### 不使用 Fixture (手动管理)
```python
async def test_create_document_manual():
    # 手动创建引擎
    engine = create_async_engine(...)
    
    # 手动创建会话
    async_session = async_sessionmaker(engine, ...)
    async with async_session() as session:
        # 手动创建服务
        service = DocumentService(session)
        
        # 手动创建测试数据
        data = {"title": "测试", ...}
        
        # 执行测试
        doc = await service.create_document(**data)
        assert doc.title == "测试"
        
        # 手动清理
        await session.rollback()
    
    # 手动关闭引擎
    await engine.dispose()
```

#### 使用 Fixture (自动管理)
```python
async def test_create_document(db_session, sample_document_data):
    # pytest 自动注入 db_session 和 sample_document_data
    service = DocumentService(db_session)
    doc = await service.create_document(**sample_document_data)
    assert doc.title == sample_document_data["title"]
    # pytest 自动清理
```

**优势**: 代码更简洁、复用性强、自动清理资源！
