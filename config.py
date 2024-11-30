import json



class Config:
    def __init__(self):
        """初始化配置"""
        self._config = self._load_config()
        
        # Telegram 配置
        self.token = self._config['telegram']['token']
        
        # Google API 配置
        self.google_api_key = self._config['google']['api_key']
        
        # 模型配置
        self.online_search_model = self._config['models']['online_search']
        self.default_model = self._config['models']['default']
        self.fallback_model = self._config['models']['fallback']
        self.check_model = self._config['models']['check']
        self.trans_model = self._config['models']['translate']
        self.sight_model = self._config['models']['sight']
        self.compress_model = self._config['models']['compress']
        self.long_chat_model=self._config['models']['long_chat']
        self.no_restrict_model=self._config['models']['no_restrict']
        self.math_model=self._config['models']['math']
        self.code_model=self._config['models']['code']
        
        # OpenAI 配置
        self.openai_key = self._config['openai']['api_key']
        self.openai_base_url = self._config['openai']['base_url']
        self.moderate_key = self._config['openai']['moderation_key']
        self.moderate_url = self._config['openai']['moderation_url']
        
        # 聊天配置
        self.chat_threshold = self._config['chat_settings']['chat_threshold']
        self.expire_minutes = self._config['chat_settings']['expire_minutes']
        
        # 端点配置
        self.sdxl_endpoint = self._config['endpoints']['sdxl']
        self.improve_prompt_endpoint = self._config['endpoints']['improve_prompt']
        self.image_gen_endpoint = self._config['endpoints']['image_gen']

    def print_config(self):
        """打印配置"""
        print(self._config)

    def _load_config(self):
        """加载配置文件"""
        try:
            with open('misc/config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception("配置文件 'config.json' 未找到")
        except json.JSONDecodeError:
            raise Exception("配置文件 'config.json' 格式错误")
        


ai_config = Config()