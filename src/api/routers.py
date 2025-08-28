import json

from fastapi import APIRouter, HTTPException, Depends

from ..models.recommendations import BusinessRecommendationRequest, BusinessRecommendationResponse, ChatbotResponse, ChatbotRequest, SearchRequest
from ..rag.RAGEngine import RAGEngine
from ..utils.query_builder import _build_business_query, _build_chatbot_query

router = APIRouter(prefix="/api", tags=["api"])

# 용도별로 다른 RAG 인스턴스를 관리하기 위한 딕셔너리
# 각 인덱스 타입별로 하나의 인스턴스만 생성 (싱글톤 패턴 유지)
rag_engines = {}


def get_rag_engine(index_type: str = "default"):
    """
    용도별 RAG 엔진 인스턴스를 반환
    
    Args:
        index_type (str): 'default' (공고 추천용) 또는 'chatbot' (챗봇용)
    
    Returns:
        RAGEngine: 해당 용도의 RAG 엔진 인스턴스
    """
    global rag_engines
    
    # 해당 index_type의 인스턴스가 없으면 새로 생성
    if index_type not in rag_engines:
        rag_engines[index_type] = RAGEngine(index_type=index_type)
    
    return rag_engines[index_type]


# 새로운 업장 기반 추천 API - 기본 공고 인덱스 사용
@router.post("/recommendations", response_model=BusinessRecommendationResponse)
async def get_business_recommendations(
        request: BusinessRecommendationRequest,
        engine: RAGEngine = Depends(lambda: get_rag_engine("default"))
):
    try:
        q = _build_business_query(request.businessInfo)
        policy_ids = engine.retrieve_policy_ids(q, k=10, topn=5)
        return BusinessRecommendationResponse(
            business_id=request.businessInfo.id,
            recommended_policy_ids=policy_ids
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 생성 중 오류 발생: {str(e)}")


# 폐업 절차 혹은 세무 관련 행정에 대한 질의에 답변하는 챗봇 API
# chatbot 인덱스를 사용 (세무 지식, 행정 처리 데이터가 담겨있음)
@router.post("/chatbot", response_model=ChatbotResponse)
async def chatbot(
    request: ChatbotRequest, 
    engine: RAGEngine = Depends(lambda: get_rag_engine("chatbot"))):
    try:
        # 사업자 정보를 바탕으로 챗봇용 쿼리 생성
        query = _build_chatbot_query(request.businessInfo, request.question)
        
        # RAG를 통해 답변 생성 (챗봇 인덱스에서 세무/행정 지식 검색)
        answer = engine.retrieve_answer(query)
        
        return ChatbotResponse( 
            question=request.question,
            answer=answer
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 응답 생성 중 오류 발생: {str(e)}") 
