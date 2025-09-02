import os
import json
import logging
from self_developed.VAR.VAR import *
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class VariableManager:
    def __init__(self, env: str = "test", data_dir: str = "VAR", test_group: str = ""):
        """
        初始化变量管理器（支持测试组隔离）

        Args:
            env: 环境标识，可选"test"或"uat"
            data_dir: 数据目录，默认"VAR"
            test_group: 测试组标识（如"vps"或"cloud"），用于隔离并行任务
        """
        self.env = env
        self.data_dir = data_dir
        self.test_group = test_group  # 新增：测试组标识，实现并行隔离
        self.static_vars = {}
        self.runtime_vars = {}
        self.load_static_variables()
        self.load_runtime_variables()

    def load_static_variables(self):
        """加载对应环境的静态变量文件"""
        static_files = {
            "test": os.path.join(self.data_dir, "test_data.json"),
            "uat": os.path.join(self.data_dir, "uat_data.json")
        }
        file_path = static_files.get(self.env, os.path.join(self.data_dir, "test_data.json"))

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.static_vars = json.load(f)
                logger.info(f"[{DATETIME_NOW}] 成功加载静态变量: {file_path}")
                # print(f"[{DATETIME_NOW}] 成功加载静态变量: {file_path}")
            except Exception as e:
                logger.error(f"[{DATETIME_NOW}] 静态变量加载失败: {str(e)}")
                self.static_vars = {}
                # print(f"[{DATETIME_NOW}] 静态变量加载失败: {str(e)}")
        else:
            logger.warning(f"[{DATETIME_NOW}] 静态变量文件不存在: {file_path}")
            self.static_vars = {}
            # print(f"[{DATETIME_NOW}] 静态变量文件不存在: {file_path}")

    def load_runtime_variables(self):
        """加载运行时动态变量文件（根据测试组隔离）"""
        # 新增：根据test_group生成独立的变量文件名
        if self.test_group:
            file_name = f"runtime_vars_{self.test_group}.json"
        else:
            file_name = "runtime_vars.json"  # 兼容旧模式
        file_path = os.path.join(self.data_dir, file_name)

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.runtime_vars = json.load(f)
                logger.info(f"[{DATETIME_NOW}] 成功加载运行时变量: {file_path}")
                # print(f"[{DATETIME_NOW}] 成功加载运行时变量: {file_path}")
            except Exception as e:
                logger.error(f"[{DATETIME_NOW}] 运行时变量加载失败: {str(e)}")
                self.runtime_vars = {}
                # print(f"[{DATETIME_NOW}] 运行时变量加载失败: {str(e)}")
        else:
            logger.warning(f"[{DATETIME_NOW}] 运行时变量文件不存在: {file_path}")
            self.runtime_vars = {}
            # print(f"[{DATETIME_NOW}] 运行时变量文件不存在: {file_path}")

    def get_variable(
            self,
            name: str,
            from_runtime: bool = False,
            default: Optional[Any] = None
    ) -> Any:
        """获取变量（逻辑不变）"""
        if from_runtime:
            return self._get_nested_variable(self.runtime_vars, name, default)
        else:
            # 先从运行时变量获取（高优先级）
            runtime_value = self._get_nested_variable(self.runtime_vars, name, None)
            if runtime_value is not None:
                return runtime_value
            # 再从静态变量获取
            return self._get_nested_variable(self.static_vars, name, default)

    def set_runtime_variable(self, name: str, value: Any) -> None:
        """设置运行时变量并保存到文件（逻辑不变）"""
        self._set_nested_variable(self.runtime_vars, name, value)
        self.save_runtime_variables()

    def save_runtime_variables(self) -> None:
        """保存运行时变量到文件（根据测试组隔离）"""
        # 新增：根据test_group生成独立的变量文件名
        if self.test_group:
            file_name = f"runtime_vars_{self.test_group}.json"
        else:
            file_name = "runtime_vars.json"
        file_path = os.path.abspath(os.path.join(self.data_dir, file_name))

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.runtime_vars, f, ensure_ascii=False, indent=2)
            logger.info(f"[{DATETIME_NOW}] 运行时变量已保存到: {file_path}")
        except Exception as e:
            logger.error(f"[{DATETIME_NOW}] 保存运行时变量失败: {str(e)}")

    # 以下方法（_get_nested_variable、_set_nested_variable等）保持不变
    def _get_nested_variable(
            self,
            data: Dict[str, Any],
            name: str,
            default: Optional[Any]
    ) -> Any:
        parts = name.split(".")
        current = data

        for part in parts:
            if part in current:
                current = current[part]
            else:
                return default

        return current

    def _set_nested_variable(self, data: Dict[str, Any], name: str, value: Any) -> None:
        parts = name.split(".")
        current = data

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def append_to_list(self, var_name: str, value: Any) -> None:
        current_value = self.get_variable(var_name, from_runtime=True, default=[])
        if not isinstance(current_value, list):
            logger.warning(f"[{DATETIME_NOW}] 变量 {var_name} 不是列表类型，将重置为列表")
            current_value = []
        current_value.append(value)
        self.set_runtime_variable(var_name, current_value)
        logger.info(f"[{DATETIME_NOW}] 向列表 {var_name} 追加值: {value}")

    def get_variable_list(self, name: str, default: List[Any] = None) -> List[Any]:
        default = default or []
        value = self.get_variable(name, from_runtime=True, default=default)
        if not isinstance(value, list):
            logger.warning(f"[{DATETIME_NOW}] 变量 {name} 不是列表类型，强制转换为列表（原值: {value}）")
            return default
        return value

    def set_batch_variables(self, var_dict: Dict[str, Any]) -> None:
        for var_name, value in var_dict.items():
            self.set_runtime_variable(var_name, value)
        self.save_runtime_variables()
        logger.info(f"[{DATETIME_NOW}] 批量设置 {len(var_dict)} 个运行时变量")

    def delete_variable(self, name: str) -> None:
        parts = name.split(".")
        current = self.runtime_vars

        try:
            for part in parts[:-1]:
                current = current[part]
            del current[parts[-1]]
            self.save_runtime_variables()
            logger.info(f"[{DATETIME_NOW}] 删除运行时变量: {name}")
        except KeyError:
            logger.warning(f"[{DATETIME_NOW}] 变量 {name} 不存在，无法删除")
        except Exception as e:
            logger.error(f"[{DATETIME_NOW}] 删除变量失败: {str(e)}")
