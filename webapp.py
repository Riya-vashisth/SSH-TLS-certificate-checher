import os
import asyncio
from typing import Dict, Any, List

from fastapi import FastAPI

from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import the existing CLI logic
from certcheck import check_certificate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="CertCheck Web", version="1.0.0")

# If you open the page from the same server, CORS is not strictly needed,
# but it doesn't hurt for local usage.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


from fastapi import Request


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with open(os.path.join(BASE_DIR, "templates", "index.html"), "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html, status_code=200)


@app.post("/api/check")
async def api_check(payload: Dict[str, Any]):

    # Expected payload: { "urls": ["https://example.com", ...], "debug": false }
    urls = payload.get("urls") or []
    debug = bool(payload.get("debug", False))

    # Normalize: allow a single string or list
    if isinstance(urls, str):
        urls = [urls]

    urls = [str(u).strip() for u in urls if str(u).strip()]
    if not urls:
        return {"ok": False, "error": "No URLs provided", "results": []}

    # Run checks concurrently via existing async function
    results_list = await asyncio_gather_check(urls=urls, debug=debug)

    merged: Dict[str, dict] = {}
    for item in results_list:
        if not isinstance(item, dict):
            continue
        for k, v in item.items():
            merged[k] = v

    return {"ok": True, "results": merged}


async def asyncio_gather_check(urls: List[str], debug: bool):
    import asyncio

    # check_certificate returns: {url: {...}}
    coros = [check_certificate(url, debug=debug) for url in urls]
    return await asyncio.gather(*coros)

