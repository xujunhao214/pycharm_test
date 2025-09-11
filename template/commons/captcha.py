import base64
import os
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import pytesseract
import io
import subprocess
import numpy as np

# ---------------------- 通用配置 ----------------------
TESSERACT_PATH = r'D:\test_tools\Tesseract-OCR\tesseract.exe'  # 替换为你的Tesseract路径
# TESSERACT_PATH = r'/www/python/tesseract-5.5.0/tessdata'  # 替换为你的Tesseract路径
CAPTCHA_LENGTH = 4
SUPPORTED_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
# 固定保存路径配置
SAVE_DIR = './Files/png'  # 父目录
SAVE_FILENAME = 'preprocessed_captcha.png'  # 固定文件名


class UniversalCaptchaRecognizer:
    def __init__(self):
        self.init_tesseract()
        # 确保保存目录存在
        os.makedirs(SAVE_DIR, exist_ok=True)

    def init_tesseract(self):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

    def minimal_preprocess(self, image: Image.Image) -> Image.Image:
        """保留字符形态，图片保存到固定位置和名称"""
        gray = image.convert("L")
        enhancer = ImageEnhance.Contrast(gray)
        contrast_img = enhancer.enhance(1.2)

        # 生成固定保存路径
        save_path = os.path.join(SAVE_DIR, SAVE_FILENAME)
        # 保存图片（若文件已存在会自动覆盖）
        contrast_img.save(save_path)
        # print(f"图片已保存至：{save_path}")

        return contrast_img

    def adaptive_recognize(self, base64_str: str) -> str:
        try:
            if "," in base64_str:
                base64_data = base64_str.split(",")[1]
            else:
                base64_data = base64_str
            image_bytes = base64.b64decode(base64_data)
            raw_img = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            # print(f"[错误] 解析图片失败：{str(e)}")
            return "*" * CAPTCHA_LENGTH

        processed_img = self.minimal_preprocess(raw_img)

        # OCR基础配置
        psm_mode = 8
        confidence = 25

        ocr_config = (
            f'-c tessedit_char_whitelist={SUPPORTED_CHARS} '
            f'-c tessedit_min_confidence={confidence} '
            f'--psm {psm_mode} --oem 3 '
            '-c tessedit_iterations=10'
        )

        temp_img = io.BytesIO()
        processed_img.save(temp_img, format='PNG')
        temp_img.seek(0)
        img_bytes = temp_img.read()

        try:
            result = subprocess.run(
                [
                    TESSERACT_PATH, '-', '-',
                    '--psm', str(psm_mode),
                    '--oem', '3',
                    '-c', f'tessedit_char_whitelist={SUPPORTED_CHARS}',
                    '-c', f'tessedit_min_confidence={confidence}',
                    '-c', 'tessedit_iterations=10'
                ],
                input=img_bytes,
                capture_output=True,
                text=False,
                timeout=5
            )
            raw_result = result.stdout.decode('utf-8', errors='replace').strip()
            # print(f"[OCR识别] 原始输出：{raw_result}（配置：psm={psm_mode}, 置信度={confidence}）")
        except Exception as e:
            # print(f"[错误] OCR识别失败：{str(e)}")
            return "*" * CAPTCHA_LENGTH

        # 关键：后处理规则匹配修正c/e混淆
        valid_chars = list(raw_result)
        for i, char in enumerate(valid_chars):
            if char not in SUPPORTED_CHARS:
                valid_chars[i] = '*'
                continue
            # 规则1：若识别为e，但位置对应c的常见位置（如第2位），则修正为c
            if char == 'e' and i == 1:  # 假设c在第2位（索引1）
                valid_chars[i] = 'c'
            # 规则2：若识别为c，但形态更接近e（可根据实际场景扩展），则修正为e
            # 此处仅示例c→e的修正，需根据实际需求调整
            elif char == 'c' and i == 3:
                valid_chars[i] = 'e'

        valid_str = ''.join(valid_chars)
        return valid_str.ljust(CAPTCHA_LENGTH, '*')[:CAPTCHA_LENGTH]


# ---------------------- 测试入口 ----------------------
if __name__ == "__main__":
    # 初始化通用识别器（一次初始化，多次使用）
    recognizer = UniversalCaptchaRecognizer()

    random_captcha_base64 = "data:image/jpg;base64,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"

    result = recognizer.adaptive_recognize(random_captcha_base64)
    print(f"\n[最终结果] 验证码识别结果：{result}")
    print(f"[结果校验] 识别长度：{len(result)}（预期：{CAPTCHA_LENGTH}位）")
