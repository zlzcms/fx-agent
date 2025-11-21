#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据湖查询统计分析工具
用于分析query_statistics.log文件，生成查询性能报告
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings


class QueryStatisticsAnalyzer:
    """查询统计分析器"""

    def __init__(self, log_file_path: Optional[str] = None):
        self.log_file_path = log_file_path or os.path.join(
            settings.LOG_DIR, "query_statistics.log"
        )
        self.query_stats = defaultdict(list)
        self.error_stats = defaultdict(int)
        self.table_stats = defaultdict(list)
        self.hourly_stats = defaultdict(int)

    def parse_log_file(self) -> bool:
        """解析日志文件"""
        if not os.path.exists(self.log_file_path):
            print(f"日志文件不存在: {self.log_file_path}")
            return False

        try:
            with open(self.log_file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        if "QUERY_STAT:" in line:
                            # 提取JSON部分
                            json_start = line.find("QUERY_STAT:") + len("QUERY_STAT:")
                            json_str = line[json_start:].strip()
                            data = json.loads(json_str)
                            self._process_log_entry(data)
                    except json.JSONDecodeError as e:
                        print(f"第{line_num}行JSON解析错误: {e}")
                        continue
                    except Exception as e:
                        print(f"第{line_num}行处理错误: {e}")
                        continue
            return True
        except Exception as e:
            print(f"读取日志文件错误: {e}")
            return False

    def _process_log_entry(self, data: Dict[str, Any]):
        """处理单条日志记录"""
        event = data.get("event")

        if event == "QUERY_SUMMARY":
            query_type = data.get("query_type", "unknown")
            execution_time = data.get("execution_time", 0)
            row_count = data.get("row_count", 0)
            table_name = data.get("table_name", "unknown")
            status = data.get("status", "unknown")
            timestamp = data.get("timestamp")

            # 记录查询统计
            self.query_stats[query_type].append(
                {
                    "execution_time": execution_time,
                    "row_count": row_count,
                    "table_name": table_name,
                    "status": status,
                    "timestamp": timestamp,
                }
            )

            # 记录表统计
            self.table_stats[table_name].append(
                {
                    "execution_time": execution_time,
                    "row_count": row_count,
                    "query_type": query_type,
                    "status": status,
                    "timestamp": timestamp,
                }
            )

            # 记录错误统计
            if status == "ERROR":
                self.error_stats[query_type] += 1

            # 记录小时统计
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    hour_key = dt.strftime("%Y-%m-%d %H:00")
                    self.hourly_stats[hour_key] += 1
                except:
                    pass

    def generate_summary_report(self) -> str:
        """生成汇总报告"""
        report = []
        report.append("=" * 80)
        report.append("数据湖查询统计报告")
        report.append("=" * 80)
        report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"日志文件: {self.log_file_path}")
        report.append("")

        # 总体统计
        total_queries = sum(len(queries) for queries in self.query_stats.values())
        total_errors = sum(self.error_stats.values())
        success_rate = (
            ((total_queries - total_errors) / total_queries * 100)
            if total_queries > 0
            else 0
        )

        report.append("总体统计:")
        report.append(f"  总查询次数: {total_queries}")
        report.append(f"  成功查询: {total_queries - total_errors}")
        report.append(f"  失败查询: {total_errors}")
        report.append(f"  成功率: {success_rate:.2f}%")
        report.append("")

        return "\n".join(report)

    def generate_query_type_report(self) -> str:
        """生成查询类型报告"""
        report = []
        report.append("查询类型统计:")
        report.append("-" * 60)

        for query_type, queries in sorted(self.query_stats.items()):
            if not queries:
                continue

            execution_times = [
                q["execution_time"] for q in queries if q["execution_time"] > 0
            ]
            row_counts = [q["row_count"] for q in queries]
            success_count = len([q for q in queries if q["status"] == "SUCCESS"])
            error_count = len([q for q in queries if q["status"] == "ERROR"])

            report.append(f"查询类型: {query_type}")
            report.append(f"  总次数: {len(queries)}")
            report.append(f"  成功: {success_count}")
            report.append(f"  失败: {error_count}")

            if execution_times:
                avg_time = sum(execution_times) / len(execution_times)
                max_time = max(execution_times)
                min_time = min(execution_times)
                report.append(f"  平均执行时间: {avg_time:.4f}秒")
                report.append(f"  最大执行时间: {max_time:.4f}秒")
                report.append(f"  最小执行时间: {min_time:.4f}秒")

            if row_counts:
                avg_rows = sum(row_counts) / len(row_counts)
                max_rows = max(row_counts)
                total_rows = sum(row_counts)
                report.append(f"  平均返回行数: {avg_rows:.1f}")
                report.append(f"  最大返回行数: {max_rows}")
                report.append(f"  总返回行数: {total_rows}")

            report.append("")

        return "\n".join(report)

    def generate_table_report(self) -> str:
        """生成表统计报告"""
        report = []
        report.append("数据表统计:")
        report.append("-" * 60)

        for table_name, queries in sorted(self.table_stats.items()):
            if not queries:
                continue

            execution_times = [
                q["execution_time"] for q in queries if q["execution_time"] > 0
            ]
            row_counts = [q["row_count"] for q in queries]
            query_types = set(q["query_type"] for q in queries)

            report.append(f"表名: {table_name}")
            report.append(f"  查询次数: {len(queries)}")
            report.append(f"  涉及查询类型: {', '.join(sorted(query_types))}")

            if execution_times:
                avg_time = sum(execution_times) / len(execution_times)
                max_time = max(execution_times)
                min_time = min(execution_times)
                report.append(f"  平均执行时间: {avg_time:.4f}秒")
                report.append(f"  最大执行时间: {max_time:.4f}秒")
                report.append(f"  最小执行时间: {min_time:.4f}秒")

            if row_counts:
                avg_rows = sum(row_counts) / len(row_counts)
                max_rows = max(row_counts)
                total_rows = sum(row_counts)
                report.append(f"  平均返回行数: {avg_rows:.1f}")
                report.append(f"  最大返回行数: {max_rows}")
                report.append(f"  总返回行数: {total_rows}")

            report.append("")

        return "\n".join(report)

    def generate_performance_report(self) -> str:
        """生成性能报告"""
        report = []
        report.append("性能分析:")
        report.append("-" * 60)

        # 找出最慢的查询
        all_queries = []
        for query_type, queries in self.query_stats.items():
            for query in queries:
                if query["execution_time"] > 0:
                    all_queries.append(
                        {
                            "query_type": query_type,
                            "execution_time": query["execution_time"],
                            "row_count": query["row_count"],
                            "table_name": query["table_name"],
                            "timestamp": query["timestamp"],
                        }
                    )

        if all_queries:
            # 按执行时间排序
            all_queries.sort(key=lambda x: x["execution_time"], reverse=True)

            report.append("最慢的10个查询:")
            for i, query in enumerate(all_queries[:10], 1):
                report.append(
                    f"  {i}. {query['query_type']} - {query['execution_time']:.4f}秒 "
                    f"(表: {query['table_name']}, 行数: {query['row_count']})"
                )

            report.append("")

            # 执行时间分布
            execution_times = [q["execution_time"] for q in all_queries]
            fast_queries = len([t for t in execution_times if t < 0.1])
            medium_queries = len([t for t in execution_times if 0.1 <= t < 1.0])
            slow_queries = len([t for t in execution_times if t >= 1.0])

            report.append("执行时间分布:")
            report.append(
                f"  快速查询 (<0.1秒): {fast_queries} ({fast_queries/len(execution_times)*100:.1f}%)"
            )
            report.append(
                f"  中等查询 (0.1-1秒): {medium_queries} ({medium_queries/len(execution_times)*100:.1f}%)"
            )
            report.append(
                f"  慢查询 (>=1秒): {slow_queries} ({slow_queries/len(execution_times)*100:.1f}%)"
            )

        return "\n".join(report)

    def generate_hourly_report(self) -> str:
        """生成小时统计报告"""
        report = []
        report.append("小时查询分布:")
        report.append("-" * 60)

        if self.hourly_stats:
            sorted_hours = sorted(self.hourly_stats.items())
            for hour, count in sorted_hours:
                report.append(f"  {hour}: {count}次查询")

        return "\n".join(report)

    def generate_full_report(self) -> str:
        """生成完整报告"""
        reports = [
            self.generate_summary_report(),
            self.generate_query_type_report(),
            self.generate_table_report(),
            self.generate_performance_report(),
            self.generate_hourly_report(),
        ]

        return "\n".join(reports)

    def save_report(self, report: str, output_file: Optional[str] = None):
        """保存报告到文件"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(
                settings.LOG_DIR, f"query_report_{timestamp}.txt"
            )

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"报告已保存到: {output_file}")
        except Exception as e:
            print(f"保存报告失败: {e}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = None

    analyzer = QueryStatisticsAnalyzer(log_file)

    print("开始分析查询统计日志...")
    if not analyzer.parse_log_file():
        print("日志文件解析失败")
        return

    print("生成统计报告...")
    report = analyzer.generate_full_report()

    print("\n" + report)

    # 保存报告
    analyzer.save_report(report)


if __name__ == "__main__":
    main()
