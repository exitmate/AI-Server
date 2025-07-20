# MongoDB 연결 인터페이스

MongoDB와의 연결 및 CRUD 작업을 위한 Python 패키지입니다.
모든 API는 비동기 사용을 전제로 작성되어, async with 구문과 함께 사용해야 합니다.


## 데이터베이스 연결 설정

### 환경변수 설정 (.env 파일)

```env
# MongoDB 연결 설정
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=crawling_db
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password
MONGODB_AUTH_SOURCE=admin
MONGODB_AUTH_MECHANISM=SCRAM-SHA-1

# 또는 Connection String으로 한 번에 정의 가능 (본 옵션은 위의 설정을 Override함)
MONGODB_CONNECTION_STRING=mongodb://username:password@host:port/database
```

## 사용법

### 1. 데이터베이스 설정

```python
from mongodb import DatabaseConfig

# 방법 1: 직접 설정
config = DatabaseConfig(
    host="localhost",
    port=27017,
    database="crawling_db"
)

# 방법 2: 환경변수에서 자동 로드
config = DatabaseConfig()
```

### 2. 데이터베이스 연결

```python
from mongodb import AsyncMongoDBConnection, AsyncMongoDBOperations
import asyncio

async def main():
    # 연결 설정
    config = DatabaseConfig(
        host="localhost",
        port=27017,
        database="crawling_db"
    )
    
    # 컨텍스트 매니저를 사용한 연결
    async with AsyncMongoDBConnection(config) as connection:
        if not await connection.is_connected():
            print("MongoDB 연결에 실패했습니다.")
            return
        
        print("MongoDB 연결 성공!")
        
        # 작업 객체 생성
        operations = AsyncMongoDBOperations(connection)
        
        # 여기에 데이터베이스 작업 코드 작성

# 실행
asyncio.run(main())
```

## CRUD 작업

### 컬렉션 생성

```python
# 컬렉션 생성
collection_name = "crawled_data"
await connection.create_collection(collection_name)
```

### 인덱스 생성

```python
# 단일 필드 인덱스
await operations.create_index(collection_name, [("url", 1)], unique=True)

# 복합 인덱스
await operations.create_index(collection_name, [("created_at", -1), ("status", 1)])

# 유니크 인덱스
await operations.create_index(collection_name, [("email", 1)], unique=True)
```

### 데이터 삽입

```python
from datetime import datetime

# 단일 문서 삽입
sample_data = {
    "url": "https://example.com",
    "title": "예제 페이지",
    "content": "이것은 크롤링된 데이터입니다.",
    "created_at": datetime.now(),
    "status": "success"
}

inserted_id = await operations.insert_one(collection_name, sample_data)
if inserted_id:
    print(f"문서 삽입 성공: {inserted_id}")

# 여러 문서 삽입
multiple_data = [
    {
        "url": "https://example1.com",
        "title": "예제 페이지 1",
        "content": "첫 번째 크롤링 데이터",
        "created_at": datetime.now(),
        "status": "success"
    },
    {
        "url": "https://example2.com",
        "title": "예제 페이지 2",
        "content": "두 번째 크롤링 데이터",
        "created_at": datetime.now(),
        "status": "success"
    }
]

inserted_ids = await operations.insert_many(collection_name, multiple_data)
if inserted_ids:
    print(f"여러 문서 삽입 성공: {len(inserted_ids)}개")
```

### 데이터 조회

```python
# 단일 문서 조회
document = await operations.find_one(collection_name, {"url": "https://example.com"})
if document:
    print(f"조회된 문서: {document['title']}")

# 여러 문서 조회 (최근 10개)
documents = await operations.find_many(
    collection_name,
    {"status": "success"},
    limit=10,
    sort=[("created_at", -1)]
)
print(f"조회된 문서 수: {len(documents)}개")

# 특정 필드만 조회
documents = await operations.find_many(
    collection_name,
    {"status": "success"},
    projection={"title": 1, "url": 1, "_id": 0}
)
```

### 데이터 업데이트

```python
# 단일 문서 업데이트
update_result = await operations.update_one(
    collection_name,
    {"url": "https://example.com"},
    {"$set": {"status": "updated", "updated_at": datetime.now()}}
)
if update_result:
    print("문서 업데이트 성공")

# 여러 문서 업데이트
update_result = await operations.update_many(
    collection_name,
    {"status": "pending"},
    {"$set": {"status": "processed"}}
)

# upsert 옵션 (문서가 없으면 생성)
update_result = await operations.update_one(
    collection_name,
    {"url": "https://new-example.com"},
    {"$set": {"title": "새 페이지", "created_at": datetime.now()}},
    upsert=True
)
```

### 데이터 삭제

```python
# 단일 문서 삭제
delete_result = await operations.delete_one(collection_name, {"url": "https://example.com"})
if delete_result:
    print("문서 삭제 성공")

# 여러 문서 삭제
delete_result = await operations.delete_many(collection_name, {"status": "error"})
if delete_result:
    print("문서들 삭제 성공")
```

### 문서 수 계산

```python
# 전체 문서 수
total_count = await operations.count_documents(collection_name)
print(f"전체 문서 수: {total_count}")

# 조건에 맞는 문서 수
success_count = await operations.count_documents(collection_name, {"status": "success"})
print(f"성공 상태 문서 수: {success_count}")
```

## 데이터베이스 관리

### 컬렉션 목록 확인

```python
collections = await connection.list_collections()
print(f"컬렉션 목록: {collections}")
```

### 데이터베이스 통계 확인

```python
stats = await connection.get_database_stats()
if stats:
    print(f"데이터베이스 크기: {stats.get('dataSize', 0)} bytes")
    print(f"컬렉션 수: {stats.get('collections', 0)}")
```

### 컬렉션 삭제

```python
success = await connection.drop_collection("temp_collection")
if success:
    print("컬렉션 삭제 성공")
```

### 인덱스 삭제

```python
success = await operations.drop_index(collection_name, "index_name")
if success:
    print("인덱스 삭제 성공")
```

## 동시 작업 예제

```python
import asyncio

async def concurrent_operations_example():
    config = DatabaseConfig(
        host="localhost",
        port=27017,
        database="crawling_db"
    )
    
    async with AsyncMongoDBConnection(config) as connection:
        if not await connection.is_connected():
            print("MongoDB 연결에 실패했습니다.")
            return
        
        operations = AsyncMongoDBOperations(connection)
        collection_name = "concurrent_test"
        
        # 여러 작업을 동시에 실행
        tasks = []
        
        # 10개의 문서를 동시에 삽입
        for i in range(10):
            data = {
                "index": i,
                "message": f"동시 작업 테스트 {i}",
                "timestamp": datetime.now()
            }
            task = operations.insert_one(collection_name, data)
            tasks.append(task)
        
        # 모든 작업을 동시에 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for result in results if result is not None)
        print(f"동시 삽입 성공: {success_count}/10개")

# 실행
asyncio.run(concurrent_operations_example())
```

## 에러 처리

```python
async def safe_database_operation():
    try:
        async with AsyncMongoDBConnection(config) as connection:
            if not await connection.is_connected():
                raise ConnectionError("MongoDB 연결에 실패했습니다.")
            
            operations = AsyncMongoDBOperations(connection)
            
            # 데이터베이스 작업 수행
            result = await operations.insert_one("test_collection", {"test": "data"})
            
            if result is None:
                raise Exception("데이터 삽입에 실패했습니다.")
                
            print("작업 성공!")
            
    except ConnectionError as e:
        print(f"연결 오류: {e}")
    except Exception as e:
        print(f"일반 오류: {e}")
```

## 주요 클래스 및 메서드

### DatabaseConfig
- `__init__()`: 데이터베이스 설정 초기화
- `get_connection_string()`: MongoDB 연결 문자열 생성
- `get_database_name()`: 데이터베이스 이름 반환
- `to_dict()`: 설정을 딕셔너리로 변환

### AsyncMongoDBConnection
- `connect()`: MongoDB에 연결
- `disconnect()`: MongoDB 연결 해제
- `is_connected()`: 연결 상태 확인
- `get_database()`: 데이터베이스 객체 반환
- `get_collection()`: 컬렉션 객체 반환
- `list_collections()`: 컬렉션 목록 반환
- `create_collection()`: 컬렉션 생성
- `drop_collection()`: 컬렉션 삭제
- `get_database_stats()`: 데이터베이스 통계 정보 반환

### AsyncMongoDBOperations
- `insert_one()`: 단일 문서 삽입
- `insert_many()`: 여러 문서 삽입
- `find_one()`: 단일 문서 조회
- `find_many()`: 여러 문서 조회
- `update_one()`: 단일 문서 업데이트
- `update_many()`: 여러 문서 업데이트
- `delete_one()`: 단일 문서 삭제
- `delete_many()`: 여러 문서 삭제
- `count_documents()`: 문서 수 계산
- `create_index()`: 인덱스 생성
- `drop_index()`: 인덱스 삭제
