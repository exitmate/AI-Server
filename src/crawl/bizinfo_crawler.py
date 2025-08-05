# 중소기업 성공 길잡이 기업마당 > 정책정보 > 지원사업 공고

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://www.bizinfo.go.kr"
LIST_URL = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"

params = {
    "rows": 15,
    "cpage": 1,
    "schAreaDetailCodes": "6260000",  # 부산
    "schEndAt": "N",  # 마감 안 된 공고만
    "condition": "searchPblancNm",
    "condition1": "AND",
    "preKeywords": "폐업",
    "keyword": "폐업"
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": LIST_URL
}

results = []


def setup_driver():
    """Selenium 드라이버 초기화"""
    options = Options()
    options.add_argument("--headless")  # 브라우저 창 없이 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def download_file(url: str, save_path: str):
    """첨부파일 다운로드"""
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(resp.content)
    print(f"파일 다운로드 완료: {save_path}")


def get_attachments_with_selenium(driver, detail_url: str):
    """상세 페이지에서 첨부파일 리스트 파싱 (Selenium 사용)"""
    driver.get(detail_url)

    # 첨부파일 영역 로딩 대기
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.view_cont"))
        )
    except:
        print(f"첨부파일 로딩 실패: {detail_url}")
        return None

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # 첨부파일 리스트 파싱
    attachments = []
    file_items = soup.select("div.attached_file_list li")
    for li in file_items:
        file_name_tag = li.select_one("div.file_name")
        file_download_tag = li.select_one("a[href*='getImageFile']")
        if file_name_tag and file_download_tag:
            filename = file_name_tag.get_text(strip=True)
            file_url = urljoin(BASE_URL, file_download_tag["href"])
            attachments.append({
                "파일명": filename,
                "URL": file_url
            })

    # fileLoad 방식도 함께 확인 (보조)
    fileload_tags = soup.select("a#fileLoad")
    for tag in fileload_tags:
        if tag.has_attr("onclick"):
            onclick_value = tag["onclick"]
            import re
            match = re.search(r"fileLoad\((.+)\)", onclick_value)
            if match:
                args = [a.strip().strip("'").strip('"') for a in match.group(1).split(",")]
                raw_path = args[0]
                filename = args[1] if len(args) > 1 else "첨부파일"
                if "+" in raw_path:
                    parts = [p.strip().strip("'").strip('"') for p in raw_path.split("+")]
                    full_path = "".join(parts)
                else:
                    full_path = raw_path
                attachments.append({
                    "파일명": filename,
                    "URL": urljoin(BASE_URL, full_path)
                })

    return attachments if attachments else None


def crawl_bizinfo():
    driver = setup_driver()

    while True:
        print(f"\n[{params['cpage']}페이지]")
        response = requests.get(LIST_URL, params=params, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.select("table tbody tr")
        if not rows:
            print("더 이상 행이 없습니다.")
            break

        has_data = False
        for row in rows:
            cols = row.find_all("td")

            if len(cols) == 1 and "검색된 내용이 없습니다" in cols[0].get_text():
                print("더 이상 공고 없음")
                break

            if len(cols) < 8:
                continue

            has_data = True

            # 기본 정보
            분야 = cols[1].get_text(strip=True)
            제목_태그 = cols[2].select_one("a")
            제목 = 제목_태그.get_text(strip=True)
            상대링크 = 제목_태그["href"]
            pblanc_id = 상대링크.split("pblancId=")[-1]
            상세링크 = f"{BASE_URL}/web/lay1/bbs/S1T122C128/AS/74/view.do?pblancId={pblanc_id}"

            신청기간 = cols[3].get_text(strip=True)
            소관부처 = cols[4].get_text(strip=True)
            수행기관 = cols[5].get_text(strip=True)
            등록일 = cols[6].get_text(strip=True)
            조회수 = cols[7].get_text(strip=True)

            # 상세 페이지 요청 (requests로 기본 내용만 파싱)
            detail_resp = requests.get(상세링크, headers=headers)
            detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
            content_div = detail_soup.select_one("div.view_cont")

            상세정보 = {}
            안내문 = None

            if content_div:
                # 상세 항목 파싱
                for li in content_div.select("ul > li"):
                    title_el = li.select_one(".s_title")
                    value_el = li.select_one(".txt")
                    if not title_el or not value_el:
                        continue
                    key = title_el.get_text(strip=True)
                    if key == "사업개요":
                        value = "\n".join(p.get_text(strip=True) for p in value_el.select("p"))
                    elif value_el.select_one("a"):
                        a = value_el.select_one("a")
                        value = f"{a.get_text(strip=True)} ({a['href']})"
                    else:
                        value = value_el.get_text(strip=True)
                    상세정보[key] = value

                # 표 처리
                표리스트 = [table.get_text(strip=True) for table in content_div.select("table")]
                if 표리스트:
                    상세정보["표내용"] = 표리스트

                # 안내 문구
                notice = content_div.select_one("div[style*='text-align:center']")
                if notice:
                    안내문 = notice.get_text(strip=True)

            # 첨부파일은 Selenium으로 파싱
            첨부파일 = get_attachments_with_selenium(driver, 상세링크)

            # 첨부파일 다운로드
            if 첨부파일:
                os.makedirs("downloads", exist_ok=True)
                for file in 첨부파일:
                    if file["파일명"].lower().endswith(".zip"):
                        print(f"⏭ ZIP 파일 다운로드 건너뜀: {file['파일명']}")
                        continue
                     
                    if "webapp/upload" in file["URL"]:
                      print(f"⏭ fileLoad 파일 다운로드 스킵: {file['파일명']} ({file['URL']})")
                      continue
                    
                    try:
                        local_file = os.path.join("downloads", file["파일명"])
                        download_file(file["URL"], local_file)
                        file["로컬경로"] = local_file
                    except Exception as e:
                        print(f"첨부파일 다운로드 실패: {file['파일명']} - {e}")

            result = {
                "제목": 제목,
                "분야": 분야,
                "신청기간": 신청기간,
                "소관부처": 소관부처,
                "수행기관": 수행기관,
                "등록일": 등록일,
                "조회수": 조회수,
                "상세링크": 상세링크,
                "상세정보": 상세정보,
                "첨부파일": 첨부파일,
                "안내문": 안내문
            }

            results.append(result)

        if not has_data:
            print("📭 더 이상 유효한 공고 없음")
            break

        params["cpage"] += 1

    driver.quit()

    # JSON 저장
    save_dir = os.path.join(os.path.dirname(__file__), "../../data")
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, "bizinfo_results.json")

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(results)}건 저장 완료 → {save_path}")


if __name__ == "__main__":
    crawl_bizinfo()
