# 测试一下pytest是否可用，以及asyncio标记是否可用



import pytest

import asyncio 
@pytest.mark.asyncio
async def test_asyncio_marker_works():
    """测试 asyncio 标记是否正常工作"""
    assert True

@pytest.mark.asyncio
async def test_async_operation():
    """测试异步操作"""
    await asyncio.sleep(0.1)
    result = 1 + 1
    assert result == 2