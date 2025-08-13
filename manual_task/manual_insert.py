"""
수동 공고 등록 유틸리티

사용 예시:
# 최소 인자(필수 4개): 제목, 주최, 첨부 디렉토리, 수기 텍스트 파일
# 하단 예시를 사용할 때 반드시 title, host 그리고 첨부 디렉토리는 직접 수정하기!

python manual_task/manual_insert.py \
    --title "서울시 폐업점포 철거지원" \
    --host "서울특별시" \
    --attachments-dir manual_task \
    --manual-text-file manual_task/notice.txt

"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.utils import env_loader
from src.processing.parser.upstage_parser import parse_document_with_upstage, extract_text
from src.processing.formatter.gpt_formatter import format_with_gpt
from src.pipeline.schemas.common_schema import schema as COMMON_SCHEMA
from src.utils.date_utils import convert_support_projects_dates
from src.mongodb.config import DatabaseConfig
from src.mongodb.connection import AsyncMongoDBConnection
from src.mongodb.operations import AsyncMongoDBOperations


# -----------------------------
# 입력 데이터 모델 (가독성 용)
# -----------------------------
@dataclass
class ManualCrawledData:
    title: str
    host: str
    bodyText: Optional[str] = None  # 수기 본문 텍스트(권장)


def _read_manual_text(file_path: Optional[str]) -> Optional[str]:
    if not file_path:
        return None
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"수기 텍스트 파일이 없습니다: {file_path}")
    return p.read_text(encoding="utf-8")


def _parse_attachments_with_upstage(attachments_dir: str, notice_title: str) -> List[Dict[str, Any]]:
    """
    업스테이지 파서를 사용해 첨부파일을 텍스트로 변환.
    - 기존 `parse_files.py`와 유사한 형태로 "파싱결과" 필드를 만들어 둡니다.
    - ZIP 등 비대상 포맷은 스킵합니다.
    """
    results: List[Dict[str, Any]] = []
    # 스크립트와 같은 디렉토리를 사용할 수 있으므로, 문서형 확장자만 허용해 안전하게 필터링
    allowed_exts = {
        ".pdf", ".hwp", ".hwpx", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".jpg", ".jpeg", ".png"
    }
    base = Path(attachments_dir)
    if not base.exists() or not base.is_dir():
        raise NotADirectoryError(f"첨부 디렉토리를 찾을 수 없습니다: {attachments_dir}")

    for file_path in sorted(base.iterdir()):
        if not file_path.is_file():
            continue
        name_lower = file_path.name.lower()
        if name_lower.endswith(".zip"):
            print(f"ZIP 파일 스킵: {file_path.name}")
            continue
        if file_path.suffix.lower() not in allowed_exts:
            # 파이썬 파일 등 비문서 파일은 스킵 (같은 폴더에 스크립트가 있을 수 있음)
            continue

        print(f"업스테이지 파싱 시작: {file_path.name}")
        try:
            parsed = parse_document_with_upstage(str(file_path))
            text_only = extract_text(parsed)
        except Exception as e:
            print(f"업스테이지 파싱 실패: {file_path.name} → {e}")
            continue

        results.append(
            {
                "공고제목": notice_title,
                "파일명": file_path.name,
                "파싱결과": text_only,
            }
        )

    return results


def _build_combined_payload(manual: ManualCrawledData, parsed_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    GPT에 전달할 텍스트(JSON 문자열) 구성을 위해 원본 Dict를 만듭니다.
    - 기존 포매터는 내부에서 prompt를 만들며, 여기에 전달되는 데이터는 자유형입니다.
    - 다만 일관성을 위해 "crawled_data" / "parsed_data" 키를 그대로 유지합니다.
    """
    crawled_entry: Dict[str, Any] = {
        "제목": manual.title,
        "주최": manual.host,
    }

    # 선택 필드: 본문만 유지 (첨부 텍스트와 함께 LLM 정확도 향상)
    if manual.bodyText:
        crawled_entry["본문"] = manual.bodyText

    return {
        "crawled_data": [crawled_entry],
        "parsed_data": parsed_items,
    }


def _normalize_formatted_result(result_from_llm: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    LLM이 반환한 결과(JSON)를 표준 형태로 변환.
    - 기대: [{ "supportProjects": [...], "services": [...] }]
    - 변형: { "supportProjects": [...], "services": [...] }도 허용
    반환: (support_projects, services)
    """
    obj: Optional[Dict[str, Any]] = None
    if isinstance(result_from_llm, list) and len(result_from_llm) > 0 and isinstance(result_from_llm[0], dict):
        obj = result_from_llm[0]
    elif isinstance(result_from_llm, dict):
        obj = result_from_llm

    if not obj:
        return [], []

    support_projects = obj.get("supportProjects") or []
    services = obj.get("services") or []

    if not isinstance(support_projects, list):
        support_projects = []
    if not isinstance(services, list):
        services = []

    return support_projects, services


def _normalize_service_type(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip().upper()
    # 이미 enum이면 그대로
    allowed = {
        "STORE_DEMOLITION_SUBSIDY",
        "CLOSURE_SUPPORT_SUBSIDY",
        "CLOSURE_CONSULTING",
        "REEMPLOYMENT_EDUCATION",
        "BUSINESS_EDUCATION",
    }
    if s in allowed:
        return s
    # 한국어/자연어 → enum 매핑
    mapping = {
        # 철거/원상복구 지원
        "전포철거지원금": "STORE_DEMOLITION_SUBSIDY",
        "철거": "STORE_DEMOLITION_SUBSIDY",
        "원상복구": "STORE_DEMOLITION_SUBSIDY",
        # 폐업 지원금/정리 지원
        "폐업지원금": "CLOSURE_SUPPORT_SUBSIDY",
        "폐업 지원": "CLOSURE_SUPPORT_SUBSIDY",
        # 컨설팅
        "폐업 컨설팅": "CLOSURE_CONSULTING",
        "컨설팅": "CLOSURE_CONSULTING",
        # 재취업/재창업 교육
        "재취업": "REEMPLOYMENT_EDUCATION",
        "재창업": "REEMPLOYMENT_EDUCATION",
        "재취업/재창업": "REEMPLOYMENT_EDUCATION",
        # 경영 교육
        "경영 교육": "BUSINESS_EDUCATION",
        "교육": "BUSINESS_EDUCATION",
    }
    for key, val in mapping.items():
        if key.replace(" ", "") in s.replace(" ", ""):
            return val
    return None


def _parse_max_amount_to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return int(value)
        except Exception:
            return None
    s = str(value)
    # 숫자와 구분자만 남기고 파싱 (예: "3,000,000원", "300만원")
    s_clean = re.sub(r"[^0-9]", "", s)
    if not s_clean:
        return None
    try:
        return int(s_clean)
    except Exception:
        return None


def _normalize_services(services: List[Dict[str, Any]], default_project_title: str) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for svc in services:
        if not isinstance(svc, dict):
            continue
        project_title = svc.get("projectTitle") or default_project_title
        raw_type = svc.get("type")
        enum_type = _normalize_service_type(raw_type)
        max_amount = _parse_max_amount_to_int(svc.get("maxAmount"))

        item: Dict[str, Any] = {"projectTitle": project_title}
        if enum_type is not None:
            item["type"] = enum_type
        if max_amount is not None:
            item["maxAmount"] = max_amount
        normalized.append(item)
    return normalized


def _normalize_support_projects(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # 현재는 날짜 변환은 별도로 처리. 여기서는 배열/타입 정합성만 가볍게 보정
    normalized: List[Dict[str, Any]] = []
    for prj in projects:
        if not isinstance(prj, dict):
            continue
        # requiredDocs 보정: 단일 문자열이면 배열화
        required_docs = prj.get("requiredDocs")
        if isinstance(required_docs, str):
            prj["requiredDocs"] = [required_docs]
        elif required_docs is None:
            prj["requiredDocs"] = []
        normalized.append(prj)
    return normalized


async def _insert_into_mongo(support_projects: List[Dict[str, Any]], services: List[Dict[str, Any]]) -> None:
    """
    MongoDB에 결과를 삽입합니다.
    - 날짜 필드는 가능한 datetime으로 변환하여 저장(쿼리/정렬에 유리)
    - 컬렉션명은 환경변수 또는 기본값 사용
    """
    # 컬렉션명 고정
    projects_col = "SupportProject"
    services_col = "Service"

    # 날짜 변환: convert_support_projects_dates는 dict 형태를 기대하므로 감싸서 사용
    container: Dict[str, Any] = {"supportProjects": support_projects}
    container = convert_support_projects_dates(container)
    support_projects = container.get("supportProjects", support_projects)

    # Mongo 연결 및 삽입
    config = DatabaseConfig()
    async with AsyncMongoDBConnection(config) as connection:
        if not await connection.is_connected():
            raise ConnectionError("MongoDB 연결에 실패했습니다.")

        operations = AsyncMongoDBOperations(connection)

        if support_projects:
            inserted_ids = await operations.insert_many(projects_col, support_projects)
            print(f"SupportProjects 삽입: {0 if inserted_ids is None else len(inserted_ids)}건")
        else:
            print("SupportProjects 없음")

        if services:
            inserted_ids = await operations.insert_many(services_col, services)
            print(f"Services 삽입: {0 if inserted_ids is None else len(inserted_ids)}건")
        else:
            print("Services 없음")


# 유저가 입력하는 인자들을 정의
# 공고 제목, 주최단체는 확정적인 결과값 정의를 위해 유저가 직접 입력하도록 했음
# 공고 첨부파일은 필수, 그리고 llm에게 좀 더 상세한 결과값을 위해 직접 우리가 입력하는 텍스트 파일 경로도 넣음(이건 필수X)
def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="수동 공고 등록 유틸리티")
    p.add_argument("--attachments-dir", type=str, required=True, help="첨부파일 디렉토리 절대경로(필수)")
    p.add_argument("--manual-text-file", type=str, required=True, help="공고 상세 텍스트 파일 절대경로(필수)")

    # 최소 메타데이터
    p.add_argument("--title", type=str, required=True, help="공고 제목")
    p.add_argument("--host", type=str, required=True, help="주최/주관 단체")

    return p


def _ensure_env_loaded() -> None:
    # .env 로드. 별도 지정 없으면 PYTHON_ENV 또는 development
    env_loader.load_env_config(None)


def _run_gpt_formatter(combined_payload: Dict[str, Any]) -> Any:
    # 기존 포매터는 내부에서 prompt 생성. 우리는 JSON 문자열로 투입
    json_text = json.dumps(combined_payload, ensure_ascii=False)

    return format_with_gpt(json_text, COMMON_SCHEMA)

# 이 함수의 각 단계별로 로그 출력
async def _run(args: argparse.Namespace) -> None:
    _ensure_env_loaded()

    # 수기 텍스트 파일 읽고 manual 객체로 관련 데이터들을 묶어 저장
    manual = ManualCrawledData(
        title=args.title,
        host=args.host,
        bodyText=_read_manual_text(args.manual_text_file),
    )

    # 첨부 파싱 후 결과값 초반 일부만 로그로 출력
    parsed_items = _parse_attachments_with_upstage(args.attachments_dir, notice_title=args.title)
    if parsed_items:
        preview_text = parsed_items[0].get("파싱결과", "")
        print(f"첨부 파싱 결과: {preview_text[:100]}...")
    else:
        print("첨부 파싱 결과 없음")

    combined_payload = _build_combined_payload(manual, parsed_items)
    print("GPT 변환 시작...")
    llm_result = _run_gpt_formatter(combined_payload)

    if not llm_result:
        print("LLM 결과가 비어 있습니다. 종료합니다.")
        return

    support_projects, services = _normalize_formatted_result(llm_result)
    # 스키마 정합성 보정
    support_projects = _normalize_support_projects(support_projects)
    services = _normalize_services(services, default_project_title=args.title)
    print(f"LLM 결과 - SupportProjects: {len(support_projects)}개, Services: {len(services)}개")

    await _insert_into_mongo(support_projects, services)
    print("MongoDB 삽입 완료")


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()


