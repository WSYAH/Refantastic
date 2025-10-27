"""创建完整的测试数据集"""
import sys
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timedelta
import bcrypt

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from loguru import logger

from models import (
    User, Role, Permission, UserRole, RolePermission,
    Template, TemplateVariable,
    Document, DocumentVersion,
    Workflow, WorkflowNode, WorkflowInstance, WorkflowTask,
    KnowledgeDocument, KnowledgeCategory,
    AuditLog
)
from core.database import Base

# 创建数据目录和数据库连接
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/refantastic.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def hash_password(password: str) -> str:
    """使用原生 bcrypt 哈希密码"""
    # 确保密码不超过 72 字节
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # 生成 salt 并哈希
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


async def create_users_and_roles(session: AsyncSession):
    """创建用户、角色和权限"""
    logger.info("创建用户、角色和权限...")
    
    # 创建角色
    roles = [
        Role(
            id=str(uuid.uuid4()),
            name="系统管理员",
            code="admin",
            description="拥有系统所有权限",
            is_system=True
        ),
        Role(
            id=str(uuid.uuid4()),
            name="部门经理",
            code="manager",
            description="部门管理权限",
            is_system=False
        ),
        Role(
            id=str(uuid.uuid4()),
            name="普通员工",
            code="employee",
            description="基本文档操作权限",
            is_system=False
        ),
        Role(
            id=str(uuid.uuid4()),
            name="审批人",
            code="approver",
            description="文档审批权限",
            is_system=False
        )
    ]
    
    for role in roles:
        session.add(role)
    await session.flush()
    
    role_dict = {r.code: r for r in roles}
    
    # 创建权限
    permissions = [
        # 文档权限
        Permission(id=str(uuid.uuid4()), name="创建文档", code="document:create", resource="document", action="create", description="创建新文档"),
        Permission(id=str(uuid.uuid4()), name="查看文档", code="document:read", resource="document", action="read", description="查看文档"),
        Permission(id=str(uuid.uuid4()), name="编辑文档", code="document:update", resource="document", action="update", description="编辑文档"),
        Permission(id=str(uuid.uuid4()), name="删除文档", code="document:delete", resource="document", action="delete", description="删除文档"),
        # 模板权限
        Permission(id=str(uuid.uuid4()), name="创建模板", code="template:create", resource="template", action="create", description="创建新模板"),
        Permission(id=str(uuid.uuid4()), name="查看模板", code="template:read", resource="template", action="read", description="查看模板"),
        Permission(id=str(uuid.uuid4()), name="编辑模板", code="template:update", resource="template", action="update", description="编辑模板"),
        Permission(id=str(uuid.uuid4()), name="删除模板", code="template:delete", resource="template", action="delete", description="删除模板"),
        # 工作流权限
        Permission(id=str(uuid.uuid4()), name="审批文档", code="workflow:approve", resource="workflow", action="update", description="审批文档"),
        Permission(id=str(uuid.uuid4()), name="管理工作流", code="workflow:manage", resource="workflow", action="create", description="管理工作流"),
        # 用户管理权限
        Permission(id=str(uuid.uuid4()), name="用户管理", code="user:manage", resource="user", action="create", description="管理用户"),
        Permission(id=str(uuid.uuid4()), name="角色管理", code="role:manage", resource="role", action="create", description="管理角色"),
    ]
    
    for permission in permissions:
        session.add(permission)
    await session.flush()
    
    # 分配权限给角色
    # 管理员拥有所有权限
    for perm in permissions:
        session.add(RolePermission(
            id=str(uuid.uuid4()),
            role_id=role_dict["admin"].id,
            permission_id=perm.id
        ))
    
    # 经理拥有文档、模板、审批权限
    manager_perms = [p for p in permissions if p.resource in ["document", "template", "workflow"]]
    for perm in manager_perms:
        session.add(RolePermission(
            id=str(uuid.uuid4()),
            role_id=role_dict["manager"].id,
            permission_id=perm.id
        ))
    
    # 员工拥有基本文档权限
    employee_perms = [p for p in permissions if p.code in ["document:create", "document:read", "template:read"]]
    for perm in employee_perms:
        session.add(RolePermission(
            id=str(uuid.uuid4()),
            role_id=role_dict["employee"].id,
            permission_id=perm.id
        ))
    
    # 审批人拥有审批权限
    approver_perms = [p for p in permissions if "read" in p.action or p.code == "workflow:approve"]
    for perm in approver_perms:
        session.add(RolePermission(
            id=str(uuid.uuid4()),
            role_id=role_dict["approver"].id,
            permission_id=perm.id
        ))
    
    # 创建用户
    users_data = [
        {"username": "admin", "email": "admin@example.com", "full_name": "系统管理员", "department": "技术部", "position": "系统管理员", "role": "admin"},
        {"username": "manager1", "email": "manager1@example.com", "full_name": "张经理", "department": "行政部", "position": "部门经理", "role": "manager"},
        {"username": "manager2", "email": "manager2@example.com", "full_name": "李经理", "department": "财务部", "position": "部门经理", "role": "manager"},
        {"username": "employee1", "email": "emp1@example.com", "full_name": "王小明", "department": "行政部", "position": "专员", "role": "employee"},
        {"username": "employee2", "email": "emp2@example.com", "full_name": "刘小红", "department": "财务部", "position": "专员", "role": "employee"},
        {"username": "approver1", "email": "app1@example.com", "full_name": "陈审批", "department": "行政部", "position": "主管", "role": "approver"},
    ]
    
    users = []
    for user_data in users_data:
        user = User(
            id=str(uuid.uuid4()),
            username=user_data["username"],
            email=user_data["email"],
            password_hash=hash_password("password123"),  # 使用新的哈希函数
            full_name=user_data["full_name"],
            department=user_data["department"],
            position=user_data["position"],
            is_active=True,
            is_superuser=(user_data["role"] == "admin")
        )
        session.add(user)
        users.append(user)
        
        # 分配角色
        session.add(UserRole(
            id=str(uuid.uuid4()),
            user_id=user.id,
            role_id=role_dict[user_data["role"]].id
        ))
    
    await session.commit()
    logger.info(f"创建了 {len(users)} 个用户，{len(roles)} 个角色，{len(permissions)} 个权限")
    
    return {u.username: u for u in users}


async def create_templates_and_variables(session: AsyncSession, users: dict):
    """创建模板和模板变量"""
    logger.info("创建模板和模板变量...")
    
    admin_id = users["admin"].id
    
    templates_data = [
        {
            "name": "请示报告",
            "doc_type": "请示",
            "category": "行政公文",
            "content": "{{title}}\n\n{{recipient}}：\n\n{{content}}\n\n特此请示，请予批准。\n\n申请部门：{{department}}\n申请日期：{{date}}",
            "variables": [
                {"name": "title", "type": "text", "label": "标题", "required": True},
                {"name": "recipient", "type": "text", "label": "收件人", "required": True},
                {"name": "content", "type": "text", "label": "正文内容", "required": True},
                {"name": "department", "type": "text", "label": "申请部门", "required": True},
                {"name": "date", "type": "date", "label": "申请日期", "required": True},
            ]
        },
        {
            "name": "会议通知",
            "doc_type": "通知",
            "category": "行政公文",
            "content": "关于{{meeting_topic}}的通知\n\n各相关部门：\n\n兹定于{{meeting_time}}在{{meeting_location}}召开{{meeting_topic}}会议。\n\n参会人员：{{participants}}\n\n会议议程：\n{{agenda}}\n\n请准时参加。\n\n通知部门：{{department}}\n{{date}}",
            "variables": [
                {"name": "meeting_topic", "type": "text", "label": "会议主题", "required": True},
                {"name": "meeting_time", "type": "date", "label": "会议时间", "required": True},
                {"name": "meeting_location", "type": "text", "label": "会议地点", "required": True},
                {"name": "participants", "type": "text", "label": "参会人员", "required": True},
                {"name": "agenda", "type": "text", "label": "会议议程", "required": True},
                {"name": "department", "type": "text", "label": "通知部门", "required": True},
                {"name": "date", "type": "date", "label": "通知日期", "required": True},
            ]
        },
        {
            "name": "请假申请",
            "doc_type": "申请",
            "category": "人事文档",
            "content": "请假申请\n\n申请人：{{name}}\n部门：{{department}}\n职位：{{position}}\n\n请假类型：{{leave_type}}\n请假时间：{{start_date}} 至 {{end_date}}\n请假天数：{{days}}天\n\n请假事由：\n{{reason}}\n\n申请人签字：______\n日期：{{apply_date}}",
            "variables": [
                {"name": "name", "type": "text", "label": "姓名", "required": True},
                {"name": "department", "type": "text", "label": "部门", "required": True},
                {"name": "position", "type": "text", "label": "职位", "required": True},
                {"name": "leave_type", "type": "select", "label": "请假类型", "required": True, "options": ["病假", "事假", "年假", "婚假", "产假"]},
                {"name": "start_date", "type": "date", "label": "开始日期", "required": True},
                {"name": "end_date", "type": "date", "label": "结束日期", "required": True},
                {"name": "days", "type": "number", "label": "请假天数", "required": True},
                {"name": "reason", "type": "text", "label": "请假事由", "required": True},
                {"name": "apply_date", "type": "date", "label": "申请日期", "required": True},
            ]
        },
        {
            "name": "工作总结",
            "doc_type": "总结",
            "category": "工作报告",
            "content": "{{period}}工作总结\n\n部门：{{department}}\n报告人：{{author}}\n\n一、工作回顾\n{{review}}\n\n二、主要成绩\n{{achievements}}\n\n三、存在问题\n{{problems}}\n\n四、下步工作计划\n{{plans}}\n\n{{date}}",
            "variables": [
                {"name": "period", "type": "text", "label": "时期", "required": True},
                {"name": "department", "type": "text", "label": "部门", "required": True},
                {"name": "author", "type": "text", "label": "报告人", "required": True},
                {"name": "review", "type": "text", "label": "工作回顾", "required": True},
                {"name": "achievements", "type": "text", "label": "主要成绩", "required": False},
                {"name": "problems", "type": "text", "label": "存在问题", "required": False},
                {"name": "plans", "type": "text", "label": "下步计划", "required": True},
                {"name": "date", "type": "date", "label": "日期", "required": True},
            ]
        }
    ]
    
    templates = []
    for template_data in templates_data:
        template = Template(
            id=str(uuid.uuid4()),
            name=template_data["name"],
            doc_type=template_data["doc_type"],
            category=template_data["category"],
            content=template_data["content"],
            variable_names=[v["name"] for v in template_data["variables"]],
            description=f"{template_data['name']}标准模板",
            is_system=True,
            is_active=True,
            creator_id=admin_id
        )
        session.add(template)
        templates.append(template)
        
        # 创建模板变量
        for idx, var_data in enumerate(template_data["variables"]):
            var = TemplateVariable(
                id=str(uuid.uuid4()),
                template_id=template.id,
                variable_name=var_data["name"],
                variable_type=var_data["type"],
                label=var_data["label"],
                is_required=var_data["required"],
                options=var_data.get("options"),
                sort_order=idx
            )
            session.add(var)
    
    await session.commit()
    logger.info(f"创建了 {len(templates)} 个模板及其变量")
    
    return templates


async def create_workflows(session: AsyncSession, users: dict):
    """创建工作流"""
    logger.info("创建工作流...")
    
    manager1_id = users["manager1"].id
    manager2_id = users["manager2"].id
    approver_id = users["approver1"].id
    
    # 请示审批工作流
    workflow1 = Workflow(
        id=str(uuid.uuid4()),
        name="请示审批流程",
        doc_type="请示",
        description="请示文档的标准审批流程",
        is_active=True,
        config={"auto_notify": True, "timeout_days": 3}
    )
    session.add(workflow1)
    
    nodes1 = [
        WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow1.id,
            name="提交申请",
            node_type="start",
            sort_order=1
        ),
        WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow1.id,
            name="部门经理审批",
            node_type="approval",
            approver_type="user",
            approver_id=manager1_id,
            sort_order=2
        ),
        WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow1.id,
            name="主管审批",
            node_type="approval",
            approver_type="user",
            approver_id=approver_id,
            sort_order=3
        ),
        WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow1.id,
            name="完成",
            node_type="end",
            sort_order=4
        )
    ]
    
    for node in nodes1:
        session.add(node)
    
    # 请假审批工作流
    workflow2 = Workflow(
        id=str(uuid.uuid4()),
        name="请假审批流程",
        doc_type="申请",
        description="请假申请的审批流程",
        is_active=True,
        config={"auto_notify": True, "timeout_days": 1}
    )
    session.add(workflow2)
    
    nodes2 = [
        WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow2.id,
            name="提交申请",
            node_type="start",
            sort_order=1
        ),
        WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow2.id,
            name="直属领导审批",
            node_type="approval",
            approver_type="role",
            approver_id="manager",
            sort_order=2
        ),
        WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=workflow2.id,
            name="完成",
            node_type="end",
            sort_order=3
        )
    ]
    
    for node in nodes2:
        session.add(node)
    
    await session.commit()
    logger.info("创建了 2 个工作流")
    
    return [workflow1, workflow2], nodes1 + nodes2


async def create_documents_and_versions(session: AsyncSession, users: dict, templates: list):
    """创建文档和版本"""
    logger.info("创建文档和版本...")
    
    employee1 = users["employee1"]
    employee2 = users["employee2"]
    manager1 = users["manager1"]
    
    documents_data = [
        {
            "title": "关于采购办公设备的请示",
            "doc_type": "请示",
            "content": "关于采购办公设备的请示\n\n行政部：\n\n因业务发展需要，我部门需要采购以下办公设备：\n1. 台式电脑10台，预算3万元\n2. 打印机3台，预算1.5万元\n3. 办公桌椅20套，预算0.5万元\n合计预算5万元。\n\n特此请示，请予批准。\n\n申请部门：技术部\n申请日期：2024-01-15",
            "creator": employee1,
            "template": templates[0],
            "status": "reviewing",
            "tags": ["采购", "办公设备"],
        },
        {
            "title": "2024年第一季度工作总结",
            "doc_type": "总结",
            "content": "2024年第一季度工作总结\n\n部门：行政部\n报告人：王小明\n\n一、工作回顾\n本季度完成了年度工作计划中的各项既定目标，主要开展了以下工作...\n\n二、主要成绩\n1. 完成办公自动化系统上线\n2. 组织公司年会活动\n3. 完成新员工培训\n\n三、存在问题\n部分工作进度有所滞后，需要加强跨部门协作。\n\n四、下步工作计划\n继续推进重点项目，提升工作效率。\n\n2024-03-31",
            "creator": employee1,
            "template": templates[3],
            "status": "published",
            "tags": ["工作总结", "季度报告"],
            "published_at": datetime.now() - timedelta(days=5)
        },
        {
            "title": "关于召开2024年度工作会议的通知",
            "doc_type": "通知",
            "content": "关于召开2024年度工作会议的通知\n\n各相关部门：\n\n兹定于2024年2月1日14:00在公司会议室召开2024年度工作会议。\n\n参会人员：各部门经理及主管\n\n会议议程：\n1. 2023年工作总结\n2. 2024年工作计划\n3. 重点项目讨论\n\n请准时参加。\n\n通知部门：行政部\n2024-01-25",
            "creator": manager1,
            "template": templates[1],
            "status": "published",
            "tags": ["会议通知", "年度会议"],
            "published_at": datetime.now() - timedelta(days=10)
        },
        {
            "title": "病假申请",
            "doc_type": "申请",
            "content": "请假申请\n\n申请人：刘小红\n部门：财务部\n职位：专员\n\n请假类型：病假\n请假时间：2024-01-20 至 2024-01-22\n请假天数：3天\n\n请假事由：\n感冒发烧，需要休息治疗。\n\n申请人签字：______\n日期：2024-01-19",
            "creator": employee2,
            "template": templates[2],
            "status": "approved",
            "tags": ["请假", "病假"],
        }
    ]
    
    documents = []
    for doc_data in documents_data:
        doc = Document(
            id=str(uuid.uuid4()),
            title=doc_data["title"],
            doc_type=doc_data["doc_type"],
            content=doc_data["content"],
            creator_id=doc_data["creator"].id,
            template_id=doc_data["template"].id,
            status=doc_data["status"],
            tags=doc_data["tags"],
            published_at=doc_data.get("published_at"),
            doc_number=f"DOC-{datetime.now().year}-{len(documents)+1:04d}"
        )
        session.add(doc)
        documents.append(doc)
        
        # 创建文档版本
        version = DocumentVersion(
            id=str(uuid.uuid4()),
            document_id=doc.id,
            version=1,
            title=doc.title,
            content=doc.content,
            change_type="create",
            change_description="初始创建",
            created_by=doc_data["creator"].id
        )
        session.add(version)
    
    await session.commit()
    logger.info(f"创建了 {len(documents)} 个文档及其版本")
    
    return documents


async def create_knowledge_base(session: AsyncSession):
    """创建知识库"""
    logger.info("创建知识库...")
    
    # 创建知识分类
    categories = [
        KnowledgeCategory(
            id=str(uuid.uuid4()),
            name="公文写作规范",
            description="各类公文的写作规范和标准",
            icon="📝",
            sort_order=1
        ),
        KnowledgeCategory(
            id=str(uuid.uuid4()),
            name="流程制度",
            description="公司各项流程和制度文档",
            icon="📋",
            sort_order=2
        ),
        KnowledgeCategory(
            id=str(uuid.uuid4()),
            name="模板示例",
            description="各类文档模板和示例",
            icon="📄",
            sort_order=3
        ),
        KnowledgeCategory(
            id=str(uuid.uuid4()),
            name="常见问题",
            description="常见问题解答",
            icon="❓",
            sort_order=4
        )
    ]
    
    for cat in categories:
        session.add(cat)
    await session.flush()
    
    # 创建知识文档
    knowledge_docs = [
        KnowledgeDocument(
            id=str(uuid.uuid4()),
            title="公文写作基本规范",
            content="一、公文的基本要素\n公文应当包括标题、主送机关、正文、落款等基本要素...\n\n二、公文的格式要求\n1. 标题居中，使用小二号字体\n2. 正文使用三号字体，行间距1.5倍\n3. 页边距上下左右各2.5cm\n\n三、公文的语言要求\n语言应当准确、简洁、规范，避免使用口语化表达...",
            doc_type="规范文档",
            author="行政部",
            department="行政部",
            tags=["公文", "规范", "写作"],
            keywords=["公文写作", "格式规范", "语言要求"],
            is_vectorized=False,
            quality_score=95,
            view_count=156,
            status="active",
            is_public=True
        ),
        KnowledgeDocument(
            id=str(uuid.uuid4()),
            title="请示报告写作指南",
            content="请示报告是下级机关向上级机关请求指示或批准的公文。\n\n一、请示的适用范围\n1. 需要上级批准的事项\n2. 需要上级指示的问题\n3. 需要上级协调的工作\n\n二、请示的写作要点\n1. 事由明确，一文一事\n2. 理由充分，条理清晰\n3. 请求具体，切实可行\n\n三、请示的注意事项\n1. 不得越级请示\n2. 请示应当一文一事\n3. 受双重领导的机关应当写明主送机关",
            doc_type="写作指南",
            author="办公室",
            department="行政部",
            tags=["请示", "写作指南"],
            keywords=["请示报告", "公文写作", "写作要点"],
            is_vectorized=False,
            quality_score=90,
            view_count=234,
            status="active",
            is_public=True
        ),
        KnowledgeDocument(
            id=str(uuid.uuid4()),
            title="文档审批流程说明",
            content="本公司文档审批遵循以下流程：\n\n一、草拟阶段\n1. 起草人根据模板撰写文档\n2. 文档需包含必要的附件和说明\n\n二、审核阶段\n1. 部门负责人初审\n2. 相关部门会签（如需要）\n3. 分管领导审批\n\n三、发布阶段\n1. 办公室统一编号\n2. 正式发布和分发\n3. 归档保存\n\n四、时限要求\n- 普通文档：3个工作日\n- 紧急文档：1个工作日\n- 特别紧急：当日办结",
            doc_type="流程制度",
            author="办公室",
            department="行政部",
            tags=["审批流程", "制度"],
            keywords=["文档审批", "流程说明", "时限要求"],
            is_vectorized=False,
            quality_score=88,
            view_count=445,
            status="active",
            is_public=True
        ),
        KnowledgeDocument(
            id=str(uuid.uuid4()),
            title="常见公文错误及纠正",
            content="在公文写作中，经常出现以下错误：\n\n一、格式错误\n1. 标题格式不规范\n2. 字体字号不统一\n3. 页边距不符合要求\n\n二、内容错误\n1. 主题不明确\n2. 层次不清晰\n3. 用语不规范\n\n三、逻辑错误\n1. 前后矛盾\n2. 条理混乱\n3. 重点不突出\n\n四、纠正方法\n1. 严格按照规范格式\n2. 认真审查内容\n3. 多次校对修改",
            doc_type="指导文档",
            author="培训组",
            department="人力资源部",
            tags=["常见错误", "纠正方法"],
            keywords=["公文错误", "写作规范", "纠正方法"],
            is_vectorized=False,
            quality_score=85,
            view_count=189,
            status="active",
            is_public=True
        )
    ]
    
    for doc in knowledge_docs:
        session.add(doc)
    
    # 更新分类文档数量
    categories[0].doc_count = 2
    categories[1].doc_count = 1
    categories[3].doc_count = 1
    
    await session.commit()
    logger.info(f"创建了 {len(categories)} 个知识分类和 {len(knowledge_docs)} 个知识文档")


async def create_audit_logs(session: AsyncSession, users: dict):
    """创建审计日志"""
    logger.info("创建审计日志...")
    
    logs = [
        AuditLog(
            id=str(uuid.uuid4()),
            user_id=users["admin"].id,
            action="user:login",
            resource_type="auth",
            resource_id=users["admin"].id,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            response_status=200,
            created_at=datetime.now() - timedelta(hours=2)
        ),
        AuditLog(
            id=str(uuid.uuid4()),
            user_id=users["employee1"].id,
            action="document:create",
            resource_type="document",
            resource_id=str(uuid.uuid4()),
            ip_address="192.168.1.101",
            user_agent="Mozilla/5.0",
            request_data={"title": "新建文档", "type": "请示"},
            response_status=201,
            created_at=datetime.now() - timedelta(hours=1, minutes=30)
        ),
        AuditLog(
            id=str(uuid.uuid4()),
            user_id=users["manager1"].id,
            action="document:approve",
            resource_type="workflow",
            resource_id=str(uuid.uuid4()),
            ip_address="192.168.1.102",
            user_agent="Mozilla/5.0",
            request_data={"action": "approve", "comment": "同意"},
            response_status=200,
            created_at=datetime.now() - timedelta(minutes=45)
        ),
        AuditLog(
            id=str(uuid.uuid4()),
            user_id=users["employee2"].id,
            action="template:read",
            resource_type="template",
            resource_id=str(uuid.uuid4()),
            ip_address="192.168.1.103",
            user_agent="Mozilla/5.0",
            response_status=200,
            created_at=datetime.now() - timedelta(minutes=15)
        )
    ]
    
    for log in logs:
        session.add(log)
    
    await session.commit()
    logger.info(f"创建了 {len(logs)} 条审计日志")


async def init_database():
    """初始化数据库"""
    logger.info("初始化数据库...")
    async with engine.begin() as conn:
        # 删除所有表
        await conn.run_sync(Base.metadata.drop_all)
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库初始化完成")

async def main():
    """主函数"""
    logger.info("开始创建测试数据集...")
    
    # 初始化数据库
    await init_database()
    
    async with AsyncSessionLocal() as session:
        # 创建用户和角色
        users = await create_users_and_roles(session)
        
        # 创建模板
        templates = await create_templates_and_variables(session, users)
        
        # 创建工作流
        workflows, nodes = await create_workflows(session, users)
        
        # 创建文档
        documents = await create_documents_and_versions(session, users, templates)
        
        # 创建知识库
        await create_knowledge_base(session)
        
        # 创建审计日志
        await create_audit_logs(session, users)
    
    logger.info("=" * 50)
    logger.info("测试数据集创建完成！")
    logger.info(f"数据库位置: {DATA_DIR}/refantastic.db")
    logger.info("=" * 50)
    logger.info("用户账号信息：")
    logger.info("  管理员: admin / password123")
    logger.info("  经理1: manager1 / password123")
    logger.info("  经理2: manager2 / password123")
    logger.info("  员工1: employee1 / password123")
    logger.info("  员工2: employee2 / password123")
    logger.info("  审批人: approver1 / password123")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
