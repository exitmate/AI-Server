import logging
from typing import Optional, Dict, Any
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from .config import DatabaseConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncMongoDBConnection:
    """MongoDB Connection Instance 클래스"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        MongoDB 연결 초기화
        
        Args:
            config: 데이터베이스 설정 (None인 경우 기본 설정 사용)
        """
        self.config = config or DatabaseConfig()
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self._is_connected = False
    
    async def connect(self) -> bool:
        """
        MongoDB에 연결
        
        Returns:
            연결 성공 여부
        """
        try:
            connection_string = self.config.get_connection_string()
            logger.info(f"MongoDB 연결 시도: {self.config.host}:{self.config.port}")
            
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            await self.client.admin.command('ping')
            
            self.database = self.client[self.config.get_database_name()]
            
            self._is_connected = True
            logger.info(f"MongoDB 연결 성공: {self.config.get_database_name()}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB 연결 실패: {e}")
            self._is_connected = False
            return False
        except Exception as e:
            logger.error(f"MongoDB 연결 중 오류 발생: {e}")
            self._is_connected = False
            return False
    
    async def disconnect(self) -> None:
        """MongoDB 연결 해제"""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self._is_connected = False
            logger.info("MongoDB 연결 해제")
    
    async def is_connected(self) -> bool:
        """
        연결 상태 확인
        
        Returns:
            연결 상태
        """
        if not self._is_connected or not self.client:
            return False
        
        try:
            await self.client.admin.command('ping')
            return True
        except:
            self._is_connected = False
            return False
    
    def get_database(self) -> Optional[AsyncIOMotorDatabase]:
        """
        데이터베이스 객체 반환
        
        Returns:
            MongoDB 데이터베이스 객체
        """
        if not self._is_connected:
            logger.warning("MongoDB에 연결되지 않았습니다.")
            return None
        return self.database
    
    def get_collection(self, collection_name: str) -> Optional[AsyncIOMotorCollection]:
        """
        컬렉션 객체 반환
        
        Args:
            collection_name: 컬렉션 이름
            
        Returns:
            MongoDB 컬렉션 객체
        """
        database = self.get_database()
        if database:
            return database[collection_name]
        return None
    
    async def list_collections(self) -> list:
        """
        컬렉션 목록 반환
        
        Returns:
            컬렉션 목록
        """
        database = self.get_database()
        if database:
            return await database.list_collection_names()
        return []
    
    async def create_collection(self, collection_name: str, **kwargs) -> Optional[AsyncIOMotorCollection]:
        """
        컬렉션 생성
        
        Args:
            collection_name: 컬렉션 이름
            **kwargs: 컬렉션 생성 옵션
            
        Returns:
            생성된 컬렉션 객체
        """
        database = self.get_database()
        if database:
            try:
                return await database.create_collection(collection_name, **kwargs)
            except Exception as e:
                logger.error(f"컬렉션 생성 실패: {e}")
                return None
        return None
    
    async def drop_collection(self, collection_name: str) -> bool:
        """
        컬렉션 삭제
        
        Args:
            collection_name: 컬렉션 이름
            
        Returns:
            삭제 성공 여부
        """
        database = self.get_database()
        if database:
            try:
                await database.drop_collection(collection_name)
                logger.info(f"컬렉션 삭제 성공: {collection_name}")
                return True
            except Exception as e:
                logger.error(f"컬렉션 삭제 실패: {e}")
                return False
        return False
    
    async def get_database_stats(self) -> Optional[Dict[str, Any]]:
        """
        데이터베이스 통계 정보 반환
        
        Returns:
            데이터베이스 통계 정보
        """
        database = self.get_database()
        if database:
            try:
                return await database.command("dbStats")
            except Exception as e:
                logger.error(f"데이터베이스 통계 조회 실패: {e}")
                return None
        return None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect() 