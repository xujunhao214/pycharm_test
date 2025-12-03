import os
import xml.etree.ElementTree as ET
import argparse
import logging
from enum import Enum
from VAR.VAR import *


class Environment(Enum):
    TEST = "test"
    UAT = "uat"


BASE_ENV_CONFIG = {
    Environment.TEST.value: {
        "test_environment": "测试环境",
        "browser_version": f"{PROJECT_NAME}",
        "base_url": "http://39.99.136.49/api",
        "vps_url": "http://39.98.109.212/vps",
    },
    Environment.UAT.value: {
        "test_environment": "UAT环境",
        "browser_version": f"{PROJECT_NAME}",
        "base_url": "https://uat.atcp.top/api",
        "vps_url": "https://39.101.181.190/vps",
    }
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def add_param(parent, key, value):
    param = ET.SubElement(parent, "parameter")
    ET.SubElement(param, "key").text = key
    ET.SubElement(param, "value").text = value


def get_pure_report_paths(markdown_report_path):
    """生成Jenkins/本地的报告链接"""
    pure_md_path = markdown_report_path.replace("file:///", "").replace("file://", "")
    html_report_path = pure_md_path.replace(".md", ".html")

    if "JENKINS_URL" in os.environ:
        # Jenkins环境：生成Jenkins可访问的链接（适配Publish HTML reports）
        jenkins_url = os.environ["JENKINS_URL"].rstrip("/")
        job_name = os.environ.get("JOB_NAME", "QA-Documentatio-test")
        build_number = os.environ.get("BUILD_NUMBER", "latest")
        # 格式：Jenkins地址/job/任务名/构建号/HTML_Report/报告文件名
        md_url = f"{jenkins_url}/job/{job_name}/{build_number}/MDReport"
        html_url = f"{jenkins_url}/job/{job_name}/{build_number}/MDReport"
    else:
        # 本地环境：file协议路径
        if os.name == "nt":
            md_abs = os.path.abspath(pure_md_path).replace("\\", "/")
            html_abs = os.path.abspath(html_report_path).replace("\\", "/")
            md_url = f"file:///{md_abs}"
            html_url = f"file:///{html_abs}"
        else:
            md_abs = os.path.abspath(pure_md_path)
            html_abs = os.path.abspath(html_report_path)
            md_url = f"file://{md_abs}"
            html_url = f"file://{html_abs}"

    return md_url, html_url


def generate_environment_xml(output_dir, env_value, markdown_report_path=""):
    try:
        if env_value not in BASE_ENV_CONFIG:
            raise ValueError(f"未知环境: {env_value}，可选值: {list(BASE_ENV_CONFIG.keys())}")

        env_config = BASE_ENV_CONFIG[env_value]
        md_url, html_url = get_pure_report_paths(markdown_report_path) if markdown_report_path else ("无", "无")

        environment = ET.Element("environment")
        add_param(environment, "环境", env_config["test_environment"])
        add_param(environment, "版本", env_config["browser_version"])
        add_param(environment, "BASE_URL", env_config["base_url"])
        add_param(environment, "VPS_URL", env_config["vps_url"])
        add_param(environment, "测试报告", html_url)

        os.makedirs(output_dir, exist_ok=True)
        env_file = os.path.join(output_dir, "environment.xml")
        ET.ElementTree(environment).write(env_file, encoding="utf-8", xml_declaration=True)

        logger.info(f"环境文件生成成功: {env_file}")
        return True
    except Exception as e:
        logger.error(f"环境文件生成失败: {str(e)}", exc_info=True)
        return False


def generate_merged_env(merged_results_dir, markdown_report_path, env_value="test"):
    try:
        if env_value not in BASE_ENV_CONFIG:
            raise ValueError(f"未知环境: {env_value}")
        env_config = BASE_ENV_CONFIG[env_value]

        # 清理旧环境文件
        for dir_path in [
            os.path.join(os.path.dirname(merged_results_dir), "vps_results"),
            os.path.join(os.path.dirname(merged_results_dir), "cloud_results"),
            merged_results_dir
        ]:
            env_file = os.path.join(dir_path, "environment.xml")
            if os.path.exists(env_file):
                os.remove(env_file)
                print(f"清理旧环境文件: {env_file}")

        md_url, html_url = get_pure_report_paths(markdown_report_path) if markdown_report_path else ("无", "无")

        root = ET.Element("environment")
        add_param(root, "环境", env_config["test_environment"])
        add_param(root, "版本", env_config["browser_version"])
        add_param(root, "BASE_URL", env_config["base_url"])
        add_param(root, "VPS_URL", env_config["vps_url"])
        add_param(root, "汇总报告", html_url)

        env_file = os.path.join(merged_results_dir, "environment.xml")
        ET.ElementTree(root).write(env_file, encoding="utf-8", xml_declaration=True)

        print(f"合并环境文件生成成功: {env_file}")
        return True
    except Exception as e:
        print(f"合并环境文件生成失败: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成Allure环境文件")
    parser.add_argument("--env", required=True, help=f"环境: {[e.value for e in Environment]}")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--markdown-report-path", default="", help="MD报告路径")
    parser.add_argument("--mode", choices=["single", "merged"], default="single")
    args = parser.parse_args()

    if args.mode == "single":
        generate_environment_xml(args.output_dir, args.env, args.markdown_report_path)
    else:
        generate_merged_env(args.output_dir, args.markdown_report_path, args.env)
