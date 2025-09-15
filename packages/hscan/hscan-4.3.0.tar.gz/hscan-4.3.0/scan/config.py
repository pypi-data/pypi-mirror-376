import configparser
from scan import logger


class Config:
    def __init__(self, cfg_file_path):
        if cfg_file_path:
            self.config: configparser.ConfigParser = self.base_config(cfg_file_path)
        else:
            logger.warning('没有指定配置文件')

    @staticmethod
    def base_config(cfg_file_path=None):
        config = configparser.ConfigParser()
        config.read(cfg_file_path, encoding="utf-8")
        return config

    def admin(self):
        try:
            return dict(self.config.items('admin'))
        except AttributeError:
            return {'url': 'http://localhost', 'token': ''}

    def postgres(self):
        return dict(self.config.items('postgres'))

    def mongo(self):
        return dict(self.config.items('mongo'))

    def redis(self):
        return dict(self.config.items('redis'))

    def rabbitmq(self):
        return dict(self.config.items('rabbitmq'))

    def client(self):
        return dict(self.config.items('client'))

    def oss(self):
        return dict(self.config.items('oss'))

    def kafka(self):
        return dict(self.config.items('kafka'))

    def other(self):
        return dict(self.config.items('other'))

    # @staticmethod
    # def explain(func_text):
    #     """
    #     :param func_text: 函数的字符串形式，函数名必须为parse_func
    #     :return:
    #     """
    #     exec(func_text, globals())
    #     parse_func = eval('parse_func')
    #     return parse_func
