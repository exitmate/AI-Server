from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .utils import load_env_config


env = load_env_config("development")

app = FastAPI()

# 개발 단계에선 cors 무지성 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 테스트용 라우터
@app.get("/")
async def root():
    return {"AI": "Server", "env": env}


