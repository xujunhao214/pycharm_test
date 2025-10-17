# @class_retry(max_retries=2)  # 最多重试2次
class TestDemo:
    def test_case1(self):
        print("执行测试用例1")  # 对应 test_case1
        # 模拟异常（用于验证重试）
        assert 1 == 2, "用例1故意失败，验证重试"

    def test_case2(self):
        print("执行测试用例2")  # 对应 test_case2
        assert True  # 正常通过

    def test_case3(self):
        print("执行测试用例3")  # 对应 test_case3，仅在该用例执行时打印
        assert True  # 正常通过
