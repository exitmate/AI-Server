import os
import requests
from pathlib import Path
from typing import Dict, Any
from bs4 import BeautifulSoup

from src.utils import env_loader

# ===============================
# 업스테이지 API 설정
# ===============================
env = env_loader.load_env_config("development")
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY") 

if not UPSTAGE_API_KEY:
    raise EnvironmentError("환경 변수 'UPSTAGE_API_KEY'가 설정되지 않았습니다.")

API_URL = "https://api.upstage.ai/v1/document-digitization"
HEADERS = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}


# ===============================
# 문서 파싱 함수
# ===============================
def parse_document_with_upstage(file_path: str, ocr: str = "force", model: str = "document-parse") -> Dict[str, Any]:
    """
    업스테이지 Document Parsing API로 문서를 파싱하고 text 필드가 비어있으면 html을 파싱해서 채움.
    """
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    files = {"document": open(file, "rb")}
    data = {
        "ocr": ocr,
        "base64_encoding": "['table']",
        "model": model
    }

    print(f"업스테이지 API 요청: {file.name}")
    response = requests.post(API_URL, headers=HEADERS, files=files, data=data)
    files["document"].close()

    if response.status_code != 200:
        raise RuntimeError(f"업스테이지 API 요청 실패: {response.status_code}, {response.text}")

    result = response.json()
    for element in result.get("elements", []):
      if not element["content"].get("text"):
          html_content = element["content"].get("html", "")
          if html_content:
              soup = BeautifulSoup(html_content, "html.parser")
              element["content"]["text"] = soup.get_text(separator="\n").strip()

    return result



def extract_text(parsed_result: Dict[str, Any]) -> str:
    """파싱 결과(JSON)에서 텍스트만 합쳐서 반환"""
    texts = []
    for element in parsed_result.get("elements", []):
        text = element["content"].get("text")
        if not text:
            html_content = element["content"].get("html", "")
            if html_content:
                soup = BeautifulSoup(html_content, "html.parser")
                text = soup.get_text(separator="\n").strip()
        if text:
            texts.append(text)
    return "\n".join(texts)
