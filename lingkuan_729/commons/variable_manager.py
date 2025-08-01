# commons/variable_manager.py
import os
import json
import logging
from lingkuan_729.VAR.VAR import *
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class VariableManager:
    def __init__(self, env: str = "test", data_dir: str = "VAR"):
        """
        初始化变量管理器

        Args:
            env: 环境标识，可选"test"或"prod"
            data_dir: 数据目录，默认"VAR"
        """
        self.env = env
        self.data_dir = data_dir
        self.static_vars = {}
        self.runtime_vars = {}
        self.load_static_variables()
        self.load_runtime_variables()

    def load_static_variables(self):
        """加载对应环境的静态变量文件"""
        static_files = {
            "test": os.path.join(self.data_dir, "test_data.json"),
            "prod": os.path.join(self.data_dir, "prod_data.json")
        }
        file_path = static_files.get(self.env, os.path.join(self.data_dir, "test_data.json"))

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.static_vars = json.load(f)
                logger.info(f"[{DATETIME_NOW}] 成功加载静态变量: {file_path}")
            except Exception as e:
                logger.error(f"[{DATETIME_NOW}] 静态变量加载失败: {str(e)}")
                self.static_vars = {}
        else:
            logger.warning(f"[{DATETIME_NOW}] 静态变量文件不存在: {file_path}")
            self.static_vars = {}

    def load_runtime_variables(self):
        """加载运行时动态变量文件"""
        file_path = os.path.join(self.data_dir, "runtime_vars.json")

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.runtime_vars = json.load(f)
                logger.info(f"[{DATETIME_NOW}] 成功加载运行时变量: {file_path}")
            except Exception as e:
                logger.error(f"[{DATETIME_NOW}] 运行时变量加载失败: {str(e)}")
                self.runtime_vars = {}
        else:
            logger.warning(f"[{DATETIME_NOW}] 运行时变量文件不存在: {file_path}")
            self.runtime_vars = {}

    def get_variable(
            self,
            name: str,
            from_runtime: bool = False,
            default: Optional[Any] = None
    ) -> Any:
        """
        获取变量

        Args:
            name: 变量名，支持点号分隔的嵌套路径
            from_runtime: 是否从运行时变量获取，默认False（从静态变量获取）
            default: 变量不存在时的默认值

        Returns:
            变量值或默认值
        """
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
        """设置运行时变量并保存到文件"""
        self._set_nested_variable(self.runtime_vars, name, value)
        self.save_runtime_variables()

    def save_runtime_variables(self) -> None:
        """保存运行时变量到文件"""
        file_path = os.path.abspath("VAR/runtime_vars.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.runtime_vars, f, ensure_ascii=False, indent=2)
            logger.info(f"[{DATETIME_NOW}] 运行时变量已保存")
        except Exception as e:
            logger.error(f"[{DATETIME_NOW}] 保存运行时变量失败: {str(e)}")

    def _get_nested_variable(
            self,
            data: Dict[str, Any],
            name: str,
            default: Optional[Any]
    ) -> Any:
        """获取嵌套变量（支持点号分隔路径）"""
        parts = name.split(".")
        current = data

        for part in parts:
            if part in current:
                current = current[part]
            else:
                return default

        return current

    def _set_nested_variable(self, data: Dict[str, Any], name: str, value: Any) -> None:
        """设置嵌套变量"""
        parts = name.split(".")
        current = data

        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def append_to_list(self, var_name: str, value: Any) -> None:
        """
        向列表变量追加值

        Args:
            var_name: 变量名，支持点号分隔的嵌套路径
            value: 要追加的值
        """
        # 获取当前变量值
        current_value = self.get_variable(var_name, from_runtime=True, default=[])

        # 确保变量是列表类型
        if not isinstance(current_value, list):
            logger.warning(f"[{DATETIME_NOW}] 变量 {var_name} 不是列表类型，将重置为列表")
            current_value = []

        # 追加新值
        current_value.append(value)

        # 更新变量
        self.set_runtime_variable(var_name, current_value)
        logger.info(f"[{DATETIME_NOW}] 向列表 {var_name} 追加值: {value}")

    def get_variable_list(self, name: str, default: List[Any] = None) -> List[Any]:
        """
        获取列表类型的变量（自动转换非列表类型为列表）

        Args:
            name: 变量名，支持点号分隔的嵌套路径
            default: 变量不存在或非列表时的默认值，默认为空列表

        Returns:
            列表类型的变量值
        """
        default = default or []
        value = self.get_variable(name, from_runtime=True, default=default)

        # 确保返回值为列表类型
        if not isinstance(value, list):
            logger.warning(f"[{DATETIME_NOW}] 变量 {name} 不是列表类型，强制转换为列表（原值: {value}）")
            return default
        return value

    def set_batch_variables(self, var_dict: Dict[str, Any]) -> None:
        """
        批量设置运行时变量

        Args:
            var_dict: 变量字典，格式为 {变量名: 值, ...}
        """
        for var_name, value in var_dict.items():
            self.set_runtime_variable(var_name, value)
        self.save_runtime_variables()
        logger.info(f"[{DATETIME_NOW}] 批量设置 {len(var_dict)} 个运行时变量")

    def delete_variable(self, name: str) -> None:
        """
        删除运行时变量

        Args:
            name: 要删除的变量名
        """
        parts = name.split(".")
        current = self.runtime_vars

        try:
            # 导航到嵌套变量的父级
            for part in parts[:-1]:
                current = current[part]

            # 删除目标变量
            del current[parts[-1]]
            self.save_runtime_variables()
            logger.info(f"[{DATETIME_NOW}] 删除运行时变量: {name}")
        except KeyError:
            logger.warning(f"[{DATETIME_NOW}] 变量 {name} 不存在，无法删除")
        except Exception as e:
            logger.error(f"[{DATETIME_NOW}] 删除变量失败: {str(e)}")
