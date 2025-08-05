schema = {
    "supportProjects": [  # SupportProject 배열
        {
            "logoSrc": "string?",  # 로고 이미지 URL (nullable)
            "title": "string",  # 제목 (필수)
            "host": "string",  # 주최 단체 (필수)
            "applicationType": "enum(ALWAYS, FIRST_COME, DEADLINED)",  # 지원사업 모집 종류 (상시, 소진 시 종료, 마감일 존재) (필수)
            "deadline": "datetime?",  # 마감일자 (nullable)
            "isOpen": "boolean",  # 모집 여부 (필수)
            "detailPageUrl": "string?",  # 상세 페이지 URL (nullable)
            "inquiryPhone": "string?",  # 문의 전화 (nullable)
            "inquiryEmail": "string?",  # 문의 이메일 (nullable)
            "requiredDocs": ["string"],  # 필요서류 (필수, 배열)
            "eligibility": {  # 지원 자격 (필수)
                "mustBeInRegion": "string?",  # 지역 제한 (nullable)
                "mustBePlannedClosure": "boolean",  # 폐업 예정자만 해당 (필수)
                "mustBeClosed": "boolean",  # 기폐업자만 해당 (필수)
                "mustBeClosedAfter": "datetime?",  # 폐업일 제한 (nullable)
                "mustBeClosedWithin": "int?",  # 폐업일 기준 일수 제한 (nullable)
                "mustOperateAtLeast": "int?",  # 최소 운영 일수 (nullable)
                "mustNotBeCorporation": "boolean"  # 법인 불가 여부 (필수)
            },
            "applicationRequirements": ["string"],  # 자격 요건 목록 (필수, 배열)
            "restrictions": ["string"],  # 제한사항 (필수, 배열)
            "createdAt": "datetime",  # 공고일자 (필수)
            "updatedAt": "datetime"  # 공고 마지막 수정일자 (필수)
        }
    ],
    "services": [  # Service 배열
        {
            "projectTitle": "string",  # 연결 기준: SupportProject.title과 매핑
            "type": "enum(STORE_DEMOLITION_SUBSIDY, CLOSURE_SUPPORT_SUBSIDY, CLOSURE_CONSULTING, REEMPLOYMENT_EDUCATION, BUSINESS_EDUCATION)", # 전포철거지원금, 폐업지원금, 폐업 컨설팅, 재취업/재창업 교육, 경영 교육  
            "maxAmount": "int?"  # 지원금액 (nullable)
        }
    ]
}
