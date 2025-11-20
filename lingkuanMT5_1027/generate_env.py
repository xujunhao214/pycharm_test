import os
import xml.etree.ElementTree as ET
import argparse
import logging
from enum import Enum

try:
    from .VAR.VAR import *
except ImportError:
    from lingkuanMT5_1027.VAR.VAR import *


# ------------------------------
# 统一配置（复用逻辑，避免冗余）
# ------------------------------
# 环境枚举（全局共用）
class Environment(Enum):
    TEST = "test"
    UAT = "uat"


# 基础环境配置（独立执行和合并执行共用）
BASE_ENV_CONFIG = {
    Environment.TEST.value: {
        "test_environment": "测试环境",
        "browser_version": f"{PROJECT_NAME}",
        "base_url": "http://39.99.136.49/api",
        "MT5vps_url": "http://39.98.109.212/vps",
        "db_host": "39.99.136.49",
        "db_port": 3306
    },
    Environment.UAT.value: {
        "test_environment": "UAT环境",
        "browser_version": f"{PROJECT_NAME}",
        "base_url": "https://uat.atcp.top/api",
        "MT5vps_url": "https://39.101.181.190/vps",
        "db_host": "39.99.241.16",
        "db_port": 3306
    }
}

# 日志配置（仅独立执行时使用）
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ------------------------------
# 公共辅助函数（复用）
# ------------------------------
def add_param(parent, key, value):
    """辅助函数：向XML添加参数节点（共用）"""
    param = ET.SubElement(parent, "parameter")
    ET.SubElement(param, "key").text = key
    ET.SubElement(param, "value").text = value


# ------------------------------
# 独立执行环境生成（原 generate_env.py 逻辑）
# ------------------------------
def generate_environment_xml(output_dir, env_value, markdown_report_path=""):
    """
    生成 Allure 环境信息文件（仅用于VPS/Cloud独立执行）
    :param output_dir: 输出目录路径
    :param env_value: 执行环境（test/uat）
    :param markdown_report_path: 独立报告的 Markdown 路径（带 file:/// 协议）
    :return: 生成是否成功
    """
    try:
        # 验证环境
        if env_value not in BASE_ENV_CONFIG:
            raise ValueError(f"未知环境: {env_value}，可选值: {list(BASE_ENV_CONFIG.keys())}")

        # 拼接完整配置（添加 Markdown 路径占位符）
        env_config = BASE_ENV_CONFIG[env_value].copy()
        env_config["markdown_report_path"] = markdown_report_path

        # 构建XML
        environment = ET.Element("environment")
        add_param(environment, "环境", env_config["test_environment"])
        add_param(environment, "版本", env_config["browser_version"])
        add_param(environment, "BASE_URL", env_config["base_url"])
        add_param(environment, "VPS_URL", env_config["MT5vps_url"])
        # add_param(environment, "DB Host", env_config["db_host"])
        # add_param(environment, "DB Port", str(env_config["db_port"]))
        add_param(environment, "Markdown报告", env_config["markdown_report_path"])

        # 写入文件
        os.makedirs(output_dir, exist_ok=True)
        env_file_path = os.path.join(output_dir, "environment.xml")
        tree = ET.ElementTree(environment)
        tree.write(env_file_path, encoding="utf-8", xml_declaration=True)

        logger.info(f"独立执行环境文件生成成功: {env_file_path}")
        return True
    except Exception as e:
        logger.error(f"生成独立执行环境文件失败: {str(e)}", exc_info=True)
        return False


# ------------------------------
# 合并执行环境生成（原 generate_merged_env.py 逻辑）
# ------------------------------
def generate_merged_env(merged_results_dir, markdown_report_path, env_value="test"):
    """
    生成 Allure 环境信息文件（仅用于VPS+Cloud合并执行）
    :param merged_results_dir: 合并后的 Allure 结果目录
    :param markdown_report_path: 汇总报告的 Markdown 路径（带 file:/// 协议）
    :param env_value: 执行环境（test/uat）
    :return: 生成是否成功
    """
    try:
        # 验证环境
        if env_value not in BASE_ENV_CONFIG:
            raise ValueError(f"未知环境: {env_value}，可选值: {list(BASE_ENV_CONFIG.keys())}")
        env_config = BASE_ENV_CONFIG[env_value]

        # 强制清理旧环境文件（避免残留）
        clean_dirs = [
            os.path.join(os.path.dirname(merged_results_dir), "vps_results"),
            os.path.join(os.path.dirname(merged_results_dir), "cloud_results"),
            merged_results_dir
        ]
        for dir_path in clean_dirs:
            env_file = os.path.join(dir_path, "environment.xml")
            if os.path.exists(env_file):
                os.remove(env_file)
                print(f"已清理旧环境文件：{env_file}")

        # 构建XML（复用基础配置，添加汇总Markdown路径）
        root = ET.Element("environment")
        add_param(root, "环境", env_config["test_environment"])
        add_param(root, "版本", env_config["browser_version"])
        add_param(root, "BASE_URL", env_config["base_url"])
        add_param(root, "VPS_URL", env_config["MT5vps_url"])
        # add_param(root, "DB Host", env_config["db_host"])
        # add_param(root, "DB Port", str(env_config["db_port"]))
        add_param(root, "Markdown报告", markdown_report_path)

        # 写入文件
        env_file_path = os.path.join(merged_results_dir, "environment.xml")
        tree = ET.ElementTree(root)
        tree.write(env_file_path, encoding="utf-8", xml_declaration=True)

        print(f"合并执行环境文件生成成功：{env_file_path}")
        return True
    except Exception as e:
        print(f"生成合并执行环境文件失败：{str(e)}")
        return False


# ------------------------------
# 命令行调用入口（仅独立执行时使用）
# ------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 Allure 环境信息文件（支持独立执行/合并执行）")
    # 公共参数
    parser.add_argument("--env", required=True, help=f"测试环境名称，可选值：{[e.value for e in Environment]}")
    parser.add_argument("--output-dir", required=True, help="输出目录路径（独立执行时用）/ 合并结果目录（合并执行时用）")
    parser.add_argument("--markdown-report-path", default="", help="Markdown 报告的 file:/// 路径")
    # 新增：区分执行模式（默认独立执行）
    parser.add_argument("--mode", choices=["single", "merged"], default="single",
                        help="执行模式：single=独立执行（默认），merged=合并执行")

    args = parser.parse_args()

    # 根据模式调用对应函数
    if args.mode == "single":
        generate_environment_xml(args.output_dir, args.env, args.markdown_report_path)
    else:
        generate_merged_env(args.output_dir, args.markdown_report_path, args.env)
