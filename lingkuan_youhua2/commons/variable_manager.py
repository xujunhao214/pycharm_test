import json
import os
from pathlib import Path
from typing import Dict, Any
from lingkuan_youhua2.commons.enums import Environment  # 从公共模块导入


class VariableManager:
    """变量管理类：管理测试变量，支持静态数据源和动态运行时变量"""

    def __init__(self, environment: Environment, data_source_dir: str = "VAR"):
        self.environment = environment
        self.data_source_dir = data_source_dir
        self.variables: Dict[str, Any] = {}

        # 动态变量文件路径（放入VAR目录）
        var_dir = Path(self.data_source_dir)
        var_dir.mkdir(parents=True, exist_ok=True)  # 确保VAR目录存在
        self.runtime_vars_path = str(var_dir / "runtime_vars.json")

        self._load_data_source()
        self._load_runtime_vars()

        print(f"变量管理器初始化 - 环境: {environment.value}")
        print(f"数据源目录: {data_source_dir}, 动态变量文件: {self.runtime_vars_path}")

    def _load_data_source(self):
        """加载静态数据源（test_data.json/prod_data.json）"""
        data_source_file = {
            "test": "test_data.json",
            "prod": "prod_data.json"
        }.get(self.environment.value)

        if not data_source_file:
            raise ValueError(f"不支持的环境: {self.environment.value}")

        data_source_path = os.path.join(self.data_source_dir, data_source_file)

        try:
            if os.path.exists(data_source_path):
                with open(data_source_path, "r", encoding="utf-8") as f:
                    self.variables = json.load(f)
                print(f"成功加载静态数据源: {data_source_path}, 变量数: {len(self.variables)}")
            else:
                print(f"警告: 静态数据源不存在: {data_source_path}, 将使用空变量")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"静态数据源解析失败: {e}, 路径: {data_source_path}")

    def _load_runtime_vars(self):
        """加载动态运行时变量（runtime_vars.json）"""
        if os.path.exists(self.runtime_vars_path):
            try:
                with open(self.runtime_vars_path, "r", encoding="utf-8") as f:
                    runtime_vars = json.load(f)
                    self.variables.update(runtime_vars)
                print(f"成功加载动态变量: {self.runtime_vars_path}, 变量数: {len(runtime_vars)}")
            except json.JSONDecodeError as e:
                print(f"动态变量解析失败: {e}, 将创建新文件")

    def get_variable(self, name: str) -> Any:
        """获取变量值"""
        if name not in self.variables:
            raise ValueError(f"变量不存在: {name}, 可用变量: {list(self.variables.keys())}")
        return self.variables[name]

    def set_variable(self, name: str, value: Any, save_immediately: bool = True) -> None:
        """设置变量值，支持立即保存或延迟保存"""
        self.variables[name] = value
        print(f"设置变量: {name} = {value}")

        if save_immediately:
            self.save_runtime_vars()

    def save_runtime_vars(self):
        """保存动态变量到文件"""
        try:
            # 确保VAR目录存在（双重验证）
            var_dir = Path(self.data_source_dir)
            var_dir.mkdir(parents=True, exist_ok=True)

            # 只保存动态变量（排除静态数据源中的变量）
            dynamic_vars = self._get_dynamic_variables()
            with open(self.runtime_vars_path, "w", encoding="utf-8") as f:
                json.dump(dynamic_vars, f, ensure_ascii=False, indent=2)

            print(f"动态变量已保存: {self.runtime_vars_path}, 变量数: {len(dynamic_vars)}")
        except Exception as e:
            print(f"保存动态变量失败: {e}")

    def _get_dynamic_variables(self) -> Dict[str, Any]:
        """获取动态变量（排除静态数据源中的变量）"""
        static_keys = self._get_static_variable_keys()
        return {k: v for k, v in self.variables.items() if k not in static_keys}

    def _get_static_variable_keys(self) -> list:
        """获取静态数据源中的变量键名（需根据实际数据源调整）"""
        return ["login", "new_user", "db_query", "batch_import"]
