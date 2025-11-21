#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import task modules so they can be auto-discovered by Celery
from . import payment_tasks as payment_tasks
from . import tasks as tasks
