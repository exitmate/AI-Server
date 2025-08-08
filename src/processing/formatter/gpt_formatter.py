import json
import os
from openai import OpenAI

from src.utils import env_loader

env = env_loader.load_env_config("development")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_with_gpt(text: str, schema: dict):
    from datetime import datetime
    current_time = datetime.now().strftime("%Y년 %m월 %d일")
    
    prompt = f"""
    현재 시점: {current_time} (이 날짜를 기준으로 판단하세요)
    
    아래는 두 가지 데이터셋입니다:
    1) 크롤링 데이터: 웹사이트에서 직접 수집한 기본 정보
    2) 파싱 데이터: 첨부 문서에서 추출한 상세 정보

    이 두 데이터를 통합 분석하여, 다음 스키마에 맞는 JSON 배열을 생성해줘.
    데이터가 겹칠 경우 보완하거나 합쳐서 하나의 결과로 반환해.
    반드시 코드블록 없이(JSON 배열만) 출력해.
    isOpen 필드는 현재 시점을 기준으로 판단해.
    현재 시점이 신청 가능 기간 내에 있으면 True, 아니면 False로 판단해.
    createdAt, updatedAt 필드는 현재시점과 동일하게 설정해.

    스키마:
    {json.dumps(schema, ensure_ascii=False)}

    데이터:
    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "너는 JSON 변환 도우미야. 반드시 유효한 JSON만 반환해야 한다."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    output = response.choices[0].message.content.strip()

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print("JSON 파싱 실패. 응답:", output)
        return []

# 전체 파이프라인 (크롤링+파싱 데이터 통합)
def process_parsed_results(crawled_json_path: str, parsed_json_path: str, schema: dict):
    # 크롤링 결과 로드
    with open(crawled_json_path, "r", encoding="utf-8") as f:
        crawled_data = json.load(f)

    # 파싱 결과 로드
    with open(parsed_json_path, "r", encoding="utf-8") as f:
        parsed_data = json.load(f)

    print(f"[3] GPT JSON 변환 실행 중... 크롤링 {len(crawled_data)}개 + 파싱 {len(parsed_data)}개 항목")

    # 두 데이터 합쳐서 GPT에 전달
    combined_payload = {
        "crawled_data": crawled_data,
        "parsed_data": parsed_data
    }

    json_text = json.dumps(combined_payload, ensure_ascii=False)
    result = format_with_gpt(json_text, schema)

    return result
