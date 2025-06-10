import yaml
import os


class YamlHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_yaml(self, encoding='utf-8'):
        """读取yaml文件并返回数据"""
        if not os.path.exists(self.file_path):
            return {}

        with open(self.file_path, encoding=encoding) as f:
            return yaml.safe_load(f)

    def write_yaml(self, data, encoding='utf-8'):
        """将数据写入yaml文件"""
        # 确保目录存在
        dir_path = os.path.dirname(self.file_path)
        os.makedirs(dir_path, exist_ok=True)

        with open(self.file_path, 'w', encoding=encoding) as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
