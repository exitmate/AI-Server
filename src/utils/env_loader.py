import os
from typing import Optional
from dotenv import load_dotenv


def load_env_config(env: Optional[str] = None) -> str:
    """
    환경에 맞는 .env 파일을 로드합니다.
    
    Args:
        env: 환경명 (development, production). 
             None인 경우 PYTHON_ENV 환경변수 사용
    
    Returns:
        로드된 환경명
        
    Examples:
        >>> load_env_config('development')  # .env.development 로드
        >>> load_env_config('production')   # .env 로드
        >>> load_env_config()               # PYTHON_ENV 환경변수 기반으로 로드
    """
    if env is None:
        env = os.getenv('PYTHON_ENV', 'development').lower()
    else:
        env = env.lower()

    env_files = {
        'development': '.env.development',
        'production': '.env',
    }

    env_file = env_files.get(env, '.env.development')

    load_dotenv(env_file)
    
    print(f"환경 설정 로드: {env} ({env_file})")
    return env


def get_environment() -> str:
    """
    현재 환경을 반환합니다.
    
    Returns:
        현재 환경명
    """
    return os.getenv('PYTHON_ENV', 'development').lower() 