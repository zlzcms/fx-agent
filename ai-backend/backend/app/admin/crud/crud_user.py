#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections.abc import Sequence
from datetime import datetime

import bcrypt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload
from sqlalchemy.sql import Select
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model import Dept, Role, User
from backend.app.admin.schema.user import (
    AddOAuth2UserParam,
    AddUserParam,
    UpdateUserParam,
)
from backend.common.security.jwt import get_hash_password
from backend.utils.timezone import timezone


class CRUDUser(CRUDPlus[User]):
    """用户数据库操作类"""

    async def get(self, db: AsyncSession, user_id: int) -> User | None:
        """
        获取用户详情

        :param db: 数据库会话
        :param user_id: 用户 ID
        :return:
        """
        return await self.select_model_by_column(db, id=user_id, deleted_at=None)

    async def get_by_crm_user_id(self, db: AsyncSession, crm_user_id: str) -> User | None:
        """
        通过CRM用户ID获取用户

        :param db: 数据库会话
        :param crm_user_id: CRM用户ID
        :return: 用户对象
        """
        return await self.select_model_by_column(db, crm_user_id=crm_user_id, deleted_at=None)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """
        通过邮箱获取用户

        :param db: 数据库会话
        :param email: 用户邮箱
        :return: 用户对象
        """
        return await self.select_model_by_column(db, email=email, deleted_at=None)

    async def check_crm_user_id(self, db: AsyncSession, crm_user_id: str) -> User | None:
        """
        检查CRM用户ID是否已存在

        :param db: 数据库会话
        :param crm_user_id: CRM用户ID
        :return: 如果存在则返回用户对象，否则返回None
        """
        return await self.select_model_by_column(db, crm_user_id=crm_user_id, deleted_at=None)

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        """
        通过用户名获取用户

        :param db: 数据库会话
        :param username: 用户名
        :return:
        """
        return await self.select_model_by_column(db, username=username, deleted_at=None)

    async def get_all(self, db: AsyncSession) -> Sequence[User]:
        """
        获取所有用户

        :param db: 数据库会话
        :return:
        """
        return await self.select_models(
            db,
            load_options=[selectinload(self.model.roles).options(selectinload(Role.menus), selectinload(Role.scopes))],
            load_strategies=["dept"],
        )

    async def get_by_nickname(self, db: AsyncSession, nickname: str) -> User | None:
        """
        通过昵称获取用户

        :param db: 数据库会话
        :param nickname: 昵称
        :return:
        """
        return await self.select_model_by_column(db, nickname=nickname, deleted_at=None)

    async def update_login_time(self, db: AsyncSession, username: str) -> int:
        """
        更新用户最后登录时间

        :param db: 数据库会话
        :param username: 用户名
        :return:
        """
        return await self.update_model_by_column(db, {"last_login_time": timezone.now()}, username=username)

    async def add(self, db: AsyncSession, obj: AddUserParam) -> None:
        """
        添加用户

        :param db: 数据库会话
        :param obj: 添加用户参数
        :return:
        """
        salt = bcrypt.gensalt()
        obj.password = get_hash_password(obj.password, salt)
        dict_obj = obj.model_dump(exclude={"roles"})
        dict_obj.update({"salt": salt})
        new_user = self.model(**dict_obj)

        stmt = select(Role).where(Role.id.in_(obj.roles))
        roles = await db.execute(stmt)
        new_user.roles = roles.scalars().all()

        db.add(new_user)

    async def add_by_oauth2(self, db: AsyncSession, obj: AddOAuth2UserParam) -> None:
        """
        通过 OAuth2 添加用户

        :param db: 数据库会话
        :param obj: 注册用户参数
        :return:
        """
        dict_obj = obj.model_dump()
        dict_obj.update({"is_staff": True, "salt": None})
        new_user = self.model(**dict_obj)

        stmt = select(Role)
        role = await db.execute(stmt)
        new_user.roles = [role.scalars().first()]  # 默认绑定第一个角色

        db.add(new_user)

    async def update(self, db: AsyncSession, input_user: User, obj: UpdateUserParam) -> int:
        """
        更新用户信息

        :param db: 数据库会话
        :param input_user: 用户 ID
        :param obj: 更新用户参数
        :return:
        """
        role_ids = obj.roles
        del obj.roles
        count = await self.update_model(db, input_user.id, obj)

        stmt = select(Role).where(Role.id.in_(role_ids))
        roles = await db.execute(stmt)
        input_user.roles = roles.scalars().all()
        return count

    async def update_nickname(self, db: AsyncSession, user_id: int, nickname: str) -> int:
        """
        更新用户昵称

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param nickname: 用户昵称
        :return:
        """
        return await self.update_model(db, user_id, {"nickname": nickname})

    async def update_avatar(self, db: AsyncSession, user_id: int, avatar: str) -> int:
        """
        更新用户头像

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param avatar: 头像地址
        :return:
        """
        return await self.update_model(db, user_id, {"avatar": avatar})

    async def update_email(self, db: AsyncSession, user_id: int, email: str) -> int:
        """
        更新用户邮箱

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param email: 邮箱
        :return:
        """
        return await self.update_model(db, user_id, {"email": email})

    async def delete(self, db: AsyncSession, user_id: int) -> int:
        """
        软删除用户

        :param db: 数据库会话
        :param user_id: 用户 ID
        :return:
        """
        return await self.update_model(db, user_id, {"deleted_at": datetime.now()})

    async def check_email(self, db: AsyncSession, email: str) -> User | None:
        """
        检查邮箱是否已被绑定

        :param db: 数据库会话
        :param email: 电子邮箱
        :return:
        """
        return await self.select_model_by_column(db, email=email, deleted_at=None)

    async def reset_password(self, db: AsyncSession, pk: int, password: str) -> int:
        """
        重置用户密码

        :param db: 数据库会话
        :param pk: 用户 ID
        :param password: 新密码
        :return:
        """
        salt = bcrypt.gensalt()
        new_pwd = get_hash_password(password, salt)
        return await self.update_model(db, pk, {"password": new_pwd, "salt": salt})

    async def get_list(self, dept: int | None, username: str | None, phone: str | None, status: int | None) -> Select:
        """
        获取用户列表

        :param dept: 部门 ID
        :param username: 用户名
        :param phone: 电话号码
        :param status: 用户状态
        :return:
        """
        filters = {"deleted_at": None}

        if dept:
            filters["dept_id"] = dept
        if username:
            filters["username__like"] = f"%{username}%"
        if phone:
            filters["phone__like"] = f"%{phone}%"
        if status is not None:
            filters["status"] = status

        return await self.select_order(
            "id",
            "desc",
            load_options=[
                selectinload(self.model.dept).options(noload(Dept.parent), noload(Dept.children), noload(Dept.users)),
                selectinload(self.model.roles).options(
                    noload(Role.users),
                    selectinload(Role.menus),
                    selectinload(Role.scopes),
                ),
            ],
            **filters,
        )

    async def set_super(self, db: AsyncSession, user_id: int, is_super: bool) -> int:
        """
        设置用户超级管理员状态

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param is_super: 是否超级管理员
        :return:
        """
        return await self.update_model(db, user_id, {"is_superuser": is_super})

    async def set_staff(self, db: AsyncSession, user_id: int, is_staff: bool) -> int:
        """
        设置用户后台登录状态

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param is_staff: 是否可登录后台
        :return:
        """
        return await self.update_model(db, user_id, {"is_staff": is_staff})

    async def set_status(self, db: AsyncSession, user_id: int, status: int) -> int:
        """
        设置用户状态

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param status: 状态
        :return:
        """
        return await self.update_model(db, user_id, {"status": status})

    async def set_multi_login(self, db: AsyncSession, user_id: int, multi_login: bool) -> int:
        """
        设置用户多端登录状态

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param multi_login: 是否允许多端登录
        :return:
        """
        return await self.update_model(db, user_id, {"is_multi_login": multi_login})

    async def get_with_relation(
        self, db: AsyncSession, *, user_id: int | None = None, username: str | None = None
    ) -> User | None:
        """
        获取用户关联信息

        :param db: 数据库会话
        :param user_id: 用户 ID
        :param username: 用户名
        :return:
        """
        filters = {"deleted_at": None}

        if user_id:
            filters["id"] = user_id
        if username:
            filters["username"] = username

        return await self.select_model_by_column(
            db,
            load_options=[
                selectinload(self.model.dept).options(noload(Dept.parent), noload(Dept.children), noload(Dept.users)),
                selectinload(self.model.roles).options(noload(Role.users), noload(Role.menus), noload(Role.scopes)),
            ],
            **filters,
        )


user_dao: CRUDUser = CRUDUser(User)
