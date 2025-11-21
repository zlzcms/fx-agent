-- 创建sys_menu表
DROP TABLE IF EXISTS sys_menu CASCADE;

CREATE TABLE sys_menu (
    id SERIAL PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    name VARCHAR(50) NOT NULL,
    path VARCHAR(200),
    sort INTEGER NOT NULL,
    icon VARCHAR(100),
    type INTEGER NOT NULL,
    component VARCHAR(255),
    perms VARCHAR(100),
    status INTEGER NOT NULL,
    display INTEGER NOT NULL,
    cache INTEGER NOT NULL,
    link TEXT,
    remark TEXT,
    parent_id INTEGER,
    created_time TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_time TIMESTAMP WITH TIME ZONE
);

-- 插入数据
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (4, '数据概览', 'Analytics', 'analytics', 0, 'ant-design:home-outlined', 1, '/dashboard/analytics/index.vue', NULL, 1, 1, 1, '', NULL, NULL, '2023-07-27T19:17:59+08:00', '2025-08-28T18:28:45.039093+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (5, '系统管理', 'System', 'system', 6, 'eos-icons:admin', 0, NULL, NULL, 1, 1, 0, '', NULL, NULL, '2023-07-27T19:23:00+08:00', '2025-08-28T17:34:07.790549+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (6, '系统部门', 'SysDept', 'sys-dept', 2, NULL, 1, '/system/dept/index.vue', NULL, 1, 1, 1, '', NULL, 5, '2023-07-27T19:23:42+08:00', '2025-08-28T18:15:08.284047+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (7, '系统用户', 'SysUser', 'sys-user', 0, NULL, 1, '/system/user/index.vue', NULL, 1, 1, 1, '', NULL, 5, '2023-07-27T19:25:13+08:00', '2025-08-28T18:14:00.920857+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (8, '系统角色', 'SysRole', 'sys-role', 1, NULL, 1, '/system/role/index.vue', NULL, 1, 1, 1, '', NULL, 5, '2023-07-27T19:25:45+08:00', '2025-08-28T18:14:14.681581+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (9, '菜单管理', 'SysMenu', 'sys-menu', 3, NULL, 1, '/system/menu/index.vue', NULL, 1, 1, 1, '', NULL, 5, '2023-07-27T19:45:29+08:00', '2025-08-28T18:24:15.372701+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (17, '系统日志', 'Log', 'log', 7, 'carbon:cloud-logging', 0, NULL, NULL, 1, 1, 0, '', NULL, NULL, '2023-07-27T19:19:59+08:00', '2025-08-28T16:27:45.210999+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (18, '登录日志', 'Login', 'login', 0, NULL, 1, '/log/login/index.vue', NULL, 1, 1, 1, NULL, NULL, 17, '2023-07-27T19:20:56+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (19, '操作日志', 'Opera', 'opera', 1, NULL, 1, '/log/opera/index.vue', NULL, 1, 1, 1, '', NULL, 17, '2023-07-27T19:21:28+08:00', '2025-08-28T18:15:34.494312+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (24, 'AI助理', 'Ai', 'Ai', 1, 'ant-design:reddit-outlined', 0, NULL, NULL, 1, 1, 1, '', NULL, NULL, '2025-06-11T14:08:20.926046+08:00', '2025-08-28T16:26:22.506973+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (25, 'AI模型', 'AiModels', 'Ai-models', 0, NULL, 1, '/ai/models/index', NULL, 1, 1, 1, '', NULL, 32, '2025-06-11T14:11:14.017343+08:00', '2025-08-28T17:36:52.120012+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (26, '助理管理', 'AiAssistants', 'Ai-assistants', 0, NULL, 1, '/ai/assistants/index', NULL, 1, 1, 1, '', NULL, 24, '2025-06-11T14:12:04.622852+08:00', '2025-08-28T17:37:18.448206+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (27, '数据源', 'AiDatasources', 'datasources', 1, NULL, 1, '/ai/datasources/list/index', NULL, 1, 1, 1, '', NULL, 32, '2025-06-11T17:21:09.121306+08:00', '2025-08-28T21:40:04.895987+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (28, '助理模板', 'AiTemplates', 'Ai-templates', 3, NULL, 1, '/ai/templates/index', NULL, 1, 1, 1, '', NULL, 32, '2025-06-11T17:28:00.330663+08:00', '2025-08-28T18:11:48.803074+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (30, 'AI服务', 'AIService', '/ai-service', 3, 'ant-design:apartment-outlined', 0, NULL, NULL, 1, 1, 1, '', NULL, NULL, '2025-08-28T17:22:48.863486+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (31, 'AI风控', 'Risk', '/risk', 4, 'ant-design:credit-card-twotone', 0, NULL, NULL, 1, 1, 1, '', NULL, NULL, '2025-08-28T17:32:52.767973+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (32, 'AI设置', 'AISetting', '/ai-setting', 5, 'ant-design:radius-setting-outlined', 0, NULL, NULL, 1, 1, 1, '', NULL, NULL, '2025-08-28T17:33:47.547642+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (33, '助理订阅', 'AISubscription', 'subscription', 1, NULL, 1, '/ai/subscription/index', NULL, 1, 1, 1, '', NULL, 24, '2025-08-28T17:41:34.759523+08:00', '2025-08-28T17:42:31.274085+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (34, '报告记录', 'AIAssistantReports', 'reports', 2, NULL, 1, '/aiassistant/reports/index', NULL, 1, 1, 1, '', NULL, 24, '2025-08-28T17:43:04.225012+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (35, 'MCP服务', 'mcp', 'mcp', 0, NULL, 1, '/un-implement', NULL, 1, 1, 1, '', NULL, 30, '2025-08-28T17:52:39.942365+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (36, '快捷指令', 'ShortcutCommand', 'shortcut-command', 1, NULL, 1, '/un-implement', NULL, 1, 1, 1, '', NULL, 30, '2025-08-28T17:59:07.009821+08:00', '2025-08-28T17:59:19.444077+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (37, '任务调度', 'SchedulerManage', 'scheduler-manage', 2, NULL, 1, '/aiservice/scheduler/manage/index', NULL, 1, 1, 1, '', NULL, 30, '2025-08-28T18:01:08.215039+08:00', '2025-08-28T18:01:17.705062+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (38, '任务记录', 'SchedulerRecord', 'scheduler-record', 0, NULL, 1, '/aiservice/scheduler/record/index', NULL, 1, 1, 1, '', NULL, 30, '2025-08-28T18:01:54.172643+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (39, '客户风控', 'RiskCustomer', 'risk-customer', 0, NULL, 1, '/risk/risk-customer/index', NULL, 1, 1, 1, '', NULL, 31, '2025-08-28T18:03:00.522373+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (40, '员工风控', 'RiskEmployee', 'risk-employee', 1, NULL, 1, '/risk/risk-employee/index', NULL, 1, 1, 1, '', NULL, 31, '2025-08-28T18:03:31.995352+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (41, '风控配置', 'RiskAssistant', 'risk-assistant', 2, NULL, 1, '/risk/risk-assistants/index', NULL, 1, 1, 1, '', NULL, 31, '2025-08-28T18:04:19.961825+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (42, '风控等级', 'RiskLevels', 'risk-levels', 3, NULL, 1, '/risk/risk-levels/index', NULL, 1, 1, 1, '', NULL, 31, '2025-08-28T18:05:08.004194+08:00', '2025-08-28T18:07:13.587328+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (43, '标签列表', 'RiskTagList', 'risk-tag-list', 4, NULL, 1, '/risk/risk-tags/index', NULL, 1, 1, 1, '', NULL, 31, '2025-08-28T18:07:51.670295+08:00', '2025-08-28T18:08:01.484974+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (44, '标签分类', 'RiskTagCategory', 'risk-tag-category', 6, NULL, 1, '/risk/risk-tag-categories/index', NULL, 1, 1, 1, '', NULL, 31, '2025-08-28T18:09:59.118815+08:00', '2025-08-28T18:10:26.413731+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (46, '助手类型', 'AIAssistantTypes', 'assistant-types', 4, NULL, 1, '/ai/assistant-types/index', NULL, 1, 1, 1, '', NULL, 32, '2025-08-28T18:13:17.787526+08:00', NULL);
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (47, '问答记录', 'QaLog', 'qa-log', 2, NULL, 1, '/un-implement', NULL, 1, 1, 1, '', NULL, 17, '2025-08-28T18:21:49.897642+08:00', '2025-08-28T18:22:06.225904+08:00');
INSERT INTO sys_menu (id, title, name, path, sort, icon, type, component, perms, status, display, cache, link, remark, parent_id, created_time, updated_time) VALUES (50, '助理编辑', 'AIAssistantEdit', 'assistants/edit/:id', 4, NULL, 1, '/ai/assistants/form', NULL, 1, 0, 1, '', NULL, 24, '2025-08-29T12:09:54.283962+08:00', NULL);

-- 重置序列
SELECT setval('sys_menu_id_seq', (SELECT MAX(id) FROM sys_menu));
