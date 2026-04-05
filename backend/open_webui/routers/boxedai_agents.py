import logging
import os

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from open_webui.utils.auth import get_verified_user

log = logging.getLogger(__name__)

router = APIRouter()

OPENCLAW_OPENAI_PROXY = os.environ.get('OPENCLAW_OPENAI_PROXY', '').rstrip('/')


@router.get('/agents')
async def get_agents(request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = {'Accept': 'application/json'}
    authorization = request.headers.get('authorization')
    if authorization:
        headers['authorization'] = authorization

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(upstream_url, headers=headers) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Agents proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Agents upstream response error')
    except Exception as exc:
        log.exception('Agents proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Agents upstream error')
