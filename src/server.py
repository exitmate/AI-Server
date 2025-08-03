import uvicorn
import os
from .utils import load_env_config


# poetry run dev로 실행시키는 파일, 즉 서버실행용 파일이다. 현재 환경에 맞는 서버를 실행시킨다. 지금은 배포나 dev나 별차이없음


def run_dev_server():
    os.environ['PYTHON_ENV'] = 'development'
    uvicorn.run("src.app:app", reload=True)


def run_production_server():
    os.environ['PYTHON_ENV'] = 'production'
    uvicorn.run("src.app:app", reload=True)

if __name__ == "__main__":
    env = load_env_config()
    run_production_server() if env == "production" else run_dev_server()
