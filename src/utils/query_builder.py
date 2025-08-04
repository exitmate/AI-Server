from src.models.recommendations import BusinessRecommendationRequest


def _build_business_query(business: BusinessRecommendationRequest) -> str:
    query = f"""
    너는 폐업한 소상공인을 위한 정책 추천 전문가야. 다음은 한 사용자의 사업장 정보다. 이 정보를 바탕으로, 이 사용자가 받을 수 있는 정부/지자체 지원정책의 `id`를 최대 5개까지 추천해줘.
    
    💡 반드시 정책 벡터 데이터베이스에 포함된 정책만을 추천해야 해. 데이터베이스에 없는 정책은 절대 추천하면 안 돼.  
    💡 출력은 다음 JSON 형식으로만 해줘: `{{"recommended_policy_ids": ["id1", "id2", ...]}}`  
    💡 정책 이름, 설명 등은 출력하지 마. **오직 policy id 값만** 리스트로 주면 돼.
    
    ---  
    📌 사용자 사업장 정보는 다음과 같아:
    
    【업장 기본 정보】  
    - 위치: {business.region}  
    - 업종: {business.industryDetail} ({business.industryCategory})  
    - 운영 기간: {business.openedAt.strftime('%Y년 %m월')}부터  
    - 현재 상태: {"폐업" if business.isClosed else "운영중"}  
    
    【사업 규모】  
    - 월 매출: {business.monthlySalesRange}  
    - 점포 면적: {business.areaSizeM2}㎡  
    - 직원 수: {business.employeeCount}명  
    
    【임대 조건】  
    - 임대 형태: {business.leaseType}  
    - 보증금: {business.depositAmount:,}원  
    - 월세: {business.monthlyRent:,}원  
    
    【현재 상황】  
    - 폐업 여부: {'예' if business.isClosed else '아니오'}  
    - 재취업 상태: {"재취업함" if business.isReemployed else "구직중"}  
    - 건물 철거: {'예' if business.isDemolished else '아니오'}  
    
    ---  
    이 정보를 바탕으로 **가장 적합한 정책**을 최대 5개까지 벡터 기반으로 유사도 분석하고,  
    **정책 ID만** 다음 형식으로 반환해줘:
    
    ```json
    {{"recommended_policy_ids": ["id1", "id2", "id3"]}}
    ```
    
    조건을 반드시 지켜줘. 정책 이름이나 설명은 절대 포함하지 마.
    """

    return query.strip()