import os
import glob
import json
import asyncio
from typing import Callable

from src.crawl.bizinfo_crawler import crawl_bizinfo
from src.crawl.sbiz24_crawler import crawl_sbiz24

from src.mongodb.connection import AsyncMongoDBConnection
from src.mongodb.operations import AsyncMongoDBOperations
from src.processing.formatter.gpt_formatter import process_parsed_results
from src.processing.parser.parse_files import parse_files
from src.pipeline.schemas.common_schema import schema


# 크롤러 매핑
CRAWLER_MAP = {
    "bizinfo": crawl_bizinfo,
    "sbiz24": crawl_sbiz24,
}

# 파이프라인 실행 함수
async def run_pipeline(site_name: str, crawler_func: Callable):
    print(f"\n🚀 [{site_name}] 파이프라인 시작")

    # 크롤링
    crawler_func()
    print(f"[{site_name}] 크롤링 완료 → data/{site_name}_results.json")

    # 파싱 (Upstage API)
    data_dir = os.path.join(os.getcwd(), "data")
    parse_files(os.path.join(data_dir, f"{site_name}_results.json"), site_name)
    print(f"[{site_name}] 파싱 완료 → data/{site_name}_parsed_results.json")

    # GPT 변환
    formatted_results = process_parsed_results(
        f"data/{site_name}_results.json",
        f"data/{site_name}_parsed_results.json",
        schema
    )
    print(f"[{site_name}] GPT 변환 완료")

    # 결과 저장
    output_path = f"data/{site_name}_gpt_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(formatted_results, f, ensure_ascii=False, indent=2)
    print(f"[{site_name}] 변환된 데이터 저장 완료 → {output_path}")

    # DB 저장
    conn = AsyncMongoDBConnection()
    await conn.connect()
    db_ops = AsyncMongoDBOperations(conn)

    support_projects = formatted_results["supportProjects"]
    services = formatted_results["services"]

    # SupportProject 저장
    project_id_map = {}
    for project in support_projects:
        inserted_id = await db_ops.insert_one("SupportProject", project)
        project_id_map[project["title"]] = inserted_id
    print(f"[{site_name}] SupportProject 저장 완료 → {len(project_id_map)}개 문서 삽입")

    # Service 저장 (projectId 매핑)
    service_count = 0
    for svc in services:
        title = svc["projectTitle"]
        project_id = project_id_map.get(title)
        if not project_id:
            print(f"Service 매핑 실패: '{title}'에 해당하는 프로젝트 없음, 스킵")
            continue

        service_data = {
            "type": svc["type"],
            "maxAmount": svc.get("maxAmount"),
            "projectId": project_id
        }
        await db_ops.insert_one("Service", service_data)
        service_count += 1
    print(f"[{site_name}] Service 저장 완료 → {service_count}개 문서 삽입")

    await conn.disconnect()

    # 6️⃣ 중간 파일 삭제
    print(f"[{site_name}] 관련 파일 삭제 중...")
    for file_path in glob.glob(os.path.join(data_dir, f"{site_name}_*")):
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"삭제 완료: {file_path}")

    print(f"[{site_name}] 파이프라인 완료 및 파일 정리 완료")


# 전체 파이프라인 실행
async def run_all_pipelines():
    pipelines = [
        {"site": "bizinfo", "crawler": CRAWLER_MAP["bizinfo"]},
        {"site": "sbiz24", "crawler": CRAWLER_MAP["sbiz24"]},
    ]

    for p in pipelines:
        await run_pipeline(p["site"], p["crawler"])


if __name__ == "__main__":
    asyncio.run(run_all_pipelines())
