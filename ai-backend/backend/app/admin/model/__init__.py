# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-03 17:05:24
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from backend.app.admin.model.ai_assistant import AIAssistant, AIDataPermission, AINotificationMethod, AIPersonnel
from backend.app.admin.model.ai_assistant_data_analysis import AIDataAnalysis
from backend.app.admin.model.ai_assistant_report_log import AiAssistantReportLog
from backend.app.admin.model.ai_assistant_report_user_read import AiAssistantReportUserRead
from backend.app.admin.model.ai_model import AIModel
from backend.app.admin.model.ai_subscription import (
    AISubscription,
    AISubscriptionNotification,
    AISubscriptionNotificationMethod,
)
from backend.app.admin.model.ai_training_log import AITrainingLog
from backend.app.admin.model.api_key import ApiKey
from backend.app.admin.model.assistant_type import AssistantType
from backend.app.admin.model.data_rule import DataRule
from backend.app.admin.model.data_scope import DataScope
from backend.app.admin.model.database_metadata import DatabaseMetadata
from backend.app.admin.model.datasource import DataSource
from backend.app.admin.model.datasource_collection import DataSourceCollection
from backend.app.admin.model.dept import Dept
from backend.app.admin.model.login_log import LoginLog
from backend.app.admin.model.menu import Menu
from backend.app.admin.model.notice_log import NoticeLog
from backend.app.admin.model.opera_log import OperaLog
from backend.app.admin.model.recommended_question import RecommendedQuestion
from backend.app.admin.model.risk_assistant import RiskAssistant
from backend.app.admin.model.risk_level import RiskLevel
from backend.app.admin.model.risk_member_analysis import RiskMemberAnalysis
from backend.app.admin.model.risk_report_log import RiskReportLog
from backend.app.admin.model.risk_tag import RiskTag
from backend.app.admin.model.risk_tasks import RiskTasks
from backend.app.admin.model.role import Role
from backend.app.admin.model.user import User
