#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
滑点功能测试套件

运行所有滑点相关的测试用例。
"""

import sys
import os
import pytest

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)


def run_slippage_tests():
    """运行所有滑点测试"""
    print("=== EmuTrader 滑点功能测试套件 ===\n")
    
    # 测试文件列表
    test_files = [
        'test_slippage_core.py',
        'test_slippage_integration.py', 
        'test_jq_compatibility.py'
    ]
    
    # 构建测试路径
    test_paths = []
    for test_file in test_files:
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(test_path):
            test_paths.append(test_path)
            print(f"发现测试文件: {test_file}")
        else:
            print(f"警告: 测试文件不存在: {test_file}")
    
    if not test_paths:
        print("[FAIL] 没有找到任何测试文件")
        return False
    
    print(f"\n准备运行 {len(test_paths)} 个测试文件...\n")
    
    # 运行pytest
    try:
        # 设置pytest参数
        pytest_args = [
            '-v',  # 详细输出
            '--tb=short',  # 短格式的traceback
            '--color=yes',  # 彩色输出
        ] + test_paths
        
        # 运行测试
        exit_code = pytest.main(pytest_args)
        
        if exit_code == 0:
            print("\n[SUCCESS] 所有滑点测试通过！")
            print("\n测试覆盖范围:")
            print("[OK] 核心滑点类功能 (FixedSlippage, PriceRelatedSlippage, StepRelatedSlippage)")
            print("[OK] SlippageManager配置管理")
            print("[OK] EmuTrader集成和交易执行")
            print("[OK] JoinQuant API 100%兼容性")
            print("[OK] 错误处理和边界情况")
            print("[OK] 货币基金零滑点强制执行")
            print("[OK] 多级配置优先级系统")
            return True
        else:
            print(f"\n[FAIL] 测试失败，退出码: {exit_code}")
            return False
            
    except Exception as e:
        print(f"\n[FAIL] 运行测试时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_specific_test_category(category):
    """运行特定类别的测试"""
    print(f"=== 运行 {category} 测试 ===\n")
    
    if category == "core":
        test_file = "test_slippage_core.py"
    elif category == "integration":
        test_file = "test_slippage_integration.py"
    elif category == "compatibility":
        test_file = "test_jq_compatibility.py"
    else:
        print(f"[FAIL] 未知的测试类别: {category}")
        return False
    
    test_path = os.path.join(os.path.dirname(__file__), test_file)
    
    if not os.path.exists(test_path):
        print(f"[FAIL] 测试文件不存在: {test_file}")
        return False
    
    try:
        exit_code = pytest.main([
            '-v',
            '--tb=short',
            '--color=yes',
            test_path
        ])
        
        if exit_code == 0:
            print(f"\n[OK] {category} 测试通过！")
            return True
        else:
            print(f"\n[FAIL] {category} 测试失败，退出码: {exit_code}")
            return False
            
    except Exception as e:
        print(f"\n[FAIL] 运行 {category} 测试时发生错误: {e}")
        return False


def run_quick_verification():
    """运行快速验证测试"""
    print("=== 滑点功能快速验证 ===\n")
    
    # 导入必要的模块
    try:
        from emutrader import (
            get_jq_account, FixedSlippage, PriceRelatedSlippage, StepRelatedSlippage,
            set_slippage, order_shares
        )
        print("[OK] 成功导入所有滑点相关模块")
    except Exception as e:
        print(f"[FAIL] 模块导入失败: {e}")
        return False
    
    # 基础功能测试
    try:
        # 创建账户
        context = get_jq_account("quick_test", 100000)
        print("[OK] 成功创建策略账户")
        
        # 测试设置不同类型滑点
        set_slippage(FixedSlippage(0.02))
        set_slippage(PriceRelatedSlippage(0.001), security_type='stock')
        set_slippage(StepRelatedSlippage(2), security_type='futures')
        print("[OK] 成功设置各种类型滑点")
        
        # 验证滑点配置
        from emutrader.api import get_current_emutrader
        emu = get_current_emutrader()
        
        configs = emu.get_all_slippage_configurations()
        assert 'default' in configs
        assert 'type_configs' in configs
        print("[OK] 滑点配置管理正常")
        
        # 测试价格计算
        buy_price = emu.calculate_slippage_price('000001.SZ', 10.0, 1000, 'open', 'stock')
        sell_price = emu.calculate_slippage_price('000001.SZ', 10.0, 1000, 'close', 'stock')
        
        assert buy_price > 10.0  # 买入滑点
        assert sell_price < 10.0  # 卖出滑点
        print("[OK] 滑点价格计算正常")
        
        # 测试货币基金零滑点
        mmf_price = emu.calculate_slippage_price('511880.SH', 100.0, 1000, 'open', 'mmf')
        assert mmf_price == 100.0
        print("[OK] 货币基金零滑点正常")
        
        print("\n[SUCCESS] 快速验证通过！滑点功能正常工作")
        return True
        
    except Exception as e:
        print(f"[FAIL] 快速验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("EmuTrader 滑点功能测试")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "core":
            success = run_specific_test_category("core")
        elif command == "integration":
            success = run_specific_test_category("integration")
        elif command == "compatibility":
            success = run_specific_test_category("compatibility")
        elif command == "quick":
            success = run_quick_verification()
        else:
            print(f"未知命令: {command}")
            print("\n可用命令:")
            print("  python test_runner.py        - 运行所有测试")
            print("  python test_runner.py core    - 运行核心功能测试")
            print("  python test_runner.py integration - 运行集成测试")
            print("  python test_runner.py compatibility - 运行兼容性测试")
            print("  python test_runner.py quick   - 运行快速验证")
            success = False
    else:
        # 默认运行所有测试
        success = run_slippage_tests()
    
    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()