from fastapi import APIRouter, HTTPException, Depends

from ..models.recommendations import SearchResponse, SearchRequest
from ..rag.RAGEngine import RAGEngine

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
