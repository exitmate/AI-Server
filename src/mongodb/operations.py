import logging
from typing import List, Dict, Any, Optional, Union
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import PyMongoError
from .connection import AsyncMongoDBConnection

logger = logging.getLogger(__name__)


class AsyncMongoDBOperations:
    """MongoDB CRUD 클래스"""
    
    def __init__(self, connection: AsyncMongoDBConnection):
        """
        MongoDB 연결 초기화
        
        Args:
            connection: MongoDB 연결 객체
        """
        self.connection = connection
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        """
        단일 문서 삽입
        
        Args:
            collection_name: 컬렉션 이름
            document: 삽입할 문서
            
        Returns:
            삽입된 문서의 ObjectId (문자열)
        """
        collection = self.connection.get_collection(collection_name)
        try:
            result = await collection.insert_one(document)
            logger.info(f"문서 삽입 성공: {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"문서 삽입 실패: {e}")
            return None
    
    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> Optional[List[str]]:
        """
        여러 문서 삽입
        
        Args:
            collection_name: 컬렉션 이름
            documents: 삽입할 문서 리스트
            
        Returns:
            삽입된 문서들의 ObjectId 리스트
        """
        collection = self.connection.get_collection(collection_name)
        try:
            result = await collection.insert_many(documents)
            inserted_ids = [str(id) for id in result.inserted_ids]
            logger.info(f"문서 삽입 성공: {len(inserted_ids)}개")
            return inserted_ids
        except PyMongoError as e:
            logger.error(f"문서 삽입 실패: {e}")
            return None
    
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any], projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        단일 문서 조회
        
        Args:
            collection_name: 컬렉션 이름
            filter_dict: 조회 조건
            projection: 조회할 필드 지정
            
        Returns:
            조회된 문서
        """
        collection = self.connection.get_collection(collection_name)
        try:
            document = await collection.find_one(filter_dict, projection)
            if document:
                logger.info(f"문서 조회 성공: {filter_dict}")
            else:
                logger.info(f"문서를 찾을 수 없습니다: {filter_dict}")
            return document
        except PyMongoError as e:
            logger.error(f"문서 조회 실패: {e}")
            return None
    
    async def find_many(self, collection_name: str, filter_dict: Dict[str, Any], projection: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """
        여러 문서 조회
        
        Args:
            collection_name: 컬렉션 이름
            filter_dict: 조회 조건
            projection: 조회할 필드 지정
            limit: 조회할 문서 수 제한
            sort: 정렬 조건 [(필드명, 방향), ...]
            
        Returns:
            조회된 문서 리스트
        """
        collection = self.connection.get_collection(collection_name)
        try:
            cursor = collection.find(filter_dict, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            
            if limit:
                cursor = cursor.limit(limit)
            
            documents = await cursor.to_list(length=limit or 0)
            logger.info(f"문서 조회 성공: {len(documents)}개")
            return documents
        except PyMongoError as e:
            logger.error(f"문서 조회 실패: {e}")
            return []
    
    async def update_one(self, collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any], upsert: bool = False) -> bool:
        """
        단일 문서 업데이트
        
        Args:
            collection_name: 컬렉션 이름
            filter_dict: 업데이트할 문서 조건
            update_dict: 업데이트할 내용
            upsert: 문서가 없으면 생성할지 여부
            
        Returns:
            업데이트 성공 여부
        """
        collection = self.connection.get_collection(collection_name)
        try:
            result = await collection.update_one(filter_dict, update_dict, upsert=upsert)
            logger.info(f"문서 업데이트 성공: {result.modified_count}개 수정, {result.upserted_id} 생성")
            return True
        except PyMongoError as e:
            logger.error(f"문서 업데이트 실패: {e}")
            return False
    
    async def update_many(self, collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any], upsert: bool = False) -> bool:
        """
        여러 문서 업데이트
        
        Args:
            collection_name: 컬렉션 이름
            filter_dict: 업데이트할 문서 조건
            update_dict: 업데이트할 내용
            upsert: 문서가 없으면 생성할지 여부
            
        Returns:
            업데이트 성공 여부
        """
        collection = self.connection.get_collection(collection_name)
        try:
            result = await collection.update_many(filter_dict, update_dict, upsert=upsert)
            logger.info(f"문서 업데이트 성공: {result.modified_count}개 수정, {result.upserted_id} 생성")
            return True
        except PyMongoError as e:
            logger.error(f"문서 업데이트 실패: {e}")
            return False
    
    async def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """
        단일 문서 삭제
        
        Args:
            collection_name: 컬렉션 이름
            filter_dict: 삭제할 문서 조건
            
        Returns:
            삭제 성공 여부
        """
        collection = self.connection.get_collection(collection_name)
        try:
            result = await collection.delete_one(filter_dict)
            logger.info(f"문서 삭제 성공: {result.deleted_count}개")
            return True
        except PyMongoError as e:
            logger.error(f"문서 삭제 실패: {e}")
            return False
    
    async def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """
        여러 문서 삭제
        
        Args:
            collection_name: 컬렉션 이름
            filter_dict: 삭제할 문서 조건
            
        Returns:
            삭제 성공 여부
        """
        collection = self.connection.get_collection(collection_name)
        try:
            result = await collection.delete_many(filter_dict)
            logger.info(f"문서 삭제 성공: {result.deleted_count}개")
            return True
        except PyMongoError as e:
            logger.error(f"문서 삭제 실패: {e}")
            return False
    
    async def count_documents(self, collection_name: str, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """
        문서 수 계산
        
        Args:
            collection_name: 컬렉션 이름
            filter_dict: 계산할 문서 조건 (None이면 전체)
            
        Returns:
            문서 수
        """
        collection = self.connection.get_collection(collection_name)
        try:
            count = await collection.count_documents(filter_dict or {})
            logger.info(f"문서 수 계산 성공: {count}개")
            return count
        except PyMongoError as e:
            logger.error(f"문서 수 계산 실패: {e}")
            return 0
    
    async def create_index(self, collection_name: str, index_fields: List[tuple], index_name: Optional[str] = None, unique: bool = False) -> bool:
        """
        인덱스 생성
        
        Args:
            collection_name: 컬렉션 이름
            index_fields: 인덱스 필드 리스트 [(필드명, 방향), ...]
            index_name: 인덱스 이름 (None이면 자동 생성)
            unique: 유니크 인덱스 여부
            
        Returns:
            인덱스 생성 성공 여부
        """
        collection = self.connection.get_collection(collection_name)
        try:
            if index_name:
                await collection.create_index(index_fields, name=index_name, unique=unique)
            else:
                await collection.create_index(index_fields, unique=unique)
            
            logger.info(f"인덱스 생성 성공: {index_fields}")
            return True
        except PyMongoError as e:
            logger.error(f"인덱스 생성 실패: {e}")
            return False
    
    async def drop_index(self, collection_name: str, index_name: str) -> bool:
        """
        인덱스 삭제
        
        Args:
            collection_name: 컬렉션 이름
            index_name: 삭제할 인덱스 이름
            
        Returns:
            인덱스 삭제 성공 여부
        """
        collection = self.connection.get_collection(collection_name)
        try:
            await collection.drop_index(index_name)
            logger.info(f"인덱스 삭제 성공: {index_name}")
            return True
        except PyMongoError as e:
            logger.error(f"인덱스 삭제 실패: {e}")
            return False 