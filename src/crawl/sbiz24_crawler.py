import os
import re
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def extract_fields(soup):
    """상세 페이지에서 모든 필드를 자동 추출"""
    data = {}
    fields = soup.select("div.form-field.info-field")
    for field in fields:
        label = field.find("label")
        span = field.find("span")
        if label and span:
            key = label.get("title").strip()
            value = span.get_text(separator="\n", strip=True)
            data[key] = value
    return data


def clean_file_name(file_name: str) -> str:
    """파일명에서 확장자 뒤 불필요한 문자열 제거"""
    # 확장자(.hwp, .pdf 등)까지 매칭하고 그 뒤는 제거
    return re.sub(r"(\.[a-zA-Z0-9]+).*", r"\1", file_name.split("/")[-1].strip()).strip()

def setup_driver(download_dir):
    """Chrome 드라이버 설정 (자동 다운로드 경로 지정)"""
    options = Options()
    prefs = {
        "download.default_directory": download_dir,  # 다운로드 경로 지정
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1 
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")  # 필요시 주석 해제
    return webdriver.Chrome(options=options)

def download_attachments(driver, soup, title):
    """첨부파일 다운로드 후 로컬 경로 반환 (자동 다운로드 지원)"""
    attachments = []
    download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../downloads"))
    os.makedirs(download_dir, exist_ok=True)

    # 첨부파일 버튼 및 파일명 추출
    file_buttons = soup.select("div.file-group button[title]")
    file_names = soup.select("div.file-group span.block")

    for btn, span in zip(file_buttons, file_names):
        raw_name = span.get_text(strip=True).split(" 다운로드")[0]
        file_name = clean_file_name(raw_name)  # 확장자 뒤 불필요한 텍스트 제거
        
        # ZIP 파일이면 스킵
        if file_name.lower().endswith(".zip"):
            print(f"ZIP 파일 스킵: {file_name}")
            continue

        print(f"첨부파일 다운로드 시도: {file_name}")

        # 버튼 클릭 실행 (자동 다운로드)
        try:
            button_el = driver.find_element(By.XPATH, f'//button[@title="{btn["title"]}"]')
            driver.execute_script("arguments[0].click();", button_el)

            attachments.append({
                "파일명": file_name,
                "로컬경로": f"downloads/{file_name}"
            })
            print(f"다운로드 요청 완료: {file_name}")

        except Exception as e:
            print(f"첨부파일 다운로드 실패: {file_name} - {e}")

    return attachments


def crawl_sbiz24():
    base_dir = os.path.join(os.path.dirname(__file__), "../../data")
    os.makedirs(base_dir, exist_ok=True)

    download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../downloads"))
    os.makedirs(download_dir, exist_ok=True)

    driver = setup_driver(download_dir)

    url = "https://www.sbiz24.kr/#/combinePbancList"
    driver.get(url)
    time.sleep(3)

    # 지역 선택
    try:
        # 챗봇 아이콘 제거
        driver.execute_script("""
            const chatIcons = document.querySelectorAll('img[alt="소상공인 계약관리"]');
            chatIcons.forEach(icon => icon.style.display = 'none');
        """)

        region_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='지역선택']"))
        )
        driver.execute_script("arguments[0].click();", region_button)
        time.sleep(1)

        busan_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@class="modal-option " and @data-option="부산"]'))
        )
        driver.execute_script("arguments[0].click();", busan_button)
        time.sleep(0.5)

        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm-selection-btn"))
        )
        driver.execute_script("arguments[0].click();", confirm_button)
        time.sleep(1)

    except Exception as e:
        print(f"지역 선택 오류: {e}")

    # ✅ 검색어 입력
    try:
        search_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pbancNm")))
        search_input.clear()
        search_input.send_keys("폐업")
        time.sleep(1)
        search_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.submit-btn")))
        search_button.click()
        time.sleep(3)
    except Exception as e:
        print(f"검색 입력 오류: {e}")

    results = []
    page = 1

    while True:
        print(f"[Page {page}]")
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody > tr.q-tr.cursor-pointer")))
        except:
            print("더 이상 공고 없음. 종료.")
            break

        rows = driver.find_elements(By.CSS_SELECTOR, "tbody > tr.q-tr.cursor-pointer")

        for i in range(len(rows)):
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "tbody > tr.q-tr.cursor-pointer")
                row = rows[i]
                driver.execute_script("arguments[0].scrollIntoView(true);", row)
                driver.execute_script("arguments[0].click();", row)
                time.sleep(2)

                soup = BeautifulSoup(driver.page_source, "html.parser")

                fields = extract_fields(soup)
                title = fields.get("공고명", "제목없음")
                detail_url = driver.current_url

                attachments = download_attachments(driver, soup, title)

                results.append({
                    "제목": title,
                    "상세링크": detail_url,
                    **fields,
                    "첨부파일": attachments
                })

                driver.back()
                time.sleep(2)
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody > tr.q-tr.cursor-pointer")))
            except Exception as e:
                print(f"상세 페이지 진입 실패: {e}")
                try:
                    driver.back()
                    time.sleep(2)
                except:
                    pass

        try:
            next_btn = driver.find_element(By.XPATH, f'//a[text()="{page + 1}"]')
            next_btn.click()
            time.sleep(2)
            page += 1
        except:
            print("다음 페이지 없음. 종료.")
            break

    driver.quit()

    save_path = os.path.join(base_dir, "sbiz24_results.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"총 {len(results)}건 저장 완료 → {save_path}")

if __name__ == "__main__":
    crawl_sbiz24()
