# Refantastic 后端 API 文档

## 认证管理 (Auth)
- `POST /auth/login`
  - 参数: `{ "username": "string", "password": "string" }`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/change-password`
  - 参数: `{ "old_password": "string", "new_password": "string" }`

## 用户管理 (Users)
- `GET /users`
  - 参数: `page, size, search, department, is_active`
- `GET /users/{user_id}`
- `POST /users`
  - 参数: `{ "username": "string", "email": "string", "password": "string", "role_ids": ["string"] }`
- `PUT /users/{user_id}`
  - 参数: `{ "email": "string", "password": "string", "role_ids": ["string"] }`
- `DELETE /users/{user_id}`
- `GET /users/{user_id}/roles`
- `POST /users/{user_id}/roles`
  - 参数: `{ "role_ids": ["string"] }`
- `DELETE /users/{user_id}/roles/{role_id}`

## 角色管理 (Roles)
- `GET /roles`
  - 参数: `page, size, search, is_system`
- `GET /roles/{role_id}`
- `POST /roles`
  - 参数: `{ "name": "string", "code": "string", "permission_ids": ["string"] }`
- `PUT /roles/{role_id}`
  - 参数: `{ "name": "string", "code": "string" }`
- `DELETE /roles/{role_id}`
- `GET /roles/{role_id}/permissions`
- `POST /roles/{role_id}/permissions`
  - 参数: `{ "permission_ids": ["string"] }`
- `DELETE /roles/{role_id}/permissions/{permission_id}`

## 文档管理 (Documents)
- `GET /documents`
  - 参数: `doc_type, status, creator_id, is_public, skip, limit`
- `GET /documents/{document_id}`
- `POST /documents`
  - 参数: `{ "title": "string", "content": "string", "doc_type": "string" }`
- `PUT /documents/{document_id}`
  - 参数: `{ "title": "string", "content": "string" }`
- `DELETE /documents/{document_id}`
  - 参数: `soft_delete`
- `POST /documents/{document_id}/publish`
- `POST /documents/{document_id}/archive`
- `GET /documents/{document_id}/versions`
- `POST /documents/{document_id}/versions/{version_id}/restore`
- `GET /documents/stats/overview`

## 知识库管理 (Knowledge)
- `GET /knowledge/documents`
  - 参数: `doc_type, status, is_public, skip, limit`
- `GET /knowledge/documents/{doc_id}`
- `POST /knowledge/documents`
  - 参数: `{ "title": "string", "content": "string", "doc_type": "string" }`
- `PUT /knowledge/documents/{doc_id}`
  - 参数: `{ "title": "string", "content": "string" }`
- `DELETE /knowledge/documents/{doc_id}`
  - 参数: `soft_delete`
- `POST /knowledge/documents/search`
  - 参数: `{ "query": "string", "doc_type": "string", "tags": ["string"] }`
- `POST /knowledge/documents/{doc_id}/vectorize`
- `POST /knowledge/documents/batch-vectorize`
  - 参数: `{ "doc_ids": ["string"], "force": true }`
- `POST /knowledge/upload`
  - 参数: `file, title, doc_type`
- `GET /knowledge/supported-formats`
- `GET /knowledge/categories`

## 公文生成 (Generation)
- `POST /generation/generate`
  - 参数: `{ "doc_type": "string", "theme": "string", "purpose": "string" }`
- `POST /generation/search-references`
  - 参数: `{ "query": "string", "doc_type": "string", "keywords": ["string"] }`
- `GET /generation/similar/{document_id}`
  - 参数: `top_k`
