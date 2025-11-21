#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.schema import QueryDataResponse
from app.services.sql_generate_service import SQLGenerator
from core.config import settings
from core.log import logger
from core.query_logger import QueryTimer
from core.sql_config import SQL_TABLES
from db.warehouse import warehouse_db as base_db
from utils.data import convert_to_list, convert_to_timestamp
from utils.date import get_register_time
from utils.device_name_extractor import device_extractor
from utils.query_type_helper import get_query_type_description

TABLE_MEMBER = "t_member"
TABLE_OPERATION_LOG = "t_operation_log"  # created_at 使用时间戳
TABLE_AMOUNT_LOG = "t_member_amount_log"  # create_at 使用的标准时间
TABLE_LOGIN_LOG = "t_member_login_log"  # create_time 使用的时间戳
TABLE_FORWORD_LOG = "t_member_forword_log"  # create_time 使用的时间戳
TABLE_MTLOGIN = "t_member_mtlogin"  # create_time 使用的时间戳

QUERY_TYPE_USER = "user_data"
QUERY_TYPE_OP_LOG = "user_op_log"
QUERY_TYPE_AMOUNT_LOG = "user_amount_log"
QUERY_TYPE_LOGIN_LOG = "user_login_log"
QUERY_TYPE_FORWORD_LOG = "user_forword_log"
QUERY_TYPE_MTLOGIN = "user_mtlogin"


class WarehouseUserService:
    """仓库用户服务，处理用户信息查询"""

    def __init__(self):
        self._query_start_time: Optional[float] = None
        # 采用与配置一致的数据库名，避免硬编码
        try:
            self._member_db = SQL_TABLES.get("t_member", {}).get("database_name")
        except Exception:
            self._member_db = None

    def _build_user_conditions(
        self, parameters: Dict[str, Any], sql_generator: SQLGenerator
    ) -> None:
        """构建用户查询条件"""
        user_conditions = []
        condition_params = []

        username = parameters.get("username")
        if username:
            # username 只支持模糊搜索，不支持数组
            if isinstance(username, (str, int)):
                user_conditions.append(f"t_member.nickname LIKE %s")
                condition_params.append(f"%{username}%")
            else:
                # 如果传入数组，抛出错误
                raise ValueError("username 参数只支持单个字符串，不支持数组格式，请使用 user_name 参数进行数组查询")

        user_id = parameters.get("user_id")
        if user_id is not None:
            if isinstance(user_id, (str, int)):
                user_conditions.append(f"t_member.id = %s")
                condition_params.append(int(user_id))
            elif isinstance(user_id, list) and len(user_id) > 0:
                placeholders = ", ".join(["%s"] * len(user_id))
                user_conditions.append(f"t_member.id IN ({placeholders})")
                condition_params.extend([int(uid) for uid in user_id])

        user_name = convert_to_list(parameters.get("user_name", []))

        user_sql_parts = []
        if user_name:
            placeholders = ", ".join(["%s"] * len(user_name))
            user_sql_parts.append(f"t_member.nickname IN ({placeholders})")
            condition_params.extend(user_name)

        if user_sql_parts:
            user_conditions.append("(" + " OR ".join(user_sql_parts) + ")")

        if user_conditions:
            # 将OR条件整体包裹括号，确保与其他条件按AND正确结合
            or_condition = "(" + " OR ".join(user_conditions) + ")"
            sql_generator.add_raw_condition(or_condition, *condition_params)

    async def _execute_query_with_timing(
        self, sql: str, params: List[Any]
    ) -> Tuple[List[Any], float]:
        """执行查询并计时"""
        start_time = time.time()
        results = await base_db.execute_query(sql, params)
        execution_time = time.time() - start_time
        return results, execution_time

    def _build_sql_info(
        self,
        sql_generator: SQLGenerator,
        sql: str,
        params: List[Any],
        execution_time: float,
        row_count: int,
    ) -> Dict[str, Any]:
        """构建SQL信息字典"""
        return {
            "table": sql_generator.table_name,
            "sql": sql,
            "parameters": params,
            "execution_time": execution_time,
            "row_count": row_count,
        }

    def _build_query_metadata(self, query_type: str) -> Dict[str, Any]:
        """构建查询元数据"""
        return {"query_type": query_type, "timestamp": datetime.now().isoformat()}

    async def _query_log_data(
        self,
        table_name: str,
        parameters: Dict[str, Any],
        query_type: str,
        time_field: str = "create_time",
        process_result: Optional[callable] = None,
        **kwargs,
    ) -> QueryDataResponse:
        """通用日志查询方法"""
        try:
            member_id = await self._get_user_id(parameters)
            sql_generator = SQLGenerator(table_name)
            if member_id:
                sql_generator.add_condition("member_id", "in", member_id)
            elif table_name != "t_member":
                sql_generator.add_join_table(
                    "t_member",
                    "member_id",
                    "id",
                    join_type="LEFT JOIN",
                    table_alias="user",
                )

            sql, params = sql_generator.generate_sql(
                parameters,
                time_field=time_field,
                isstrptime=kwargs.get("isstrptime", True),
                order_by=(time_field, "DESC"),
            )

            # 使用查询计时器记录SQL执行情况
            with QueryTimer(
                query_type, parameters, sql, table_name, sql_params=params
            ) as timer:
                self._query_start_time = time.time()
                results, execution_time = await self._execute_query_with_timing(
                    sql, params
                )

                # 记录查询结果
                timer.log_result(len(results) if results else 0, results)

            if process_result and results:
                results = process_result(results)

            sql_info = self._build_sql_info(
                sql_generator,
                sql,
                params,
                execution_time,
                len(results) if results else 0,
            )
            query_metadata = self._build_query_metadata(query_type)

            # 无论是否有结果，都返回success=True，没有数据时返回空列表
            return QueryDataResponse(
                success=True,
                message="查询成功"
                if results
                else f"未找到{get_query_type_description(query_type)}",
                data=results if results else [],
                parameters=parameters,
                sql_info=sql_info,
                query_metadata=query_metadata,
            )
        except Exception as e:
            logger.error(f"查询{get_query_type_description(query_type)}错误: {str(e)}")

            return QueryDataResponse(
                success=False,
                message=str(e),
                data=None,
                parameters=parameters,
                sql_info=None,
                query_metadata={
                    "query_type": query_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    async def get_user(self, parameters: Dict[str, Any]) -> QueryDataResponse:
        """查询用户信息"""
        try:
            sql_generator = SQLGenerator(TABLE_MEMBER)

            self._build_user_conditions(parameters, sql_generator)

            # 授权限制：根据crm_user_id判断角色与范围
            crm_user_id = parameters.get("crm_user_id")
            if crm_user_id is not None and str(crm_user_id).strip():
                try:
                    scope = await self._get_crm_access_scope(int(crm_user_id))
                    if not scope.get("exists"):
                        return QueryDataResponse(
                            success=False,
                            message="crm_user不存在或不可用",
                            data=None,
                            parameters=parameters,
                            sql_info=None,
                            query_metadata={
                                "query_type": QUERY_TYPE_USER,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )
                    # admin放行，非admin按范围限制
                    if not scope.get("is_admin"):
                        restrict_ids = scope.get("accessible_member_ids") or []
                        if not restrict_ids:
                            return QueryDataResponse(
                                success=False,
                                message="无权限或无可访问成员",
                                data=None,
                                parameters=parameters,
                                sql_info=None,
                                query_metadata={
                                    "query_type": QUERY_TYPE_USER,
                                    "timestamp": datetime.now().isoformat(),
                                },
                            )

                        # 对于 user_name 或 user_id 数组查询，需要特殊处理权限检查
                        if (
                            parameters.get("user_name")
                            and isinstance(parameters.get("user_name"), list)
                        ) or (
                            parameters.get("user_id")
                            and isinstance(parameters.get("user_id"), list)
                        ):
                            # 先查询所有匹配的用户（不限制权限，但应用limit限制）
                            temp_sql_generator = SQLGenerator(TABLE_MEMBER)
                            self._build_user_conditions(parameters, temp_sql_generator)

                            # 应用limit限制
                            limit_param = parameters.get("limit")
                            if limit_param is not None and limit_param > 0:
                                temp_sql_generator.limit(limit_param)
                            else:
                                temp_sql_generator.limit(settings.DEFAULT_LIMIT)

                            temp_sql, temp_params = temp_sql_generator.generate_select()
                            temp_results, _ = await self._execute_query_with_timing(
                                temp_sql, temp_params
                            )

                            if temp_results:
                                # 检查是否有无权限的用户
                                unauthorized_users = [
                                    user
                                    for user in temp_results
                                    if user.get("id") not in restrict_ids
                                ]
                                if unauthorized_users:
                                    # 获取无权限的用户信息（包含ID和昵称）
                                    unauthorized_info = []
                                    for user in unauthorized_users:
                                        nickname = user.get("nickname")
                                        user_id = user.get("id")
                                        if nickname and user_id:
                                            unauthorized_info.append(
                                                f"{nickname}(ID:{user_id})"
                                            )
                                        elif nickname:
                                            unauthorized_info.append(nickname)

                                    return QueryDataResponse(
                                        success=False,
                                        message=f"您没有查询用户 {', '.join(unauthorized_info)} 的权限",
                                        data=None,
                                        parameters=parameters,
                                        sql_info=None,
                                        query_metadata={
                                            "query_type": QUERY_TYPE_USER,
                                            "timestamp": datetime.now().isoformat(),
                                        },
                                    )

                        sql_generator.add_condition(
                            "id", "in", restrict_ids, TABLE_MEMBER
                        )
                except Exception:
                    # crm_user_id 非法时，返回错误
                    return QueryDataResponse(
                        success=False,
                        message="crm_user_id参数无效",
                        data=None,
                        parameters=parameters,
                        sql_info=None,
                        query_metadata={
                            "query_type": QUERY_TYPE_USER,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

            user_type = parameters.get("user_type")
            if user_type:
                sql_generator.add_condition("userType", "=", user_type, TABLE_MEMBER)

            country_param = convert_to_list(parameters.get("country", []))
            if country_param:
                country_param = [
                    c.capitalize() if isinstance(c, str) else c for c in country_param
                ]
                sql_generator.add_condition(
                    "country", "in", country_param, TABLE_MEMBER
                )

            if "kyc" in parameters:
                sql_generator.add_condition(
                    "kyc_status", "=", parameters.get("kyc"), TABLE_MEMBER
                )

            if "email" in parameters:
                email_param = convert_to_list(parameters.get("email", []))
                if email_param:
                    sql_generator.add_condition(
                        "email", "in", email_param, TABLE_MEMBER
                    )

            register_time = None
            # check_date = self.check_user_params(parameters)
            if "register_time" in parameters:
                register_time = parameters.get("register_time")
            # else:
            #     if not check_date and "range_time" in parameters:
            #         register_time = parameters.get("range_time")
            if register_time:
                register_start_time, register_end_time = get_register_time(
                    register_time
                )
                if register_start_time:
                    sql_generator.add_condition(
                        "create_time", ">=", register_start_time
                    )
                if register_end_time:
                    sql_generator.add_condition("create_time", "<=", register_end_time)

            sql_generator.order_by_clause("create_time", "DESC", TABLE_MEMBER)

            # 处理限制条数
            limit_param = parameters.get("limit")
            if limit_param is not None:
                if limit_param == 0:
                    return QueryDataResponse(
                        success=False,
                        message="limit参数不能为0，请指定一个大于0的数值或不传该参数使用默认限制",
                        data=None,
                        parameters=parameters,
                        sql_info=None,
                        query_metadata={
                            "query_type": QUERY_TYPE_USER,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                elif limit_param > 0:
                    sql_generator.limit(limit_param)
                else:
                    return QueryDataResponse(
                        success=False,
                        message=f"limit参数必须是正整数，当前值: {limit_param}",
                        data=None,
                        parameters=parameters,
                        sql_info=None,
                        query_metadata={
                            "query_type": QUERY_TYPE_USER,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
            else:
                sql_generator.limit(settings.DEFAULT_LIMIT)

            if not sql_generator.conditions:
                return QueryDataResponse(
                    success=True,
                    message="未找到用户",
                    data=[],
                    parameters=parameters,
                    sql_info=None,
                    query_metadata={
                        "query_type": QUERY_TYPE_USER,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            sql, params = sql_generator.generate_select()

            # 使用查询计时器记录SQL执行情况
            with QueryTimer(
                QUERY_TYPE_USER, parameters, sql, TABLE_MEMBER, sql_params=params
            ) as timer:
                results, execution_time = await self._execute_query_with_timing(
                    sql, params
                )

                # 记录查询结果
                timer.log_result(len(results) if results else 0, results)

            sql_info = self._build_sql_info(
                sql_generator,
                sql,
                params,
                execution_time,
                len(results) if results else 0,
            )
            query_metadata = self._build_query_metadata(QUERY_TYPE_USER)

            # 检查是否因为权限限制导致查询结果为空
            if not results and crm_user_id is not None and str(crm_user_id).strip():
                try:
                    scope = await self._get_crm_access_scope(int(crm_user_id))
                    if scope.get("exists") and not scope.get("is_admin"):
                        # 检查是否有明确的用户名查询但结果为空
                        if parameters.get("user_name") or parameters.get("username"):
                            # 先查询所有匹配的用户（不限制权限）来获取具体信息
                            temp_params = parameters.copy()
                            temp_params.pop("crm_user_id", None)
                            temp_user_info = await self.get_user(temp_params)

                            if temp_user_info.success and temp_user_info.data:
                                # 获取查询到的用户信息（包含ID和昵称）
                                found_users = (
                                    temp_user_info.data
                                    if isinstance(temp_user_info.data, list)
                                    else [temp_user_info.data]
                                )
                                unauthorized_info = []
                                for user in found_users:
                                    nickname = user.get("nickname")
                                    user_id = user.get("id")
                                    if nickname and user_id:
                                        unauthorized_info.append(
                                            f"{nickname}(ID:{user_id})"
                                        )
                                    elif nickname:
                                        unauthorized_info.append(nickname)

                                if unauthorized_info:
                                    return QueryDataResponse(
                                        success=False,
                                        message=f"您没有查询用户 {', '.join(unauthorized_info)} 的权限",
                                        data=None,
                                        parameters=parameters,
                                        sql_info=sql_info,
                                        query_metadata=query_metadata,
                                    )
                            return QueryDataResponse(
                                success=False,
                                message="您没有查询该用户的权限",
                                data=None,
                                parameters=parameters,
                                sql_info=sql_info,
                                query_metadata=query_metadata,
                            )
                except Exception:
                    pass

            # 无论是否有结果，都返回success=True，没有数据时返回空列表
            return QueryDataResponse(
                success=True,
                message="查询成功" if results else "未找到用户",
                data=results if results else [],
                parameters=parameters,
                sql_info=sql_info,
                query_metadata=query_metadata,
            )

        except Exception as e:
            logger.error(f"查询用户信息错误: {str(e)}")

            return QueryDataResponse(
                success=False,
                message=str(e),
                data=None,
                parameters=parameters,
                sql_info=None,
                query_metadata={
                    "query_type": QUERY_TYPE_USER,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    async def get_user_op_log(self, parameters: Dict[str, Any]) -> QueryDataResponse:
        """查询用户操作日志"""
        return await self._query_log_data(
            TABLE_OPERATION_LOG, parameters, QUERY_TYPE_OP_LOG, time_field="created_at"
        )

    async def get_user_amount_log(
        self, parameters: Dict[str, Any]
    ) -> QueryDataResponse:
        """查询用户资金情况"""
        return await self._query_log_data(
            table_name=TABLE_AMOUNT_LOG,
            parameters=parameters,
            query_type=QUERY_TYPE_AMOUNT_LOG,
            time_field="created_at",
            process_result=None,
            isstrptime=False,
        )

    async def get_user_login_log(self, parameters: Dict[str, Any]) -> QueryDataResponse:
        """查询用户登录日志"""

        def process_device_names(results):
            for result in results:
                device_info = (
                    device_extractor.extract_device_name(result.get("agent", "")) or {}
                )
                result["agent"] = device_info.get("device_name")
            return results

        return await self._query_log_data(
            TABLE_LOGIN_LOG,
            parameters,
            QUERY_TYPE_LOGIN_LOG,
            process_result=process_device_names,
        )

    async def get_user_forword_log(
        self, parameters: Dict[str, Any]
    ) -> QueryDataResponse:
        """查询用户转账情况"""
        return await self._query_log_data(
            TABLE_FORWORD_LOG, parameters, QUERY_TYPE_FORWORD_LOG
        )

    async def get_user_mtlogin(
        self,
        parameters: Dict[str, Any],
        log_query: bool = True,
        is_create_time: bool = False,
    ) -> QueryDataResponse:
        """查询mt交易账号情况"""
        try:
            member_id = await self._get_user_id(parameters)
            sql_generator = SQLGenerator(TABLE_MTLOGIN)

            # 添加关联表查询以获取db_name字段
            sql_generator.add_join(
                "t_mt_server",
                "t_member_mtlogin.mtserver = mt_server.id",
                join_type="LEFT JOIN",
                fields=["db_name"],  # 只选择需要的字段
                table_alias="mt_server",
                database_name="devapi1_mtarde_c",
            )

            if member_id:
                sql_generator.add_condition("member_id", "in", member_id)
            elif TABLE_MTLOGIN != "t_member":
                sql_generator.add_join_table(
                    "t_member",
                    "member_id",
                    "id",
                    join_type="LEFT JOIN",
                    table_alias="user",
                )

            sql, params = sql_generator.generate_sql(
                parameters,
                time_field="create_time" if is_create_time else "",
                isstrptime=True if is_create_time else False,
                order_by=("create_time", "DESC") if is_create_time else None,
            )
            print("========sql======", sql)
            print("=======params=====", params)

            # 使用查询计时器记录SQL执行情况（只有在需要记录时才使用）
            if log_query:
                with QueryTimer(
                    QUERY_TYPE_MTLOGIN,
                    parameters,
                    sql,
                    TABLE_MTLOGIN,
                    sql_params=params,
                ) as timer:
                    self._query_start_time = time.time()
                    results, execution_time = await self._execute_query_with_timing(
                        sql, params
                    )

                    # 记录查询结果
                    timer.log_result(len(results) if results else 0, results)
            else:
                # 不记录查询日志，直接执行查询
                self._query_start_time = time.time()
                results, execution_time = await self._execute_query_with_timing(
                    sql, params
                )

            # 处理结果，添加link_db_name字段
            if results:
                for result in results:
                    # 从关联的mt_server表中获取db_name字段
                    result["link_db_name"] = result.get("mt_server_db_name")

            sql_info = self._build_sql_info(
                sql_generator,
                sql,
                params,
                execution_time,
                len(results) if results else 0,
            )
            query_metadata = self._build_query_metadata(QUERY_TYPE_MTLOGIN)

            # 无论是否有结果，都返回success=True，没有数据时返回空列表
            return QueryDataResponse(
                success=True,
                message="查询成功"
                if results
                else f"未找到{get_query_type_description(QUERY_TYPE_MTLOGIN)}",
                data=results if results else [],
                parameters=parameters,
                sql_info=sql_info,
                query_metadata=query_metadata,
            )
        except Exception as e:
            logger.error(
                f"查询{get_query_type_description(QUERY_TYPE_MTLOGIN)}错误: {str(e)}"
            )

            return QueryDataResponse(
                success=False,
                message=str(e),
                data=None,
                parameters=parameters,
                sql_info=None,
                query_metadata={
                    "query_type": QUERY_TYPE_MTLOGIN,
                    "timestamp": datetime.now().isoformat(),
                },
            )

    async def _get_accessible_member_ids_by_crm(
        self, crm_user_id: int, restrict_to: Optional[List[int]] = None
    ) -> List[int]:
        """根据 t_member_root_path 的 path 层级获取 CRM 可访问的成员ID（含本人）。

        - 先通过 `member_id = crm_user_id` 查出其 `path`
        - 再通过 `path LIKE <path>%` 查出所有下级（包含本人）
        - 如果传入 `restrict_to` 则仅返回其中属于可访问范围的ID

        返回：成员ID列表（int）
        """

        def _to_int_safe(v: Any) -> Optional[int]:
            """将可能带千分位的字符串安全转换为正整数。"""
            if v is None:
                return None
            s = str(v).replace(",", "").strip()
            if not s:
                return None
            try:
                i = int(s)
                return i if i > 0 else None
            except Exception:
                return None

        # 规范化 CRM ID
        crm_id = _to_int_safe(crm_user_id)
        if crm_id is None:
            return []

        # 查询 CRM 本人的路径
        db = self._member_db or "devapi1_mtarde_c"
        path_rows = await base_db.execute_query(
            f"SELECT path FROM {db}.t_member_root_path WHERE member_id = %s LIMIT 1",
            [crm_id],
        )
        root_path = (path_rows[0] or {}).get("path") if path_rows else None
        if not isinstance(root_path, str) or not root_path:
            # 未找到路径，返回空
            return []

        # 基础条件与参数
        where_clause = "member_id = %s OR path LIKE %s"
        base_params: List[Any] = [root_path, f"{root_path},%"]

        # 查询所有下级（包含本人）；如 restrict_to 提供则限定在该集合内
        if restrict_to:
            # 过滤、去重并排序 restrict_to 中的有效整数ID
            target_ids = sorted(
                {i for i in (_to_int_safe(uid) for uid in restrict_to) if i is not None}
            )
            if not target_ids:
                return []

            placeholders = ", ".join(["%s"] * len(target_ids))
            sql = (
                f"SELECT member_id FROM {db}.t_member_root_path "
                f"WHERE ({where_clause}) AND member_id IN ({placeholders})"
            )
            params: List[Any] = base_params + target_ids
        else:
            sql = f"SELECT member_id FROM {db}.t_member_root_path WHERE " + where_clause
            params = base_params

        rows = await base_db.execute_query(sql, params)

        # 提取有效 member_id
        ids: List[int] = []
        for row in rows or []:
            mid = _to_int_safe(row.get("member_id"))
            if mid is not None:
                ids.append(mid)
        return ids

    async def _get_crm_access_scope(self, crm_user_id: int) -> Dict[str, Any]:
        """根据crm_user_id获取访问范围信息。

        规则：
        - admin(管理员)：由`t_member.admin`标识，值为1时拥有全部访问权限
        - staff(员工)：允许查询其层级范围（通过`t_member_root_path`）
        - agent(代理商)/direct(直接客户)：仅允许查询自身

        返回字段：
        - exists: CRM用户是否存在
        - is_admin: 是否管理员（来源于`t_member.admin`）
        - user_type: 用户类型字符串（仅可能为agent/direct/staff，其他视为unknown）
        - accessible_member_ids: 允许访问的成员ID列表（admin为None）
        - crm_member_id: CRM用户自身ID
        """
        # 读取t_member的角色与类型（admin为数值标识，userType仅为agent/direct/staff）
        rows: List[Dict[str, Any]] = []
        db = self._member_db or "devapi1_mtarde_c"
        rows = await base_db.execute_query(
            f"SELECT id, userType, admin FROM {db}.t_member WHERE id = %s LIMIT 1",
            [crm_user_id],
        )

        if not rows:
            return {"exists": False}

        info = rows[0] or {}
        crm_id_raw = info.get("id")
        try:
            crm_id = int(str(crm_id_raw))
        except Exception:
            return {"exists": False}

        # 仅以admin列判断管理员身份
        raw_user_type = (info.get("userType") or "").strip().lower()
        # 规范化user_type，仅接受agent/direct/staff，其它归为unknown
        user_type = (
            raw_user_type
            if raw_user_type in {"agent", "direct", "staff"}
            else "unknown"
        )

        is_admin_val = info.get("admin")
        is_admin = False
        try:
            if is_admin_val is not None:
                is_admin = bool(int(str(is_admin_val).strip()))
        except Exception:
            is_admin = False

        if is_admin:
            return {
                "exists": True,
                "is_admin": True,
                "user_type": user_type,
                "accessible_member_ids": None,
                "crm_member_id": crm_id,
            }

        # 非admin分支
        if user_type == "staff":
            ids = await self._get_accessible_member_ids_by_crm(crm_id)
            return {
                "exists": True,
                "is_admin": False,
                "user_type": "staff",
                "accessible_member_ids": ids,
                "crm_member_id": crm_id,
            }
        elif user_type == "agent":
            return {
                "exists": True,
                "is_admin": False,
                "user_type": "agent",
                "accessible_member_ids": [crm_id],
                "crm_member_id": crm_id,
            }
        elif user_type == "direct":
            return {
                "exists": True,
                "is_admin": False,
                "user_type": "direct",
                "accessible_member_ids": [crm_id],
                "crm_member_id": crm_id,
            }
        # 未知类型：最小权限，默认仅自身
        return {
            "exists": True,
            "is_admin": False,
            "user_type": user_type,
            "accessible_member_ids": [crm_id],
            "crm_member_id": crm_id,
        }

    async def _get_user_id(self, parameters: Dict[str, Any]) -> Any:
        """获取用户ID

        优先从参数中获取user_id，如果没有则通过用户名查询获取

        参数:
            parameters: 查询参数

        返回:
            用户ID

        异常:
            Exception: 当找不到用户时抛出异常
        """
        # 统一使用 user_id 参数
        user_id = parameters.get("user_id")

        if user_id is not None:
            crm_user_id = parameters.get("crm_user_id")
            scope: Dict[str, Any] = {}
            if crm_user_id is not None and str(crm_user_id).strip():
                try:
                    scope = await self._get_crm_access_scope(int(crm_user_id))
                except Exception:
                    # 授权校验失败时默认拒绝，避免放行
                    raise Exception("crm_user_id参数无效")
            else:
                # 严格要求提供crm_user_id
                raise Exception("缺少crm_user_id参数")

            # 单个ID
            if isinstance(user_id, (str, int)) and str(user_id).strip():
                user_id_int = int(user_id)
                if user_id_int > 0:
                    if scope.get("exists"):
                        if scope.get("is_admin"):
                            return [user_id_int]
                        utype = (scope.get("user_type") or "").lower()
                        crm_mid = scope.get("crm_member_id")
                        if utype == "staff":
                            accessible_ids = scope.get("accessible_member_ids") or []
                            if user_id_int not in accessible_ids:
                                raise Exception(f"您没有用户 {user_id_int} 的数据查询权限")
                            return [user_id_int]
                        else:
                            # agent/direct/unknown：仅自身
                            if crm_mid is None or user_id_int != crm_mid:
                                raise Exception("您仅可查询自身数据")
                            return [user_id_int]
                    # 未通过exists校验（不应发生），默认拒绝
                    raise Exception("crm用户不存在或不可用")
            # 多个ID
            elif isinstance(user_id, list) and len(user_id) > 0:
                if scope.get("exists"):
                    if scope.get("is_admin"):
                        return user_id
                    utype = (scope.get("user_type") or "").lower()
                    crm_mid = scope.get("crm_member_id")
                    # 过滤出有效的待校验ID
                    check_ids: List[int] = []
                    for uid in user_id:
                        try:
                            uid_int = int(uid)
                            if uid_int > 0:
                                check_ids.append(uid_int)
                        except Exception:
                            continue

                    if utype == "staff":
                        if check_ids:
                            accessible_ids = (
                                await self._get_accessible_member_ids_by_crm(
                                    crm_mid, restrict_to=check_ids
                                )
                            )
                            # 若存在越权id，则拒绝
                            if len(accessible_ids) != len(check_ids):
                                unauthorized_ids = [
                                    uid
                                    for uid in check_ids
                                    if uid not in accessible_ids
                                ]
                                raise Exception(
                                    f"您没有用户 {', '.join(map(str, unauthorized_ids))} 的数据查询权限"
                                )
                        return user_id
                    else:
                        # agent/direct/unknown：仅允许全为自身id
                        if not check_ids or any(cid != crm_mid for cid in check_ids):
                            raise Exception("您仅可查询自身数据")
                        return user_id
                # 未通过exists校验（不应发生），默认拒绝
                raise Exception("crm用户不存在或不可用")
        # return []
        check_user_params = self.check_user_params(parameters)
        if check_user_params:
            # 对于 user_name 数组查询，需要特殊处理权限检查
            if parameters.get("user_name") and isinstance(
                parameters.get("user_name"), list
            ):
                crm_user_id = parameters.get("crm_user_id")
                if crm_user_id is not None and str(crm_user_id).strip():
                    try:
                        scope = await self._get_crm_access_scope(int(crm_user_id))
                        if scope.get("exists") and not scope.get("is_admin"):
                            # 先查询所有匹配的用户（不限制权限）
                            temp_params = parameters.copy()
                            temp_params.pop("crm_user_id", None)
                            temp_user_info = await self.get_user(temp_params)

                            if temp_user_info.success and temp_user_info.data:
                                all_users = (
                                    temp_user_info.data
                                    if isinstance(temp_user_info.data, list)
                                    else [temp_user_info.data]
                                )
                                accessible_ids = (
                                    scope.get("accessible_member_ids") or []
                                )

                                # 分离有权限和无权限的用户
                                authorized_users = [
                                    user
                                    for user in all_users
                                    if user.get("id") in accessible_ids
                                ]
                                unauthorized_users = [
                                    user
                                    for user in all_users
                                    if user.get("id") not in accessible_ids
                                ]

                                if unauthorized_users:
                                    # 获取无权限的用户信息（包含ID和昵称）
                                    unauthorized_info = []
                                    for user in unauthorized_users:
                                        nickname = user.get("nickname")
                                        user_id = user.get("id")
                                        if nickname and user_id:
                                            unauthorized_info.append(
                                                f"{nickname}(ID:{user_id})"
                                            )
                                        elif nickname:
                                            unauthorized_info.append(nickname)
                                    raise Exception(
                                        f"您没有查询用户 {', '.join(unauthorized_info)} 的权限"
                                    )

                                return (
                                    [user.get("id") for user in authorized_users]
                                    if authorized_users
                                    else []
                                )
                            else:
                                raise Exception("未找到用户")
                    except Exception as e:
                        raise e

            # 其他情况使用原有逻辑
            user_info = await self.get_user(parameters)
            if not user_info.success or not user_info.data:
                # 检查是否因为权限限制导致查询结果为空
                crm_user_id = parameters.get("crm_user_id")
                if crm_user_id is not None and str(crm_user_id).strip():
                    try:
                        scope = await self._get_crm_access_scope(int(crm_user_id))
                        if scope.get("exists") and not scope.get("is_admin"):
                            # 检查是否有明确的用户名查询但无权限
                            if parameters.get("user_name") or parameters.get(
                                "username"
                            ):
                                # 先查询所有匹配的用户（不限制权限）来获取用户名
                                temp_params = parameters.copy()
                                temp_params.pop("crm_user_id", None)
                                temp_user_info = await self.get_user(temp_params)

                                if temp_user_info.success and temp_user_info.data:
                                    # 获取查询到的用户信息（包含ID和昵称）
                                    all_users = (
                                        temp_user_info.data
                                        if isinstance(temp_user_info.data, list)
                                        else [temp_user_info.data]
                                    )
                                    unauthorized_info = []
                                    for user in all_users:
                                        nickname = user.get("nickname")
                                        user_id = user.get("id")
                                        if nickname and user_id:
                                            unauthorized_info.append(
                                                f"{nickname}(ID:{user_id})"
                                            )
                                        elif nickname:
                                            unauthorized_info.append(nickname)

                                    if unauthorized_info:
                                        raise Exception(
                                            f"您没有查询用户 {', '.join(unauthorized_info)} 的权限"
                                        )
                                raise Exception("您没有查询该用户的权限")
                    except Exception as e:
                        raise e
                raise Exception("未找到用户")

            if isinstance(user_info.data, list) and len(user_info.data) > 0:
                return [user.get("id") for user in user_info.data]
            elif isinstance(user_info.data, dict):
                return user_info.data.get("id")

            raise Exception("无法获取用户ID")

    def check_user_params(self, parameters: Dict[str, Any]) -> bool:
        """检查用户参数"""
        user_params = [
            "username",
            "userid",
            "user_name",
            "user_id",
            "user_data",
            "user_type",
            "country",
            "email",
            "register_time",
            "kyc",
        ]
        for param in user_params:
            if param in parameters:
                return True
        return False


warehouse_user_service = WarehouseUserService()
