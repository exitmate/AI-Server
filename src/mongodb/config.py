"""
데이터베이스 설정 모듈
"""

import os
from typing import Optional
from ..utils import load_env_config

class DatabaseConfig:
    """MongoDB 데이터베이스 설정 클래스"""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        auth_source: Optional[str] = None,
        auth_mechanism: Optional[str] = None,
        connection_string: Optional[str] = None
    ):
        """
        데이터베이스 설정 초기화
        
        Args:
            host: MongoDB 호스트 (default: env.MONGODB_HOST)
            port: MongoDB 포트 (default: env.MONGODB_PORT)
            username: 사용자명 (default: env.MONGODB_USERNAME)
            password: 비밀번호 (default: env.MONGODB_PASSWORD)
            database: 데이터베이스명 (default: env.MONGODB_DATABASE)
            auth_source: 인증 소스 (default: env.MONGODB_AUTH_SOURCE)
            auth_mechanism: 인증 메커니즘 (default: env.MONGODB_AUTH_MECHANISM)
            connection_string: 전체 연결 문자열. 지정된 경우 앞서 선언된 argument는 무시됨
        """

        load_env_config()
        self.connection_string = connection_string or os.getenv('MONGODB_CONNECTION_STRING')
        self.host = host or os.getenv('MONGODB_HOST', 'localhost')
        self.port = port or int(os.getenv('MONGODB_PORT', '27017'))
        self.username = username or os.getenv('MONGODB_USERNAME')
        self.password = password or os.getenv('MONGODB_PASSWORD')
        self.database = database or os.getenv('MONGODB_DATABASE', 'base_db')
        self.auth_source = auth_source or os.getenv('MONGODB_AUTH_SOURCE', 'admin')
        self.auth_mechanism = auth_mechanism or os.getenv('MONGODB_AUTH_MECHANISM', 'SCRAM-SHA-1')
    
    def get_connection_string(self) -> str:
        """
        MongoDB 연결 문자열 생성
        
        Returns:
            MongoDB 연결 문자열
        """
        if self.connection_string:
            return self.connection_string
        
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?authSource={self.auth_source}&authMechanism={self.auth_mechanism}"
        else:
            return f"mongodb://{self.host}:{self.port}/{self.database}"
    
    def get_database_name(self) -> str:
        """
        데이터베이스 이름 반환
        
        Returns:
            데이터베이스 이름
        """
        return self.database
    
    def to_dict(self) -> dict:
        """
        설정을 딕셔너리로 변환
        
        Returns:
            설정 딕셔너리
        """
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'database': self.database,
            'auth_source': self.auth_source,
            'auth_mechanism': self.auth_mechanism,
            'connection_string': self.connection_string
        } 