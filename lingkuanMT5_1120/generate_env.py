import os
import xml.etree.ElementTree as ET
import argparse
import logging
from enum import Enum
from VAR.VAR import *


# ------------------------------
# 统一配置（复用逻辑，避免冗余）
# ------------------------------
class Environment(Enum):
    TEST = "test"
    UAT = "uat"


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
    # 移除 file:// 协议，获取纯路径
    pure_md_path = markdown_report_path.replace("file:///", "").replace("file://", "")
    html_report_path = pure_md_path.replace(".md", ".html")

    # 区分本地和 Jenkins 环境
    if "JENKINS_URL" in os.environ:
        # Jenkins 环境：链接必须与 HTML Publisher 插件的发布路径一致
        job_name = os.environ.get("JOB_NAME", "默认任务名")
        build_number = os.environ.get("BUILD_NUMBER", "1")
        # 获取报告文件名
        md_filename = os.path.basename(pure_md_path)
        html_filename = os.path.basename(html_report_path)

        # 关键：根据插件配置的「Report directory path」填写子路径
        # 若插件设置了「HTML_Report」，则路径为 job/{job_name}/{build_number}/HTML_Report/
        # 若未设置，则路径为 job/{job_name}/{build_number}/artifact/lingkuanMT5_1120/report/
        # （根据你的插件配置二选一）
        # 方案A：插件设置了「Report directory path: HTML_Report」
        md_url = f"{os.environ['JENKINS_URL']}job/{job_name}/{build_number}/HTML_Report/{md_filename}"
        html_url = f"{os.environ['JENKINS_URL']}job/{job_name}/{build_number}/HTML_Report/{html_filename}"

        # 方案B：插件未设置子路径（默认发布到 artifact 目录）
        # md_url = f"{os.environ['JENKINS_URL']}job/{job_name}/{build_number}/artifact/lingkuanMT5_1120/report/{md_filename}"
        # html_url = f"{os.environ['JENKINS_URL']}job/{job_name}/{build_number}/artifact/lingkuanMT5_1120/report/{html_filename}"
    else:
        # 本地环境：使用 file:// 协议
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
        add_param(environment, "VPS_URL", env_config["MT5vps_url"])
        add_param(environment, "Markdown报告", md_url)  # 纯路径
        add_param(environment, "HTML测试报告", html_url)  # 纯路径

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
# 合并执行环境生成（纯路径版本）
# ------------------------------
def generate_merged_env(merged_results_dir, markdown_report_path, env_value="test"):
    try:
        if env_value not in BASE_ENV_CONFIG:
            raise ValueError(f"未知环境: {env_value}，可选值: {list(BASE_ENV_CONFIG.keys())}")
        env_config = BASE_ENV_CONFIG[env_value]

        # 清理旧环境文件
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

        # 获取纯路径链接（无HTML标签）
        md_url = "无"
        html_url = "无"
        if markdown_report_path:
            md_url, html_url = get_pure_report_paths(markdown_report_path)

        # 构建XML（仅纯文本参数）
        root = ET.Element("environment")
        add_param(root, "环境", env_config["test_environment"])
        add_param(root, "版本", env_config["browser_version"])
        add_param(root, "BASE_URL", env_config["base_url"])
        add_param(root, "VPS_URL", env_config["MT5vps_url"])
        add_param(root, "Markdown汇总报告", md_url)  # 纯路径
        add_param(root, "HTML汇总报告", html_url)  # 纯路径

        env_file_path = os.path.join(merged_results_dir, "environment.xml")
        tree = ET.ElementTree(root)
        tree.write(env_file_path, encoding="utf-8", xml_declaration=True)

        print(f"合并执行环境文件生成成功：{env_file_path}")
        print(f"HTML 汇总报告纯路径: {html_url}")
        return True
    except Exception as e:
        print(f"生成合并执行环境文件失败：{str(e)}")
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
    else:
        generate_merged_env(args.output_dir, args.markdown_report_path, args.env)
