#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from app.api.api_v1.endpoints import getdata

api_router = APIRouter()

api_router.include_router(getdata.router, prefix="/getdata", tags=["获取数据"])
