import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def setup_driver(download_dir):
    # 다운로드 설정: 파일을 자동으로 지정된 폴더에 저장하도록 설정
    options = Options()
    prefs = {
        "download.default_directory": download_dir,  # 다운로드 경로 지정
        "download.prompt_for_download": False,       # 다운로드 확인 창 비활성화
        "download.directory_upgrade": True,          # 디렉토리 업그레이드 허용
        "safebrowsing.enabled": True,                # 안전 브라우징 활성화
        "profile.default_content_setting_values.automatic_downloads": 1  # 자동 다운로드 허용
    }
    options.add_experimental_option("prefs", prefs)
    
    # 시스템 자원 최적화를 위한 설정
    options.add_argument("--disable-dev-shm-usage")  # /dev/shm 사용 비활성화 (메모리 최적화)
    
    # bsbsc은 동적사이트라 브라우저 ui 비활성화 시 크롤링 자체가 안됨!!!!!!!!!!!!! 브라우저 띄워야함


    
    # ChromeDriverManager를 사용하여 자동으로 드라이버 설치 및 관리
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def extract_attachments(driver, post_title):
    """첨부파일 정보 추출 - 공고명 기반 파일명 생성"""
    attachments = []
    
    try:
        download_buttons = driver.find_elements(By.CSS_SELECTOR, 'a.ltgray[href*="/api/v1/resources/business_posting/"]')
        
        for btn in download_buttons:
            try:
                # 버튼 텍스트 추출 (파일명으로 사용)
                button_text = btn.text.strip() or "첨부파일"
                
                # 공고명에서 파일명으로 사용할 수 없는 문자 제거
                safe_title = "".join(c for c in post_title if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title.replace(' ', '_')  # 공백을 언더스코어로 변경
                
                # 최종 파일명 생성: "공고명-[버튼텍스트]"
                filename = f"{safe_title}-[{button_text}]"
                
                # 파일 확장자 추가 (기본값: .pdf)
                if not any(filename.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip']):
                    filename += ".pdf"
                
                # 버튼이 클릭 가능할 때까지 대기
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.ltgray[href*="/api/v1/resources/business_posting/"]')))
                
                # 버튼 클릭
                btn.click()
                time.sleep(2)
                
                attachments.append({
                    "파일명": filename,
                    "로컬경로": f"downloads/{filename}",
                })
                
            except Exception as e:
                print(f"개별 첨부파일 처리 실패: {e}")
                continue
            
    except Exception as e:
        print(f"첨부파일 추출 실패: {e}")
    
    return attachments

def crawl_bsbsc():
    """부산시소상공인종합지원센터 크롤링"""
    # 디렉토리 설정
    base_dir = os.path.join(os.path.dirname(__file__), "../../data")
    os.makedirs(base_dir, exist_ok=True)
    
    download_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../downloads"))
    os.makedirs(download_dir, exist_ok=True)
    
    driver = setup_driver(download_dir)
    results = []
    
    try:
        url = "https://bsbsc.kr/posting?page=1&size=10&businessId=23&postingStatus=&topic=01&keyword="
        driver.get(url)
        time.sleep(2)
        
        page = 1
        while True:
            print(f"[Page {page}]")
            
            # 공고 목록 찾기
            parent_selector = "#__app_root > div > div > div:nth-child(2) > div > div.overflow-x-auto > div > div.board.bd_busi"
            parent_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, parent_selector))
            )
            list_elements = parent_element.find_elements(By.CSS_SELECTOR, ".list")
            
            if not list_elements:
                print("더 이상 공고 없음")
                break
            
            # 각 공고 처리
            for i in range(len(list_elements)):
                try:
                    # 목록 새로고침 (stale element 방지)
                    parent_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, parent_selector))
                    )
                    list_elements = parent_element.find_elements(By.CSS_SELECTOR, ".list")
                    
                    if i >= len(list_elements):
                        break
                    
                    # 공고 클릭
                    current_url = driver.current_url
                    clickable_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(list_elements[i])
                    )
                    clickable_element.click()
                    
                    # 페이지 이동 확인
                    try:
                        WebDriverWait(driver, 5).until(
                            lambda d: d.current_url != current_url and not d.current_url.startswith('data:')
                        )
                    except:
                        driver.execute_script("arguments[0].click();", clickable_element)
                        try:
                            WebDriverWait(driver, 5).until(
                                lambda d: d.current_url != current_url and not d.current_url.startswith('data:')
                            )
                        except:
                            print(f"상세페이지 접근 실패, 건너뛰기")
                            continue
                    
                    time.sleep(2)
                    
                    # 상세 정보 추출
                    try:
                        title_element = driver.find_element(By.CSS_SELECTOR, ".view_top h2")
                        title = title_element.text.strip()
                        detail_url = driver.current_url
                        
                        # 첨부파일 처리 - 셀레니움 방식 (공고명 기반 파일명 생성)
                        attachments = extract_attachments(driver, title)
                        
                        # 결과 저장
                        results.append({
                            "제목": title,
                            "상세링크": detail_url,
                            "첨부파일": attachments 
                        })
                        
                        print(f"공고 처리 완료: {title}")
                        
                    except Exception as e:
                        print(f"상세 정보 추출 실패: {e}")
                    
                    # 목록으로 돌아가기
                    driver.back()
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"공고 처리 중 오류: {e}")
                    continue
            
            # 다음 페이지 확인
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Next']")
                next_button.click()
                time.sleep(2)
                page += 1
            except:
                print("다음 페이지 없음")
                break
    
    except Exception as e:
        print(f"크롤링 중 오류: {e}")
    
    finally:
        driver.quit()
    
    # JSON 저장
    save_path = os.path.join(base_dir, "bsbsc_results.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"총 {len(results)}건 저장 완료 → {save_path}")

if __name__ == "__main__":
    crawl_bsbsc()
