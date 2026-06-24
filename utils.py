"""
Tiện ích dùng chung.

parse_published_at: chuẩn hóa published_at (scrape từ CafeF) về datetime.

CafeF trả 2 format tùy nơi lấy:
  - Trang timelinelist  -> ISO  "2026-05-01T17:39:00"
  - Trang chủ (page 1)  -> slash "01/05/2026 - 09:02"  (DD/MM/YYYY giờ VN)
Nếu lưu thẳng string, pandas/bên phân tích dễ hiểu nhầm slash theo MM/DD (kiểu Mỹ)
-> đảo ngày/tháng hoặc NaT. Vì vậy LUÔN parse về datetime ngay khi ghi vào DB.
"""

from datetime import datetime
from typing import Optional, Union

_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y - %H:%M",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
)


def parse_published_at(value: Union[str, datetime, None]) -> Optional[datetime]:
    """Trả datetime (giờ VN, naive) hoặc None. Idempotent với datetime; slash hiểu day-first."""
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None
    for fmt in _FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
