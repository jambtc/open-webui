import logging
import os
from urllib.parse import urlencode

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from open_webui.utils.auth import get_verified_user

log = logging.getLogger(__name__)

router = APIRouter()
OPENCLAW_OPENAI_PROXY = os.environ.get('OPENCLAW_OPENAI_PROXY', '').rstrip('/')


@router.post('/agents')
async def create_agent(request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    authorization = request.headers.get('authorization')
    if authorization:
        headers['authorization'] = authorization

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Invalid JSON body: {exc}')

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(upstream_url, json=body, headers=headers) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Create agent proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Create agent upstream response error')
    except Exception as exc:
        log.exception('Create agent proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Create agent upstream error')


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


@router.get('/agents/{agent_id}')
async def get_agent_detail(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = {'Accept': 'application/json'}
    authorization = request.headers.get('authorization')
    if authorization:
        headers['authorization'] = authorization

    query_items = dict(request.query_params)
    query = urlencode(query_items)
    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}"
    if query:
        upstream_url = f"{upstream_url}?{query}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(upstream_url, headers=headers) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Agent detail proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent detail upstream response error')
    except Exception as exc:
        log.exception('Agent detail proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent detail upstream error')


@router.get('/agents/{agent_id}/knowledge/tree')
async def get_agent_knowledge_tree(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = {'Accept': 'application/json'}
    authorization = request.headers.get('authorization')
    if authorization:
        headers['authorization'] = authorization

    query_items = dict(request.query_params)
    query = urlencode(query_items)
    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}/knowledge/tree"
    if query:
        upstream_url = f"{upstream_url}?{query}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(upstream_url, headers=headers) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Agent knowledge tree proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge tree upstream response error')
    except Exception as exc:
        log.exception('Agent knowledge tree proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge tree upstream error')


@router.post('/agents/{agent_id}/knowledge/folders')
async def create_agent_knowledge_folder(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    authorization = request.headers.get('authorization')
    if authorization:
        headers['authorization'] = authorization

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Invalid JSON body: {exc}')

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}/knowledge/folders"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(upstream_url, json=body, headers=headers) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Agent knowledge folder create proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge folder create upstream response error')
    except Exception as exc:
        log.exception('Agent knowledge folder create proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge folder create upstream error')


@router.patch('/agents/{agent_id}')
async def update_agent(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    authorization = request.headers.get('authorization')
    if authorization:
        headers['authorization'] = authorization

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Invalid JSON body: {exc}')

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(upstream_url, json=body, headers=headers) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Update agent proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Update agent upstream response error')
    except Exception as exc:
        log.exception('Update agent proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Update agent upstream error')


@router.delete('/agents/{agent_id}')
async def delete_agent(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = {'Accept': 'application/json'}
    authorization = request.headers.get('authorization')
    if authorization:
        headers['authorization'] = authorization

    query_items = dict(request.query_params)
    query = urlencode(query_items)
    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}"
    if query:
        upstream_url = f"{upstream_url}?{query}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(upstream_url, headers=headers) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Delete agent proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Delete agent upstream response error')
    except Exception as exc:
        log.exception('Delete agent proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Delete agent upstream error')
