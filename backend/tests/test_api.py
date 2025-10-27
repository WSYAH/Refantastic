# import pytest
# from httpx import AsyncClient


# class TestHealthCheck:
#     """健康检查测试"""
    
#     @pytest.mark.asyncio
#     async def test_root(self, client: AsyncClient):
#         """测试根路径"""
#         response = await client.get("/")
#         assert response.status_code == 200
#         data = response.json()
#         assert data["name"] == "Refantastic"
#         assert data["status"] == "running"
    
#     @pytest.mark.asyncio
#     async def test_health(self, client: AsyncClient):
#         """测试健康检查"""
#         response = await client.get("/health")
#         assert response.status_code == 200
#         data = response.json()
#         assert data["status"] == "healthy"


# class TestTemplateAPI:
#     """模板 API 测试"""
    
#     @pytest.mark.asyncio
#     async def test_create_template(self, client: AsyncClient, sample_template_data):
#         """测试创建模板"""
#         response = await client.post(
#             "/api/v1/templates",
#             json=sample_template_data
#         )
#         assert response.status_code == 200
#         data = response.json()
#         assert data["name"] == sample_template_data["name"]
#         assert data["category"] == sample_template_data["category"]
#         assert "id" in data
    
#     @pytest.mark.asyncio
#     async def test_list_templates(self, client: AsyncClient, sample_template_data):
#         """测试获取模板列表"""
#         # 先创建一个模板
#         await client.post("/api/v1/templates", json=sample_template_data)
        
#         # 获取列表
#         response = await client.get("/api/v1/templates")
#         assert response.status_code == 200
#         data = response.json()
#         assert len(data) > 0
#         assert data[0]["name"] == sample_template_data["name"]
    
#     @pytest.mark.asyncio
#     async def test_get_template(self, client: AsyncClient, sample_template_data):
#         """测试获取单个模板"""
#         # 创建模板
#         create_response = await client.post(
#             "/api/v1/templates",
#             json=sample_template_data
#         )
#         template_id = create_response.json()["id"]
        
#         # 获取模板
#         response = await client.get(f"/api/v1/templates/{template_id}")
#         assert response.status_code == 200
#         data = response.json()
#         assert data["id"] == template_id
#         assert data["name"] == sample_template_data["name"]
    
#     @pytest.mark.asyncio
#     async def test_update_template(self, client: AsyncClient, sample_template_data):
#         """测试更新模板"""
#         # 创建模板
#         create_response = await client.post(
#             "/api/v1/templates",
#             json=sample_template_data
#         )
#         template_id = create_response.json()["id"]
        
#         # 更新模板
#         update_data = sample_template_data.copy()
#         update_data["name"] = "更新后的请示报告"
#         response = await client.put(
#             f"/api/v1/templates/{template_id}",
#             json=update_data
#         )
#         assert response.status_code == 200
#         data = response.json()
#         assert data["name"] == "更新后的请示报告"
    
#     @pytest.mark.asyncio
#     async def test_delete_template(self, client: AsyncClient, sample_template_data):
#         """测试删除模板"""
#         # 创建模板
#         create_response = await client.post(
#             "/api/v1/templates",
#             json=sample_template_data
#         )
#         template_id = create_response.json()["id"]
        
#         # 删除模板
#         response = await client.delete(f"/api/v1/templates/{template_id}")
#         assert response.status_code == 200
        
#         # 验证已删除
#         get_response = await client.get(f"/api/v1/templates/{template_id}")
#         assert get_response.status_code == 404


# class TestDocumentAPI:
#     """文档 API 测试"""
    
#     @pytest.mark.asyncio
#     async def test_generate_document(self, client: AsyncClient, sample_template_data):
#         """测试生成文档"""
#         # 先创建模板
#         template_response = await client.post(
#             "/api/v1/templates",
#             json=sample_template_data
#         )
#         template_id = template_response.json()["id"]
        
#         # 生成文档
#         generate_data = {
#             "template_id": template_id,
#             "variables": {
#                 "title": "关于采购办公设备的请示",
#                 "department": "行政部",
#                 "content": "因业务发展需要，拟采购电脑10台，预算5万元"
#             }
#         }
#         response = await client.post(
#             "/api/v1/documents/generate",
#             json=generate_data
#         )
#         assert response.status_code == 200
#         data = response.json()
#         assert "content" in data
#         assert "关于采购办公设备的请示" in data["content"]
    
#     @pytest.mark.asyncio
#     async def test_list_documents(self, client: AsyncClient):
#         """测试获取文档列表"""
#         response = await client.get("/api/v1/documents")
#         assert response.status_code == 200
#         data = response.json()
#         assert isinstance(data, list)


# class TestValidation:
#     """数据验证测试"""
    
#     @pytest.mark.asyncio
#     async def test_create_template_missing_fields(self, client: AsyncClient):
#         """测试创建模板缺少必填字段"""
#         invalid_data = {
#             "name": "测试模板"
#             # 缺少其他必填字段
#         }
#         response = await client.post(
#             "/api/v1/templates",
#             json=invalid_data
#         )
#         assert response.status_code == 422
    
#     @pytest.mark.asyncio
#     async def test_get_nonexistent_template(self, client: AsyncClient):
#         """测试获取不存在的模板"""
#         response = await client.get("/api/v1/templates/99999")
#         assert response.status_code == 404
