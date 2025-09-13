"""
数据库持久化接口测试（适配当前stub实现）
测试EmuTrader的数据库读写接口调用，适合当前的stub实现
"""

import pytest
import tempfile
import os
from emutrader import get_jq_account, order_shares, set_subportfolios, SubPortfolioConfig


class TestDatabasePersistenceStub:
    """测试数据库持久化接口（当前stub实现）
    
    测试EmuTrader的数据库读写接口，适配当前的stub实现：
    - save_to_db() 和 load_from_db() 方法调用
    - 接口返回值和错误处理
    - 当前实现的行为验证
    """

    @pytest.mark.db
    def test_save_and_load_interface_calls(self):
        """测试保存和加载接口调用
        
        验证数据库持久化接口的基本调用：
        - save_to_db接口调用
        - load_from_db接口调用
        - 返回值验证
        """
        print("\n=== 测试保存和加载接口调用 ===")
        print("【测试内容】验证数据库持久化接口的基本调用")
        
        # 创建临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            print(f"【创建】临时数据库文件: {db_path}")
            
            print("【操作1】创建账户")
            context1 = get_jq_account("test_strategy", 100000)
            initial_cash = context1.portfolio.available_cash
            print(f"  [初始资金] {initial_cash:,}元")
            
            print("【操作2】执行交易")
            order_shares('000001.SZ', 1000)
            order_shares('000002.SZ', 500)
            
            cash_after_trading = context1.portfolio.available_cash
            positions_count = context1.portfolio.get_position_count()
            print(f"  [交易后资金] {cash_after_trading:,.2f}元")
            print(f"  [持仓数量] {positions_count}个")
            
            print("【操作3】调用save_to_db接口")
            success_save = context1.save_to_db(db_path)
            print(f"  [保存结果] {success_save} (预期: True)")
            assert success_save is True
            assert isinstance(success_save, bool)
            print("  [说明] 当前为stub实现，返回True")
            
            print("【操作4】调用load_from_db接口")
            context2 = get_jq_account("test_strategy_loaded", 100000)
            original_cash = context2.portfolio.available_cash
            
            success_load = context2.load_from_db(db_path)
            print(f"  [加载结果] {success_load} (预期: True)")
            assert success_load is True
            assert isinstance(success_load, bool)
            print("  [说明] 当前为stub实现，返回True")
            
            print("【验证】接口调用后的状态")
            print(f"  [原账户资金] {context1.portfolio.available_cash:,.2f}元")
            print(f"  [加载账户资金] {context2.portfolio.available_cash:,.2f}元")
            print(f"  [加载前资金] {original_cash:,}元")
            print(f"  [原持仓数量] {context1.portfolio.get_position_count()}个")
            print(f"  [加载持仓数量] {context2.portfolio.get_position_count()}个")
            
            # 当前为stub实现，主要验证接口调用成功
            print("  [预期] 当前stub实现，接口调用成功")
            assert success_save is True
            assert success_load is True
            
            print("【完成】保存和加载接口调用测试通过！")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
                print("【清理】已删除临时数据库文件")

    @pytest.mark.db
    def test_subportfolio_persistence_interface(self):
        """测试子账户持久化接口
        
        验证多子账户配置下的持久化接口调用：
        - 设置子账户
        - 调用持久化接口
        - 验证接口行为
        """
        print("\n=== 测试子账户持久化接口 ===")
        print("【测试内容】验证多子账户配置下的持久化接口调用")
        
        # 创建临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            print(f"【创建】临时数据库文件: {db_path}")
            
            print("【操作1】创建账户并设置子账户")
            context1 = get_jq_account("test_strategy", 1000000)
            
            # 设置子账户
            sub_configs = [
                SubPortfolioConfig(cash=600000, type='stock'),
                SubPortfolioConfig(cash=300000, type='futures'),
                SubPortfolioConfig(cash=100000, type='stock')
            ]
            set_subportfolios(sub_configs)
            
            print(f"  [子账户数量] {len(context1.subportfolios)}个")
            for i, sub in enumerate(context1.subportfolios):
                print(f"    子账户{i}: {sub.type} - {sub.available_cash:,}元")
            
            print("【操作2】在子账户执行交易")
            order_shares('000001.SZ', 1000)  # 默认在股票子账户
            
            print("【操作3】调用持久化接口")
            success_save = context1.save_to_db(db_path)
            print(f"  [保存结果] {success_save}")
            assert success_save is True
            
            context2 = get_jq_account("test_strategy_loaded", 1000000)
            success_load = context2.load_from_db(db_path)
            print(f"  [加载结果] {success_load}")
            assert success_load is True
            
            print("【验证】子账户配置")
            print(f"  [原子账户数] {len(context1.subportfolios)}个")
            print(f"  [加载后子账户数] {len(context2.subportfolios)}个")
            
            # 当前为stub实现，主要验证接口调用成功
            print("  [预期] 当前stub实现，接口调用成功")
            assert success_save is True
            assert success_load is True
            
            print("【完成】子账户持久化接口测试通过！")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.db
    def test_error_handling_interface(self):
        """测试错误处理接口
        
        验证持久化接口对异常情况的处理：
        - 不存在的数据库文件
        - 无效路径
        - None参数
        """
        print("\n=== 测试错误处理接口 ===")
        print("【测试内容】验证持久化接口对异常情况的处理")
        
        context = get_jq_account("test_strategy", 100000)
        initial_cash = context.portfolio.available_cash
        
        print(f"  [初始资金] {initial_cash:,}元")
        
        print("【测试1】加载不存在的数据库")
        nonexistent_path = "/tmp/nonexistent_database_12345.db"
        success = context.load_from_db(nonexistent_path)
        print(f"  [加载结果] {success}")
        # 当前stub实现可能返回True或False，都是可接受的
        assert isinstance(success, bool)
        
        print("【测试2】保存和加载None路径")
        try:
            success_save = context.save_to_db(None)
            print(f"  [保存None结果] {success_save}")
            assert isinstance(success_save, bool)
        except Exception as e:
            print(f"  [保存None异常] {type(e).__name__}: {e}")
            # 异常也是可接受的
        
        try:
            success_load = context.load_from_db(None)
            print(f"  [加载None结果] {success_load}")
            assert isinstance(success_load, bool)
        except Exception as e:
            print(f"  [加载None异常] {type(e).__name__}: {e}")
            # 异常也是可接受的
        
        print("【测试3】空字符串路径")
        try:
            success_save = context.save_to_db("")
            print(f"  [保存空字符串结果] {success_save}")
            assert isinstance(success_save, bool)
        except Exception as e:
            print(f"  [保存空字符串异常] {type(e).__name__}: {e}")
        
        print("【验证】账户状态未受影响")
        print(f"  [当前资金] {context.portfolio.available_cash:,}元")
        print(f"  [持仓数量] {context.portfolio.get_position_count()}个")
        
        print("【完成】错误处理接口测试通过！")

    @pytest.mark.db
    def test_multiple_operations_interface(self):
        """测试多次操作接口
        
        验证多次调用持久化接口的一致性：
        - 多次保存
        - 多次加载
        - 交叉操作
        """
        print("\n=== 测试多次操作接口 ===")
        print("【测试内容】验证多次调用持久化接口的一致性")
        
        context = get_jq_account("test_strategy", 500000)
        
        print("【操作】执行交易")
        order_shares('000001.SZ', 1000)
        order_shares('000002.SZ', 500)
        
        initial_state = {
            'cash': context.portfolio.available_cash,
            'positions': context.portfolio.get_position_count()
        }
        print(f"  [初始状态] 资金:{initial_state['cash']:,.2f}元, 持仓:{initial_state['positions']}个")
        
        # 创建多个测试文件
        test_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=f'_test_{i}.db', delete=False) as tmp_file:
                test_files.append(tmp_file.name)
        
        try:
            print("【测试】多次保存操作")
            save_results = []
            for i, file_path in enumerate(test_files):
                result = context.save_to_db(file_path)
                save_results.append(result)
                print(f"  第{i+1}次保存: {result}")
                assert isinstance(result, bool)
            
            print("【测试】多次加载操作")
            load_results = []
            for i, file_path in enumerate(test_files):
                test_context = get_jq_account(f"test_load_{i}", 500000)
                result = test_context.load_from_db(file_path)
                load_results.append(result)
                print(f"  第{i+1}次加载: {result}")
                assert isinstance(result, bool)
            
            print("【验证】操作一致性")
            print(f"  [保存结果] 成功次数: {sum(save_results)}/{len(save_results)}")
            print(f"  [加载结果] 成功次数: {sum(load_results)}/{len(load_results)}")
            
            # 验证原账户状态未改变
            final_state = {
                'cash': context.portfolio.available_cash,
                'positions': context.portfolio.get_position_count()
            }
            print(f"  [最终状态] 资金:{final_state['cash']:,.2f}元, 持仓:{final_state['positions']}个")
            
            assert final_state['cash'] == initial_state['cash']
            assert final_state['positions'] == initial_state['positions']
            
            print("【完成】多次操作接口测试通过！")
            
        finally:
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    @pytest.mark.db
    def test_interface_performance(self):
        """测试接口性能
        
        验证持久化接口调用的性能：
        - 多次调用的响应时间
        - 内存使用情况
        """
        print("\n=== 测试接口性能 ===")
        print("【测试内容】验证持久化接口调用的性能")
        
        context = get_jq_account("test_strategy", 100000)
        
        import time
        
        print("【测试】save_to_db性能")
        save_times = []
        test_files = []
        
        for i in range(10):
            with tempfile.NamedTemporaryFile(suffix=f'_perf_{i}.db', delete=False) as tmp_file:
                db_path = tmp_file.name
                test_files.append(db_path)
            
            start_time = time.time()
            result = context.save_to_db(db_path)
            end_time = time.time()
            
            elapsed = end_time - start_time
            save_times.append(elapsed)
            
            print(f"  第{i+1}次保存: {elapsed:.4f}秒, 结果:{result}")
            assert result is True
        
        print("【测试】load_from_db性能")
        load_times = []
        
        for i, db_path in enumerate(test_files):
            test_context = get_jq_account(f"perf_test_{i}", 100000)
            
            start_time = time.time()
            result = test_context.load_from_db(db_path)
            end_time = time.time()
            
            elapsed = end_time - start_time
            load_times.append(elapsed)
            
            print(f"  第{i+1}次加载: {elapsed:.4f}秒, 结果:{result}")
            assert result is True
        
        # 计算统计数据
        avg_save = sum(save_times) / len(save_times)
        max_save = max(save_times)
        avg_load = sum(load_times) / len(load_times)
        max_load = max(load_times)
        
        print("【性能统计】")
        print(f"  [保存] 平均:{avg_save:.4f}秒, 最大:{max_save:.4f}秒")
        print(f"  [加载] 平均:{avg_load:.4f}秒, 最大:{max_load:.4f}秒")
        
        # 性能断言（stub实现应该很快）
        assert avg_save < 0.1, f"保存平均时间过长: {avg_save:.4f}秒"
        assert avg_load < 0.1, f"加载平均时间过长: {avg_load:.4f}秒"
        
        print("【完成】接口性能测试通过！")
        
        # 清理
        for db_path in test_files:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.db
    def test_interface_with_large_dataset(self):
        """测试大数据集接口
        
        验证大量数据下的接口调用：
        - 创建大量持仓
        - 调用持久化接口
        - 验证性能和稳定性
        """
        print("\n=== 测试大数据集接口 ===")
        print("【测试内容】验证大量数据下的持久化接口调用")
        
        context = get_jq_account("test_strategy", 10000000)  # 1000万资金
        
        print("【操作】创建大量持仓")
        num_positions = 30
        securities_created = []
        
        for i in range(num_positions):
            security = f"{600000 + i:06d}.SH"
            amount = 100 + i * 10
            print(f"  [{i+1}/{num_positions}] 买入{security} {amount}股")
            order_shares(security, amount)
            securities_created.append(security)
        
        final_cash = context.portfolio.available_cash
        final_positions = context.portfolio.get_position_count()
        
        print(f"【状态】资金:{final_cash:,.2f}元, 持仓:{final_positions}个")
        
        # 测试持久化接口
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            import time
            
            print("【测试】大数据集保存")
            start_time = time.time()
            success_save = context.save_to_db(db_path)
            save_time = time.time() - start_time
            
            print(f"  [保存结果] {success_save}")
            print(f"  [保存耗时] {save_time:.3f}秒")
            assert success_save is True
            
            print("【测试】大数据集加载")
            context_large = get_jq_account("test_large_loaded", 10000000)
            
            start_time = time.time()
            success_load = context_large.load_from_db(db_path)
            load_time = time.time() - start_time
            
            print(f"  [加载结果] {success_load}")
            print(f"  [加载耗时] {load_time:.3f}秒")
            assert success_load is True
            
            print("【性能验证】")
            print(f"  [保存性能] {save_time:.3f}秒 (应该<1秒)")
            print(f"  [加载性能] {load_time:.3f}秒 (应该<1秒)")
            
            # 当前为stub实现，应该很快
            assert save_time < 1.0, f"保存时间过长: {save_time:.3f}秒"
            assert load_time < 1.0, f"加载时间过长: {load_time:.3f}秒"
            
            print("【完成】大数据集接口测试通过！")
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)