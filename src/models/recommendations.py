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
    FROM_2000_TO_5000 = "FROM_1500_TO_5000"
    OVER_5000 = "OVER_5000"


class LeaseType(str, Enum):
    MONTHLY = "MONTHLY"
    OWNERSHIP = "OWNERSHIP"


class BusinessInfo(BaseModel):
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
