# commons/variable_manager.py
import json
import os
import logging
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class VariableManager:
    """变量管理类：负责读取、存储和管理测试变量"""

    def __init__(self, var_file: str = "test_vars.json"):
        """
        初始化变量管理器

        Args:
            var_file: 变量文件路径
        """
        self.var_file = var_file
        self.variables: Dict[str, Any] = {}
        self.load_variables()

    def load_variables(self) -> None:
        """从文件加载变量"""
        if os.path.exists(self.var_file):
            try:
                with open(self.var_file, 'r', encoding='utf-8') as f:
                    self.variables = json.load(f)
                logger.info(f"从 {self.var_file} 加载 {len(self.variables)} 个变量")
            except json.JSONDecodeError:
                logger.error(f"变量文件 {self.var_file} 格式错误，创建新的变量文件")
                self.variables = {}
            except Exception as e:
                logger.error(f"加载变量文件失败: {str(e)}")
                self.variables = {}
        else:
            logger.info(f"变量文件 {self.var_file} 不存在，创建新的变量文件")
            self.save_variables()

    def save_variables(self) -> None:
        """保存变量到文件"""
        try:
            with open(self.var_file, 'w', encoding='utf-8') as f:
                json.dump(self.variables, f, ensure_ascii=False, indent=2)
            logger.info(f"保存 {len(self.variables)} 个变量到 {self.var_file}")
        except Exception as e:
            logger.error(f"保存变量文件失败: {str(e)}")

    def set_variable(self, name: str, value: Any) -> None:
        """设置变量"""
        self.variables[name] = value
        self.save_variables()
        logger.info(f"设置变量: {name} = {value}")

    def get_variable(self, name: str, default: Optional[Any] = None) -> Any:
        """获取变量"""
        value = self.variables.get(name, default)
        logger.info(f"获取变量 {name}: {value}")
        return value

    def delete_variable(self, name: str) -> None:
        """删除变量"""
        if name in self.variables:
            del self.variables[name]
            self.save_variables()
            logger.info(f"删除变量: {name}")

    def clear_variables(self) -> None:
        """清空所有变量"""
        self.variables = {}
        self.save_variables()
        logger.info("清空所有变量")
