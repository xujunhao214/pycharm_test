import base64
import os
import logging  # 1. 导入日志模块（必须添加）
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import pytesseract
import io
import subprocess
import numpy as np

# ---------------------- 通用配置 ----------------------
# ！！！修复1：TESSERACT_PATH 指向 tesseract 可执行文件，而非 tessdata 目录
TESSERACT_PATH = r'/usr/bin/tesseract'  # 正确路径：可执行文件
CAPTCHA_LENGTH = 4
SUPPORTED_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
# ！！！修复2：用绝对路径，避免 Jenkins 执行时相对路径混乱
SAVE_DIR = '/www/python/jenkins/workspace/Community/template/Files/png'  # 绝对路径
SAVE_FILENAME = 'preprocessed_captcha.png'  # 固定文件名


class UniversalCaptchaRecognizer:
    def __init__(self):
        self.init_tesseract()
        # 确保保存目录存在（用绝对路径后更可靠）
        os.makedirs(SAVE_DIR, exist_ok=True)
        logging.info(f"初始化完成：保存目录={SAVE_DIR}，Tesseract路径={TESSERACT_PATH}")

    def init_tesseract(self):
        # 配置 pytesseract 路径（若用 subprocess 调用，此配置不影响，但保留避免其他问题）
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        # ！！！修复3：强制设置 TESSDATA_PREFIX，避免语言包加载失败
        os.environ["TESSDATA_PREFIX"] = '/usr/bin/tesseract/tessdata/'
        logging.info(f"TESSDATA_PREFIX 已设置：{os.getenv('TESSDATA_PREFIX')}")

    def minimal_preprocess(self, image: Image.Image) -> Image.Image:
        """保留字符形态，图片保存到固定位置和名称"""
        gray = image.convert("L")
        enhancer = ImageEnhance.Contrast(gray)
        contrast_img = enhancer.enhance(1.2)

        # 生成固定保存路径（绝对路径）
        save_path = os.path.join(SAVE_DIR, SAVE_FILENAME)
        # 保存图片（若文件已存在会自动覆盖）
        contrast_img.save(save_path)
        logging.info(f"预处理后图片已保存：{save_path}（大小：{os.path.getsize(save_path)} 字节）")

        return contrast_img

    def adaptive_recognize(self, base64_str: str) -> str:
        try:
            # ---------------------- 新增：Base64解析与实时图片保存 ----------------------
            if "," in base64_str:
                base64_data = base64_str.split(",")[1]
                logging.info(f"Base64字符串含前缀（如data:image/png;base64,），已截取后长度：{len(base64_data)}")
            else:
                base64_data = base64_str
                logging.info(f"Base64字符串无前缀，长度：{len(base64_data)}（正常应>1000字符）")

            # 解码Base64并保存原始图片（未预处理，用于与命令行对比）
            img_data = base64.b64decode(base64_data)
            # 原始图片保存路径（与预处理图片同目录，便于对比）
            raw_save_path = os.path.join(SAVE_DIR, 'code_from_jenkins_raw.png')
            with open(raw_save_path, "wb") as f:
                f.write(img_data)
            # 强制打印+日志双输出，确保Jenkins能捕获
            print(f"原始验证码图片已保存至：{raw_save_path}（大小：{len(img_data)} 字节）")
            logging.info(f"原始验证码图片已保存：{raw_save_path}（大小：{len(img_data)} 字节）")

            # 解析为PIL图片
            raw_img = Image.open(io.BytesIO(img_data))
            logging.info(f"成功解析图片：格式={raw_img.format}，尺寸={raw_img.size}，模式={raw_img.mode}")

        except Exception as e:
            # 新增：打印异常详情，便于定位解码失败原因
            error_msg = f"解析图片失败：{str(e)}"
            print("解析图片失败")
            logging.error(error_msg)
            return "*" * CAPTCHA_LENGTH

        # 图片预处理（已有保存逻辑，无需修改）
        processed_img = self.minimal_preprocess(raw_img)

        # OCR基础配置（建议psm_mode改为10，与命令行识别一致，提高验证码识别率）
        psm_mode = 10  # ！！！优化：psm=10（单字符识别），验证码专用模式（原psm=8适合整行文本）
        confidence = 25

        ocr_config = (
            f'-c tessedit_char_whitelist={SUPPORTED_CHARS} '
            f'-c tessedit_min_confidence={confidence} '
            f'--psm {psm_mode} --oem 3 '
            '-c tessedit_iterations=10'
        )
        logging.info(f"OCR配置：{ocr_config}")

        # 转换为PNG字节流（与之前一致，无需修改）
        temp_img = io.BytesIO()
        processed_img.save(temp_img, format='PNG')
        temp_img.seek(0)
        img_bytes = temp_img.read()
        logging.info(f"预处理后PNG字节流大小：{len(img_bytes)} 字节")

        try:
            # ---------------------- 新增：打印Tesseract调用命令 ----------------------
            tesseract_cmd = [
                TESSERACT_PATH, '-', '-',
                '--psm', str(psm_mode),
                '--oem', '3',
                '-c', f'tessedit_char_whitelist={SUPPORTED_CHARS}',
                '-c', f'tessedit_min_confidence={confidence}',
                '-c', 'tessedit_iterations=10'
            ]
            logging.info(f"执行Tesseract命令：{' '.join(tesseract_cmd)}")

            # 调用Tesseract（与之前一致，新增错误输出日志）
            result = subprocess.run(
                tesseract_cmd,
                input=img_bytes,
                capture_output=True,
                text=False,
                timeout=5
            )

            # ---------------------- 新增：打印Tesseract错误输出（关键排障） ----------------------
            if result.stderr:
                stderr_msg = result.stderr.decode('utf-8', errors='replace').strip()
                if stderr_msg:  # 仅当有错误信息时打印
                    logging.error(f"Tesseract错误输出：{stderr_msg}")
                    print(f"Tesseract错误输出：{stderr_msg}")

            # 解析识别结果
            raw_result = result.stdout.decode('utf-8', errors='replace').strip()
            # 强制打印+日志双输出，确认识别结果
            print(f"Tesseract原始识别结果：'{raw_result}'（长度：{len(raw_result)}）")
            logging.info(f"Tesseract原始识别结果：'{raw_result}'（长度：{len(raw_result)}）")

        except Exception as e:
            error_msg = f"OCR识别失败：{str(e)}"
            print(f"{error_msg}")
            logging.error(error_msg)
            return "*" * CAPTCHA_LENGTH

        # 后处理规则（与之前一致，无需修改）
        valid_chars = list(raw_result)
        for i, char in enumerate(valid_chars):
            if char not in SUPPORTED_CHARS:
                valid_chars[i] = '*'
                logging.warning(f"识别到无效字符：'{char}'，替换为'*'")
                continue
            # 规则1：e→c（索引1）
            if char == 'e' and i == 1:
                logging.info(f"触发规则1：索引{i}的'{char}'修正为'c'")
                valid_chars[i] = 'c'
            # 规则2：c→e（索引3）
            elif char == 'c' and i == 3:
                logging.info(f"触发规则2：索引{i}的'{char}'修正为'e'")
                valid_chars[i] = 'e'

        valid_str = ''.join(valid_chars)
        final_result = valid_str.ljust(CAPTCHA_LENGTH, '*')[:CAPTCHA_LENGTH]
        # 新增：打印最终结果
        print(f"最终验证码结果：'{final_result}'（长度：{len(final_result)}）")
        logging.info(f"最终验证码结果：'{final_result}'（长度：{len(final_result)}，预期：{CAPTCHA_LENGTH}位）")

        return final_result


# ---------------------- 测试入口 ----------------------
if __name__ == "__main__":
    # 初始化通用识别器（一次初始化，多次使用）
    recognizer = UniversalCaptchaRecognizer()

    random_captcha_base64 = "data:image/jpg;base64,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"

    result = recognizer.adaptive_recognize(random_captcha_base64)
    print(f"\n[最终结果] 验证码识别结果：{result}")
    print(f"[结果校验] 识别长度：{len(result)}（预期：{CAPTCHA_LENGTH}位）")
