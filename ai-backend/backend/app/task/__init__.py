#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

from backend.core.path_conf import BASE_PATH

from .actions import *  # noqa: F403
from .celery import celery_app  # noqa: F401

# 导入项目根目录
sys.path.append(str(BASE_PATH.parent))
