import json

from fastapi import APIRouter, HTTPException, Depends

from ..models.recommendations import BusinessRecommendationRequest, BusinessRecommendationResponse, SearchResponse, \
    SearchRequest
from ..rag.RAGEngine import RAGEngine
from ..utils.query_builder import _build_business_query

router = APIRouter(prefix="/api", tags=["api"])

# 이렇게 None으로 선언하고 나중에 주입하면 싱글톤 패턴이 적용된다고..
rag_engine = None


def get_rag_engine():
    global rag_engine
    rag_engine = RAGEngine() if rag_engine is None else rag_engine

    return rag_engine


# 질의 api 라우터
@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest, engine: RAGEngine = Depends(get_rag_engine)):
    answer = engine.retrieve_answer(request.query)
    return SearchResponse(
        question=request.query,
        answer=answer,
    )


# 새로운 업장 기반 추천 API
@router.post("/recommendations", response_model=BusinessRecommendationResponse)
async def get_business_recommendations(
        request: BusinessRecommendationRequest,
        engine: RAGEngine = Depends(get_rag_engine)
):
    try:
        # 업장 정보를 기반으로 좀더 세밀하게 조정된 쿼리 문자열 생성
        recommendation_query = _build_business_query(request.businessInfo)
        recommendations = engine.retrieve_answer(recommendation_query)

        try:
            parsed_response = json.loads(recommendations)
            policy_ids = parsed_response.get("recommended_policy_ids", [])
        except json.JSONDecodeError:
            policy_ids = []

        return BusinessRecommendationResponse(
            business_id=request.businessInfo.id,
            recommended_policy_ids=policy_ids
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 생성 중 오류 발생: {str(e)}")
