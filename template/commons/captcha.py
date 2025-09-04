import base64
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import io
import subprocess

# ---------------------- 基础配置（根据实际调整） ----------------------
# 1. Tesseract可执行文件路径
TESSERACT_PATH = r'D:\test_tools\Tesseract-OCR\tesseract.exe'
# 2. 验证码字符类型（包含字母+数字，重点支持6）
CHAR_WHITELIST = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
# 3. 验证码固定长度
CAPTCHA_LENGTH = 4


def init_tesseract():
    """初始化Tesseract路径"""
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def preprocess_captcha(image: Image.Image) -> Image.Image:
    """
    针对性优化：强化数字6的形态，区分字母与数字
    """
    # 1. 转为灰度图
    gray_img = image.convert("L")

    # 2. 手动调整二值化阈值（平衡字母与数字6的清晰度）
    threshold = 190  # 适中阈值，保留字母轮廓和数字6的封闭圈
    binary_img = gray_img.point(lambda p: 255 if p > threshold else 0)
    print(f"[预处理] 手动设置二值化阈值：{threshold}")

    # 3. 降噪（中值滤波，size=3避免过度模糊）
    denoised_img = binary_img.filter(ImageFilter.MedianFilter(size=3))

    # 4. 字符形态增强（针对数字6的封闭圈和字母U/r/g的形态）
    sharpened_img = denoised_img.filter(ImageFilter.SHARPEN)
    # 膨胀核size=3（奇数，适配6的封闭圈和字母的笔画）
    expanded_img = sharpened_img.filter(ImageFilter.MaxFilter(size=3))

    # 5. 去除边缘噪点
    final_img = ImageOps.expand(expanded_img, border=1, fill=255)

    # 保存预处理图（当前目录）
    final_img.save("../Files/png/preprocessed_captcha.png")
    print("[预处理] 图片已保存为 preprocessed_captcha.png（当前目录）")

    return final_img


def recognize_captcha_base64(base64_str: str) -> str:
    """
    优化OCR配置：适配字母+数字混合（重点识别6）
    """
    # 1. 初始化Tesseract
    init_tesseract()

    # 2. 解析Base64字符串
    if "," in base64_str:
        base64_data = base64_str.split(",")[1]
    else:
        base64_data = base64_str
    image_bytes = base64.b64decode(base64_data)
    try:
        raw_img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        print(f"[错误] 解析Base64图片失败：{str(e)}")
        return ""

    # 3. 图片预处理
    processed_img = preprocess_captcha(raw_img)

    # 4. OCR识别（调整配置，支持数字6）
    ocr_config = (
        f'-c tessedit_char_whitelist={CHAR_WHITELIST} '
        f'-c tessedit_min_confidence=35 '  # 降低阈值，适配数字与字母的混合
        '--psm 8 --oem 3'  # psm8：单字块模式，适配分散的字符排列
    )

    temp_img = io.BytesIO()
    processed_img.save(temp_img, format='PNG')
    temp_img.seek(0)
    img_bytes = temp_img.read()

    cmd = [
        TESSERACT_PATH,
        '-', '-',
        '--psm', '8',
        '--oem', '3',
        '-c', f'tessedit_char_whitelist={CHAR_WHITELIST}',
        '-c', 'tessedit_min_confidence=35'
    ]

    try:
        result = subprocess.run(
            cmd,
            input=img_bytes,
            capture_output=True,
            text=False,
            timeout=5
        )
        raw_result = result.stdout.decode('utf-8', errors='replace').strip()
        print(f"[OCR识别] 原始输出：{raw_result}")
    except subprocess.TimeoutExpired:
        print("[错误] OCR识别超时（>5秒）")
        return ""
    except Exception as e:
        print(f"[错误] OCR识别失败：{str(e)}")
        return ""

    # 5. 结果后处理（保留原始字符，确保长度）
    valid_result = [c for c in raw_result if c in CHAR_WHITELIST]
    valid_str = ''.join(valid_result)
    final_result = valid_str.ljust(CAPTCHA_LENGTH, '*')[:CAPTCHA_LENGTH]

    return final_result


# ---------------------- 测试入口 ----------------------
if __name__ == "__main__":
    # 替换为实际的验证码Base64字符串
    captcha_base64 = "这里替换为实际的Base64字符串"

    result = recognize_captcha_base64(captcha_base64)

    print(f"\n[最终结果] 验证码识别结果：{result}")
    print(f"[结果校验] 识别长度：{len(result)}（预期：{CAPTCHA_LENGTH}位）")


# ---------------------- 测试入口 ----------------------
if __name__ == "__main__":
    random_captcha_base64 = "data:image/jpg;base64,/9j/4AAQSkZJRgABAgAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAjAGkDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3lI4is0au53Md/wC9YlSR0BzleCOBjGaaBPF5G52mwuyTaqjcePnPPAGDwPX2prsftTQxPGjOnmEjG4EEDJHcEcdsY68jHA698YfDfhvxZNoOqJf295blBPdLbI8LApvA4cvghuOOCeeM0Ad+Z3gmWOUDy3fasrSKMk8hcce49fu9cnE7q7ZCvtBUjIHIPYjPHr2riPBnxE0bx1BdrotheolhLAJY7uJRxIzbSu12xtK59gOPbsfMDXUZAnwN8f3SEzwefyOD06jPIoAnUFUALFiBgscZPvxSSs6xO0ab3Ckqmcbj6Z7V514q+NHhTwvrP9nyXN3e3MDvHdQ2UKuI2AHBZmUbsnHyk4wwYA4xseB/iHo3juxvJdJS982xKrNFdRqkh3A7WG0ledrDqOQcgDGQDqxGxL75CylwygfLtAA4yOvIJ/HFPZlRSzEKoGSScACszVdU07T9Plv795EtbaMXEz7G/dp94MVHJ5ToAT7YzXgulWHiL456tdavrE11b+F7ebyorGzuFG1wOAA3G4K+TIVyc7RgH5AD6NYkDhSeRwKpR6rbSJv8xCG+4I3EjMcDIwuSSM84yMYOfTzvwt8Iv+EK8Y2eo6F4ivDp43fb9PuHx5wKShGJTAbDMuAy9mIPauq8S+KbHwlo0viS7tdQntwyQzxwRpvhB+6WViuAGOOpOZO4xgA6ZmxIuXUA5GD1J68fgD/kUSb/ACn8rb5m07d3TPbPtXPWfiXSdb8Hr4strqeLTfsrzs0iH92IyS25MN8ylGGQD0OM8Gsrwr4w03xz4dmutJsLmDT7S4WKT7dHGiSsMMwxGzYxlWJIA57jdgBnaIjhyWlLDJwMAcHHX6c46cHnJ5qSs2S5uJdSW2jUqYlWVsA7SSGBUnjIPGCAeQeOONKgCrFbyK8n76dV83cMsG3DqRyOBzjH+yPU5+ftU0qx1r9q1rDUraO6tHdHeGTlWKWYdcjuNyjg8HocjivofdL54UxDyyCd4bp0wMe+W/L3rCbwT4fHi0+LE00HXccXJnkAJ8vy/u52/d4+779aANhIEa5W9jjWOWSNUlLRje6DJVSevylmwM4G5uOc05JS95LHv/1ag7dpH3u5yOeh5B7kEcU+FpWQ+bGEcHGFbcD7g8fqB/WkhjZYojMVedUCtJgcnjP5kUAfNHwd1PRvDvxD1lPGTxQa4GeOO+vZgVimVmEwMhJUO398nnDAH5sN7zYa9oGt6nfSabd2N5JZpDJcXNsyviPEhQb0JyQwk+U4wGPGGyaniX4d+F/E2pJf6volvcuFbzZUZ4pWIAAJMeDJwoGGJwAMY5za8M+FdA8Lac58O2AsIp3Es2N0rygDGCWJYgDOMHGTkZycgF/xFYPrXh7UtIhdVa9tprVpSc+TvjYBiO/JHHvXifwd8VWPgqTVfA3i2MaVd/ann827dViJKKCjE8DIUMrZKsDwfu7velheO7eVXykmN6NxtwOCMD88+3PGDieJvA3hzxeYv7b0mC5ePG2cExygAnCb1wxX5m4zjnOM8gAq23xC8M3XiPTvD+n6tDfXl2HCJbMJwqqrtuaUEqOIzxkt8ykgDJrc1zRrPxDod7pF+m+1u4mifABK56MuQQGBwQccEA1heHvAPg7wvdvd6Jo1tBe7iiySu8jqwVuFMhYplSc7eoPcYreuY5biyht7ryRJK4Vwq71bGTxuBA4GeQemM9DQB8sWvjO98P8Awn8ReCbrzotRXUVt1BuiGijbcZkVQPuhoirAHB88/wDAvoX4c+HF8M+C9M0eSzktrpYlurghuXmflw7KACQflwc/KqjJxT73wL4Ov/EX/CV3lgh1KOdJPtb3MqBZIiFU7dwXgoB0wcd810bE3cbgwHdDN8odmRWKkEHOOR+GMjv1oAW2ukuZ3CScxjEkJwShyccgkZ4ORk9une1VPa9vbJJdXuCj72dyAuDxtOMZHPX1wfarlABTZI0lQpIiuh6qwyDRRQAeWvm+Zj59u3PqPf8Az3PrSSxRzxmOWNJEPVXGQfwoooAfTJYo54zHLGsiHqrjIP4UUUALJGssTxuMo6lWHqDTqKKAIktoY8bIkGG3DjocYz+XH046VIVVipKglTkEjoen9TRRQAtMeNJNu4ZKsGU5wQf8/oSKKKAH0UUUAf/Z"

    result = recognize_captcha_base64(random_captcha_base64)
    print(f"\n[最终结果] 验证码识别结果：{result}")
    print(f"[结果校验] 识别长度：{len(result)}（预期：{CAPTCHA_LENGTH}位）")
