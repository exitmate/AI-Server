import asyncio
from .mongodb import DatabaseConfig
from .mongodb.connection import AsyncMongoDBConnection
from .utils import load_env_config
import os

async def test_database_connection():
    print("=== 데이터베이스 연결 테스트 시작 ===")
    
    try:
        env = load_env_config()
        print(f"현재 환경: {env}")
        
        config = DatabaseConfig()
        print(f"데이터베이스 설정: {config.get_connection_string()}")
        connection = AsyncMongoDBConnection(config)
        
        print("MongoDB 연결 시도 중...")
        is_connected = await connection.connect()
        
        if is_connected:
            print("MongoDB 연결 성공")
            
            is_still_connected = await connection.is_connected()
            if is_still_connected:
                print("연결 상태 확인 성공")
            else:
                print("연결 상태 확인 실패")
            
            collections = await connection.list_collections()
            print(f"컬렉션 목록: {collections}")
            
            stats = await connection.get_database_stats()
            if stats:
                print(f"데이터베이스 통계: {stats.get('collections', 0)}개 컬렉션, {stats.get('objects', 0)}개 문서")
            
            await connection.disconnect()
            print("연결 해제 완료")
            
        else:
            print("MongoDB 연결 실패")
            
    except Exception as e:
        print(f"데이터베이스 테스트 중 오류 발생: {e}")

def main():
    print(f"크롤링 서버 시작 - 환경: {os.environ['PYTHON_ENV']}")
    
    asyncio.run(test_database_connection())
    print("서버가 성공적으로 시작되었습니다!")

def production():
    os.environ['PYTHON_ENV'] = 'production'
    main()

def dev():
    os.environ['PYTHON_ENV'] = 'development'
    main()

if __name__ == "__main__":
    if 'PYTHON_ENV' not in os.environ:
        os.environ['PYTHON_ENV'] = 'development'
    main() 