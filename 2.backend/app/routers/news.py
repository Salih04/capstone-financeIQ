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

_FALLBACK_ARTICLES = [
    {"id": "fb-1", "title": "BIST100 weekly market wrap: momentum held above key support", "source": "Internal Feed", "published_at": "2025-12-30T09:00:00+00:00", "summary": "Momentum remained mixed; leadership stocks held above short-term trend lines as volume normalised heading into year-end.", "url": None, "sentiment": None, "ai_insight": "Quality balance-sheet names outperformed; watch for rotation into cyclicals if rates soften."},
    {"id": "fb-2", "title": "Earnings revisions and consensus shifts across BIST sectors", "source": "Internal Feed", "published_at": "2025-12-29T11:00:00+00:00", "summary": "Forward revisions favored quality balance-sheet names while consensus trimmed estimates for highly-leveraged industrials.", "url": None, "sentiment": None, "ai_insight": None},
    {"id": "fb-3", "title": "Macro watch: rates, FX, and liquidity conditions", "source": "Internal Feed", "published_at": "2025-12-28T08:30:00+00:00", "summary": "Liquidity-sensitive sectors saw dispersion increase as TL volatility picked up ahead of TCMB decision.", "url": None, "sentiment": None, "ai_insight": None},
    {"id": "fb-4", "title": "Energy sector: production and distribution outlook Q4 2025", "source": "Internal Feed", "published_at": "2025-12-27T10:00:00+00:00", "summary": "Thermal generation rebounded as hydro reserves normalised; electricity distribution margins remained under regulatory pressure.", "url": None, "sentiment": None, "ai_insight": "Enerji distribution names with regulated returns offer defensive characteristics in current regime."},
    {"id": "fb-5", "title": "Banking sector: capital adequacy and NPL trends", "source": "Internal Feed", "published_at": "2025-12-26T09:15:00+00:00", "summary": "Capital ratios held above regulatory minimums across large-cap banks; NPL ratios ticked up marginally in SME portfolios.", "url": None, "sentiment": None, "ai_insight": None},
    {"id": "fb-6", "title": "Real estate and REITs: transaction volumes in Q4", "source": "Internal Feed", "published_at": "2025-12-24T08:00:00+00:00", "summary": "Transaction volumes declined seasonally but prime Istanbul commercial assets retained valuation premiums.", "url": None, "sentiment": None, "ai_insight": None},
    {"id": "fb-7", "title": "Technology and telecom: subscriber growth and ARPU update", "source": "Internal Feed", "published_at": "2025-12-23T11:30:00+00:00", "summary": "Mobile subscriber additions decelerated; fixed-line ARPU growth continued driven by tariff indexation.", "url": None, "sentiment": None, "ai_insight": "Telecom names with inflation-linked tariffs provide earnings visibility in high-rate environment."},
    {"id": "fb-8", "title": "Consumer staples: pricing power and volume dynamics", "source": "Internal Feed", "published_at": "2025-12-22T09:00:00+00:00", "summary": "Staples producers maintained positive pricing spread vs input cost inflation; volume growth moderated as consumer adjusted.", "url": None, "sentiment": None, "ai_insight": None},
    {"id": "fb-9", "title": "Industrial metals: steel and aluminium outlook for 2026", "source": "Internal Feed", "published_at": "2025-12-21T10:00:00+00:00", "summary": "Domestic steel consumption held firm; export competitiveness improved on TL depreciation, supporting margin recovery.", "url": None, "sentiment": None, "ai_insight": None},
]


def _fallback_page(date_key: str, page: int, max_pages: int) -> dict[str, Any]:
    limit = 3
    offset = (page - 1) * limit
    articles = _FALLBACK_ARTICLES[offset:offset + limit]
    return {
        "date": date_key,
        "page": page,
        "limit": limit,
        "max_pages": max_pages,
        "max_articles_per_day": max_pages * limit,
        "message": None,
        "articles": articles,
    }


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
        return _fallback_page(date_key, page, max_pages)

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