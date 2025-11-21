#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备名称提取器
从各种格式的设备信息中提取设备名称
"""

import json
import re
from typing import Dict, List, Optional


class DeviceNameExtractor:
    """设备名称提取器类"""

    def __init__(self):
        # 定义各种设备类型的正则表达式
        self.patterns = {
            "desktop": {
                "windows": r"Windows NT (\d+\.\d+)",
                "mac": r"Macintosh; Intel Mac OS X (\d+_\d+_\d+)",
                "linux": r"Linux[^;]*",
            },
            "mobile": {
                "android": r"Android[^;]*",
                "iphone": r"iPhone; CPU iPhone OS (\d+_\d+)",
                "ipad": r"iPad; CPU OS (\d+_\d+)",
            },
            "browser": {
                "chrome": r"Chrome/(\d+\.\d+\.\d+\.\d+)",
                "firefox": r"Firefox/(\d+\.\d+)",
                "safari": r"Safari/(\d+\.\d+)",
                "edge": r"Edge/(\d+\.\d+)",
            },
            "app": {
                "fxapp": r"fxapp (\w+) (\d+\.\d+\.\d+)",
                "custom_app": r"(\w+)/(\d+\.\d+\.\d+)",
            },
        }

    def extract_device_name(self, user_agent: str) -> Dict[str, str]:
        """
        从User-Agent字符串中提取设备信息

        Args:
            user_agent: User-Agent字符串

        Returns:
            包含设备信息的字典
        """
        result = {
            "original": user_agent,
            "device_type": "unknown",
            "os": "unknown",
            "os_version": "unknown",
            "browser": "unknown",
            "browser_version": "unknown",
            "app_name": "unknown",
            "app_version": "unknown",
            "device_name": "unknown",
        }

        user_agent_lower = user_agent.lower()

        # 检测设备类型
        if (
            "mobile" in user_agent_lower
            or "iphone" in user_agent_lower
            or "android" in user_agent_lower
        ):
            result["device_type"] = "mobile"
        elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
            result["device_type"] = "tablet"
        elif (
            "desktop" in user_agent_lower
            or "macintosh" in user_agent_lower
            or "windows" in user_agent_lower
        ):
            result["device_type"] = "desktop"

        # 检测操作系统
        if "windows" in user_agent_lower:
            result["os"] = "Windows"
            match = re.search(self.patterns["desktop"]["windows"], user_agent)
            if match:
                result["os_version"] = match.group(1)
        elif "macintosh" in user_agent_lower:
            result["os"] = "macOS"
            match = re.search(self.patterns["desktop"]["mac"], user_agent)
            if match:
                result["os_version"] = match.group(1).replace("_", ".")
        elif "linux" in user_agent_lower:
            result["os"] = "Linux"
            match = re.search(self.patterns["desktop"]["linux"], user_agent)
            if match:
                result["os_version"] = match.group(0)
        elif "android" in user_agent_lower:
            result["os"] = "Android"
            match = re.search(self.patterns["mobile"]["android"], user_agent)
            if match:
                result["os_version"] = match.group(0)
        elif "iphone" in user_agent_lower:
            result["os"] = "iOS"
            match = re.search(self.patterns["mobile"]["iphone"], user_agent)
            if match:
                result["os_version"] = match.group(1).replace("_", ".")

        # 检测浏览器
        if "chrome" in user_agent_lower:
            result["browser"] = "Chrome"
            match = re.search(self.patterns["browser"]["chrome"], user_agent)
            if match:
                result["browser_version"] = match.group(1)
        elif "firefox" in user_agent_lower:
            result["browser"] = "Firefox"
            match = re.search(self.patterns["browser"]["firefox"], user_agent)
            if match:
                result["browser_version"] = match.group(1)
        elif "safari" in user_agent_lower:
            result["browser"] = "Safari"
            match = re.search(self.patterns["browser"]["safari"], user_agent)
            if match:
                result["browser_version"] = match.group(1)
        elif "edge" in user_agent_lower:
            result["browser"] = "Edge"
            match = re.search(self.patterns["browser"]["edge"], user_agent)
            if match:
                result["browser_version"] = match.group(1)

        # 检测应用
        if "fxapp" in user_agent_lower:
            result["app_name"] = "fxapp"
            match = re.search(self.patterns["app"]["fxapp"], user_agent)
            if match:
                result["app_version"] = match.group(2)

        # 生成设备名称
        result["device_name"] = self._generate_device_name(result)

        return result

    def _generate_device_name(self, info: Dict[str, str]) -> str:
        """根据提取的信息生成设备名称"""
        if info["app_name"] != "unknown":
            return f"{info['app_name']} {info['app_version']}"

        if info["device_type"] == "mobile":
            if info["os"] == "iOS":
                return f"iPhone iOS {info['os_version']}"
            elif info["os"] == "Android":
                return f"Android {info['os_version']}"

        if info["device_type"] == "desktop":
            if info["os"] == "macOS":
                return f"Mac {info['os_version']}"
            elif info["os"] == "Windows":
                return f"Windows {info['os_version']}"
            elif info["os"] == "Linux":
                return f"Linux {info['os_version']}"

        if info["browser"] != "unknown":
            return f"{info['browser']} {info['browser_version']}"

        return "Unknown Device"

    def batch_extract(self, user_agents: List[str]) -> List[Dict[str, str]]:
        """批量处理多个User-Agent字符串"""
        return [self.extract_device_name(ua) for ua in user_agents]

    def filter_by_device_type(
        self, results: List[Dict[str, str]], device_type: str
    ) -> List[Dict[str, str]]:
        """按设备类型过滤结果"""
        return [r for r in results if r["device_type"] == device_type]

    def filter_by_os(
        self, results: List[Dict[str, str]], os: str
    ) -> List[Dict[str, str]]:
        """按操作系统过滤结果"""
        return [r for r in results if r["os"].lower() == os.lower()]


device_extractor = DeviceNameExtractor()
# def main():
#     """主函数，演示使用方法"""
#     # 示例数据
#     sample_user_agents = [
#         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
#         "fxapp android 1.0.30 app",
#         "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#         "Mozilla/5.0 (Android 12; Mobile; rv:109.0) Gecko/109.0 Firefox/115.0"
#     ]

#     extractor = DeviceNameExtractor()

#     print("=== 设备信息提取结果 ===\n")

#     # 处理每个User-Agent
#     results = extractor.batch_extract(sample_user_agents)

#     for i, result in enumerate(results, 1):
#         print(f"设备 {i}:")
#         print(f"  原始信息: {result['original']}")
#         print(f"  设备名称: {result['device_name']}")
#         print(f"  设备类型: {result['device_type']}")
#         print(f"  操作系统: {result['os']} {result['os_version']}")
#         print(f"  浏览器: {result['browser']} {result['browser_version']}")
#         print(f"  应用: {result['app_name']} {result['app_version']}")
#         print()

#     # 只显示设备名称
#     print("=== 仅设备名称 ===")
#     for i, result in enumerate(results, 1):
#         print(f"设备 {i}: {result['device_name']}")

#     # 按设备类型过滤
#     print("\n=== 按设备类型过滤 ===")
#     mobile_devices = extractor.filter_by_device_type(results, 'mobile')
#     print(f"移动设备 ({len(mobile_devices)}个):")
#     for device in mobile_devices:
#         print(f"  - {device['device_name']}")

#     desktop_devices = extractor.filter_by_device_type(results, 'desktop')
#     print(f"桌面设备 ({len(desktop_devices)}个):")
#     for device in desktop_devices:
#         print(f"  - {device['device_name']}")

# if __name__ == "__main__":
#     main()
