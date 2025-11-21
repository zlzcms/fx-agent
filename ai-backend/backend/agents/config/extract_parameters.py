from backend.agents.schema.agent import ExtractParametersConstraint

parameters_constraints = [
    ExtractParametersConstraint(
        name="user_type",
        description="请提取用户类型包括'客户'、'代理'、'员工'。没有指明用户类型默认是客户",
        required=True,
        data_type="字符串",
        validator_rules=["必须是以下定义值之一", "direct: 客户", "agent: 代理", "staff: 员工"],
        example_value="输入：查询张三信息。提取:user_type为'direct'",
    ),
    ExtractParametersConstraint(
        name="user_name",
        description="请提取用户的名称，支持多个用户名同时提取",
        data_type="列表",
        required=False,
        validator_rules=["如果只有一个用户名，仍返回数组格式"],
        example_value="输入：查询'张三','李四','王五'用户信息。提取:user_name为['张三','李四','王五']",
    ),
    ExtractParametersConstraint(
        name="user_id",
        description="请提取用户id,支持多个用户id同时提取",
        data_type="列表",
        required=False,
        validator_rules=[
            "id必须为数字",
        ],
        example_value="输入：查询'133','254','354','45','57'用户信息。提取:user_id为['133','254','354','45','57']",
    ),
    ExtractParametersConstraint(
        name="country",
        description="请提取国家名称，支持多个国家名称同时提取",
        data_type="列表",
        required=False,
        validator_rules=[
            "每个元素必须是有效的国家名称",
            "如果非标准国家的英语名称，请转换为标准英语国家名称",
        ],
        example_value="输入：查询'中国','美国','india'用户信息。提取:country为['china','united states','india']",
    ),
    ExtractParametersConstraint(
        name="kyc",
        description="请提取kyc值，包括'未KYC'、'问卷调查'、'基础信息'、'上传证件'、'签署合同'、'上传住址证明'、'KYC成功'、'KYC失败'。没有指明kyc值默认是'未KYC'",
        data_type="数字0或1",
        required=False,
        validator_rules=[
            "必须是以下预定义值之一",
            "0: 未KYC",
            "1: 问卷调查",
            "2: 基础信息",
            "3: 上传证件",
            "4: 签署合同",
            "5: 上传住址证明",
            "9: KYC成功",
            "-1: KYC失败",
        ],
        example_value="输入：查询kyc为'问卷调查'的用户信息。提取:kyc为1",
    ),
    ExtractParametersConstraint(
        name="register_time",
        description="请提取用户注册时间，默认是空",
        data_type="字典",
        required=False,
        validator_rules=[
            "必须是用户明确指明注册的用户的时候有效",
            "没有指明注册时间默认是空",
            "根据当前时间计算有效的时间格式",
            "start_date: 开始日期",
            "end_date: 结束日期",
        ],
        example_value="输入：查询一个月前注册的用户信息。假设当前时间是2024-02-01，提取:register_time为{'start_date': '2024-01-01', 'end_date': '2024-02-01'}",
    ),
    # ExtractParametersConstraint(
    #     name="range_time",
    #     description="请提取时间范围",
    #     data_type="字典",
    #     required=False,
    #     validator_rules=[
    #         "请结合当前时间提取查询时间范围条件，包括开始日期和结束日期",
    #         "start_date: 开始日期",
    #         "end_date: 结束日期",
    #     ],
    #     example_value="输入：查询一个月内注册的用户信息。假设当前时间是2024-02-01，提取:range_time为{'start_date': '2024-01-01', 'end_date': '2024-02-01'}",
    # ),
    ExtractParametersConstraint(
        name="limit",
        description="请提取限制的用户数量",
        required=False,
        data_type="数字",
        validator_rules=["必须是有效的数字"],
        example_value="输入：查询前100用户信息。提取:limit为100",
    ),
    # ExtractParametersConstraint(
    #     name="child_args",
    #     description="如果子服务中存在child_args值，提取子服务中child_args中的值",
    #     required=True,
    #     data_type="列表",
    #     validator_rules=["支持多个数据源同时提取", "必须是子服务中存在child_args值"],
    #     example_value="""假设智能助理的子服务‘客户风控助理’存在child_args值[{'user_amount_log': '资金'}, 'user_login_log':'登录'}]。
    #                      输入：客户风控助理生成一份关于用户mei1的资金报告。
    #                      提取:child_args为[{'user_amount_log': '资金'}]
    #     """,
    # ),
]


intent_recognition_parameters_constraints = [
    ExtractParametersConstraint(
        name="intent_type",
        description="请提取意图类型",
        required=True,
        data_type="select",
        required_format="单选，用户意图类型",
        validator_rules=[
            "必须是以下预定义值之一",
            "mcp<mcp服务类型>:需要查询、分析等某用户信息的时候，表示要调用mcp服务。",
            "transaction<事务操作类型>:需要生成某用户报告，风险评估某用户等要求完成一个事务操作的时候，表示要调用事务操作工具。",
            "chat<普通对话类型>:只是询问或普通对话，不需要调用mcp服务或事务操作。",
            "无法识别用户意图时候，默认是chat",
        ],
        example_value="mcp",
    ),
    ExtractParametersConstraint(
        name="confirm",
        description="是否对上一次对话进行确认",
        required=False,
        data_type="boolean",
        required_format="布尔类型，回答是或否，默认否",
        validator_rules=[
            "必须是以下预定义值之一",
            "1: 是",
            "0: 否",
            "默认否",
        ],
        example_value="1",
    ),
    ExtractParametersConstraint(
        name="tools",
        description="请提取指定的使用的工具名称，例如：assistant",
        required=False,
        data_type="dict",
        required_format="字典格式，包括工具值和工具名称",
        validator_rules=[
            "必须为以下预定义值",
            "assistant: 用户表名使用某某助手",
            "如果用户表达模糊，默认返回空",
        ],
        example_value="{{'assistant': '风控监控助手'}}",
    ),
    ExtractParametersConstraint(
        name="history_link",
        description="用于用户的历史对话识别是否与本次输入有关联",
        required=True,
        data_type="boolean",
        required_format="布尔类型，",
        validator_rules=["结合对话历史理解提取历史对话"],
        example_value="1",
    ),
]
