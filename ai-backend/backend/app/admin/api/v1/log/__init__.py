#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from backend.app.admin.api.v1.log.chat_log import router as chat_log
from backend.app.admin.api.v1.log.login_log import router as login_log
from backend.app.admin.api.v1.log.notice_log import router as notice_log
from backend.app.admin.api.v1.log.opera_log import router as opera_log

router = APIRouter(prefix="/logs")

router.include_router(login_log, prefix="/login", tags=["登录日志"])
router.include_router(opera_log, prefix="/opera", tags=["操作日志"])
router.include_router(chat_log, prefix="/chat", tags=["问答记录"])
router.include_router(notice_log, prefix="/notice", tags=["通知日志"])
