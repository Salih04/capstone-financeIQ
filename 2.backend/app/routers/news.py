from datetime import datetime

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.forecasting import NewsOut

router = APIRouter(tags=["news"])


@router.get("/news/updates", response_model=NewsOut)
def news_updates(
    sector: str = "All",
    _: User = Depends(get_current_user),
):
    now = datetime.utcnow().isoformat()
    updates = [
        {
            "title": f"{sector} sector weekly market wrap",
            "source": "Internal Feed",
            "published_at": now,
            "summary": "Momentum remained mixed; leadership stocks held above short-term trend.",
        },
        {
            "title": f"{sector} earnings revisions and consensus shifts",
            "source": "Internal Feed",
            "published_at": now,
            "summary": "Forward revisions favored quality balance-sheet names.",
        },
        {
            "title": "Macro watch: rates, FX, and liquidity",
            "source": "Internal Feed",
            "published_at": now,
            "summary": "Liquidity-sensitive sectors saw dispersion increase over the last sessions.",
        },
    ]
    ai_insight = (
        "AI Insight: Current regime favors stocks with stable profitability, strong cash generation, "
        "and moderate leverage; prioritize names with improving quarter-over-quarter trend consistency."
    )
    return {"sector": sector, "updates": updates, "ai_insight": ai_insight}
