import os
from .mongodb import DatabaseConfig

def load_env_config():
    """.env 파일 로드"""
    env = os.getenv('PYTHON_ENV', 'development').lower()
    
    env_files = {
        'development': '.env.development',
        'production': '.env'
    }
    
    env_file = env_files.get(env, '.env.development')
    
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    print(f"환경 설정 로드: {env} ({env_file})")
    return env

def main():
    """기본 메인 함수"""
    env = load_env_config()
    print(f"크롤링 서버 시작 - 환경: {env}")
    
    config = DatabaseConfig()
    print(f"데이터베이스 설정 로드됨: {config}")
    
    print("서버가 성공적으로 시작되었습니다!")

def dev():
    """개발 환경 메인 함수"""
    os.environ['PYTHON_ENV'] = 'development'
    main()

if __name__ == "__main__":
    os.environ['PYTHON_ENV'] = 'production'
    main() 