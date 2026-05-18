from fastapi import FastAPI

from psx_agent.providers.factory import get_provider
from psx_agent.report import build_morning_report

app = FastAPI(title="PSX Agent by Arfa", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/report")
def report() -> dict:
    return build_morning_report().model_dump()


@app.get("/quotes")
def quotes() -> dict:
    provider = get_provider()
    if not hasattr(provider, "get_quotes"):
        return {"status": "error", "message": "Current provider does not support live quotes.", "data": []}
    data = provider.get_quotes()  # type: ignore[attr-defined]
    return {"status": "ok", "data": [quote.model_dump() for quote in data], "count": len(data)}
