# generate_env.py
import os
import xml.etree.ElementTree as ET
import argparse
import logging
from enum import Enum


# ------------------------------
# 这个文件是配置allure报告里面的环境信息
# ------------------------------
# 环境枚举
class Environment(Enum):
    TEST = "test"
    UAT = "uat"


# 环境配置映射（使用有序字典确保配置内部顺序）
ENV_CONFIG = {
    Environment.TEST.value: {
        "test_environment": "测试环境",
        "browser_version": "自研跟单1.4.2",
        "base_url": "http://39.99.136.49:9000",
        "vps_url": "http://39.99.136.49:9001",
        "db_host": "39.99.136.49",
        "db_port": 3306,
    },
    Environment.UAT.value: {
        "test_environment": "UAT环境",
        "browser_version": "自研跟单1.4.2",
        "base_url": "https://uat.atcp.top/api",
        "vps_url": "https://39.99.145.155/vps",
        "db_host": "39.99.241.16",
        "db_port": 3306,
    }
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_environment_xml(output_dir, env_value):
    """生成 Allure 环境信息文件，按固定顺序添加参数"""
    try:
        # 验证环境是否存在
        if env_value not in ENV_CONFIG:
            raise ValueError(f"未知环境: {env_value}，可选值: {list(ENV_CONFIG.keys())}")

        # 获取当前环境配置
        env_config = ENV_CONFIG[env_value]

        # 创建XML根节点
        environment = ET.Element("environment")

        # 按期望的顺序逐个添加参数（关键修改点）
        add_param(environment, "Test Environment", env_config["test_environment"])
        add_param(environment, "Browser.Version", env_config["browser_version"])
        add_param(environment, "BASE_URL", env_config["base_url"])
        add_param(environment, "VPS_URL", env_config["vps_url"])
        add_param(environment, "DB Host", env_config["db_host"])
        add_param(environment, "DB Port", str(env_config["db_port"]))

        # 写入文件
        os.makedirs(output_dir, exist_ok=True)
        env_file_path = os.path.join(output_dir, "environment.xml")
        tree = ET.ElementTree(environment)
        tree.write(env_file_path, encoding="utf-8", xml_declaration=True)

        logger.info(f"已生成 Allure 环境信息文件: {env_file_path}")
        return True
    except Exception as e:
        logger.error(f"生成环境信息文件失败: {str(e)}", exc_info=True)
        return False


def add_param(parent, key, value):
    """辅助函数：向XML添加参数节点"""
    param = ET.SubElement(parent, "parameter")
    ET.SubElement(param, "key").text = key
    ET.SubElement(param, "value").text = value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 Allure 环境信息文件")
    parser.add_argument("--env", required=True, help=f"测试环境名称，可选值：{[e.value for e in Environment]}")
    parser.add_argument("--output-dir", required=True, help="输出目录路径")
    args = parser.parse_args()

    generate_environment_xml(args.output_dir, args.env)
