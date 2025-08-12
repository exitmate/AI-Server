from __future__ import annotations

from datetime import datetime, date, time, timezone
from typing import Any, Optional, Dict
import re


def _normalize_z_suffix(value: str) -> str:
    # ISO 8601 'Z' → '+00:00'로 변경 (datetime.fromisoformat 호환)
    if value.endswith("Z"):
        return value[:-1] + "+00:00"
    return value


def try_parse_datetime(value: Any) -> Optional[datetime]:
    """
    문자열(여러 포맷) → datetime(UTC naive) 변환을 시도.

    규칙:
    - ISO 8601 with/without timezone 처리
    - 날짜 전용 문자열은 자정 시간으로 변환
    - 'YYYY.MM.DD', 'YYYY/MM/DD', 'YYYY년 MM월 DD일' 등 보편 포맷 지원
    - 성공 시 tz-aware는 UTC로 변환 후 tzinfo 제거, tz-naive는 그대로(UTC 가정)
    """
    if isinstance(value, datetime):
        # aware → UTC로 정규화 후 naive, naive는 그대로 반환
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    if not isinstance(value, str):
        return None

    s = value.strip()
    if not s:
        return None

    # 1) ISO 8601 시도
    try:
        # Z 처리
        s_iso = _normalize_z_suffix(s)
        # 날짜 전용(YYYY-MM-DD) 처리
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s_iso):
            dt = datetime.combine(date.fromisoformat(s_iso), time(0, 0, 0))
            return dt
        dt = datetime.fromisoformat(s_iso)
        # tz-aware → UTC naive로
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        pass

    # 2) 일반적인 날짜 포맷들 시도
    date_patterns = [
        (r"^(\d{4})\.(\d{1,2})\.(\d{1,2})$", "."),
        (r"^(\d{4})/(\d{1,2})/(\d{1,2})$", "/"),
        (r"^(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일$", "kr"),
    ]

    for pattern, kind in date_patterns:
        m = re.match(pattern, s)
        if not m:
            continue
        try:
            year = int(m.group(1))
            month = int(m.group(2))
            day = int(m.group(3))
            return datetime(year, month, day)
        except Exception:
            continue

    return None


def convert_support_projects_dates(formatted_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    formatted_results 내 SupportProject 배열의 날짜 필드를 datetime으로 변환.
    - 대상 필드: createdAt, updatedAt, deadline, eligibility.mustBeClosedAfter
    변환 실패 시 원래 값을 유지.
    """
    if not formatted_results or not isinstance(formatted_results, dict):
        return formatted_results

    projects = formatted_results.get("supportProjects") or []
    for project in projects:
        if not isinstance(project, dict):
            continue

        for field_name in ["createdAt", "updatedAt", "deadline"]:
            if field_name in project:
                parsed = try_parse_datetime(project[field_name])
                if parsed is not None:
                    project[field_name] = parsed

        eligibility = project.get("eligibility")
        if isinstance(eligibility, dict) and "mustBeClosedAfter" in eligibility:
            parsed = try_parse_datetime(eligibility.get("mustBeClosedAfter"))
            if parsed is not None:
                eligibility["mustBeClosedAfter"] = parsed

    return formatted_results


