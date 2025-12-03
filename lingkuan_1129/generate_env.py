import os
import xml.etree.ElementTree as ET
import argparse
import logging
import shutil
from enum import Enum
from datetime import datetime
from VAR.VAR import *


# 注意：VAR.VAR需确保存在，若不存在需注释/替换
# from VAR.VAR import *


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
        "vps_url": "http://39.98.109.212/vps",
        "db_host": "39.99.136.49",
        "db_port": 3306
    },
    Environment.UAT.value: {
        "test_environment": "UAT环境",
        "browser_version": f"{PROJECT_NAME}",
        "base_url": "https://uat.atcp.top/api",
        "vps_url": "https://39.101.181.190/vps",
        "db_host": "39.99.241.16",
        "db_port": 3306
    }
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ------------------------------
# 公共辅助函数（修复历史记录覆盖问题）
# ------------------------------
def add_param(parent, key, value):
    """仅添加纯文本参数，不包含任何HTML标签"""
    param = ET.SubElement(parent, "parameter")
    ET.SubElement(param, "key").text = key
    ET.SubElement(param, "value").text = value


# ------------------------------
# 公共辅助函数（修复datetime命名冲突）
# ------------------------------
def get_unique_build_identifier():
    """获取Jenkins构建号（本地返回空）"""
    import datetime as dt
    if "JENKINS_URL" in os.environ:
        # Jenkins环境：使用BUILD_NUMBER（自增序号，如28）
        return os.environ.get("BUILD_NUMBER", dt.datetime.now().strftime("%Y%m%d%H%M%S"))
    else:
        return ""


def get_pure_report_paths(markdown_report_path):
    """修复Jenkins报告链接格式（指向workspace永久路径）"""
    # 1. 处理本地路径（剥离file协议）
    pure_md_path = markdown_report_path.replace("file:///", "").replace("file://", "")
    html_report_path = pure_md_path.replace(".md", ".html")

    # 2. 获取构建信息（仅Jenkins）
    build_id = get_unique_build_identifier()
    md_filename = os.path.basename(pure_md_path)
    html_filename = os.path.basename(html_report_path)

    # 3. Jenkins环境处理（核心：链接指向workspace）
    if "JENKINS_URL" in os.environ:
        jenkins_url = os.environ["JENKINS_URL"].rstrip("/")
        job_name = os.environ.get("JOB_NAME", "QA-Documentatio-test")
        build_number = os.environ.get("BUILD_NUMBER", build_id)

        # 关键修正：ws = workspace，指向永久存储路径
        md_url = (
            f"{jenkins_url}/job/{job_name}/{build_number}/ws/lingkuan_1129/report/build_{build_number}/{md_filename}"
        )
        html_url = (
            f"{jenkins_url}/job/{job_name}/{build_number}/ws/lingkuan_1129/report/build_{build_number}/{html_filename}"
        )

    else:
        # 本地环境：直接使用file协议
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

        # 获取带构建号的纯路径链接
        md_url = "无"
        html_url = "无"
        if markdown_report_path:
            md_url, html_url = get_pure_report_paths(markdown_report_path)

        # 构建XML（仅纯文本参数）
        environment = ET.Element("environment")
        add_param(environment, "环境", env_config["test_environment"])
        add_param(environment, "版本", env_config["browser_version"])
        add_param(environment, "BASE_URL", env_config["base_url"])
        add_param(environment, "VPS_URL", env_config["vps_url"])
        add_param(environment, "Markdown报告", md_url)  # 启用带构建号的MD链接
        add_param(environment, "测试报告", html_url)  # 带构建号的HTML链接

        os.makedirs(output_dir, exist_ok=True)
        env_file_path = os.path.join(output_dir, "environment.xml")
        tree = ET.ElementTree(environment)
        tree.write(env_file_path, encoding="utf-8", xml_declaration=True)

        logger.info(f"独立执行环境文件生成成功: {env_file_path}")
        logger.info(f"HTML 报告纯路径: {html_url}")
        logger.info(f"MD 报告纯路径: {md_url}")
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
                logger.info(f"已清理旧环境文件：{env_file}")

        # 获取带构建号的纯路径链接
        md_url = "无"
        html_url = "无"
        if markdown_report_path:
            md_url, html_url = get_pure_report_paths(markdown_report_path)

        # 构建XML（仅纯文本参数）
        root = ET.Element("environment")
        add_param(root, "环境", env_config["test_environment"])
        add_param(root, "版本", env_config["browser_version"])
        add_param(root, "BASE_URL", env_config["base_url"])
        add_param(root, "VPS_URL", env_config["vps_url"])
        add_param(root, "汇总报告", html_url)  # 带构建号的HTML汇总链接
        add_param(root, "Markdown汇总报告", md_url)  # 启用MD汇总链接

        env_file_path = os.path.join(merged_results_dir, "environment.xml")
        tree = ET.ElementTree(root)
        tree.write(env_file_path, encoding="utf-8", xml_declaration=True)

        logger.info(f"合并执行环境文件生成成功：{env_file_path}")
        logger.info(f"HTML 汇总报告纯路径: {html_url}")
        logger.info(f"MD 汇总报告纯路径: {md_url}")
        return True
    except Exception as e:
        logger.error(f"生成合并执行环境文件失败：{str(e)}", exc_info=True)
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
