# 用户管理 API 设计文档

## 概述

用户管理模块提供了完整的 RBAC (基于角色的访问控制) 功能，包括用户、角色、权限的增删改查及关联管理。

## API 基础路径

```
/api/v1/users     - 用户管理
/api/v1/roles     - 角色管理
/api/v1/permissions - 权限管理
/api/v1/auth      - 认证相关
```

---

## 1. 认证管理 (Auth)

### 1.1 用户登录
```
POST /api/v1/auth/login
```
**功能**: 用户登录获取访问令牌
**请求体**: `{ username, password }`
**响应**: `{ access_token, token_type, user_info }`
**权限**: 公开

### 1.2 用户登出
```
POST /api/v1/auth/logout
```
**功能**: 用户登出，使令牌失效
**权限**: 需要认证

### 1.3 刷新令牌
```
POST /api/v1/auth/refresh
```
**功能**: 刷新访问令牌
**请求体**: `{ refresh_token }`
**响应**: `{ access_token, token_type }`
**权限**: 需要认证

### 1.4 修改密码
```
POST /api/v1/auth/change-password
```
**功能**: 修改当前用户密码
**请求体**: `{ old_password, new_password }`
**权限**: 需要认证

### 1.5 重置密码请求
```
POST /api/v1/auth/reset-password-request
```
**功能**: 请求重置密码（发送邮件）
**请求体**: `{ email }`
**权限**: 公开

### 1.6 重置密码确认
```
POST /api/v1/auth/reset-password-confirm
```
**功能**: 使用重置令牌设置新密码
**请求体**: `{ token, new_password }`
**权限**: 公开

### 1.7 获取当前用户信息
```
GET /api/v1/auth/me
```
**功能**: 获取当前登录用户的详细信息
**响应**: 用户对象（包含角色和权限）
**权限**: 需要认证

---

## 2. 用户管理 (Users)

### 2.1 获取用户列表
```
GET /api/v1/users
```
**功能**: 分页查询用户列表
**查询参数**:
- `page`: 页码（默认 1）
- `size`: 每页数量（默认 20）
- `search`: 搜索关键词（用户名、邮箱、姓名）
- `department`: 部门筛选
- `is_active`: 状态筛选（true/false）
- `role_id`: 角色筛选
- `sort`: 排序字段（created_at, username, email）
- `order`: 排序方向（asc/desc）

**响应**: `{ items: [], total, page, size }`
**权限**: `user:read` 或管理员

### 2.2 获取用户详情
```
GET /api/v1/users/{user_id}
```
**功能**: 获取指定用户的详细信息
**路径参数**: `user_id` - 用户ID
**响应**: 用户对象（包含角色列表）
**权限**: `user:read` 或本人

### 2.3 创建用户
```
POST /api/v1/users
```
**功能**: 创建新用户
**请求体**:
```json
{
  "username": "string (必填)",
  "email": "string (必填)",
  "password": "string (必填)",
  "full_name": "string (必填)",
  "department": "string (可选)",
  "position": "string (可选)",
  "phone": "string (可选)",
  "is_active": "boolean (默认 true)",
  "role_ids": ["string"] (可选，角色ID数组)
}
```
**响应**: 创建的用户对象
**权限**: `user:create` 或管理员

### 2.4 更新用户
```
PUT /api/v1/users/{user_id}
```
**功能**: 更新用户信息
**路径参数**: `user_id` - 用户ID
**请求体**: 同创建用户（password 可选）
**响应**: 更新后的用户对象
**权限**: `user:update` 或本人（限制字段）

### 2.5 部分更新用户
```
PATCH /api/v1/users/{user_id}
```
**功能**: 部分更新用户字段
**路径参数**: `user_id` - 用户ID
**请求体**: 需要更新的字段
**响应**: 更新后的用户对象
**权限**: `user:update` 或本人（限制字段）

### 2.6 删除用户
```
DELETE /api/v1/users/{user_id}
```
**功能**: 删除用户（软删除或硬删除）
**路径参数**: `user_id` - 用户ID
**查询参数**: `hard_delete` - 是否硬删除（默认 false）
**权限**: `user:delete` 或管理员

### 2.7 批量删除用户
```
DELETE /api/v1/users/batch
```
**功能**: 批量删除用户
**请求体**: `{ user_ids: ["id1", "id2"] }`
**权限**: `user:delete` 或管理员

### 2.8 启用/禁用用户
```
PATCH /api/v1/users/{user_id}/toggle-active
```
**功能**: 切换用户激活状态
**路径参数**: `user_id` - 用户ID
**请求体**: `{ is_active: boolean }`
**权限**: `user:update` 或管理员

### 2.9 更新用户头像
```
POST /api/v1/users/{user_id}/avatar
```
**功能**: 上传用户头像
**路径参数**: `user_id` - 用户ID
**请求体**: 文件上传（multipart/form-data）
**响应**: `{ avatar_url }`
**权限**: 本人或管理员

---

## 3. 用户角色关联

### 3.1 获取用户角色列表
```
GET /api/v1/users/{user_id}/roles
```
**功能**: 获取指定用户的所有角色
**路径参数**: `user_id` - 用户ID
**响应**: 角色对象数组
**权限**: `user:read` 或本人

### 3.2 为用户分配角色
```
POST /api/v1/users/{user_id}/roles
```
**功能**: 为用户添加角色
**路径参数**: `user_id` - 用户ID
**请求体**: `{ role_ids: ["id1", "id2"] }`
**权限**: `user:update` 或管理员

### 3.3 移除用户角色
```
DELETE /api/v1/users/{user_id}/roles/{role_id}
```
**功能**: 移除用户的指定角色
**路径参数**: 
- `user_id` - 用户ID
- `role_id` - 角色ID
**权限**: `user:update` 或管理员

### 3.4 替换用户角色
```
PUT /api/v1/users/{user_id}/roles
```
**功能**: 替换用户的所有角色
**路径参数**: `user_id` - 用户ID
**请求体**: `{ role_ids: ["id1", "id2"] }`
**权限**: `user:update` 或管理员

---

## 4. 角色管理 (Roles)

### 4.1 获取角色列表
```
GET /api/v1/roles
```
**功能**: 查询角色列表
**查询参数**:
- `page`: 页码
- `size`: 每页数量
- `search`: 搜索关键词
- `is_system`: 是否系统角色

**响应**: `{ items: [], total, page, size }`
**权限**: `role:read` 或管理员

### 4.2 获取角色详情
```
GET /api/v1/roles/{role_id}
```
**功能**: 获取角色详细信息（包含权限列表）
**路径参数**: `role_id` - 角色ID
**权限**: `role:read` 或管理员

### 4.3 创建角色
```
POST /api/v1/roles
```
**功能**: 创建新角色
**请求体**:
```json
{
  "name": "string (必填)",
  "code": "string (必填，唯一)",
  "description": "string (可选)",
  "permission_ids": ["string"] (可选)
}
```
**权限**: `role:create` 或管理员

### 4.4 更新角色
```
PUT /api/v1/roles/{role_id}
```
**功能**: 更新角色信息
**路径参数**: `role_id` - 角色ID
**请求体**: 同创建角色
**权限**: `role:update` 或管理员

### 4.5 删除角色
```
DELETE /api/v1/roles/{role_id}
```
**功能**: 删除角色（系统角色不可删除）
**路径参数**: `role_id` - 角色ID
**权限**: `role:delete` 或管理员

### 4.6 获取角色的用户列表
```
GET /api/v1/roles/{role_id}/users
```
**功能**: 获取拥有该角色的所有用户
**路径参数**: `role_id` - 角色ID
**查询参数**: 同用户列表
**权限**: `role:read` 或管理员

### 4.7 获取角色的权限列表
```
GET /api/v1/roles/{role_id}/permissions
```
**功能**: 获取角色的所有权限
**路径参数**: `role_id` - 角色ID
**权限**: `role:read` 或管理员

### 4.8 为角色分配权限
```
POST /api/v1/roles/{role_id}/permissions
```
**功能**: 为角色添加权限
**路径参数**: `role_id` - 角色ID
**请求体**: `{ permission_ids: ["id1", "id2"] }`
**权限**: `role:update` 或管理员

### 4.9 移除角色权限
```
DELETE /api/v1/roles/{role_id}/permissions/{permission_id}
```
**功能**: 移除角色的指定权限
**路径参数**:
- `role_id` - 角色ID
- `permission_id` - 权限ID
**权限**: `role:update` 或管理员

### 4.10 替换角色权限
```
PUT /api/v1/roles/{role_id}/permissions
```
**功能**: 替换角色的所有权限
**路径参数**: `role_id` - 角色ID
**请求体**: `{ permission_ids: ["id1", "id2"] }`
**权限**: `role:update` 或管理员

---

## 5. 权限管理 (Permissions)

### 5.1 获取权限列表
```
GET /api/v1/permissions
```
**功能**: 查询权限列表
**查询参数**:
- `page`: 页码
- `size`: 每页数量
- `resource`: 资源类型筛选
- `action`: 操作类型筛选
- `search`: 搜索关键词

**响应**: `{ items: [], total, page, size }`
**权限**: `permission:read` 或管理员

### 5.2 获取权限详情
```
GET /api/v1/permissions/{permission_id}
```
**功能**: 获取权限详细信息
**路径参数**: `permission_id` - 权限ID
**权限**: `permission:read` 或管理员

### 5.3 创建权限
```
POST /api/v1/permissions
```
**功能**: 创建新权限
**请求体**:
```json
{
  "name": "string (必填)",
  "code": "string (必填，格式: resource:action)",
  "resource": "string (必填)",
  "action": "string (必填，如: create/read/update/delete)",
  "description": "string (可选)"
}
```
**权限**: `permission:create` 或管理员

### 5.4 更新权限
```
PUT /api/v1/permissions/{permission_id}
```
**功能**: 更新权限信息
**路径参数**: `permission_id` - 权限ID
**请求体**: 同创建权限
**权限**: `permission:update` 或管理员

### 5.5 删除权限
```
DELETE /api/v1/permissions/{permission_id}
```
**功能**: 删除权限
**路径参数**: `permission_id` - 权限ID
**权限**: `permission:delete` 或管理员

### 5.6 按资源分组权限
```
GET /api/v1/permissions/grouped
```
**功能**: 按资源类型分组返回权限
**响应**: `{ resource1: [permissions], resource2: [permissions] }`
**权限**: `permission:read` 或管理员

### 5.7 获取权限的角色列表
```
GET /api/v1/permissions/{permission_id}/roles
```
**功能**: 获取拥有该权限的所有角色
**路径参数**: `permission_id` - 权限ID
**权限**: `permission:read` 或管理员

---

## 6. 用户操作历史

### 6.1 获取用户操作日志
```
GET /api/v1/users/{user_id}/audit-logs
```
**功能**: 获取用户的操作历史记录
**路径参数**: `user_id` - 用户ID
**查询参数**:
- `page`, `size`: 分页
- `action`: 操作类型筛选
- `resource_type`: 资源类型筛选
- `start_date`, `end_date`: 时间范围

**权限**: `user:read` 或本人或管理员

### 6.2 获取用户登录历史
```
GET /api/v1/users/{user_id}/login-history
```
**功能**: 获取用户登录记录
**路径参数**: `user_id` - 用户ID
**查询参数**: 分页参数
**权限**: 本人或管理员

---

## 7. 批量操作

### 7.1 批量导入用户
```
POST /api/v1/users/import
```
**功能**: 从 Excel/CSV 批量导入用户
**请求体**: 文件上传
**响应**: `{ success_count, failed_count, errors: [] }`
**权限**: `user:create` 或管理员

### 7.2 导出用户列表
```
GET /api/v1/users/export
```
**功能**: 导出用户列表为 Excel/CSV
**查询参数**: 同用户列表筛选条件
**响应**: 文件下载
**权限**: `user:read` 或管理员

### 7.3 批量分配角色
```
POST /api/v1/users/batch/assign-roles
```
**功能**: 为多个用户批量分配角色
**请求体**: `{ user_ids: [], role_ids: [] }`
**权限**: `user:update` 或管理员

### 7.4 批量修改部门
```
PATCH /api/v1/users/batch/department
```
**功能**: 批量修改用户部门
**请求体**: `{ user_ids: [], department: "string" }`
**权限**: `user:update` 或管理员

---

## 8. 统计与分析

### 8.1 用户统计概览
```
GET /api/v1/users/statistics
```
**功能**: 获取用户统计信息
**响应**:
```json
{
  "total_users": 100,
  "active_users": 95,
  "inactive_users": 5,
  "by_department": { "技术部": 30, "行政部": 20 },
  "by_role": { "管理员": 5, "员工": 90 },
  "new_users_this_month": 10
}
```
**权限**: 管理员

### 8.2 角色统计
```
GET /api/v1/roles/statistics
```
**功能**: 获取角色统计信息
**响应**: 角色分布、用户数量等
**权限**: 管理员

### 8.3 权限使用统计
```
GET /api/v1/permissions/statistics
```
**功能**: 获取权限使用情况
**响应**: 各权限被分配的次数
**权限**: 管理员

---

## 9. 权限验证

### 9.1 检查用户权限
```
POST /api/v1/users/{user_id}/check-permission
```
**功能**: 检查用户是否拥有指定权限
**路径参数**: `user_id` - 用户ID
**请求体**: `{ permission_code: "document:create" }`
**响应**: `{ has_permission: boolean }`
**权限**: 本人或管理员

### 9.2 获取用户所有权限
```
GET /api/v1/users/{user_id}/all-permissions
```
**功能**: 获取用户通过角色获得的所有权限
**路径参数**: `user_id` - 用户ID
**响应**: 权限对象数组
**权限**: 本人或管理员

---

## 数据模型

### User 对象
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "department": "string",
  "position": "string",
  "phone": "string",
  "avatar": "string (url)",
  "is_active": "boolean",
  "is_superuser": "boolean",
  "last_login": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime",
  "roles": ["Role对象数组"]
}
```

### Role 对象
```json
{
  "id": "uuid",
  "name": "string",
  "code": "string",
  "description": "string",
  "is_system": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime",
  "permissions": ["Permission对象数组"]
}
```

### Permission 对象
```json
{
  "id": "uuid",
  "name": "string",
  "code": "string",
  "resource": "string",
  "action": "string",
  "description": "string",
  "created_at": "datetime"
}
```

---

## 错误码

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 400 | USER_ALREADY_EXISTS | 用户名或邮箱已存在 |
| 400 | INVALID_PASSWORD | 密码格式不正确 |
| 401 | INVALID_CREDENTIALS | 用户名或密码错误 |
| 401 | TOKEN_EXPIRED | 令牌已过期 |
| 403 | PERMISSION_DENIED | 权限不足 |
| 403 | CANNOT_DELETE_SYSTEM_ROLE | 不能删除系统角色 |
| 404 | USER_NOT_FOUND | 用户不存在 |
| 404 | ROLE_NOT_FOUND | 角色不存在 |
| 404 | PERMISSION_NOT_FOUND | 权限不存在 |
| 409 | ROLE_CODE_EXISTS | 角色代码已存在 |
| 409 | PERMISSION_CODE_EXISTS | 权限代码已存在 |

---

## 注意事项

1. **权限控制**: 所有 API 都需要根据用户权限进行访问控制
2. **密码安全**: 密码使用 bcrypt 加密存储，传输使用 HTTPS
3. **令牌管理**: JWT Token 有效期建议设置为 24 小时
4. **审计日志**: 所有用户、角色、权限的变更都应记录审计日志
5. **系统角色**: 系统预置角色不允许删除或修改核心属性
6. **批量操作**: 批量操作应有数量限制，建议不超过 1000 条
7. **软删除**: 建议使用软删除，保留用户历史数据
8. **并发控制**: 使用乐观锁或悲观锁处理并发更新

---

## API 实现优先级

### 第一阶段（核心功能）
1. 认证管理（登录、登出、获取当前用户）
2. 用户 CRUD（增删改查）
3. 角色 CRUD
4. 权限查询
5. 用户-角色关联
6. 角色-权限关联

### 第二阶段（扩展功能）
1. 批量操作
2. 导入导出
3. 统计分析
4. 操作历史
5. 密码重置

### 第三阶段（优化功能）
1. 头像上传
2. 高级筛选
3. 权限验证优化
4. 缓存机制
