# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-21 16:35:00
# @Last Modified time: 2025-07-07 20:15:30
import logging

from datetime import datetime, timedelta
from enum import Enum

# 添加backend目录到Python路径
# sys.path.append('/home/user/www/ai-backend')
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import URL, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.sql.schema import Table

from backend.app.admin.model.risk_member_analysis import RiskMemberAnalysis
from backend.app.admin.schema.warehouse_user import (
    AgentQueryParams,
    AgentResponse,
    CrmUserQueryParams,
    UserDetailResponse,
    WarehouseUserQueryParams,
    WarehouseUserResponse,
)
from backend.common.enums import RiskType
from backend.common.pagination import PageData
from backend.core.conf import settings


class UserType(str, Enum):
    """用户类型枚举"""

    WAREHOUSE = "warehouse"  # 普通用户
    CRM = "crm"  # CRM用户 (userType='staff')
    AGENT = "agent"  # 代理商 (userType='agent')


logger = logging.getLogger(__name__)


class WarehouseUserService:
    def __init__(self):
        self.database_name = (
            settings.DATABASE_WAREHOUSE_NAME
            if hasattr(settings, "DATABASE_WAREHOUSE_NAME") and settings.DATABASE_WAREHOUSE_NAME
            else "devapi1_mtarde_c"
        )
        self._engine = None
        self._engine_lock = None

    async def _get_engine(self):
        """获取或创建数据库引擎（单例模式）"""
        if self._engine is None:
            if self._engine_lock is None:
                import asyncio

                self._engine_lock = asyncio.Lock()

            async with self._engine_lock:
                if self._engine is None:
                    url = self._create_warehouse_url()
                    self._engine = create_async_engine(
                        url,
                        pool_size=20,  # 增加基本连接池大小
                        max_overflow=30,  # 增加溢出连接数
                        pool_timeout=30,  # 获取连接超时时间
                        pool_recycle=3600,  # 1小时回收连接
                        pool_pre_ping=True,  # 连接前检测
                        echo=False,
                    )
                    logger.info("Created warehouse database engine")
        return self._engine

    # SQLAlchemy 会在进程结束时自动清理连接池，不需要手动管理

    """数据仓用户服务"""

    def _create_warehouse_url(self, database_name: Optional[str] = None) -> URL:
        """创建数据仓库连接URL"""
        return URL.create(
            drivername="mysql+asyncmy",
            username=settings.DATABASE_WAREHOUSE_USER,
            password=settings.DATABASE_WAREHOUSE_PASSWORD,
            host=settings.DATABASE_WAREHOUSE_HOST,
            port=settings.DATABASE_WAREHOUSE_PORT,
            database=database_name or self.database_name,
            query={"charset": settings.DATABASE_WAREHOUSE_CHARSET},
        )

    async def get_t_member_table(self, db: AsyncSession) -> Optional[Table]:
        """获取 t_member 表结构"""
        try:
            # 使用连接池管理的数据库连接
            engine = await self._get_engine()

            # 使用反射获取表结构
            async with engine.connect() as conn:
                # 检查表是否存在
                result = await conn.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.tables "
                        "WHERE table_schema = :db AND table_name = :table"
                    ),
                    {"db": self.database_name, "table": "t_member"},
                )

                if result.scalar() == 0:
                    return None

                # 获取表结构
                result = await conn.execute(
                    text(
                        "SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :table"
                    ),
                    {"db": self.database_name, "table": "t_member"},
                )

                columns = result.fetchall()
                [col[0] for col in columns]

            # 不再手动 dispose 引擎，由连接池管理

            # 使用MetaData创建Table对象
            from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table

            metadata = MetaData()

            # 定义列类型映射
            type_mapping = {
                "int": Integer,
                "varchar": String,
                "char": String,
                "text": String,
                "admin": Integer,
                "tinyint": Boolean,
                "datetime": DateTime,
                "timestamp": DateTime,
            }

            # 创建列对象
            table_columns = []
            for col in columns:
                col_name = col[0]
                data_type = col[1]

                # 确定列类型
                col_type = None
                for db_type, sa_type in type_mapping.items():
                    if db_type in data_type.lower():
                        if db_type == "varchar" or db_type == "char":
                            # 尝试提取长度
                            import re

                            match = re.search(r"\((\d+)\)", data_type)
                            length = int(match.group(1)) if match else 255
                            col_type = sa_type(length)
                        else:
                            col_type = sa_type()
                        break

                # 如果没有匹配的类型，使用String
                if col_type is None:
                    col_type = String()

                table_columns.append(Column(col_name, col_type))

            # 创建Table对象
            t_member = Table("t_member", metadata, *table_columns)
            return t_member

        except Exception as e:
            logger.error(f"Failed to get t_member table: {e}")
            return None

    async def check_t_member_root_path_exists(self) -> bool:
        """检查 t_member_root_path 表是否存在"""
        try:
            # 创建数据仓库连接
            url = self._create_warehouse_url()
            engine = create_async_engine(url)

            # 检查表是否存在
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.tables "
                        "WHERE table_schema = :db AND table_name = :table"
                    ),
                    {"db": self.database_name, "table": "t_member_root_path"},
                )

                exists = result.scalar() > 0

            await engine.dispose()
            return exists

        except Exception as e:
            logger.error(f"Failed to check t_member_root_path table: {e}")
            return False

    async def _execute_query(
        self, query_sql: str, params: Dict = None, page: int = 1, size: int = 10
    ) -> Dict[str, Any]:
        """执行查询并返回分页结果"""
        try:
            # 创建数据仓库连接
            url = self._create_warehouse_url()
            engine = create_async_engine(url)

            async with engine.connect() as conn:
                # 执行计数查询
                count_sql = f"SELECT COUNT(*) FROM ({query_sql}) as total_count"
                count_result = await conn.execute(text(count_sql), params or {})
                total = count_result.scalar() or 0

                # 添加分页
                paged_sql = f"{query_sql} LIMIT {size} OFFSET {(page - 1) * size}"
                result = await conn.execute(text(paged_sql), params or {})

                # 获取结果
                rows = result.fetchall()
                items = [dict(row._mapping) for row in rows]

            await engine.dispose()

            return {"items": items, "total": total, "page": page, "size": size}

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {"items": [], "total": 0, "page": page, "size": size}

    async def _execute_query_all(self, query_sql: str, params: Dict = None) -> List[Dict[str, Any]]:
        """执行查询并返回所有结果（不分页）"""
        try:
            # 创建数据仓库连接
            url = self._create_warehouse_url()
            engine = create_async_engine(url)

            async with engine.connect() as conn:
                result = await conn.execute(text(query_sql), params or {})
                # 获取所有结果
                rows = result.fetchall()
                items = [dict(row._mapping) for row in rows]

            await engine.dispose()
            return items

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    def _build_where_clause(self, conditions: List[str]) -> str:
        """构建WHERE子句"""
        if not conditions:
            return ""
        return "WHERE " + " AND ".join(conditions)

    def _build_user_conditions(
        self,
        user_type: UserType,
        params: Union[WarehouseUserQueryParams, CrmUserQueryParams, AgentQueryParams],
        t_member=None,
    ) -> tuple[List[str], Dict[str, Any]]:
        """构建用户查询条件"""
        conditions = []
        query_params = {}

        # 根据用户类型添加条件
        if user_type == UserType.CRM:
            conditions.append("userType = 'staff'")
        elif user_type == UserType.AGENT:
            conditions.append("userType = 'agent'")
        # WAREHOUSE类型不需要额外的userType条件

        # 通用查询参数
        if hasattr(params, "nickname") and params.nickname:
            conditions.append("nickname LIKE :nickname")
            query_params["nickname"] = f"%{params.nickname}%"

        if hasattr(params, "email") and params.email:
            conditions.append("email LIKE :email")
            query_params["email"] = f"%{params.email}%"

        if hasattr(params, "username") and params.username:
            conditions.append("username LIKE :username")
            query_params["username"] = f"%{params.username}%"

        if hasattr(params, "sex") and params.sex is not None:
            conditions.append("sex = :sex")
            query_params["sex"] = params.sex

        if hasattr(params, "status") and params.status is not None:
            conditions.append("status = :status")
            query_params["status"] = 1 if params.status else 0

        # 关键词搜索
        if hasattr(params, "keyword") and params.keyword:
            keyword_conditions = []
            keyword_conditions.append("nickname LIKE :keyword")
            if hasattr(params, "email"):
                keyword_conditions.append("email LIKE :keyword")
            keyword_conditions.append("username LIKE :keyword")

            # 代理商特有的domain字段
            if user_type == UserType.AGENT and t_member and hasattr(t_member.c, "domain"):
                keyword_conditions.append("domain LIKE :keyword")

            conditions.append(f"({' OR '.join(keyword_conditions)})")
            query_params["keyword"] = f"%{params.keyword}%"

        return conditions, query_params

    def _get_select_fields(self, user_type: UserType) -> str:
        """根据用户类型获取查询字段"""
        base_fields = "id, nickname, status, create_time, last_login_time, avatar"

        if user_type in (UserType.WAREHOUSE, UserType.CRM):
            return f"{base_fields}, email, username, sex, phone, level"
        elif user_type == UserType.AGENT:
            return f"{base_fields}, username, email, domain"

        return base_fields

    async def get_users(
        self,
        db: AsyncSession,
        *,
        user_type: UserType,
        params: Union[WarehouseUserQueryParams, CrmUserQueryParams, AgentQueryParams],
        page: Optional[int] = None,
        size: Optional[int] = None,
    ) -> Union[PageData, List[Union[WarehouseUserResponse, AgentResponse]]]:
        """统一的用户查询方法

        Args:
            user_type: 用户类型
            params: 查询参数
            page: 页码（如果提供则返回分页结果）
            size: 每页大小（如果提供则返回分页结果）

        Returns:
            如果提供page和size则返回PageData，否则返回List
        """
        # 尝试获取表结构
        t_member = await self.get_t_member_table(db)
        if t_member is None:
            if page is not None and size is not None:
                return PageData(
                    items=[],
                    total=0,
                    page=page,
                    size=size,
                    total_pages=0,
                    links={
                        "first": f"?page=1&size={size}",
                        "last": f"?page=1&size={size}",
                        "self": f"?page={page}&size={size}",
                        "next": None,
                        "prev": None,
                    },
                )
            else:
                return []

        # 构建查询条件
        conditions, query_params = self._build_user_conditions(user_type, params, t_member)

        # 构建SQL
        select_fields = self._get_select_fields(user_type)
        where_clause = self._build_where_clause(conditions)
        query_sql = f"""
            SELECT {select_fields}
            FROM t_member
            {where_clause}
            ORDER BY id DESC
        """

        # 执行查询
        if page is not None and size is not None:
            # 分页查询
            result = await self._execute_query(query_sql, query_params, page, size)

            # 计算分页链接
            from math import ceil

            total = result["total"]
            total_pages = ceil(total / size) if total > 0 else 1

            # 转换为响应模型
            if user_type == UserType.AGENT:
                items = [AgentResponse(**item) for item in result["items"]]
            else:
                items = [WarehouseUserResponse(**item) for item in result["items"]]

            return PageData(
                items=items,
                total=result["total"],
                page=page,
                size=size,
                total_pages=total_pages,
                links={
                    "first": f"?page=1&size={size}",
                    "last": f"?page={total_pages}&size={size}",
                    "self": f"?page={page}&size={size}",
                    "next": f"?page={page + 1}&size={size}" if page < total_pages else None,
                    "prev": f"?page={page - 1}&size={size}" if page > 1 else None,
                },
            )
        else:
            # 不分页查询
            items = await self._execute_query_all(query_sql, query_params)

            # 转换为响应模型
        if user_type == UserType.AGENT:
            return [AgentResponse(**item) for item in items]
        else:
            return [WarehouseUserResponse(**item) for item in items]

    async def get_user_detail(
        self,
        db: AsyncSession,
        user_id: int,
        user_type: Optional[UserType] = None,
    ) -> Optional[UserDetailResponse]:
        """统一的用户详情查询方法"""
        # 尝试获取表结构
        t_member = await self.get_t_member_table(db)
        if t_member is None:
            return None

        # 构建查询条件
        conditions = [f"id = {user_id}"]

        # 根据用户类型添加额外条件
        if user_type == UserType.CRM:
            conditions.append("userType = 'staff'")
        elif user_type == UserType.AGENT:
            # 检查t_member_root_path表是否存在
            has_root_path_table = await self.check_t_member_root_path_exists()

            if has_root_path_table:
                # 使用EXISTS子查询检查用户ID是否在path中
                query_sql = f"""
                    SELECT m.*
                    FROM t_member m
                    WHERE m.id = {user_id}
                    AND EXISTS (
                        SELECT 1
                        FROM t_member_root_path
                        WHERE FIND_IN_SET({user_id}, path) > 0
                    )
                    LIMIT 1
                """
            else:
                # 如果t_member_root_path表不存在，使用is_agent字段
                if hasattr(t_member.c, "is_agent"):
                    conditions.append("is_agent = 1")

                # 构建SQL
                where_clause = self._build_where_clause(conditions)
                query_sql = f"""
                    SELECT * FROM t_member
                    {where_clause}
                    LIMIT 1
                """
        else:
            # 普通用户或未指定类型
            where_clause = self._build_where_clause(conditions)
            query_sql = f"""
                SELECT * FROM t_member
                {where_clause}
                LIMIT 1
            """

        try:
            # 使用连接池管理的数据库连接
            engine = await self._get_engine()
            async with engine.connect() as conn:
                result = await conn.execute(text(query_sql))
                user = result.fetchone()

            if user:
                user_dict = dict(user._mapping)
                converted_user_dict = self._convert_user_data_for_pydantic(user_dict)

                if converted_user_dict is None:
                    logger.error(f"Failed to convert user data for user ID: {user_dict.get('id', 'unknown')}")
                    return None

                try:
                    return UserDetailResponse(**converted_user_dict)
                except Exception as validation_error:
                    logger.error(
                        f"Failed to create UserDetailResponse for user {converted_user_dict.get('id', 'unknown')}: {validation_error}"
                    )
                    logger.error(f"User data: {converted_user_dict}")
                    return None

            return None

        except Exception as e:
            logger.error(f"Failed to get user detail: {e}")
            return None

    async def get_warehouse_user_list(
        self,
        db: AsyncSession,
        *,
        params: WarehouseUserQueryParams,
        page: int = 1,
        size: int = 10,
    ) -> PageData:
        """获取普通用户列表"""
        return await self.get_users(db, user_type=UserType.WAREHOUSE, params=params, page=page, size=size)

    async def get_all_warehouse_users(
        self,
        db: AsyncSession,
        *,
        params: WarehouseUserQueryParams,
    ) -> List[WarehouseUserResponse]:
        """获取所有普通用户（不分页）"""
        return await self.get_users(db, user_type=UserType.WAREHOUSE, params=params)

    async def get_warehouse_user_detail(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[UserDetailResponse]:
        """获取普通用户详情"""
        return await self.get_user_detail(db, user_id, UserType.WAREHOUSE)

    async def get_crm_user_list(
        self,
        db: AsyncSession,
        *,
        params: CrmUserQueryParams,
        page: int = 1,
        size: int = 10,
    ) -> PageData:
        """获取CRM用户列表"""
        return await self.get_users(db, user_type=UserType.CRM, params=params, page=page, size=size)

    async def get_crm_user_detail(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[UserDetailResponse]:
        """获取CRM用户详情"""
        return await self.get_user_detail(db, user_id, UserType.CRM)

    async def get_agent_list(
        self,
        db: AsyncSession,
        *,
        params: AgentQueryParams,
        page: int = 1,
        size: int = 10,
    ) -> PageData:
        """获取代理商列表"""
        return await self.get_users(db, user_type=UserType.AGENT, params=params, page=page, size=size)

    async def get_all_agents(
        self,
        db: AsyncSession,
        *,
        params: AgentQueryParams,
    ) -> List[AgentResponse]:
        """获取所有代理商（不分页）"""
        return await self.get_users(db, user_type=UserType.AGENT, params=params)

    async def get_all_crm_users(
        self,
        db: AsyncSession,
        *,
        params: CrmUserQueryParams,
    ) -> List[WarehouseUserResponse]:
        """获取所有CRM用户（不分页）"""
        return await self.get_users(db, user_type=UserType.CRM, params=params)

    async def get_agent_detail(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[UserDetailResponse]:
        """获取代理商详情"""
        return await self.get_user_detail(db, user_id, UserType.AGENT)

    async def get_users_under_agent(self, db: AsyncSession, *, agent_ids: List[int]) -> List[int]:
        """获取代理商下的所有用户ID

        查询指定代理商下属的所有用户ID。
        如果t_member_root_path表存在，使用该表的path字段来确定层级关系；
        否则尝试使用其他字段来确定关系。

        参数:
        - agent_ids: 代理商ID列表

        返回:
        - 用户ID列表
        """
        if not agent_ids:
            logger.warning("get_users_under_agent called with empty agent_ids list")
            return []

        # 确保agent_ids是列表类型且包含有效ID
        valid_agent_ids = []
        for id in agent_ids:
            try:
                valid_agent_ids.append(int(id))
            except (ValueError, TypeError):
                logger.warning(f"Skipping invalid agent id: {id}")
                continue

        if not valid_agent_ids:
            logger.warning("No valid agent IDs after filtering")
            return []

        # 检查t_member_root_path表是否存在
        has_root_path_table = await self.check_t_member_root_path_exists()

        try:
            # 创建数据仓库连接
            url = self._create_warehouse_url()
            engine = create_async_engine(url)

            async with engine.connect() as conn:
                if has_root_path_table:
                    # 如果t_member_root_path表存在，使用该表查询层级关系
                    agent_ids_str = ",".join(map(str, valid_agent_ids))
                    query_sql = f"""
                        SELECT DISTINCT m.id
                        FROM t_member m
                        JOIN t_member_root_path rp ON
                            (
                                -- 查找所有在代理商路径中的用户
                                {" OR ".join([f"FIND_IN_SET({agent_id}, rp.path) > 0" for agent_id in valid_agent_ids])}
                            )
                            AND FIND_IN_SET(m.id, rp.path) > 0
                            -- 排除代理商自己
                            AND m.id NOT IN ({agent_ids_str})
                    """
                else:
                    # 如果不存在t_member_root_path表，尝试使用parent_id字段或其他关联字段
                    # 这里提供一个基础实现，实际应根据数据库结构调整
                    query_sql = f"""
                        SELECT id FROM t_member
                        WHERE parent_id IN ({",".join(map(str, valid_agent_ids))})
                    """

                result = await conn.execute(text(query_sql))
                user_ids = [row[0] for row in result.fetchall()]

            await engine.dispose()
            return user_ids

        except Exception as e:
            logger.error(f"Failed to get users under agent: {e}")
            return []

    async def get_analyzed_member_ids(
        self,
        db: AsyncSession,
        *,
        risk_type: str,
    ) -> List[str]:
        """获取已分析的用户ID列表

        根据风险类型查询已经分析过的用户ID

        参数:
        - risk_type: 风险类型

        返回:
        - 已分析的用户ID列表
        """
        try:
            # 创建查询
            query = select(RiskMemberAnalysis.member_id).where(RiskMemberAnalysis.risk_type == risk_type).distinct()

            result = await db.execute(query)
            member_ids = [str(row[0]) for row in result.fetchall()]

            return member_ids
        except Exception as e:
            logger.error(f"Failed to get analyzed member IDs: {e}")
            return []

    async def get_unanalyzed_users_by_risk_type(
        self,
        db: AsyncSession,
        *,
        risk_type: str,
        limit: int = 1,
    ) -> List[UserDetailResponse]:
        """获取未分析的用户

        根据风险类型获取未分析的用户

        参数:
        - risk_type: 风险类型，不同的风险类型将使用不同的SQL查询
        - limit: 返回用户数量限制

        返回:
        - 未分析用户信息列表
        """
        # 获取已分析的用户ID
        analyzed_ids = await self.get_analyzed_member_ids(db, risk_type=risk_type)

        # 构建查询条件
        conditions = []
        query_params = {}

        # 排除已分析的用户
        if analyzed_ids:
            analyzed_ids_str = ",".join(analyzed_ids)
            conditions.append(f"id NOT IN ({analyzed_ids_str})")

        # 根据用户类型构建不同的查询
        if risk_type == RiskType.ALL_EMPLOYEE:
            # 客户条件：userType='direct'
            conditions.append("userType = 'direct'")

            # 构建SQL
            where_clause = self._build_where_clause(conditions)
            limit_clause = f"LIMIT {limit}" if limit is not None else ""
            query_sql = f"""
                SELECT id, nickname, email, username, sex, status,
                       create_time, last_login_time, avatar, phone, level
                FROM t_member
                {where_clause}
                ORDER BY id ASC
                {limit_clause}
            """

        elif risk_type == RiskType.CRM_USER:
            # 员工条件：userType='staff'
            conditions.append("userType = 'staff'")

            # 构建SQL
            where_clause = self._build_where_clause(conditions)
            limit_clause = f"LIMIT {limit}" if limit is not None else ""
            query_sql = f"""
                SELECT id, nickname, email, username, sex, status,
                       create_time, last_login_time, avatar, phone, level
                FROM t_member
                {where_clause}
                ORDER BY id ASC
                {limit_clause}
            """

        elif risk_type == RiskType.AGENT_USER:
            # 代理用户条件：userType='agent'
            conditions.append("userType = 'agent'")

            # 构建SQL
            where_clause = self._build_where_clause(conditions)
            limit_clause = f"LIMIT {limit}" if limit is not None else ""
            query_sql = f"""
                SELECT id, nickname, email, username, sex, status,
                       create_time, last_login_time, avatar, phone, level
                FROM t_member
                {where_clause}
                ORDER BY id ASC
                {limit_clause}
            """

        elif risk_type == RiskType.PAYMENT:
            # 财务风控：查询所有用户（可根据业务需求调整条件）
            # 构建SQL
            where_clause = self._build_where_clause(conditions)
            limit_clause = f"LIMIT {limit}" if limit is not None else ""
            query_sql = f"""
                SELECT id, nickname, email, username, sex, status,
                       create_time, last_login_time, avatar, phone, level
                FROM t_member
                {where_clause}
                ORDER BY id ASC
                {limit_clause}
            """
        else:
            # 不支持的用户类型
            logger.error(f"Unsupported user_type: {risk_type}")
            return []

        try:
            # 创建数据仓库连接
            url = self._create_warehouse_url()
            engine = create_async_engine(url)

            async with engine.connect() as conn:
                result = await conn.execute(text(query_sql), query_params)
                users = result.fetchall()

            await engine.dispose()

            # 转换数据并创建UserDetailResponse对象
            converted_users = []
            for user in users:
                user_dict = dict(user._mapping)
                converted_user_dict = self._convert_user_data_for_pydantic(user_dict)

                if converted_user_dict is None:
                    logger.warning(f"Skipping user due to conversion failure: {user_dict.get('id', 'unknown')}")
                    continue

                try:
                    user_response = UserDetailResponse(**converted_user_dict)
                    converted_users.append(user_response)
                except Exception as validation_error:
                    logger.error(
                        f"Failed to create UserDetailResponse for user {converted_user_dict.get('id', 'unknown')}: {validation_error}"
                    )
                    logger.error(f"User data: {converted_user_dict}")
                    continue

            return converted_users

        except Exception as e:
            logger.error(f"Failed to get unanalyzed users: {e}")
            return []

    async def get_all_countries(self) -> List[Dict[str, Any]]:
        """获取所有国家列表（不分页）"""
        try:
            # 创建数据仓库连接
            url = self._create_warehouse_url()
            engine = create_async_engine(url)

            async with engine.connect() as conn:
                # 检查表是否存在
                result = await conn.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.tables "
                        "WHERE table_schema = :db AND table_name = :table"
                    ),
                    {"db": self.database_name, "table": "t_country"},
                )

                if result.scalar() == 0:
                    await engine.dispose()
                    logger.warning("t_country table does not exist")
                    return []

                # 查询所有国家数据
                query_sql = "SELECT * FROM t_country"
                result = await conn.execute(text(query_sql))
                countries = result.fetchall()

            await engine.dispose()

            # 转换为字典列表
            return [dict(country._mapping) for country in countries]

        except Exception as e:
            logger.error(f"Failed to get countries: {e}")
            return []

    async def get_agent_user_id(self, agent_ids: list) -> Optional[int]:
        """根据智能体ID获取用户ID"""
        try:
            # 检查t_member_root_path表是否存在
            has_root_path_table = await self.check_t_member_root_path_exists()
            url = self._create_warehouse_url()
            engine = create_async_engine(url)
            if has_root_path_table:
                condict = ""
                for agent_id in agent_ids:
                    condict += (
                        f"path LIKE '{agent_id},%' OR path LIKE '%,{agent_id},%' OR path LIKE '%,{agent_id}' AND "
                    )
                condict = condict[:-5]
                async with engine.connect() as conn:
                    query_sql = f"""
                        SELECT member_id
                        FROM t_member_root_path
                        WHERE {condict}
                    """
                    result = await conn.execute(text(query_sql))
                    user_ids = [row[0] for row in result.fetchall()]
                await engine.dispose()
                return user_ids

        except Exception as e:
            logger.error(f"Failed to get agent user ID: {e}")
            return None

    async def get_need_analyzed_user_ids(self, condition: dict) -> List[int]:
        """获取需要分析用户ID列表"""

        try:
            user_ids = []
            condict = ""
            if condition.get("agent"):
                agent_user_ids = await self.get_agent_user_id(condition["agent"])
                if agent_user_ids:
                    user_ids.extend(agent_user_ids)
            if condition.get("customer"):
                customer_data = condition["customer"]
                if isinstance(customer_data, list):
                    user_ids.extend(customer_data)
                elif isinstance(customer_data, (int, str)):
                    user_ids.append(int(customer_data))
                else:
                    logger.warning(f"Unsupported customer data type: {type(customer_data)}")
            if condition.get("user"):
                user_data = condition["user"]
                if isinstance(user_data, list):
                    user_ids.extend(user_data)
                elif isinstance(user_data, (int, str)):
                    user_ids.append(int(user_data))
                else:
                    logger.warning(f"Unsupported user data type: {type(user_data)}")
            if condition.get("country") and isinstance(condition["country"], list):
                country_list = "','".join(condition["country"])
                condict += f"country IN ('{country_list}') AND "
            if condition.get("user_tag"):
                condict += f"user_tag = '{condition['user_tag']}' AND "
            if condition.get("kyc_status"):
                condict += f"kyc_status = '{condition['kyc_status']}' AND "
            if condition.get("register_time"):
                days_ago = int(condition["register_time"])  # 确保是整数
                cutoff_date = datetime.now() - timedelta(days=days_ago)
                cutoff_timestamp = int(cutoff_date.timestamp())
                condict += f"create_time >= '{cutoff_timestamp}' AND "
            if not condict and len(user_ids) > 0:
                return user_ids

            if len(user_ids) > 0:
                condict += f"id IN ({','.join([f'{user_id}' for user_id in user_ids])}) AND "
            if condict:
                condict = condict[:-5]
                url = self._create_warehouse_url()
                engine = create_async_engine(url)
                async with engine.connect() as conn:
                    query_sql = f"""
                        SELECT DISTINCT id
                        FROM t_member
                        WHERE {condict}
                    """
                    result = await conn.execute(text(query_sql))
                    member_ids = [row[0] for row in result.fetchall()]
                await engine.dispose()
                return member_ids
            return []
        except Exception as e:
            logger.error(f"Failed to get analyzed user IDs: {e}")
            return []

    async def get_user_id_by_username(self, username: str | List[str]) -> Optional[int] | List[int]:
        """通过用户名查找用户ID

        参数:
        - username: 用户名或用户名列表

        返回:
        - 单个用户名: 返回用户ID，如果未找到则返回None
        - 用户名列表: 返回用户ID列表，只包含找到的用户ID
        """
        try:
            # 创建数据仓库连接
            url = self._create_warehouse_url()
            engine = create_async_engine(url)

            # 处理单个用户名
            if isinstance(username, str):
                async with engine.connect() as conn:
                    query_sql = "SELECT id FROM t_member WHERE username = :username LIMIT 1"
                    result = await conn.execute(text(query_sql), {"username": username})
                    user = result.fetchone()

                await engine.dispose()

                if user:
                    return user[0]
                return None

            # 处理用户名列表
            elif isinstance(username, list) and username:
                usernames = [u for u in username if isinstance(u, str)]
                if not usernames:
                    return []

                placeholders = ", ".join([f":username{i}" for i in range(len(usernames))])
                params = {f"username{i}": username for i, username in enumerate(usernames)}

                async with engine.connect() as conn:
                    query_sql = f"SELECT id, username FROM t_member WHERE username IN ({placeholders})"
                    result = await conn.execute(text(query_sql), params)
                    users = result.fetchall()

                await engine.dispose()

                # 返回找到的用户ID列表
                return [user[0] for user in users]

            return [] if isinstance(username, list) else None

        except Exception as e:
            logger.error(f"Failed to get user ID by username: {e}")
            return [] if isinstance(username, list) else None

    def _convert_user_data_for_pydantic(self, user_data: dict) -> dict:
        """
        转换用户数据以符合Pydantic模型要求

        Args:
            user_data: 从数据库查询得到的原始用户数据

        Returns:
            转换后的用户数据字典

        Note:
            status字段转换规则：
            - 1 (已激活) → True
            - 0 (未激活) → False
            - -1 (已删除) → None
        """
        converted_data = dict(user_data)

        # 转换status字段：将int类型的status转换为bool类型
        if "status" in converted_data:
            status_value = converted_data["status"]
            if isinstance(status_value, int):
                # 根据业务逻辑：0-未激活，1-已激活，-1-已删除
                if status_value == 1:
                    converted_data["status"] = True  # 已激活
                elif status_value == 0:
                    converted_data["status"] = False  # 未激活
                elif status_value == -1:
                    converted_data["status"] = None  # 已删除
                else:
                    # 对于其他未知值，设置为None并记录警告
                    converted_data["status"] = None
                    logger.warning(f"Unknown status value: {status_value}, setting to None")
            elif isinstance(status_value, bool):
                # 如果已经是bool类型，保持不变
                pass
            else:
                # 其他类型设置为None
                converted_data["status"] = None
                logger.warning(f"Unexpected status type: {type(status_value)}, value: {status_value}, setting to None")

        # 转换其他可能需要类型转换的字段
        # 确保id字段是int类型
        if "id" in converted_data:
            try:
                converted_data["id"] = int(converted_data["id"])
            except (ValueError, TypeError):
                logger.error(f"Invalid id value: {converted_data['id']}")
                return None

        # 转换sex字段：确保是int类型
        if "sex" in converted_data and converted_data["sex"] is not None:
            try:
                converted_data["sex"] = int(converted_data["sex"])
            except (ValueError, TypeError):
                converted_data["sex"] = None
                logger.warning(f"Invalid sex value: {converted_data['sex']}, setting to None")

        # 转换level字段：确保是int类型
        if "level" in converted_data and converted_data["level"] is not None:
            try:
                converted_data["level"] = int(converted_data["level"])
            except (ValueError, TypeError):
                converted_data["level"] = None
                logger.warning(f"Invalid level value: {converted_data['level']}, setting to None")

        # 转换scope和admin字段：确保是int类型
        for field in ["scope", "admin"]:
            if field in converted_data and converted_data[field] is not None:
                try:
                    converted_data[field] = int(converted_data[field])
                except (ValueError, TypeError):
                    converted_data[field] = None
                    logger.warning(f"Invalid {field} value: {converted_data[field]}, setting to None")

        return converted_data


# 创建服务实例
warehouse_user_service = WarehouseUserService()

# if __name__ == "__main__":
#     import asyncio
#     from backend.database.db import async_engine
#     from sqlalchemy.ext.asyncio import AsyncSession

#     async def get_agent_user():
#         condition = {
#             "register_time": 30,
#             # "customer": [
#             #     3600,
#             #     3601
#             # ],

#             # "agent": [3598],
#             "country": [
#                 "Albania",
#                 "Algeria"
#             ],
#             "user_tag": "0",
#             "kyc_status": "0"
#         }
#         async with AsyncSession(async_engine) as session:
#             countries = await warehouse_user_service.get_analyzed_user_ids(condition)
#             print(countries)

#     # 运行测试
#     asyncio.run(get_agent_user())
