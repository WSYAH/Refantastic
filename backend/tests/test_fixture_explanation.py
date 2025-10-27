"""
Pytest Fixture 机制说明示例
"""
import pytest

# ============ Fixture 定义 ============

@pytest.fixture
def simple_fixture():
    """
    简单的 fixture 示例
    """
    print("\n[setup] 创建 simple_fixture")
    value = "Hello"
    yield value  # 将 value 传递给使用它的测试函数
    print("[teardown] 清理 simple_fixture")


@pytest.fixture
def dependent_fixture(simple_fixture):
    """
    依赖其他 fixture 的示例
    
    参数 simple_fixture 会自动注入上面定义的 simple_fixture 的返回值
    """
    print(f"[setup] 创建 dependent_fixture，收到: {simple_fixture}")
    value = f"{simple_fixture} World"
    yield value
    print("[teardown] 清理 dependent_fixture")


# ============ 测试函数 ============

def test_with_simple_fixture(simple_fixture):
    """
    使用 simple_fixture 的测试
    
    参数名 simple_fixture 告诉 pytest：
    "我需要名为 simple_fixture 的 fixture"
    
    执行流程：
    1. pytest 发现测试函数需要 simple_fixture
    2. 查找并执行 simple_fixture fixture
    3. simple_fixture yield 'Hello'
    4. pytest 将 'Hello' 作为参数传递给测试函数
    5. 测试函数执行 assert
    6. 测试结束，执行 simple_fixture 的 teardown
    """
    print(f"[test] 收到的值: {simple_fixture}")
    assert simple_fixture == "Hello"


def test_with_dependent_fixture(dependent_fixture):
    """
    使用依赖其他 fixture 的测试
    
    执行流程：
    1. pytest 发现需要 dependent_fixture
    2. dependent_fixture 依赖 simple_fixture
    3. 先执行 simple_fixture (yield "Hello")
    4. 再执行 dependent_fixture (收到 "Hello", yield "Hello World")
    5. 测试函数收到 "Hello World"
    6. 测试结束后，依次清理 dependent_fixture、simple_fixture
    """
    print(f"[test] 收到的值: {dependent_fixture}")
    assert dependent_fixture == "Hello World"


# ============ 异步 Fixture 示例 ============

@pytest_asyncio.fixture
async def async_fixture():
    """
    异步 fixture 示例
    
    需要使用 @pytest_asyncio.fixture 装饰器
    """
    print("\n[async setup] 创建异步资源")
    await asyncio.sleep(0.1)  # 模拟异步操作
    yield "async value"
    print("[async teardown] 清理异步资源")
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_with_async_fixture(async_fixture):
    """
    使用异步 fixture 的测试
    
    需要：
    1. 测试函数用 async def 定义
    2. 添加 @pytest.mark.asyncio 装饰器
    3. fixture 用 @pytest_asyncio.fixture 装饰
    """
    print(f"[async test] 收到的值: {async_fixture}")
    assert async_fixture == "async value"
