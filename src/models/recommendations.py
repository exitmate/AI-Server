from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)


class SearchResponse(BaseModel):
    question: str
    answer: str


class IndustryCategory(str, Enum):
    FOOD_SERVICE = "FOOD_SERVICE"
    NON_ALCOHOL_CAFE = "NON_ALCOHOL_CAFE"
    OTHER = "OTHER"


class MonthlySalesRange(str, Enum):
    UNDER_500 = "UNDER_500"
    FROM_500_TO_1000 = "FROM_500_TO_1000"
    FROM_1000_TO_1500 = "FROM_1000_TO_1500"
    FROM_1500_TO_2000 = "FROM_1500_TO_2000"
    FROM_2000_TO_5000 = "FROM_2000_TO_5000"
    OVER_5000 = "OVER_5000"


class LeaseType(str, Enum):
    MONTHLY = "MONTHLY"
    OWNERSHIP = "OWNERSHIP"


class BusinessInfo(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123",
                "region": "부산시",
                "industryCategory": "FOOD_SERVICE",
                "industryDetail": "카페",
                "openedAt": "2020-01-15T00:00:00",
                "isClosed": False,
                "closedAt": None,  # 폐업일
                "isReemployed": False,
                "isDemolished": False,
                "monthlySalesRange": "FROM_1000_TO_1500",
                "areaSizeM2": 33.0,
                "employeeCount": 2,
                "leaseType": "MONTHLY",
                "depositAmount": 20000000,
                "monthlyRent": 1500000
            }
        }
    }
    
    id: str
    region: str
    industryCategory: IndustryCategory
    industryDetail: str
    openedAt: datetime
    isClosed: bool
    closedAt: Optional[datetime] = None
    isReemployed: bool
    isDemolished: bool
    monthlySalesRange: MonthlySalesRange
    areaSizeM2: float
    employeeCount: int
    leaseType: LeaseType
    depositAmount: int  # 원 단위
    monthlyRent: int  # 원 단위


class BusinessRecommendationRequest(BaseModel):
    businessInfo: BusinessInfo


class BusinessRecommendationResponse(BaseModel):
    business_id: str
    recommended_policy_ids: list[str]


class ChatbotRequest(BaseModel):
    """
    챗봇 요청 모델
    - businessInfo: 사업자의 기본 정보 (폐업 절차나 세무 처리에 필요한 맥락 제공)
    - question: 사용자가 궁금한 폐업 절차나 세무 관련 질문
    """
    model_config = {
        "json_schema_extra": {
            "example": {
                "businessInfo": {
                    "id": "123",
                    "region": "부산시",
                    "industryCategory": "FOOD_SERVICE",
                    "industryDetail": "카페",
                    "openedAt": "2020-01-15T00:00:00",
                    "isClosed": False,
                    "closedAt": None,
                    "isReemployed": False,
                    "isDemolished": False,
                    "monthlySalesRange": "FROM_1000_TO_1500",
                    "areaSizeM2": 33.0,
                    "employeeCount": 2,
                    "leaseType": "MONTHLY",
                    "depositAmount": 20000000,
                    "monthlyRent": 1500000
                },
                "question": "폐업을 어떻게 하는지 궁금해"
            }
        }
    }
    
    businessInfo: BusinessInfo
    question: str


class ChatbotResponse(BaseModel):
    question: str
    answer: str
