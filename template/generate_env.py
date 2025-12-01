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
    DEV = "dev"


# 环境配置映射（使用有序字典确保配置内部顺序）
BASE_ENV_CONFIG = {
    Environment.TEST.value: {
        "test_environment": "测试环境",
        "browser_version": "跟单社区",
        "base_url": "https://test.lgcopytrade.top/api",
        # "vps_url": "http://39.99.136.49:9001",
        "db_host": "39.103.138.2",
        "db_port": 3306,
    },
    Environment.DEV.value: {
        "test_environment": "DEV环境",
        "browser_version": "跟单社区",
        "base_url": "https://dev.lgcopytrade.top/api",
        # "vps_url": "https://39.101.181.190/vps",
        "db_host": "39.99.146.95",
        "db_port": 3306,
    }
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ------------------------------
# 公共辅助函数（还原为原始版本）
# ------------------------------
def add_param(parent, key, value):
    """仅添加纯文本参数，不包含任何HTML标签"""
    param = ET.SubElement(parent, "parameter")
    ET.SubElement(param, "key").text = key
    ET.SubElement(param, "value").text = value


def get_pure_report_paths(markdown_report_path):
    pure_md_path = markdown_report_path.replace("file:///", "").replace("file://", "")
    html_report_path = pure_md_path.replace(".md", ".html")

    if "JENKINS_URL" in os.environ:
        # Jenkins 环境：生成与实际访问路径一致的 URL（包含 view 前缀）
        job_name = os.environ.get("JOB_NAME", "默认任务名")

        # 关键：根据实际路径格式拼接（包含 view/自动化测试/ 前缀）
        # 正确格式：http://{Jenkins地址}/view/自动化测试/job/{任务名}/{构建号}/HTML_Report/{报告文件名}
        # 注意：view 名称固定为“自动化测试”，与你的实际路径匹配
        md_url = f"{os.environ['JENKINS_URL']}view/自动化测试/job/{job_name}/MDReport"
        html_url = f"{os.environ['JENKINS_URL']}view/自动化测试/job/{job_name}/MDReport"
    else:
        # 本地环境：保留 file:// 协议（直接打开）
        if os.name == "nt":
            md_abs_path = os.path.abspath(pure_md_path).replace("\\", "/")
            html_abs_path = os.path.abspath(html_report_path).replace("\\", "/")
            md_url = f"file:///{md_abs_path}"
            html_url = f"file:///{html_abs_path}"
        else:
            md_abs_path = os.path.abspath(pure_md_path)
            html_abs_path = os.path.abspath(html_report_path)
            md_url = f"file://{md_abs_path}"
            html_url = f"file://{html_abs_path}"

    return md_url, html_url


# ------------------------------
# 独立执行环境生成（纯路径版本）
# ------------------------------
def generate_environment_xml(output_dir, env_value, markdown_report_path=""):
    try:
        if env_value not in BASE_ENV_CONFIG:
            raise ValueError(f"未知环境: {env_value}，可选值: {list(BASE_ENV_CONFIG.keys())}")

        env_config = BASE_ENV_CONFIG[env_value].copy()
        env_config["markdown_report_path"] = markdown_report_path

        # 获取纯路径链接（无HTML标签）
        md_url = "无"
        html_url = "无"
        if markdown_report_path:
            md_url, html_url = get_pure_report_paths(markdown_report_path)

        # 构建XML（仅纯文本参数）
        environment = ET.Element("environment")
        add_param(environment, "环境", env_config["test_environment"])
        add_param(environment, "版本", env_config["browser_version"])
        add_param(environment, "BASE_URL", env_config["base_url"])
        # add_param(environment, "VPS_URL", env_config["vps_url"])
        # add_param(environment, "Markdown报告", md_url)  # 纯路径
        add_param(environment, "测试报告", html_url)  # 纯路径

        os.makedirs(output_dir, exist_ok=True)
        env_file_path = os.path.join(output_dir, "environment.xml")
        tree = ET.ElementTree(environment)
        tree.write(env_file_path, encoding="utf-8", xml_declaration=True)

        logger.info(f"独立执行环境文件生成成功: {env_file_path}")
        logger.info(f"HTML 报告纯路径: {html_url}")
        return True
    except Exception as e:
        logger.error(f"生成独立执行环境文件失败: {str(e)}", exc_info=True)
        return False


# ------------------------------
# 命令行调用入口
# ------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 Allure 环境信息文件（纯路径链接版本）")
    parser.add_argument("--env", required=True, help=f"测试环境名称，可选值：{[e.value for e in Environment]}")
    parser.add_argument("--output-dir", required=True, help="输出目录路径/合并结果目录")
    parser.add_argument("--markdown-report-path", default="", help="Markdown 报告的纯路径")
    parser.add_argument("--mode", choices=["single", "merged"], default="single", help="执行模式")

    args = parser.parse_args()

    if args.mode == "single":
        generate_environment_xml(args.output_dir, args.env, args.markdown_report_path)
