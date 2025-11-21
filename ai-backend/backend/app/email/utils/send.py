#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os.path

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiofiles

from aiosmtplib import SMTP
from jinja2 import Template
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.enums import StatusType
from backend.common.log import log
from backend.core.path_conf import PLUGIN_DIR
from backend.database.db import async_engine
from backend.plugin.config.crud.crud_config import config_dao
from backend.utils.serializers import select_list_serialize
from backend.utils.timezone import timezone


async def render_message(subject: str, from_header: str, content: str | dict, template: str | None) -> bytes:
    """
    渲染邮件内容

    :param subject: 邮件内容主题
    :param from_header: 邮件来源
    :param content: 邮件内容
    :param template: 邮件内容模板
    :return:
    """
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = from_header
    message["date"] = timezone.now().strftime("%a, %d %b %Y %H:%M:%S %z")

    if template:
        async with aiofiles.open(os.path.join(PLUGIN_DIR, "email", "templates", template), "r", encoding="utf-8") as f:
            html = Template(await f.read(), enable_async=True)
        mail_body = MIMEText(await html.render_async(**content), "html", "utf-8")
    else:
        mail_body = MIMEText(content, "plain", "utf-8")

    message.attach(mail_body)

    return message.as_bytes()


async def send_email(
    db: AsyncSession,
    recipients: str | list[str],
    subject: str,
    content: str | dict,
    template: str | None = None,
) -> tuple[bool, str, str]:
    """
    发送电子邮件

    :param db: 数据库会话
    :param recipients: 邮件接收者
    :param subject: 邮件内容主题
    :param content: 邮件内容
    :param template: 邮件内容模板
    :return: tuple[bool, str, str]: (is_success, rendered_content, failure_reason)
    """
    # 获取动态配置
    dynamic_config = None
    rendered_content = ""
    failure_reason = ""

    def get_config_table(conn):
        inspector = inspect(conn)
        return inspector.has_table("sys_config", schema=None)

    try:
        async with async_engine.begin() as coon:
            exists = await coon.run_sync(get_config_table)
            if exists:
                dynamic_config = await config_dao.get_all(db, "EMAIL")

        if not dynamic_config:
            failure_reason = "未找到邮件动态配置，请检查系统参数配置-邮件配置"
            log.error(failure_reason)
            return False, rendered_content, failure_reason

        _status_key = "EMAIL_STATUS"
        _host_key = "EMAIL_HOST"
        _port_key = "EMAIL_PORT"
        _ssl_key = "EMAIL_SSL"
        _username_key = "EMAIL_USERNAME"
        _password_key = "EMAIL_PASSWORD"

        configs = {d["key"]: d["value"] for d in select_list_serialize(dynamic_config)}

        # 检查EMAIL_STATUS，如果为false则不发送邮件
        email_status = configs.get(_status_key)
        if not email_status or email_status != str(StatusType.enable.value):
            failure_reason = "邮件发送已禁用"
            log.info(f"{failure_reason}，跳过邮件发送")
            return False, rendered_content, failure_reason

        if len(dynamic_config) < 6:
            failure_reason = "缺少邮件动态配置，请检查系统参数配置-邮件配置"
            return False, rendered_content, failure_reason

        email_host = configs.get(_host_key)
        email_port = int(configs.get(_port_key, 0))
        email_ssl = True if configs.get(_ssl_key, "") == str(StatusType.enable.value) else False
        email_username = configs.get(_username_key)
        email_password = configs.get(_password_key)

        # 参数验证
        if not all([email_host, email_port, email_username, email_password]):
            failure_reason = "邮件配置不完整，请检查邮件服务器配置"
            log.error(failure_reason)
            return False, rendered_content, failure_reason

        # 确保 recipients 是列表格式
        if isinstance(recipients, str):
            recipients_list = [recipients]
        else:
            recipients_list = recipients

        log.info(f"准备发送邮件: {subject} -> {', '.join(recipients_list)}")

        # 渲染邮件内容
        message = await render_message(subject, email_username, content, template)

        # 获取渲染后的内容用于日志记录
        if template:
            # 如果使用模板，获取渲染后的HTML内容
            import os.path

            import aiofiles

            from jinja2 import Template as JinjaTemplate

            template_path = os.path.join(PLUGIN_DIR, "email", "templates", template)
            async with aiofiles.open(template_path, "r", encoding="utf-8") as f:
                html_template = JinjaTemplate(await f.read(), enable_async=True)
            rendered_content = await html_template.render_async(**content)
        else:
            rendered_content = str(content)

        # 创建SMTP客户端，增加超时配置
        smtp_client = SMTP(
            hostname=email_host,
            port=email_port,
            use_tls=email_ssl,
            timeout=30,  # 连接超时30秒
        )

        # 使用更详细的错误处理
        async with smtp_client:
            log.debug(f"尝试连接到SMTP服务器: {email_host}:{email_port}, SSL: {email_ssl}")

            # 登录验证
            await smtp_client.login(email_username, email_password)
            log.debug(f"SMTP登录成功: {email_username}")

            # 发送邮件
            await smtp_client.sendmail(email_username, recipients_list, message)

        log.info(f"邮件发送成功: {subject} -> {', '.join(recipients_list)}")
        return True, rendered_content, ""

    except Exception as e:
        failure_reason = str(e)
        log.error(f"邮件发送失败: {failure_reason}")
        return False, rendered_content, failure_reason
