from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
import httpx

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.forecasting import NewsOut

router = APIRouter(tags=["news"])

_NEWS_CACHE: dict[tuple[str, int], dict[str, Any]] = {}
_NEWS_TTL_SECONDS = 60 * 60 * 12


def _today_key() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _cache_get(date_key: str, page: int) -> dict[str, Any] | None:
    cached = _NEWS_CACHE.get((date_key, page))

    if not cached:
        return None

    if cached.get("expires_at", 0) < datetime.now(timezone.utc).timestamp():
        _NEWS_CACHE.pop((date_key, page), None)
        return None

    return cached.get("payload")


def _cache_set(date_key: str, page: int, payload: dict[str, Any]) -> None:
    _NEWS_CACHE[(date_key, page)] = {
        "payload": payload,
        "expires_at": datetime.now(timezone.utc).timestamp() + _NEWS_TTL_SECONDS,
    }


@router.get("/news/updates", response_model=NewsOut)
def news_updates(
    page: int = Query(default=1, ge=1),
    _: User = Depends(get_current_user),
):
    max_pages = 3

    if page > max_pages:
        raise HTTPException(status_code=422, detail="Maximum page is 3.")

    date_key = _today_key()

    cached = _cache_get(date_key, page)
    if cached:
        return cached

    try:
        from app.config import settings
        api_key = settings.NEWS_API_KEY
    except Exception:
        api_key = None

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="News feed unavailable: NEWS_API_KEY is not configured.",
        )

    limit = 3
    offset = (page - 1) * limit
    url = "https://finnhub.io/api/v1/news"

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                url,
                params={
                    "category": "general",
                    "token": api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"News provider returned an error: {exc.response.status_code}",
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"News provider request failed: {str(exc)}",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected news fetch error: {str(exc)}",
        )

    items = data if isinstance(data, list) else []
    sliced = items[offset:offset + limit]

    articles: list[dict[str, Any]] = []

    for item in sliced:
        published = item.get("datetime")

        if isinstance(published, (int, float)):
            published_at = datetime.fromtimestamp(published, tz=timezone.utc).isoformat()
        else:
            published_at = None

        articles.append(
            {
                "id": str(item.get("id") or item.get("headline") or published_at or ""),
                "title": item.get("headline") or "",
                "source": item.get("source") or "",
                "published_at": published_at or datetime.now(timezone.utc).isoformat(),
                "summary": item.get("summary") or "",
                "url": item.get("url") or "",
                "sentiment": item.get("sentiment") or None,
                "ai_insight": None,
            }
        )

    payload = {
        "date": date_key,
        "page": page,
        "limit": limit,
        "max_pages": max_pages,
        "max_articles_per_day": max_pages * limit,
        "articles": articles,
    }

    _cache_set(date_key, page, payload)

    return payload