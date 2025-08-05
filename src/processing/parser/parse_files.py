import os
import json

from .upstage_parser import extract_text, parse_document_with_upstage

def parse_files(json_path: str, output_name: str):
    # 크롤링 결과 로드
    with open(json_path, "r", encoding="utf-8") as f:
        crawled_data = json.load(f)

    parsed_results = []

    for entry in crawled_data:
        title = entry["제목"]
        attachments = entry.get("첨부파일", [])

        if not attachments:
            print(f"첨부파일 없음: {title}")
            continue

        for file in attachments:
            local_path = file.get("로컬경로")

            if not local_path or not os.path.exists(local_path):
                print(f"파일 없음, 스킵: {file['파일명']}")
                continue

            if file["파일명"].lower().endswith(".zip"):
                print(f"ZIP 파일 스킵: {file['파일명']}")
                continue

            print(f"업스테이지 파싱 시작: {file['파일명']}")
            parse_result = parse_document_with_upstage(local_path)
            text_only = extract_text(parse_result)

            parsed_results.append({
                "사이트": output_name,
                "공고제목": title,
                "파일명": file["파일명"],
                "파싱결과": text_only
            })
            try:
                os.remove(local_path)
                print(f"첨부파일 삭제 완료: {file['파일명']}")
            except Exception as e:
                print(f"첨부파일 삭제 실패: {file['파일명']} → {e}")
            

    # ✅ 프로젝트 루트 경로에 저장
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/"))
    output_path = os.path.join(project_root, f"{output_name}_parsed_results.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed_results, f, ensure_ascii=False, indent=2)
        

    print(f"\n{output_name} 파싱 완료 → {output_path}")
