from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field

env_path = Path(__file__).parent / '.env'

class Settings(BaseSettings):
    bot_token: SecretStr
    start_message: str
    input_question_message: str
    start_search: str
    help_msg:str
    model_config = SettingsConfigDict(env_file=env_path, env_file_encoding='utf-8')
config = Settings()