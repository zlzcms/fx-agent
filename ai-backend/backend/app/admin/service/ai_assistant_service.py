# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-01-XX 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 19:53:44
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.admin.crud.crud_ai_assistant import (
    crud_ai_assistant,
    crud_ai_data_permission,
    crud_ai_notification_method,
)
from backend.app.admin.crud.crud_ai_assistant_relations import crud_ai_assistant_template
from backend.app.admin.crud.crud_ai_model import crud_ai_model
from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model.ai_assistant import (
    AIAssistant,
    AIAssistantNotification,
    AIAssistantPermission,
    AIAssistantTemplate,
)
from backend.app.admin.model.ai_training_log import AITrainingLog
from backend.app.admin.schema.ai_assistant import (
    AIAssistantCreate,
    AIAssistantQueryParams,
    AIAssistantUpdate,
    AIDataPermissionCreate,
    AIDataPermissionInDB,
    AINotificationMethodCreate,
    AINotificationMethodInDB,
)
from backend.app.admin.schema.user import GetUserInfoDetail
from backend.common.exception.errors import ForbiddenError, NotFoundError
from backend.common.pagination import PageData


class AIAssistantService:
    """AI助手服务"""

    @staticmethod
    async def _convert_to_response_model(db: AsyncSession, db_obj) -> Dict[str, Any]:
        """将数据库对象转换为响应模型"""
        from backend.app.admin.crud.crud_assistant_type import crud_assistant_type

        if not db_obj:
            return None

        # 获取关联数据的详细信息
        try:
            # 获取负责人员的详细信息 - 从sys_user表获取
            responsible_persons = []
            if hasattr(db_obj, "personnel_relations"):
                for rel in db_obj.personnel_relations:
                    # 从sys_user表获取用户详细信息
                    user = await user_dao.get(db, user_id=rel.personnel_id)
                    if user:
                        responsible_persons.append(
                            {
                                "personnel_id": user.id,
                                "username": user.username,
                                "email": user.email,
                                "nickname": getattr(user, "nickname", ""),
                                "phone": getattr(user, "phone", ""),
                            }
                        )
            else:
                responsible_persons = db_obj.responsible_persons if hasattr(db_obj, "responsible_persons") else []
        except Exception:
            responsible_persons = []

        try:
            # 获取通知方式的详细信息
            notification_methods = []
            if hasattr(db_obj, "notification_relations"):
                for rel in db_obj.notification_relations:
                    if hasattr(rel, "notification_method") and rel.notification_method:
                        notification_methods.append(
                            {
                                "id": rel.notification_method.id,
                                "name": rel.notification_method.name,
                                "type": rel.notification_method.type,
                            }
                        )
            else:
                notification_methods = db_obj.notification_methods if hasattr(db_obj, "notification_methods") else []
        except Exception:
            notification_methods = []

        try:
            # 获取数据源的详细信息 - 现在只从settings字段获取
            data_sources = db_obj.data_sources if hasattr(db_obj, "data_sources") else []
        except Exception:
            data_sources = []

        try:
            # 获取数据权限的详细信息 - 现在直接使用字段值
            data_permissions = db_obj.data_permissions if hasattr(db_obj, "data_permissions") else None
        except Exception:
            data_permissions = None

        # 数据范围限制配置已移除

        # 获取助手类型显示名称
        assistant_type_display = db_obj.assistant_type_id
        try:
            assistant_type = await crud_assistant_type.get(db, id=db_obj.assistant_type_id)
            if assistant_type:
                assistant_type_display = assistant_type.name
        except Exception as e:
            print(f"获取助手类型失败: {e}")
            assistant_type_display = db_obj.assistant_type_id

        # 获取AI模型名称显示
        ai_model_name = db_obj.ai_model_id
        try:
            # 如果ai_model_id是UUID格式，则查询模型名称
            if db_obj.ai_model_id and len(db_obj.ai_model_id) > 10:  # 简单判断是否为UUID
                model = await crud_ai_model.get(db, id=db_obj.ai_model_id)
                if model:
                    ai_model_name = model.name
                else:
                    ai_model_name = db_obj.ai_model_id
            else:
                ai_model_name = db_obj.ai_model_id
        except Exception as e:
            print(f"获取AI模型名称失败: {e}")
            ai_model_name = db_obj.ai_model_id

        # 获取模板信息
        template_is_open = None
        try:
            if hasattr(db_obj, "template_relation") and db_obj.template_relation:
                template_is_open = db_obj.template_relation.is_open
        except Exception:
            template_is_open = None

        # 构建响应数据 - 只包含可序列化的基本字段，排除SQLAlchemy关联对象
        excluded_fields = {
            "responsible_persons",
            "notification_methods",
            "data_sources",
            "data_permissions",
            "personnel_relations",
            "notification_relations",
            "data_source_relations",
            "template_relation",
        }

        response_data = {
            **{
                k: v
                for k, v in db_obj.__dict__.items()
                if not k.startswith("_")
                and k not in excluded_fields
                and not hasattr(v, "__table__")  # 排除SQLAlchemy模型对象
            },
            # 覆盖需要特殊处理的字段
            "responsible_persons": responsible_persons,
            "notification_methods": notification_methods,
            "data_sources": data_sources,
            "data_permissions": data_permissions,
            # 添加关联表的显示名称
            "assistant_type_display": assistant_type_display,
            "ai_model_name": ai_model_name,
            "template_is_open": template_is_open,
        }

        # 解析output_data字段，将JSON字符串转换为字典对象
        if "output_data" in response_data and response_data["output_data"]:
            try:
                # 尝试解析JSON字符串
                import json

                output_data_str = response_data["output_data"]

                # 已经是字典类型则不处理
                if isinstance(output_data_str, dict):
                    pass
                # 字符串类型则尝试解析为字典
                elif isinstance(output_data_str, str):
                    try:
                        parsed_data = json.loads(output_data_str)

                        # 确保解析出的是字典，并进一步解析table字段
                        if isinstance(parsed_data, dict):
                            # 如果table字段是JSON字符串，也需要解析
                            if "table" in parsed_data and isinstance(parsed_data["table"], str):
                                try:
                                    parsed_data["table"] = json.loads(parsed_data["table"])
                                except Exception as table_error:
                                    print(f"解析table字段失败: {table_error}")

                            response_data["output_data"] = parsed_data
                    except json.JSONDecodeError:
                        # 如果不是有效的JSON字符串，保留原始字符串
                        print(f"output_data不是有效的JSON字符串: {output_data_str[:100]}...")
                else:
                    print(f"output_data类型不支持解析: {type(output_data_str)}")
            except Exception as e:
                print(f"解析output_data字段失败: {e}")

        # 处理旧格式的table_output_data和document_output_data字段
        # 如果output_data不存在或为空，但存在旧格式字段，则构建新格式的output_data
        if not response_data.get("output_data") and (
            "table_output_data" in response_data or "document_output_data" in response_data
        ):
            try:
                import json

                new_output_data = {}

                # 处理table_output_data
                if "table_output_data" in response_data and response_data["table_output_data"]:
                    try:
                        table_data = response_data["table_output_data"]
                        if isinstance(table_data, str):
                            table_data = json.loads(table_data)
                        new_output_data["table"] = table_data
                    except Exception as e:
                        print(f"解析旧格式table_output_data失败: {e}")
                        new_output_data["table"] = response_data.get("table_output_data", [])

                # 处理document_output_data
                if "document_output_data" in response_data and response_data["document_output_data"]:
                    new_output_data["document"] = response_data["document_output_data"]

                # 添加其他默认字段
                new_output_data["include_charts"] = response_data.get("include_charts", False)
                new_output_data["auto_export"] = response_data.get("auto_export", False)
                new_output_data["export_formats"] = response_data.get("export_formats", [])

                # 更新response_data
                if new_output_data:
                    response_data["output_data"] = new_output_data
            except Exception as e:
                print(f"构建新格式output_data失败: {e}")

        return response_data

    @staticmethod
    async def get_ai_assistant_list(
        db: AsyncSession, *, params: Optional[AIAssistantQueryParams] = None, page: int = 1, size: int = 10
    ) -> PageData[Dict[str, Any]]:
        """获取AI助手列表"""
        skip = (page - 1) * size

        # 获取列表和总数
        items = await crud_ai_assistant.get_list(db, params=params, skip=skip, limit=size)
        total = await crud_ai_assistant.get_count(db, params=params)

        # 转换为响应格式
        records = []
        for item in items:
            record = await AIAssistantService._convert_to_response_model(db, item)
            records.append(record)

        # 计算分页信息
        from math import ceil

        total_pages = ceil(total / size) if total > 0 else 1

        # 返回PageData格式，参考数据源服务的实现
        result = PageData(
            items=records,
            total=total,
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

        return result

    @staticmethod
    async def get_all_ai_assistants(db: AsyncSession, *, status: Optional[bool] = None) -> List[Dict[str, Any]]:
        """获取所有AI助手（不分页）"""
        params = AIAssistantQueryParams(status=status) if status is not None else None
        items = await crud_ai_assistant.get_list(db, params=params, skip=0, limit=1000)

        records = []
        for item in items:
            record = await AIAssistantService._convert_to_response_model(db, item)
            records.append(record)
        return records

    @staticmethod
    async def get_ai_assistant(db: AsyncSession, *, id: str, status: Optional[bool] = None) -> Dict[str, Any]:
        """获取AI助手详情"""
        params = AIAssistantQueryParams(status=status) if status is not None else None
        db_obj = await crud_ai_assistant.get(db, id=id, params=params)
        if not db_obj:
            raise NotFoundError(msg=f"AI助手 {id} 不存在")

        result = await AIAssistantService._convert_to_response_model(db, db_obj)
        if not result:
            raise NotFoundError(msg=f"AI助手 {id} 数据转换失败")

        return result

    @staticmethod
    async def get_ai_assistant_by_name(db: AsyncSession, *, name: str, status: Optional[bool] = None) -> Dict[str, Any]:
        """通过名称获取AI助手详情

        Args:
            db: 数据库会话
            name: AI助手名称
            status: 可选的状态过滤

        Returns:
            AI助手详情

        Raises:
            NotFoundError: 如果找不到指定名称的AI助手
        """
        params = AIAssistantQueryParams(status=status) if status is not None else None
        db_obj = await crud_ai_assistant.get_by_name(db, name=name)
        print("db_obj======================", db_obj)
        if not db_obj:
            raise NotFoundError(msg=f"AI助手 '{name}' 不存在")

        # 如果指定了状态过滤，检查状态是否匹配
        if params and params.status is not None and db_obj.status != params.status:
            raise NotFoundError(msg=f"AI助手 '{name}' 状态不匹配")

        return await AIAssistantService._convert_to_response_model(db, db_obj)

    @staticmethod
    async def create_ai_assistant(db: AsyncSession, *, obj_in: AIAssistantCreate) -> Dict[str, Any]:
        """创建AI助手"""
        # 检查名称是否已存在
        existing = await crud_ai_assistant.get_by_name(db, name=obj_in.name)
        if existing:
            raise ForbiddenError(msg=f"助手名称 '{obj_in.name}' 已存在")

        # 验证相关数据是否存在
        await AIAssistantService._validate_related_data(db, obj_in)

        # 处理output_data字段
        obj_in_dict = obj_in.model_dump()
        obj_in_dict = AIAssistantService._process_output_data(obj_in_dict)

        # 处理data_permission_values字段，将数字转为字符串
        if obj_in_dict.get("data_permission_values"):
            obj_in_dict["data_permission_values"] = [str(value) for value in obj_in_dict["data_permission_values"]]

        # 创建一个新的Pydantic对象
        from backend.app.admin.schema.ai_assistant import AIAssistantCreate

        obj_in = AIAssistantCreate(**obj_in_dict)

        db_obj = await crud_ai_assistant.create(db, obj_in=obj_in)
        return await AIAssistantService._convert_to_response_model(db, db_obj)

    @staticmethod
    async def update_ai_assistant(db: AsyncSession, *, id: str, obj_in: AIAssistantUpdate) -> Dict[str, Any]:
        """更新AI助手"""
        db_obj = await crud_ai_assistant.get(db, id=id)
        if not db_obj:
            raise NotFoundError(msg=f"AI助手 {id} 不存在")

        # 如果更新名称，检查是否已存在
        if obj_in.name and obj_in.name != db_obj.name:
            existing = await crud_ai_assistant.get_by_name(db, name=obj_in.name)
            if existing:
                raise ForbiddenError(msg=f"助手名称 '{obj_in.name}' 已存在")

        # 验证相关数据是否存在
        await AIAssistantService._validate_related_data(db, obj_in)

        # 处理output_data字段
        obj_in_dict = obj_in.model_dump(exclude_unset=True)
        obj_in_dict = AIAssistantService._process_output_data(obj_in_dict)

        # 处理data_permission_values字段，将数字转为字符串
        if "data_permission_values" in obj_in_dict and obj_in_dict["data_permission_values"]:
            obj_in_dict["data_permission_values"] = [str(value) for value in obj_in_dict["data_permission_values"]]

        # 创建一个新的Pydantic对象
        from backend.app.admin.schema.ai_assistant import AIAssistantUpdate

        obj_in = AIAssistantUpdate(**obj_in_dict)

        updated_obj = await crud_ai_assistant.update(db, db_obj=db_obj, obj_in=obj_in)
        return await AIAssistantService._convert_to_response_model(db, updated_obj)

    @staticmethod
    async def delete_ai_assistant(db: AsyncSession, *, ids: List[str]) -> Dict[str, Any]:
        """删除AI助手"""
        deleted_count = await crud_ai_assistant.delete_batch(db, ids=ids)
        return {"deleted_count": deleted_count, "message": f"成功删除 {deleted_count} 个AI助手"}

    @staticmethod
    async def toggle_ai_assistant_status(db: AsyncSession, *, id: str, status: bool) -> Dict[str, Any]:
        """切换AI助手状态"""
        db_obj = await crud_ai_assistant.toggle_status(db, id=id, status=status)
        if not db_obj:
            raise NotFoundError(msg=f"AI助手 {id} 不存在")

        return await AIAssistantService._convert_to_response_model(db, db_obj)

    @staticmethod
    async def clone_ai_assistant(db: AsyncSession, *, id: str, new_name: str) -> Dict[str, Any]:
        """克隆AI助手"""
        try:
            cloned_obj = await crud_ai_assistant.clone(db, id=id, new_name=new_name)
            if not cloned_obj:
                raise NotFoundError(msg=f"AI助手 {id} 不存在")

            return await AIAssistantService._convert_to_response_model(db, cloned_obj)
        except ValueError as e:
            raise ForbiddenError(msg=str(e))

    @staticmethod
    async def toggle_ai_assistant_template_status(db: AsyncSession, *, id: str, is_open: bool) -> Dict[str, Any]:
        """切换AI助手模板开启状态"""
        # 检查AI助手是否存在
        db_obj = await crud_ai_assistant.get(db, id=id)
        if not db_obj:
            raise NotFoundError(msg=f"AI助手 {id} 不存在")

        # 检查是否为模板
        if not db_obj.is_template:
            raise ForbiddenError(msg=f"AI助手 {id} 不是模板，无法切换模板状态")

        # 切换模板状态
        template_obj = await crud_ai_assistant_template.toggle_template_status(db, assistant_id=id, is_open=is_open)

        if not template_obj:
            raise NotFoundError(msg=f"AI助手模板 {id} 不存在")

        # 提交事务
        await db.commit()
        await db.refresh(db_obj)

        return await AIAssistantService._convert_to_response_model(db, db_obj)

    @staticmethod
    async def get_ai_assistant_template_list(
        db: AsyncSession, *, page: int = 1, size: int = 10
    ) -> PageData[Dict[str, Any]]:
        """获取AI助手模板列表"""
        skip = (page - 1) * size

        # 构建查询语句，关联模板表和助手表
        stmt = (
            select(AIAssistant)
            .join(AIAssistantTemplate, AIAssistant.id == AIAssistantTemplate.assistant_id)
            .options(
                selectinload(AIAssistant.notification_relations).selectinload(
                    AIAssistantNotification.notification_method
                ),
                selectinload(AIAssistant.permission_relations).selectinload(AIAssistantPermission.permission),
                selectinload(AIAssistant.template_relation),
            )
            .offset(skip)
            .limit(size)
        )

        result = await db.execute(stmt)
        items = result.scalars().all()

        # 获取总数
        count_stmt = select(func.count(AIAssistant.id)).join(
            AIAssistantTemplate, AIAssistant.id == AIAssistantTemplate.assistant_id
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # 转换为响应格式
        records = []
        for item in items:
            record = await AIAssistantService._convert_to_response_model(db, item)
            records.append(record)

        # 计算分页信息
        from math import ceil

        total_pages = ceil(total / size) if total > 0 else 1

        # 返回PageData格式
        result = PageData(
            items=records,
            total=total,
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

        return result

    @staticmethod
    async def get_ai_assistant_types(db: AsyncSession) -> List[Dict[str, str]]:
        """获取AI助手类型列表"""
        # 这里可以从数据库或配置文件中获取
        return [
            {"value": "data_analyst", "label": "数据分析师"},
            {"value": "report_generator", "label": "报告生成器"},
            {"value": "dashboard_creator", "label": "仪表板创建者"},
            {"value": "alert_monitor", "label": "告警监控"},
            {"value": "custom", "label": "自定义"},
        ]

    @staticmethod
    async def _validate_related_data(db: AsyncSession, obj_in) -> None:
        """验证相关数据是否存在"""
        # 验证通知方式是否存在
        if hasattr(obj_in, "notification_methods") and obj_in.notification_methods:
            for method_id in obj_in.notification_methods:
                method = await crud_ai_notification_method.get(db, id=method_id)
                if not method:
                    raise NotFoundError(msg=f"通知方式 {method_id} 不存在")

        # 验证负责人员是否存在 - 从sys_user表验证
        if hasattr(obj_in, "responsible_persons") and obj_in.responsible_persons:
            for person_data in obj_in.responsible_persons:
                # 从PersonnelData对象中提取personnel_id
                person_id = person_data.personnel_id if hasattr(person_data, "personnel_id") else person_data
                user = await user_dao.get(db, user_id=int(person_id))
                if not user:
                    raise NotFoundError(msg=f"用户 {person_id} 不存在")

        # 验证数据权限是否存在 - 处理单个权限而不是列表
        if hasattr(obj_in, "data_permissions") and obj_in.data_permissions and obj_in.data_permissions.strip():
            permission_id = obj_in.data_permissions.strip()
            permission = await crud_ai_data_permission.get(db, id=permission_id)
            if not permission:
                raise NotFoundError(msg=f"数据权限 {permission_id} 不存在")

    @staticmethod
    def _process_output_data(obj_dict: Dict[str, Any]) -> Dict[str, Any]:
        """处理output_data字段，将复杂结构转换为JSON字符串"""
        if "output_data" not in obj_dict or not obj_dict["output_data"]:
            return obj_dict

        import json

        output_data = obj_dict["output_data"]

        # 如果已经是字符串，检查是否是有效的JSON
        if isinstance(output_data, str):
            try:
                # 尝试解析以确保是有效的JSON
                json.loads(output_data)
                # 已经是有效的JSON字符串，无需处理
                return obj_dict
            except json.JSONDecodeError:
                # 不是有效的JSON字符串，直接保存
                return obj_dict

        # 如果是字典，需要处理嵌套结构
        if isinstance(output_data, dict):
            # 处理table字段，确保是字符串格式
            if "table" in output_data and not isinstance(output_data["table"], str):
                try:
                    output_data["table"] = json.dumps(output_data["table"])
                except Exception as e:
                    print(f"转换table字段为JSON字符串失败: {e}")

            # 将整个output_data转换为JSON字符串
            try:
                obj_dict["output_data"] = json.dumps(output_data)
            except Exception as e:
                print(f"转换output_data为JSON字符串失败: {e}")
                # 如果转换失败，清空该字段以避免保存无效数据
                obj_dict["output_data"] = ""

        return obj_dict

    @staticmethod
    def generate_cron_expression(assistant: AIAssistant) -> str:
        """
        根据助手的执行频率配置生成Celery可用的cron表达式

        Args:
            assistant: AI助手对象

        Returns:
            cron表达式，格式为 "minute hour day_of_month month day_of_week"
        """
        frequency = assistant.execution_frequency

        if frequency == "minutes":
            # 每隔X分钟执行一次
            minutes = assistant.execution_minutes or 30
            if minutes < 5:
                minutes = 5

            # 对于分钟级别的任务，返回特殊的格式，表示每隔X分钟执行一次
            return f"*/{minutes} * * * *"

        elif frequency == "hours":
            # 每隔X小时执行一次
            hours = assistant.execution_hours or 2
            if hours < 1:
                hours = 1

            # 整点执行，分钟为0
            return f"0 */{hours} * * *"

        elif frequency == "daily":
            # 每天在指定时间执行
            exec_time = assistant.execution_time or "09:00"
            hour, minute = map(int, exec_time.split(":"))

            return f"{minute} {hour} * * *"

        elif frequency == "weekly":
            # 每周在指定的星期几和时间执行
            weekday = assistant.execution_weekday or "1"  # 默认周一
            exec_time = assistant.execution_weekly_time or "19:00"
            hour, minute = map(int, exec_time.split(":"))

            return f"{minute} {hour} * * {weekday}"

        elif frequency == "monthly":
            # 每月在指定的日期和时间执行
            day = assistant.execution_day or "1"  # 默认每月1日
            exec_time = assistant.execution_monthly_time or "19:00"
            hour, minute = map(int, exec_time.split(":"))

            return f"{minute} {hour} {day} * *"

        else:
            # 默认每天凌晨2点执行
            return "0 2 * * *"

    @staticmethod
    async def get_assistant_training_logs(
        db: AsyncSession, *, assistant_id: str, log_type: Optional[str] = None, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """获取AI助手训练日志"""
        skip = (page - 1) * size

        # 构建查询条件
        stmt = (
            select(AITrainingLog)
            .where(
                AITrainingLog.assistant_id == assistant_id if assistant_id and assistant_id != "undefined" else True,
                AITrainingLog.log_type == log_type,
            )
            .order_by(AITrainingLog.created_time.desc())
        )

        # 执行查询并添加分页
        paginated_stmt = stmt.offset(skip).limit(size)
        result = await db.execute(paginated_stmt)
        logs = result.scalars().all()

        # 获取总数
        count_stmt = select(func.count(AITrainingLog.id)).where(
            AITrainingLog.assistant_id == assistant_id if assistant_id and assistant_id != "undefined" else True,
            AITrainingLog.log_type == log_type,
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # 格式化结果
        records = []
        for log in logs:
            # 处理时间字段，确保返回有效的ISO格式字符串
            created_time_str = ""
            updated_time_str = ""

            if log.created_time:
                if isinstance(log.created_time, datetime):
                    created_time_str = log.created_time.isoformat()
                elif isinstance(log.created_time, str):
                    created_time_str = log.created_time

            if log.updated_time:
                if isinstance(log.updated_time, datetime):
                    updated_time_str = log.updated_time.isoformat()
                elif isinstance(log.updated_time, str):
                    updated_time_str = log.updated_time

            # 处理数据字段，如果是JSON字符串，尝试解析为对象
            data_content = log.data
            try:
                if isinstance(log.data, str) and log.data.strip().startswith("{"):
                    import json

                    data_content = json.loads(log.data)
            except Exception:
                data_content = log.data

            # 处理AI响应字段，如果是JSON字符串，尝试解析为对象
            ai_response_content = log.ai_response
            try:
                if isinstance(log.ai_response, str) and log.ai_response.strip().startswith("{"):
                    import json

                    ai_response_content = json.loads(log.ai_response)
            except Exception:
                ai_response_content = log.ai_response

            record = {
                "id": log.id,
                "model_id": log.model_id,
                "model_name": log.model_name,
                "log_type": log.log_type,
                "prompt_template": log.prompt_template,
                "base_info": log.base_info,
                "data": data_content,
                "assistant_id": log.assistant_id,
                "success": log.success,
                "score": log.score,
                "content": log.content,
                "ai_response": ai_response_content,
                "created_time": created_time_str,
                "updated_time": updated_time_str,
            }
            records.append(record)

        # 计算总页数
        from math import ceil

        total_pages = ceil(total / size) if total > 0 else 1

        # 返回分页结果
        return {
            "items": records,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "links": {
                "first": f"?page=1&size={size}",
                "last": f"?page={total_pages}&size={size}",
                "self": f"?page={page}&size={size}",
                "next": f"?page={page + 1}&size={size}" if page < total_pages else None,
                "prev": f"?page={page - 1}&size={size}" if page > 1 else None,
            },
        }


# 人员相关服务函数 - 从 sys_user 表获取数据
async def get_all_personnel(db: AsyncSession, *, status: Optional[bool] = None) -> List[GetUserInfoDetail]:
    """获取所有人员（从sys_user表获取）"""
    try:
        # 从sys_user表获取用户列表
        users = await user_dao.get_all(db)
        result = []
        for user in users:
            # 将SQLAlchemy对象转换为GetUserInfoDetail格式
            user_dict = {
                "id": user.id,
                "uuid": user.uuid,
                "dept_id": getattr(user, "dept_id", None),
                "username": user.username,
                "nickname": getattr(user, "nickname", ""),
                "email": getattr(user, "email", None),
                "phone": getattr(user, "phone", None),
                "avatar": getattr(user, "avatar", None),
                "status": user.status,
                "is_superuser": getattr(user, "is_superuser", False),
                "is_staff": getattr(user, "is_staff", False),
                "is_multi_login": getattr(user, "is_multi_login", False),
                "join_time": getattr(user, "join_time", user.created_time),
                "last_login_time": getattr(user, "last_login_time", None),
            }
            result.append(GetUserInfoDetail(**user_dict))
        return result
    except Exception as e:
        # 如果表不存在或没有数据，返回空列表
        print(f"获取用户列表失败: {e}")
        return []


class AINotificationMethodService:
    """AI通知方式服务"""

    @staticmethod
    async def get_notification_methods(db: AsyncSession) -> List[AINotificationMethodInDB]:
        """获取通知方式列表"""
        try:
            items = await crud_ai_notification_method.get_list(db, status=True, skip=0, limit=100)
            result = []
            for item in items:
                # 将SQLAlchemy对象转换为字典
                item_dict = {
                    "id": item.id,
                    "name": item.name,
                    "type": item.type,
                    "config": item.config,
                    "status": item.status,
                    "created_time": item.created_time,
                    "updated_time": item.updated_time,
                }
                result.append(AINotificationMethodInDB(**item_dict))
            return result
        except Exception as e:
            # 如果表不存在或没有数据，返回空列表
            print(f"获取通知方式列表失败: {e}")
            return []

    @staticmethod
    async def create_notification_method(
        db: AsyncSession, *, obj_in: AINotificationMethodCreate
    ) -> AINotificationMethodInDB:
        """创建通知方式"""
        db_obj = await crud_ai_notification_method.create(db, obj_in=obj_in)
        item_dict = {
            "id": db_obj.id,
            "name": db_obj.name,
            "type": db_obj.type,
            "config": db_obj.config,
            "status": db_obj.status,
            "created_time": db_obj.created_time,
            "updated_time": db_obj.updated_time,
        }
        return AINotificationMethodInDB(**item_dict)


class AIDataPermissionService:
    """AI数据权限服务"""

    @staticmethod
    async def get_data_permissions(db: AsyncSession) -> List[AIDataPermissionInDB]:
        """获取数据权限列表"""
        try:
            items = await crud_ai_data_permission.get_list(db, status=True, skip=0, limit=100)
            result = []
            for item in items:
                # 将SQLAlchemy对象转换为字典
                item_dict = {
                    "id": item.id,
                    "name": item.name,
                    "permission_type": item.permission_type,
                    "permission_config": item.permission_config,
                    "description": item.description,
                    "status": item.status,
                    "created_time": item.created_time,
                    "updated_time": item.updated_time,
                }
                result.append(AIDataPermissionInDB(**item_dict))
            return result
        except Exception as e:
            # 如果表不存在或没有数据，返回空列表
            print(f"获取数据权限列表失败: {e}")
            return []

    @staticmethod
    async def create_data_permission(db: AsyncSession, *, obj_in: AIDataPermissionCreate) -> AIDataPermissionInDB:
        """创建数据权限"""
        db_obj = await crud_ai_data_permission.create(db, obj_in=obj_in)
        item_dict = {
            "id": db_obj.id,
            "name": db_obj.name,
            "permission_type": db_obj.permission_type,
            "permission_config": db_obj.permission_config,
            "description": db_obj.description,
            "status": db_obj.status,
            "created_time": db_obj.created_time,
            "updated_time": db_obj.updated_time,
        }
        return AIDataPermissionInDB(**item_dict)
