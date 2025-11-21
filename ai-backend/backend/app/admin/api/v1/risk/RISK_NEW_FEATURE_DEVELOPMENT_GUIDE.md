# Risk系统新功能开发指南 - 以风控等级管理为例

基于现有的风控等级管理功能，本文档记录了如何在Risk系统中新增一个完整的管理功能模块。以风控等级管理功能为例，展示完整的前后端开发流程。

## 1. 后端开发架构

### 1.1 目录结构
```
ai-backend/backend/app/admin/
├── model/                    # 数据模型层
│   ├── risk_level.py        # 新功能的数据模型
│   └── __init__.py          # 导入新模型
├── schema/                   # 数据验证层
│   └── risk_level.py        # 请求/响应数据结构
├── crud/                     # 数据访问层
│   └── crud_risk_level.py   # CRUD操作
├── service/                  # 业务逻辑层
│   └── risk_level_service.py # 业务服务
└── api/v1/risk/             # API接口层
    ├── risk_levels.py       # API路由定义
    └── __init__.py          # 路由注册
```

### 1.2 开发步骤

#### 步骤1: 创建数据模型 (`model/risk_level.py`)
```python

from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.common.model import Base


class RiskLevel(Base):
    """风控等级表"""

    __tablename__ = "risk_level"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, comment='风控等级ID，使用UUID')
    name: Mapped[str] = mapped_column(String(100), index=True, unique=True, comment='风控等级名称')
    start_score: Mapped[int] = mapped_column(Integer, comment='评分范围开始分')
    end_score: Mapped[int] = mapped_column(Integer, comment='评分范围结束分')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='风控等级描述')
```

**关键点:**
- 继承 `SchemaBase`
- 定义创建、更新、查询等不同场景的Schema
- 使用 `Field` 进行数据验证
- **业务验证器**: 如分数范围验证
- 完整的类型注解和描述

#### 步骤3: 创建CRUD操作 (`crud/crud_risk_level.py`)
```python

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid
from typing import List, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.risk_level import RiskLevel
from backend.app.admin.schema.risk_level import CreateRiskLevelParams, UpdateRiskLevelParams


class CRUDRiskLevel(CRUDPlus[RiskLevel]):
    """风控等级CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[RiskLevel]:
        """根据ID获取风控等级"""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[RiskLevel]:
        """根据名称获取风控等级"""
        result = await db.execute(
            select(self.model).where(self.model.name == name)
        )
        return result.scalars().first()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        page: int = 1,
        size: int = 10
    ) -> tuple[Sequence[RiskLevel], int]:
        """获取风控等级分页列表"""
        query = select(self.model)
        count_query = select(self.model)

        conditions = []
        if name:
            conditions.append(self.model.name.ilike(f'%{name}%'))
        if min_score is not None:
            conditions.append(self.model.end_score >= min_score)
        if max_score is not None:
            conditions.append(self.model.start_score <= max_score)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 获取总数
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())

        # 分页查询
        query = query.order_by(self.model.start_score.asc())
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)

        return result.scalars().all(), total

    async def get_all(self, db: AsyncSession) -> Sequence[RiskLevel]:
        """获取所有风控等级"""
        result = await db.execute(
            select(self.model).order_by(self.model.start_score.asc())
        )
        return result.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateRiskLevelParams
    ) -> RiskLevel:
        """创建风控等级"""
        # 生成UUID作为主键
        risk_level_id = str(uuid.uuid4())

        db_obj = self.model(
            id=risk_level_id,
            name=obj_in.name,
            start_score=obj_in.start_score,
            end_score=obj_in.end_score,
            description=obj_in.description
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: RiskLevel,
        obj_in: UpdateRiskLevelParams
    ) -> RiskLevel:
        """更新风控等级"""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """删除风控等级"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        db_obj = result.scalars().first()
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> int:
        """批量删除风控等级"""
        result = await db.execute(
            select(self.model).where(self.model.id.in_(ids))
        )
        db_objs = result.scalars().all()

        deleted_count = 0
        for db_obj in db_objs:
            await db.delete(db_obj)
            deleted_count += 1

        await db.commit()
        return deleted_count

    async def check_name_exists(
        self,
        db: AsyncSession,
        *,
        name: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        """检查风控等级名称是否已存在"""
        query = select(self.model).where(self.model.name == name)
        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        result = await db.execute(query)
        return result.scalars().first() is not None

    async def check_score_range_overlap(
        self,
        db: AsyncSession,
        *,
        start_score: int,
        end_score: int,
        exclude_id: Optional[str] = None
    ) -> bool:
        """检查分数范围是否与现有记录重叠"""
        query = select(self.model).where(
            and_(
                # 检查是否有重叠：新的开始分在现有范围内，或新的结束分在现有范围内，或新的范围包含现有范围
                (
                    (self.model.start_score <= start_score) & (start_score <= self.model.end_score)
                ) | (
                    (self.model.start_score <= end_score) & (end_score <= self.model.end_score)
                ) | (
                    (start_score <= self.model.start_score) & (self.model.end_score <= end_score)
                )
            )
        )

        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        result = await db.execute(query)
        return result.scalars().first() is not None


crud_risk_level = CRUDRiskLevel(RiskLevel)
```

**关键点:**
- 继承 `CRUDPlus` 获得基础CRUD能力
- 实现特定的查询方法（分页、筛选等）
- **业务专用方法**: 如 `check_score_range_overlap` 分数范围重叠检查
- 使用UUID作为主键
- 导出实例供服务层使用

#### 步骤4: 创建服务层 (`service/risk_level_service.py`)
```python

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_risk_level import crud_risk_level
from backend.app.admin.schema.risk_level import (
    CreateRiskLevelParams,
    UpdateRiskLevelParams,
    RiskLevel,
    DeleteResponse
)
from backend.common.pagination import PageData


class RiskLevelService:
    """风控等级服务"""

    def _level_to_dict(self, risk_level: any) -> dict:
        """将风控等级转换为字典"""
        return {
            "id": risk_level.id,
            "name": risk_level.name,
            "start_score": risk_level.start_score,
            "end_score": risk_level.end_score,
            "description": risk_level.description,
            "created_time": risk_level.created_time,
            "updated_time": risk_level.updated_time
        }

    async def get_paginated_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        page: int = 1,
        size: int = 10
    ) -> PageData[dict]:
        """获取分页风控等级列表"""
        risk_levels, total = await crud_risk_level.get_list(
            db,
            name=name,
            min_score=min_score,
            max_score=max_score,
            page=page,
            size=size
        )

        # 转换为字典
        items = [self._level_to_dict(risk_level) for risk_level in risk_levels]

        from math import ceil
        total_pages = ceil(total / size) if total > 0 else 1

        return PageData(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            links={
                'first': f'?page=1&size={size}',
                'last': f'?page={total_pages}&size={size}',
                'self': f'?page={page}&size={size}',
                'next': f'?page={page + 1}&size={size}' if page < total_pages else None,
                'prev': f'?page={page - 1}&size={size}' if page > 1 else None,
            }
        )

    async def get_all(self, db: AsyncSession) -> List[dict]:
        """获取所有风控等级"""
        risk_levels = await crud_risk_level.get_all(db)
        return [self._level_to_dict(risk_level) for risk_level in risk_levels]

    async def get_detail(self, db: AsyncSession, *, level_id: str) -> Optional[dict]:
        """获取风控等级详情"""
        risk_level = await crud_risk_level.get(db, id=level_id)
        if not risk_level:
            return None
        return self._level_to_dict(risk_level)

    async def create(
        self,
        db: AsyncSession,
        *,
        request: CreateRiskLevelParams
    ) -> dict:
        """创建风控等级"""
        # 检查风控等级名称是否已存在
        if await crud_risk_level.check_name_exists(db, name=request.name):
            raise ValueError(f"风控等级名称 '{request.name}' 已存在")

        # 检查分数范围是否重叠
        if await crud_risk_level.check_score_range_overlap(
            db,
            start_score=request.start_score,
            end_score=request.end_score
        ):
            raise ValueError(f"分数范围 {request.start_score}-{request.end_score} 与现有风控等级重叠")

        # 创建风控等级
        risk_level = await crud_risk_level.create(db, obj_in=request)
        return self._level_to_dict(risk_level)

    async def update(
        self,
        db: AsyncSession,
        *,
        level_id: str,
        request: UpdateRiskLevelParams
    ) -> Optional[dict]:
        """更新风控等级"""
        # 检查风控等级是否存在
        risk_level = await crud_risk_level.get(db, id=level_id)
        if not risk_level:
            return None

        # 如果更新名称，检查是否重复
        if request.name and request.name != risk_level.name:
            if await crud_risk_level.check_name_exists(db, name=request.name, exclude_id=level_id):
                raise ValueError(f"风控等级名称 '{request.name}' 已存在")

        # 如果更新分数范围，检查是否重叠
        start_score = request.start_score if request.start_score is not None else risk_level.start_score
        end_score = request.end_score if request.end_score is not None else risk_level.end_score

        if (request.start_score is not None or request.end_score is not None):
            if await crud_risk_level.check_score_range_overlap(
                db,
                start_score=start_score,
                end_score=end_score,
                exclude_id=level_id
            ):
                raise ValueError(f"分数范围 {start_score}-{end_score} 与现有风控等级重叠")

        # 更新风控等级
        updated_level = await crud_risk_level.update(db, db_obj=risk_level, obj_in=request)
        return self._level_to_dict(updated_level)

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> DeleteResponse:
        """批量删除风控等级"""
        # 检查风控等级是否存在
        for level_id in ids:
            risk_level = await crud_risk_level.get(db, id=level_id)
            if not risk_level:
                raise ValueError(f"风控等级 ID '{level_id}' 不存在")

        # 批量删除
        deleted_count = await crud_risk_level.delete_batch(db, ids=ids)
        return DeleteResponse(deleted_count=deleted_count)


risk_level_service = RiskLevelService()
```

**关键点:**
- 封装业务逻辑
- 数据格式转换（`_level_to_dict`）
- **业务验证规则**: 唯一性检查、分数范围重叠检查等
- 统一的分页数据格式

#### 步骤5: 创建API接口 (`api/v1/risk/risk_levels.py`)
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-23 10:59:19
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-23 10:59:31
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.risk_level import (
    CreateRiskLevelParams,
    UpdateRiskLevelParams,
    RiskLevel,
    RiskLevelParams,
    DeleteParams,
    DeleteResponse
)
from backend.app.admin.service.risk_level_service import risk_level_service
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.response.response_code import CustomResponse
from backend.common.security.jwt import DependsJwtAuth
from backend.common.pagination import PageData
from backend.database.db import get_db

router = APIRouter()


@router.get('', summary='获取风控等级列表', dependencies=[DependsJwtAuth])
async def get_risk_levels(
    name: Optional[str] = Query(None, description='风控等级名称（模糊搜索）'),
    min_score: Optional[int] = Query(None, ge=0, le=1000, description='最小分数筛选'),
    max_score: Optional[int] = Query(None, ge=0, le=1000, description='最大分数筛选'),
    page: int = Query(1, ge=1, description='页码'),
    size: int = Query(10, gt=0, le=200, description='每页数量'),
    db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[PageData[dict]]:
    """获取风控等级列表"""
    data = await risk_level_service.get_paginated_list(
        db, name=name, min_score=min_score, max_score=max_score, page=page, size=size
    )
    return response_base.success(data=data)


@router.get('/all', summary='获取所有风控等级（不分页）', dependencies=[DependsJwtAuth])
async def get_all_risk_levels(
    db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[List[dict]]:
    """获取所有风控等级（不分页）"""
    data = await risk_level_service.get_all(db)
    return response_base.success(data=data)


@router.get('/{level_id}', summary='获取风控等级详情', dependencies=[DependsJwtAuth])
async def get_risk_level_detail(
    level_id: str = Path(..., description='风控等级ID'),
    db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """获取风控等级详情"""
    data = await risk_level_service.get_detail(db, level_id=level_id)
    if not data:
        return response_base.fail(res=CustomResponse(code=404, msg="风控等级不存在"), data={})
    return response_base.success(data=data)


@router.post('', summary='创建风控等级', dependencies=[DependsJwtAuth])
async def create_risk_level(
    request: CreateRiskLevelParams,
    db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """创建风控等级"""
    try:
        data = await risk_level_service.create(db, request=request)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.put('/{level_id}', summary='更新风控等级', dependencies=[DependsJwtAuth])
async def update_risk_level(
    level_id: str = Path(..., description='风控等级ID'),
    request: UpdateRiskLevelParams = ...,
    db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """更新风控等级"""
    try:
        data = await risk_level_service.update(db, level_id=level_id, request=request)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="风控等级不存在"), data={})
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})


@router.delete('', summary='删除风控等级', dependencies=[DependsJwtAuth])
async def delete_risk_levels(
    request: DeleteParams,
    db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[DeleteResponse]:
    """批量删除风控等级"""
    try:
        data = await risk_level_service.delete_batch(db, ids=request.ids)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data=DeleteResponse(deleted_count=0))
```

**关键点:**
- 使用 `APIRouter` 组织路由
- 合理的参数验证（Query、Path参数）
- **特定业务参数**: 如分数范围筛选参数
- 统一的响应格式
- 完整的错误处理

#### 步骤6: 注册路由 (`api/v1/risk/__init__.py`)
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from . import risk_levels

router = APIRouter()

router.include_router(risk_levels.router, prefix="/risk-levels", tags=["风控等级管理"])

# 定义路由器并导出
__all__ = ["router"]
```

#### 步骤7: 更新模型导入 (`model/__init__.py`)
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from backend.app.admin.model.risk_level import RiskLevel  # 新增
# ... 其他导入
```

## 2. 前端开发架构

### 2.1 目录结构
```
ai-front/apps/web-antd/src/views/risk/risk-levels/
├── data.ts          # 表格配置、表单配置
├── index.vue        # 主页面组件
└── (可选的其他组件)

ai-front/apps/web-antd/src/api/
└── risk.ts         # API接口定义
```

### 2.2 开发步骤

#### 步骤1: 添加API接口定义 (`api/risk.ts`)
```typescript


import { requestClient } from '#/api/request';

// ================== 风控等级相关接口 ==================

// 风控等级接口类型
export interface RiskLevel {
  id: string;
  name: string;
  start_score: number;
  end_score: number;
  description?: string;
  created_time: string;
  updated_time: string;
}

export interface RiskLevelParams {
  name?: string;
  min_score?: number;
  max_score?: number;
  page?: number;
  size?: number;
}

export interface CreateRiskLevelParams {
  name: string;
  start_score: number;
  end_score: number;
  description?: string;
}

export interface UpdateRiskLevelParams {
  name?: string;
  start_score?: number;
  end_score?: number;
  description?: string;
}

// ================== 风控等级 API ==================

/**
 * 获取风控等级列表
 */
export async function getRiskLevelListApi(params: RiskLevelParams) {
  return requestClient.get<{
    items: RiskLevel[];
    total: number;
    page: number;
    size: number;
    total_pages: number;
  }>('/api/v1/risk/risk-levels', { params });
}

/**
 * 获取所有风控等级（不分页）
 */
export async function getAllRiskLevelsApi() {
  return requestClient.get<RiskLevel[]>('/api/v1/risk/risk-levels/all');
}

/**
 * 获取风控等级详情
 */
export async function getRiskLevelApi(id: string) {
  return requestClient.get<RiskLevel>(`/api/v1/risk/risk-levels/${id}`);
}

/**
 * 创建风控等级
 */
export async function createRiskLevelApi(data: CreateRiskLevelParams) {
  return requestClient.post<RiskLevel>('/api/v1/risk/risk-levels', data);
}

/**
 * 更新风控等级
 */
export async function updateRiskLevelApi(id: string, data: UpdateRiskLevelParams) {
  return requestClient.put<RiskLevel>(`/api/v1/risk/risk-levels/${id}`, data);
}

/**
 * 删除风控等级
 */
export async function deleteRiskLevelApi(ids: string[]) {
  return requestClient.delete<{
    deleted_count: number;
  }>('/api/v1/risk/risk-levels', {
    data: { ids },
  });
}

```

#### 步骤2: 创建数据配置 (`views/risk/risk-levels/data.ts`)
```typescript

import type { VbenFormSchema } from '#/adapter/form';
import type {
  OnActionClickFn,
  VxeGridProps,
} from '#/adapter/vxe-table';

import { z } from '#/adapter/form';

// 风控等级接口类型
interface RiskLevel {
  id: string;
  name: string;
  start_score: number;
  end_score: number;
  description?: string;
  created_time: string;
  updated_time: string;
}

// 查询表单配置
export const querySchema: VbenFormSchema[] = [
  {
    component: 'Input',
    fieldName: 'name',
    label: '等级名称',
    componentProps: {
      placeholder: '请输入等级名称',
    },
  },
  {
    component: 'InputNumber',
    fieldName: 'min_score',
    label: '最小分数',
    componentProps: {
      placeholder: '请输入最小分数',
      min: 0,
      max: 1000,
    },
  },
  {
    component: 'InputNumber',
    fieldName: 'max_score',
    label: '最大分数',
    componentProps: {
      placeholder: '请输入最大分数',
      min: 0,
      max: 1000,
    },
  },
];

// 表格列配置
export function useColumns(
  onActionClick?: OnActionClickFn<RiskLevel>,
): VxeGridProps['columns'] {
  return [
    {
      field: 'seq',
      title: '序号',
      type: 'seq',
      width: 60,
    },
    {
      field: 'name',
      title: '等级名称',
      minWidth: 150,
      showOverflow: 'ellipsis',
    },
    {
      field: 'start_score',
      title: '开始分',
      width: 100,
      align: 'center',
    },
    {
      field: 'end_score',
      title: '结束分',
      width: 100,
      align: 'center',
    },
    {
      field: 'score_range',
      title: '分数范围',
      width: 150,
      align: 'center',
      formatter({ row }) {
        return `${row.start_score} - ${row.end_score}`;
      },
    },
    {
      field: 'description',
      title: '描述',
      minWidth: 200,
      showOverflow: 'ellipsis',
      formatter({ cellValue }) {
        return cellValue || '-';
      },
    },
    {
      field: 'created_time',
      title: '创建时间',
      width: 180,
      formatter({ cellValue }) {
        if (!cellValue) return '';
        return new Date(cellValue).toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
      },
    },
    {
      field: 'updated_time',
      title: '更新时间',
      width: 180,
      formatter({ cellValue }) {
        if (!cellValue) return '';
        return new Date(cellValue).toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
      },
    },
    {
      field: 'operation',
      title: '操作',
      align: 'center',
      fixed: 'right',
      width: 120,
      cellRender: {
        attrs: {
          nameField: 'name',
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: ['edit', 'delete'],
      },
    },
  ];
}

// 添加表单配置
export function useAddSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: '等级名称',
      rules: z.string().min(1, { message: '请输入等级名称' }),
      componentProps: {
        placeholder: '请输入风控等级名称，如：低风险、中风险、高风险等',
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'start_score',
      label: '开始分',
      rules: z.number().min(0, { message: '开始分不能小于0' }).max(1000, { message: '开始分不能大于1000' }),
      componentProps: {
        placeholder: '请输入评分范围开始分',
        min: 0,
        max: 1000,
        precision: 0,
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'end_score',
      label: '结束分',
      rules: z.number().min(0, { message: '结束分不能小于0' }).max(1000, { message: '结束分不能大于1000' }),
      componentProps: {
        placeholder: '请输入评分范围结束分',
        min: 0,
        max: 1000,
        precision: 0,
      },
    },
    {
      component: 'Textarea',
      fieldName: 'description',
      label: '描述',
      componentProps: {
        placeholder: '请输入风控等级描述（可选）',
        rows: 3,
        maxlength: 500,
        showCount: true,
      },
    },
  ];
}

// 编辑表单配置
export function useEditSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      fieldName: 'name',
      label: '等级名称',
      rules: z.string().min(1, { message: '请输入等级名称' }),
      componentProps: {
        placeholder: '请输入风控等级名称，如：低风险、中风险、高风险等',
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'start_score',
      label: '开始分',
      rules: z.number().min(0, { message: '开始分不能小于0' }).max(1000, { message: '开始分不能大于1000' }),
      componentProps: {
        placeholder: '请输入评分范围开始分',
        min: 0,
        max: 1000,
        precision: 0,
      },
    },
    {
      component: 'InputNumber',
      fieldName: 'end_score',
      label: '结束分',
      rules: z.number().min(0, { message: '结束分不能小于0' }).max(1000, { message: '结束分不能大于1000' }),
      componentProps: {
        placeholder: '请输入评分范围结束分',
        min: 0,
        max: 1000,
        precision: 0,
      },
    },
    {
      component: 'Textarea',
      fieldName: 'description',
      label: '描述',
      componentProps: {
        placeholder: '请输入风控等级描述（可选）',
        rows: 3,
        maxlength: 500,
        showCount: true,
      },
    },
  ];
}
```

#### 步骤3: 创建主页面组件 (`views/risk/risk-levels/index.vue`)
```vue
<script setup lang="ts">
import type { VbenFormProps } from '@vben/common-ui';

import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';

import { onMounted, ref } from 'vue';

import { useVbenModal, VbenButton, Page } from '@vben/common-ui';
import { MaterialSymbolsAdd } from '@vben/icons';
import { $t } from '@vben/locales';

import { message } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { useVbenVxeGrid } from '#/adapter/vxe-table';

import {
  querySchema,
  useAddSchema,
  useColumns,
  useEditSchema,
} from './data';

// 导入API
import type {
  RiskLevel,
  RiskLevelParams,
  CreateRiskLevelParams,
  UpdateRiskLevelParams,
} from '#/api';

import {
  createRiskLevelApi,
  deleteRiskLevelApi,
  getRiskLevelListApi,
  updateRiskLevelApi,
  getRiskLevelApi,
} from '#/api';

/**
 * 表格配置
 */
const formOptions: VbenFormProps = {
  collapsed: true,
  showCollapseButton: true,
  submitButtonOptions: {
    content: $t('page.form.query'),
  },
  schema: querySchema,
};

const gridOptions: VxeTableGridOptions<RiskLevel> = {
  rowConfig: {
    keyField: 'id',
  },
  checkboxConfig: {
    highlight: true,
  },
  virtualYConfig: {
    enabled: true,
    gt: 0,
  },
  height: 'auto',
  exportConfig: {},
  printConfig: {},
  toolbarConfig: {
    export: true,
    print: true,
    refresh: { code: 'query' },
    custom: true,
    zoom: true,
  },
  columns: useColumns(onActionClick),
  proxyConfig: {
    ajax: {
      query: async ({ page }, formValues) => {
        const result = await getRiskLevelListApi({
          page: page.currentPage,
          size: page.pageSize,
          ...formValues,
        } as RiskLevelParams);

        return {
          items: result.items || [],
          total: result.total || 0,
        };
      },
    },
  },
};

const [Grid, gridApi] = useVbenVxeGrid({ formOptions, gridOptions });

function onRefresh() {
  gridApi.query();
}

function onActionClick({ code, row }: OnActionClickParams<RiskLevel>) {
  switch (code) {
    case 'delete': {
      deleteRiskLevelApi([row.id]).then(() => {
        message.success({
          content: `删除等级"${row.name}"成功`,
          key: 'action_process_msg',
        });
        onRefresh();
      });
      break;
    }
    case 'edit': {
      editLevel.value = row.id;
      editModalApi.setData(row).open();
      break;
    }
  }
}

/**
 * 编辑表单
 */
const [EditForm, formApi] = useVbenForm({
  showDefaultActions: false,
  schema: useEditSchema(),
});

const editLevel = ref<string>('');

const [editModal, editModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (valid) {
      editModalApi.lock();
      const data = await formApi.getValues<UpdateRiskLevelParams>();

      // 验证分数范围
      if (data.start_score !== undefined && data.end_score !== undefined && data.start_score >= data.end_score) {
        message.error('结束分必须大于开始分');
        editModalApi.unlock();
        return;
      }

      try {
        await updateRiskLevelApi(editLevel.value, data);
        await editModalApi.close();
        message.success('更新等级成功');
        onRefresh();
      } catch (error: any) {
        message.error(error?.response?.data?.msg || '更新等级失败');
      } finally {
        editModalApi.unlock();
      }
    }
  },
  async onOpenChange(isOpen) {
    if (isOpen) {
      const data = editModalApi.getData<RiskLevel>();
      formApi.resetForm();
      if (data && data.id) {
        try {
          // 通过接口获取完整的数据
          const fullData = await getRiskLevelApi(data.id);
          formApi.setValues(fullData);
        } catch (error) {
          console.error('获取等级详情失败:', error);
          message.error('获取等级详情失败');
          // 如果接口调用失败，使用原始数据
          formApi.setValues(data);
        }
      }
    }
  },
});

/**
 * 添加表单
 */
const [AddForm, addFormApi] = useVbenForm({
  showDefaultActions: false,
  schema: useAddSchema(),
});

const [addModal, addModalApi] = useVbenModal({
  destroyOnClose: true,
  async onConfirm() {
    const { valid } = await addFormApi.validate();
    if (valid) {
      addModalApi.lock();
      const data = await addFormApi.getValues<CreateRiskLevelParams>();

      // 验证分数范围
      if (data.start_score >= data.end_score) {
        message.error('结束分必须大于开始分');
        addModalApi.unlock();
        return;
      }

      try {
        await createRiskLevelApi(data);
        await addModalApi.close();
        message.success('添加等级成功');
        onRefresh();
      } catch (error: any) {
        message.error(error?.response?.data?.msg || '添加等级失败');
      } finally {
        addModalApi.unlock();
      }
    }
  },
  onOpenChange(isOpen) {
    if (isOpen) {
      const data = addModalApi.getData();
      addFormApi.resetForm();
      if (data) {
        addFormApi.setValues(data);
      }
    }
  },
});

onMounted(() => {
  // 初始化数据
});
</script>

<template>
  <Page auto-content-height>
    <Grid>
      <template #toolbar-actions>
        <VbenButton @click="() => addModalApi.setData(null).open()">
          <MaterialSymbolsAdd class="size-5" />
          添加等级
        </VbenButton>
      </template>
    </Grid>

    <!-- 编辑模态框 -->
    <editModal title="编辑风控等级">
      <EditForm />
    </editModal>

    <!-- 添加模态框 -->
    <addModal title="添加风控等级">
      <AddForm />
    </addModal>
  </Page>
</template>
```
## 3. Risk系统开发规范总结

### 3.1 命名规范
- **后端文件**: 使用下划线命名 (`risk_level.py`)
- **前端文件**: 使用短横线命名 (`risk-levels/`)
- **API路径**: 使用短横线 (`/risk-levels`)
- **数据库表**: 使用下划线单数形式 (`risk_level`)
- **类名**: 使用大驼峰命名 (`RiskLevel`, `CRUDRiskLevel`)
- **函数名**: 使用下划线命名 (`get_paginated_list`)
- **变量名**: 使用下划线命名 (`risk_level_service`)

### 3.2 Risk系统特有功能
- **分数范围管理**: 风控等级通常涉及分数区间
- **业务验证**: 分数范围重叠检查、唯一性验证
- **特定筛选**: 支持按分数范围筛选
- **排序规则**: 通常按分数或风险级别排序

### 3.3 必须实现的功能
- **列表查询**: 支持分页、筛选（名称、分数范围）
- **详情查看**: 获取单条记录
- **新增**: 数据验证、业务规则检查
- **编辑**: 部分更新支持、业务验证
- **删除**: 批量删除支持
- **业务验证**: 如分数范围重叠检查

### 3.4 关键文件清单
新增风控功能时需要创建/修改的文件：

**后端 (7个文件)**:
1. `model/{feature_name}.py` - 数据模型
2. `schema/{feature_name}.py` - 数据验证
3. `crud/crud_{feature_name}.py` - 数据访问
4. `service/{feature_name}_service.py` - 业务逻辑
5. `api/v1/risk/{feature_name}s.py` - API接口
6. `api/v1/risk/__init__.py` - 路由注册 (修改)
7. `model/__init__.py` - 模型导入 (修改)

**前端 (3个文件)**:
1. `views/risk/{feature-name}s/data.ts` - 配置文件
2. `views/risk/{feature-name}s/index.vue` - 主页面
3. `api/risk.ts` - API接口 (修改)

### 3.5 开发流程
1. **后端开发**: model → schema → crud → service → api → 路由注册
2. **前端开发**: API接口定义 → 数据配置 → 页面组件
3. **测试验证**: 接口测试 → 功能测试 → 集成测试

### 3.6 注意事项
- 风控系统通常涉及敏感数据，要特别注意权限控制
- 业务逻辑验证要严格，如分数范围不能重叠
- 前端表格要支持按业务维度排序和筛选
- API接口要有完整的文档注释
- 数据库字段要有合适的索引和约束
- 错误处理要完整，包括业务异常和系统异常

## 4. 标准CRUD模板 (Risk系统专用)

```python
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid
from typing import List, Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.{model_name} import {ModelClass}
from backend.app.admin.schema.{model_name} import Create{ModelClass}Params, Update{ModelClass}Params


class CRUD{ModelClass}(CRUDPlus[{ModelClass}]):
    """{ModelClass}CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[{ModelClass}]:
        """根据ID获取记录"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[{ModelClass}]:
        """根据名称获取记录"""
        result = await db.execute(select(self.model).where(self.model.name == name))
        return result.scalars().first()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        # TODO: 添加业务特定的筛选参数
        page: int = 1,
        size: int = 10
    ) -> tuple[Sequence[{ModelClass}], int]:
        """获取分页列表"""
        query = select(self.model)
        count_query = select(self.model)

        conditions = []
        if name:
            conditions.append(self.model.name.ilike(f'%{name}%'))
        # TODO: 添加业务特定的筛选条件

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 获取总数
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())

        # 分页查询 - TODO: 根据业务需要调整排序字段
        query = query.order_by(self.model.created_time.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)

        return result.scalars().all(), total

    async def get_all(self, db: AsyncSession) -> Sequence[{ModelClass}]:
        """获取所有记录"""
        result = await db.execute(select(self.model).order_by(self.model.name))
        return result.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: Create{ModelClass}Params
    ) -> {ModelClass}:
        """创建记录"""
        # 生成UUID作为主键
        record_id = str(uuid.uuid4())

        db_obj = self.model(
            id=record_id,
            name=obj_in.name
            # TODO: 添加其他字段
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: {ModelClass},
        obj_in: Update{ModelClass}Params
    ) -> {ModelClass}:
        """更新记录"""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """删除记录"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        db_obj = result.scalars().first()
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> int:
        """批量删除记录"""
        result = await db.execute(select(self.model).where(self.model.id.in_(ids)))
        db_objs = result.scalars().all()

        deleted_count = 0
        for db_obj in db_objs:
            await db.delete(db_obj)
            deleted_count += 1

        await db.commit()
        return deleted_count

    async def check_name_exists(
        self,
        db: AsyncSession,
        *,
        name: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        """检查名称是否已存在"""
        query = select(self.model).where(self.model.name == name)
        if exclude_id:
            query = query.where(self.model.id != exclude_id)

        result = await db.execute(query)
        return result.scalars().first() is not None

    # TODO: 添加业务特定的检查方法
    # 如：check_score_range_overlap、check_risk_threshold等


crud_{model_name} = CRUD{ModelClass}({ModelClass})
```
## 4. CRUD开发常见问题与解决方案

### 4.1 CRUD基类选择错误

**❌ 常见错误:**
```python
# 错误的基类继承
from backend.common.crud import CRUDBase

class CRUDAssistantType(CRUDBase[AssistantType, CreateAssistantTypeParams, UpdateAssistantTypeParams]):
    pass
```

**✅ 正确做法:**
```python
# 正确的基类继承
from sqlalchemy_crud_plus import CRUDPlus

class CRUDAssistantType(CRUDPlus[AssistantType]):
    pass
```

**问题说明:**
- `CRUDBase` 是旧版本的基类，不再推荐使用
- `CRUDPlus` 是当前项目标准的CRUD基类
- `CRUDPlus` 只需要一个泛型参数（模型类）

### 4.2 导入模块错误

**❌ 常见错误:**
```python
# 错误的导入
from backend.common.crud import CRUDBase
from backend.common.exception import errors
from backend.common.security.encrypt import encrypt_text, decrypt_text
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.future import select
from typing import List, Optional, Tuple
```

**✅ 正确做法:**
```python
# 正确的导入
from sqlalchemy_crud_plus import CRUDPlus
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Sequence
```

**问题说明:**
- 移除不必要的导入（`errors`, `encrypt_text`, `decrypt_text`等）
- 使用标准的 `select` 导入方式
- 使用 `Sequence` 而不是 `List` 作为返回类型

### 4.3 查询方法实现问题

**❌ 常见错误:**
```python
# 错误的总数查询方式
async def get_list(self, db, *, name=None, page=1, size=10) -> Tuple[List[Model], int]:
    query = select(self.model)
    if name:
        query = query.where(self.model.name.like(f'%{name}%'))

    # 错误：使用复杂的count查询
    count_query = select(func.count(self.model.id)).where(query.whereclause)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 错误：使用desc()函数
    query = query.order_by(desc(self.model.created_time))
    return list(items), total
```

**✅ 正确做法:**
```python
# 正确的查询方式
async def get_list(self, db, *, name=None, page=1, size=10) -> tuple[Sequence[Model], int]:
    query = select(self.model)
    count_query = select(self.model)

    conditions = []
    if name:
        conditions.append(self.model.name.ilike(f'%{name}%'))  # 使用ilike

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    # 正确：先查询所有记录再计算总数
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    # 正确：使用属性方式调用desc
    query = query.order_by(self.model.created_time.desc())
    result = await db.execute(query)

    return result.scalars().all(), total
```

**问题说明:**
- 使用 `ilike` 进行大小写不敏感的模糊搜索
- 避免复杂的 `func.count()` 查询，直接查询记录后计算长度
- 使用 `self.model.created_time.desc()` 而不是 `desc(self.model.created_time)`

### 4.4 缺少标准CRUD方法

**❌ 常见错误:**
```python
# 缺少基础的CRUD方法
class CRUDAssistantType(CRUDPlus[AssistantType]):
    async def get_list(self, db, **kwargs):
        pass

    async def create(self, db, *, obj_in):
        pass

    # 缺少 get, get_by_name, update, delete 等基础方法
```

**✅ 正确做法:**
```python
# 完整的CRUD方法实现
class CRUDAssistantType(CRUDPlus[AssistantType]):
    # 基础CRUD方法
    async def get(self, db: AsyncSession, *, id: str) -> Optional[AssistantType]:
        """根据ID获取记录"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AssistantType]:
        """根据名称获取记录"""
        result = await db.execute(select(self.model).where(self.model.name == name))
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: CreateParams) -> AssistantType:
        """创建记录"""
        # 实现创建逻辑

    async def update(self, db: AsyncSession, *, db_obj: AssistantType, obj_in: UpdateParams) -> AssistantType:
        """更新记录"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """删除记录"""
        # 实现删除逻辑

    # 业务方法
    async def get_list(self, db, **kwargs) -> tuple[Sequence[AssistantType], int]:
        """分页查询"""

    async def get_all(self, db) -> Sequence[AssistantType]:
        """获取所有记录"""

    async def delete_batch(self, db, *, ids: List[str]) -> int:
        """批量删除"""

    async def check_name_exists(self, db, *, name: str, exclude_id: Optional[str] = None) -> bool:
        """检查名称是否存在"""
```

### 4.5 CRUD开发检查清单

**创建CRUD文件时必须检查的项目:**

- [ ] **基类继承**: 使用 `CRUDPlus[Model]` 而不是 `CRUDBase`
- [ ] **导入模块**: 只导入必要的模块，使用标准导入方式
- [ ] **基础方法**: 实现 `get`, `get_by_name`, `create`, `update`, `delete` 方法
- [ ] **查询方法**: 使用 `ilike` 进行模糊搜索，正确计算总数
- [ ] **返回类型**: 使用 `Sequence` 而不是 `List`，使用 `tuple` 而不是 `Tuple`
- [ ] **排序方式**: 使用 `model.field.desc()` 而不是 `desc(model.field)`
- [ ] **业务方法**: 根据需要实现 `get_all`, `delete_batch`, `check_name_exists` 等方法
- [ ] **UUID生成**: 使用 `str(uuid.uuid4())` 生成主键
- [ ] **事务处理**: 正确使用 `db.commit()` 和 `db.refresh()`

按照这个模板和指南，可以快速搭建新的风控管理功能模块，确保代码结构一致性和可维护性。
