# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-08 21:20:49
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 21:22:19
intent_examples = """
  假设当前时间是2025-09-05 09:09:00
  示例1：
  用户输入：我想查询用户'张三','李四','王五'，国家为'中国','美国','english'，kyc为基础信息，一个月登录和5天的资金信息。
  ```json
  {
    "user_query": "...",
    "selected_service": "mcp",
    "value": '',
    "confidence": 0.95,
    "reasoning": "...",
    "data_sources": ["user_login_log","user_amount_log"]
  },
  "do_next": true,
  "suggested_response": "..."
  }
  ```

  示例2：
  用户输入：用风控助手分析今天前的用户的资金情况。
  ```json
  {
    "user_query": "...",
    "selected_service": "agent",
    "value": 'ssfs_qew', // 风控助手的value值
    "confidence": 0.95,
    "reasoning": "...",
    "data_sources": ["user_amount_log"]

  },
  "do_next": true,
  "suggested_response": "..."
  }
  ```
  示例3：
  用户输入：生成一份10天内的员工登录报告。
  ```json
  {
    "user_query": "...",
    "selected_service": "report",
    "value": '',
    "confidence": 0.95,
    "reasoning": "...",
    "data_sources": ["user_login_log"]

  },
  "do_next": true,
  "suggested_response": "..."
  }
  ```
  示例4：
  用户输入：北京天气怎么样？
  ```json
  {
    "user_query": "...",
    "selected_service": "chat",
    "value": '',
    "confidence": 0.95,
    "reasoning": "...",
    "data_sources": [],
  },
  "do_next": true,
  "suggested_response": "..."
  }
  ```
  示例5：
  用户输入：查询最近7天的出入金、登录统计汇总数据
  ```json
  {
    "user_query": "...",
    "selected_service": "mcp",
    "value": '',
    "confidence": 0.95,
    "reasoning": "...",
      "data_sources": ["direct_staff_statistics"],

    },
  },
  "do_next": true,
  "suggested_response": "..."
  }
  ```
  示例6：
  用户输入：查看TA0026代理的最近30天的，客户数，出入金，交易，返佣数据
  ```json
  {
    "user_query": "...",
    "selected_service": "mcp",
    "value": '',
    "confidence": 0.95,
    "reasoning": "...",
    "data_sources": ["user_data","agent_statistics"]
  },
  "do_next": true,
  "suggested_response": "..."
  }
  ```
  示例7：
  用户输入：请帮我分析黄金的行情
  ```json
  {
    "user_query": "...",
    "selected_service": "mcp",
    "value": '',
    "confidence": 0.95,
    "reasoning": "...",
    "data_sources": ["tool_foreign_exchange_market_data"]
  },
  "do_next": true,
  "suggested_response": "..."
  }
  ```
"""

intent_parameters_examples = """
  假设当前时间是2025-09-05 09:09:00
  示例1：
  用户输入：我想查询用户'张三','李四','王五'，国家为'中国','美国','english'，kyc为基础信息，一个月登录和5天的资金信息。
  ```json
  {
    "data_sources": {
      "user_login_log": {
        "user_name": ["张三", "李四", "王五"],
        "country": ["china", "united states", "united kingdom"],
        "kyc": 2,
        "range_time": {
          "data_start_date": "2025-08-05 00:00:00",
          "data_end_date": "2025-09-05 09:09:00"
        }
      },
      "user_amount_log": {
        "user_name": ["张三", "李四", "王五"],
        "country": ["china", "united states", "united kingdom"],
        "kyc": 2,
        "range_time": {
          "data_start_date": "2025-08-30 00:00:00",
          "data_end_date": "2025-09-05 09:09:00"
        }
      }
    },
    "tip": "...."
  }
  ```

  示例2：
  用户输入：用风控助手分析今天前的用户的资金情况。
  ```json
  {
    "data_sources": {
      "user_amount_log": {
          "range_time": {
            "data_start_date": "2025-09-05 00:00:00",
            "data_end_date": "2025-09-05 09:09:00"
          }
      }
    },
    "tip": "...."
  }
  ```
  示例3：
  用户输入：生成一份10天内的员工登录报告。
  ```json
  {
    "data_sources": {
      "user_login_log": {
        "user_type": "staff",
        "range_time": {
          "data_start_date": "2025-08-30 00:00:00",
          "data_end_date": "2025-09-05 09:09:00"
        }
      }
    },
    "tip": "...."
  }
  ```

  示例4：
  用户输入：查询最近7天的出入金、登录统计汇总数据
  ```json
  {
      "data_sources": {
      "direct_staff_statistics": {
        "statistics_name": [
          "deposit_amount",
          "withdrawal_amount",
          "login_count"
        ],
        "range_time": {
          "data_start_date": "2025-08-28 00:00:00",
          "data_end_date": "2025-09-05 09:09:00"
        }
      }
    },
    "tip": "...."
  }
  ```
  示例5：
  用户输入：查看TA0026代理的最近30天的，客户数，出入金，交易，返佣数据
  ```json
  {
    "data_sources": {
      "user_data": {
        "user_name": ["TA0026"],
      },
      "agent_statistics": {
        "user_name": ["TA0026"],
        "statistics_name": [
          "customer_count",
          "total_deposit_usd",
          "total_withdrawal_usd",
          "total_rebate_usd",
          "total_trading_volume_usd",
          "total_trading_profit_usd",
          "total_trades"
        ],
        "range_time": {
          "data_start_date": "2025-08-28 00:00:00",
          "data_end_date": "2025-09-05 09:09:00"
        }
      }
    },
    "tip": "...."
  }
  ```
  示例6：
  用户输入：请使用客户风控分析CRM用户dd、172396622，近1个月的风控数据
  ```json
  {
    "data_sources": {
      "user_data": {
        "user_name": ["dd","172396622"],
        "range_time": {
          "data_start_date": "2025-08-28 00:00:00",
          "data_end_date": "2025-09-05 09:09:00"
        }
      },
      "agent_statistics": { },
    }
    "tip": "...."
  }
  ```
  示例7：
  用户输入：请帮我分析黄金的行情
  ```json
  {
    "data_sources": {
      "tool_foreign_exchange_market_data": {
        "code": ["XAUUSD"]
      }
    },
    "tip": "...."
  }
  ```
"""
