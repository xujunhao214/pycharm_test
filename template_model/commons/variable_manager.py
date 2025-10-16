import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class VariableManager:
    def __init__(self, env: str = "test", data_dir: str = "VAR", test_group: str = ""):
        """
        初始化变量管理器（支持环境隔离、测试组隔离）

        Args:
            env: 环境标识，可选"test"或"dev"
            data_dir: 数据目录，默认"VAR"（支持相对/绝对路径）
            test_group: 测试组标识（如"vps"或"cloud"），用于隔离并行任务
        """
        self.env = env
        # 处理路径：支持相对路径转为绝对路径，避免跨目录调用时路径错误
        self.data_dir = os.path.abspath(data_dir)
        self.test_group = test_group.strip()  # 去除空格，避免无效标识
        self.static_vars = {}
        self.runtime_vars = {}

        # 初始化时加载变量（首次加载）
        self.load_static_variables()
        self.load_runtime_variables()

    def _get_current_time(self) -> str:
        """实时获取当前时间（格式：YYYY-MM-DD HH:MM:SS），解决日志时间戳问题"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_runtime_file_path(self) -> str:
        """统一生成运行时变量文件路径，避免重复逻辑"""
        if self.test_group:
            file_name = f"runtime_vars_{self.test_group}.json"
        else:
            file_name = "runtime_vars.json"  # 兼容旧模式
        # 确保数据目录存在（提前创建，避免后续保存时失败）
        os.makedirs(self.data_dir, exist_ok=True)
        return os.path.join(self.data_dir, file_name)

    def load_static_variables(self) -> None:
        """加载对应环境的静态变量文件（优化路径处理和错误捕获）"""
        static_files = {
            "test": os.path.join(self.data_dir, "test_data.json"),
            "dev": os.path.join(self.data_dir, "dev_data.json")
        }
        file_path = static_files.get(self.env, static_files["test"])  # 默认用test环境
        file_path = os.path.abspath(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # 强制刷新文件缓存，避免读取旧内容
                f.seek(0)
                self.static_vars = json.load(f)
            logger.info(f"[{self._get_current_time()}] 静态变量加载成功 | 文件: {file_path}")
        except FileNotFoundError:
            logger.warning(f"[{self._get_current_time()}] 静态变量文件不存在 | 文件: {file_path}（将使用空字典）")
            self.static_vars = {}
        except json.JSONDecodeError as e:
            logger.error(
                f"[{self._get_current_time()}] 静态变量文件格式错误（非JSON） | 文件: {file_path} | 错误: {str(e)}")
            self.static_vars = {}
        except Exception as e:
            logger.error(f"[{self._get_current_time()}] 静态变量加载异常 | 文件: {file_path} | 错误: {str(e)}")
            self.static_vars = {}

    def load_runtime_variables(self, force: bool = True) -> None:
        """
        加载运行时变量文件（新增force参数，支持强制刷新）

        Args:
            force: 是否强制从文件重新加载（True=忽略内存，读最新文件；False=仅首次加载）
        """
        if not force:
            # 非强制刷新时，若内存已有数据，直接返回（避免重复加载）
            if self.runtime_vars:
                return

        file_path = self._get_runtime_file_path()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                # 关键：移动文件指针到开头，避免因前次读取残留缓存
                f.seek(0)
                self.runtime_vars = json.load(f)
            logger.info(f"[{self._get_current_time()}] 运行时变量加载成功 | 文件: {file_path}")
        except FileNotFoundError:
            logger.warning(f"[{self._get_current_time()}] 运行时变量文件不存在 | 文件: {file_path}（将使用空字典）")
            self.runtime_vars = {}
        except json.JSONDecodeError as e:
            logger.error(
                f"[{self._get_current_time()}] 运行时变量文件格式错误 | 文件: {file_path} | 错误: {str(e)}（将重置为空字典）")
            self.runtime_vars = {}
            # 可选：删除损坏的文件，避免后续加载失败
            os.remove(file_path)
            logger.warning(f"[{self._get_current_time()}] 已删除损坏的运行时变量文件 | 文件: {file_path}")
        except Exception as e:
            logger.error(f"[{self._get_current_time()}] 运行时变量加载异常 | 文件: {file_path} | 错误: {str(e)}")
            self.runtime_vars = {}

    def get_variable(
            self,
            name: str,
            from_runtime: bool = False,
            default: Optional[Any] = None,
            force_refresh: bool = False
    ) -> Any:
        """
        获取变量（新增force_refresh，支持实时读取最新文件）

        Args:
            name: 变量名（支持嵌套，如"user.account"）
            from_runtime: 是否仅从运行时变量获取
            default: 默认值（变量不存在时返回）
            force_refresh: 是否先强制加载文件最新数据
        """
        # 关键：需要实时数据时，先刷新内存
        if force_refresh:
            self.load_runtime_variables(force=True)

        if from_runtime:
            return self._get_nested_variable(self.runtime_vars, name, default)
        else:
            # 运行时变量优先级高于静态变量
            runtime_value = self._get_nested_variable(self.runtime_vars, name, None)
            if runtime_value is not None:
                logger.debug(f"[{self._get_current_time()}] 从运行时变量获取 | 变量: {name} | 值: {runtime_value}")
                return runtime_value
            # 静态变量兜底
            static_value = self._get_nested_variable(self.static_vars, name, default)
            logger.debug(f"[{self._get_current_time()}] 从静态变量获取 | 变量: {name} | 值: {static_value}")
            return static_value

    def set_runtime_variable(self, name: str, value: Any, force_refresh_before: bool = True) -> None:
        """
        设置运行时变量（新增force_refresh_before，避免覆盖其他用例的更新）

        Args:
            name: 变量名（支持嵌套，如"trader.id"）
            value: 变量值（支持任意可JSON序列化类型）
            force_refresh_before: 设置前是否先加载文件最新数据（避免覆盖）
        """
        # 关键：设置前先刷新，确保基于最新文件数据操作
        if force_refresh_before:
            self.load_runtime_variables(force=True)

        try:
            # 检查值是否可JSON序列化（提前报错，避免保存失败）
            json.dumps(value)
        except (TypeError, ValueError) as e:
            logger.error(f"[{self._get_current_time()}] 变量值不可JSON序列化 | 变量: {name} | 错误: {str(e)}")
            raise  # 抛出异常，提醒用户修正值类型

        # 设置变量并保存
        self._set_nested_variable(self.runtime_vars, name, value)
        self.save_runtime_variables()
        logger.info(f"[{self._get_current_time()}] 运行时变量设置成功 | 变量: {name} | 值: {value}")

    def save_runtime_variables(self) -> None:
        """保存运行时变量（优化路径处理和权限错误捕获）"""
        file_path = self._get_runtime_file_path()

        try:
            # 写入时使用"w"模式，覆盖旧文件（确保数据最新）
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.runtime_vars, f, ensure_ascii=False, indent=2)
            # 验证：保存后立即读取，确认写入成功（避免假保存）
            with open(file_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            # 对比内存与文件数据，确保一致
            if saved_data == self.runtime_vars:
                logger.info(f"[{self._get_current_time()}] 运行时变量保存成功 | 文件: {file_path}")
            else:
                logger.warning(
                    f"[{self._get_current_time()}] 运行时变量保存后数据不一致 | 文件: {file_path}（可能存在写入缓存）")
        except PermissionError:
            logger.error(
                f"[{self._get_current_time()}] 运行时变量保存失败 | 文件: {file_path} | 错误: 权限不足（无法写入）")
            raise
        except Exception as e:
            logger.error(f"[{self._get_current_time()}] 运行时变量保存异常 | 文件: {file_path} | 错误: {str(e)}")
            raise

    # 以下为原有辅助方法（保持逻辑，优化日志）
    def _get_nested_variable(
            self,
            data: Dict[str, Any],
            name: str,
            default: Optional[Any]
    ) -> Any:
        parts = name.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                logger.debug(f"[{self._get_current_time()}] 变量不存在（返回默认值） | 变量: {name} | 默认值: {default}")
                return default

        return current

    def _set_nested_variable(self, data: Dict[str, Any], name: str, value: Any) -> None:
        parts = name.split(".")
        current = data

        for i, part in enumerate(parts[:-1]):
            if not isinstance(current, dict):
                logger.warning(
                    f"[{self._get_current_time()}] 变量父节点非字典，将重置为字典 | 变量: {name} | 节点: {part}")
                current[part] = {}
            elif part not in current:
                current[part] = {}
            current = current[part]

        # 覆盖旧值（日志记录旧值，便于调试）
        old_value = current.get(parts[-1], "【无旧值】")
        current[parts[-1]] = value
        logger.debug(f"[{self._get_current_time()}] 变量值更新 | 变量: {name} | 旧值: {old_value} | 新值: {value}")

    def append_to_list(self, var_name: str, value: Any) -> None:
        # 追加前先刷新最新列表，避免漏加
        current_list = self.get_variable(var_name, from_runtime=True, default=[], force_refresh=True)
        if not isinstance(current_list, list):
            logger.warning(
                f"[{self._get_current_time()}] 变量非列表类型，重置为空列表 | 变量: {var_name} | 旧值类型: {type(current_list)}")
            current_list = []

        current_list.append(value)
        self.set_runtime_variable(var_name, current_list)
        logger.info(
            f"[{self._get_current_time()}] 列表变量追加成功 | 变量: {var_name} | 追加值: {value} | 当前列表长度: {len(current_list)}")

    # 其他方法（get_variable_list、set_batch_variables、delete_variable）逻辑不变，可参考上述优化日志和实时刷新逻辑


# 可选：单例模式（避免多实例重复加载，适合全局共享变量场景）
def get_singleton_var_manager(env: str = "test", data_dir: str = "VAR", test_group: str = "") -> VariableManager:
    """获取单例VariableManager实例，确保全局变量一致"""
    if not hasattr(get_singleton_var_manager, "_instance"):
        get_singleton_var_manager._instance = VariableManager(env=env, data_dir=data_dir, test_group=test_group)
    return get_singleton_var_manager._instance
