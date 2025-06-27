# commons/variable_manager.py
import os
import json
import logging
from typing import Dict, Any, Optional

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
                logger.info(f"成功加载静态变量: {file_path}")
            except Exception as e:
                logger.error(f"静态变量加载失败: {str(e)}")
                self.static_vars = {}
        else:
            logger.warning(f"静态变量文件不存在: {file_path}")
            self.static_vars = {}

    def load_runtime_variables(self):
        """加载运行时动态变量文件"""
        file_path = os.path.join(self.data_dir, "runtime_vars.json")

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.runtime_vars = json.load(f)
                logger.info(f"成功加载运行时变量: {file_path}")
            except Exception as e:
                logger.error(f"运行时变量加载失败: {str(e)}")
                self.runtime_vars = {}
        else:
            logger.warning(f"运行时变量文件不存在: {file_path}")
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
            logger.info("运行时变量已保存")
        except Exception as e:
            logger.error(f"保存运行时变量失败: {str(e)}")

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
