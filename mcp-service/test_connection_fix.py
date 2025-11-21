#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库连接修复
"""
import asyncio
import sys

import aiomysql

from db.warehouse import warehouse_db


async def test_connection_validation():
    """测试连接验证机制"""
    print("1. 测试连接验证机制...")
    try:
        # 初始化连接池
        await warehouse_db.initialize()
        print("✓ 连接池初始化成功")

        # 获取连接并验证
        conn = await warehouse_db.get_valid_connection()
        print("✓ 获取到有效连接")

        # 验证连接
        is_valid = await warehouse_db.verify_connection(conn)
        if is_valid:
            print("✓ 连接验证成功")
            warehouse_db.pool.release(conn)
        else:
            print("✗ 连接验证失败")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

    return True


async def test_connection_context_manager():
    """测试连接上下文管理器"""
    print("\n2. 测试连接上下文管理器...")
    try:
        async with warehouse_db.connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT 1 as test")
                result = await cursor.fetchone()
                if result and result.get("test") == 1:
                    print("✓ 上下文管理器工作正常")
                    return True
                else:
                    print("✗ 查询结果异常")
                    return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def test_execute_query():
    """测试执行查询"""
    print("\n3. 测试执行查询...")
    try:
        result = await warehouse_db.execute_query("SELECT 1 as test")
        if result and len(result) > 0 and result[0].get("test") == 1:
            print("✓ 查询执行成功")
            return True
        else:
            print("✗ 查询结果异常")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def test_connection_retry():
    """测试连接重试机制"""
    print("\n4. 测试连接重试机制...")
    try:
        # 测试获取连接的重试机制
        conn1 = await warehouse_db.get_valid_connection()
        print("✓ 第一次获取连接成功")

        # 释放连接
        warehouse_db.pool.release(conn1)

        # 再次获取连接
        conn2 = await warehouse_db.get_valid_connection()
        print("✓ 第二次获取连接成功")

        warehouse_db.pool.release(conn2)
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("数据库连接修复测试")
    print("=" * 50)

    tests = [
        ("连接验证机制", test_connection_validation),
        ("连接上下文管理器", test_connection_context_manager),
        ("执行查询", test_execute_query),
        ("连接重试机制", test_connection_retry),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))

    # 清理
    try:
        await warehouse_db.close()
    except:
        pass

    # 输出结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败，请检查问题")
    print("=" * 50)

    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试异常: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
