# Crawling Server for Exit Mate

## 목차

- [설치 방법](#설치-방법)
- [환경 설정](#환경-설정)
- [실행 방법](#실행-방법)

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd crawlingServer
```

### 2. Poetry 설치

https://python-poetry.org/docs/#installing-with-the-official-installer

### 3. 의존성 설치

No such file or directory 오류가 나면, PATH에 poetry의 설치 경로를 추가한 후 계속해주세요.
```bash
poetry install
```

## 환경 설정

### 1. 환경 변수 파일 생성

프로젝트 루트에 환경 변수 파일을 생성해야 합니다.

```bash
# 개발 환경용
cp env.example .env.development

# 프로덕션 환경용
cp env.example .env
```

### 2. MongoDB 설정

`.env.development` 또는 `.env` 파일을 편집하여 MongoDB 연결 정보를 설정하세요.

```env
# MongoDB 설정
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=crawling_db
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_AUTH_SOURCE=admin
MONGODB_AUTH_MECHANISM=SCRAM-SHA-1

# 또는 Connection String으로 한 번에 정의 가능 (위 설정을 Override함)
# MONGODB_CONNECTION_STRING=mongodb://username:password@host:port/database?authSource=admin
```

## 실행 방법

### 개발 환경에서 실행

```bash
poetry run dev
```

### 프로덕션 환경에서 실행

```bash
poetry run start
```



