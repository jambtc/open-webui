import logging
import os
import re
from urllib.parse import urlencode

import aiohttp
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from open_webui.utils.auth import get_verified_user

log = logging.getLogger(__name__)

router = APIRouter()
OPENCLAW_OPENAI_PROXY = os.environ.get('OPENCLAW_OPENAI_PROXY', '').rstrip('/')
KEYCLOAK_AUTH_SOURCES = {
    'oauth_session_id.access_token',
    'oauth_session_id.id_token',
    'oauth_id_token',
}


def _derive_workspace_from_name(name: str) -> str:
    normalized = re.sub(r'[^a-zA-Z0-9._-]+', '-', (name or '').strip().lower()).strip('._-')
    if not normalized:
        normalized = 'agent'
    return normalized


def _is_workspace_missing_error(payload: object) -> bool:
    text = str(payload).lower()
    return 'workspace' in text and ('required' in text or 'missing' in text)


async def _apply_request_authorization(
    headers: dict,
    request: Request,
    user,
    include_source: bool = False,
) -> dict | tuple[dict, str | None]:
    log.info(
        'BOXEDAI auth cookies user_id=%s cookie_names=%s has_oauth_id_token=%s has_oauth_session_id=%s has_auth_header=%s has_state_token=%s',
        getattr(user, 'id', None),
        sorted(request.cookies.keys()),
        bool(request.cookies.get('oauth_id_token')),
        bool(request.cookies.get('oauth_session_id')),
        bool(request.headers.get('authorization')),
        bool(getattr(getattr(request, 'state', None), 'token', None)),
    )

    oauth_session_id = request.cookies.get('oauth_session_id')
    if oauth_session_id:
        try:
            oauth_token = await request.app.state.oauth_manager.get_oauth_token(user.id, oauth_session_id)
            if oauth_token:
                if oauth_token.get('access_token'):
                    headers['authorization'] = f"Bearer {oauth_token['access_token']}"
                    log.info('BOXEDAI auth selected source=oauth_session_id.access_token user_id=%s', getattr(user, 'id', None))
                    if include_source:
                        return headers, 'oauth_session_id.access_token'
                    return headers
                if oauth_token.get('id_token'):
                    headers['authorization'] = f"Bearer {oauth_token['id_token']}"
                    log.info('BOXEDAI auth selected source=oauth_session_id.id_token user_id=%s', getattr(user, 'id', None))
                    if include_source:
                        return headers, 'oauth_session_id.id_token'
                    return headers
            log.warning('BOXEDAI auth oauth_session_id present but no oauth token resolved user_id=%s', getattr(user, 'id', None))
        except Exception as exc:
            log.exception(f'Error getting OpenClaw OAuth token: {exc}')

    oauth_id_token = request.cookies.get('oauth_id_token')
    if oauth_id_token:
        headers['authorization'] = f'Bearer {oauth_id_token}'
        log.info('BOXEDAI auth selected source=oauth_id_token user_id=%s', getattr(user, 'id', None))
        if include_source:
            return headers, 'oauth_id_token'
        return headers

    authorization = request.headers.get('authorization')
    if authorization:
        headers['authorization'] = authorization
        log.info('BOXEDAI auth selected source=request.authorization user_id=%s', getattr(user, 'id', None))
        if include_source:
            return headers, 'request.authorization'
        return headers

    state_token = getattr(request.state, 'token', None)
    if state_token and getattr(state_token, 'credentials', None) and not request.headers.get('x-api-key'):
        headers['authorization'] = f'Bearer {state_token.credentials}'
        log.info('BOXEDAI auth selected source=request.state.token user_id=%s', getattr(user, 'id', None))
        if include_source:
            return headers, 'request.state.token'
        return headers

    log.warning('BOXEDAI auth no bearer source resolved user_id=%s', getattr(user, 'id', None))
    if include_source:
        return headers, None
    return headers


@router.get('/agents/auth-capability')
async def get_agents_auth_capability(request: Request, user=Depends(get_verified_user)):
    _, source = await _apply_request_authorization(
        {'Accept': 'application/json'},
        request,
        user,
        include_source=True,
    )
    return JSONResponse(
        content={
            'can_forward_keycloak_jwt': source in KEYCLOAK_AUTH_SOURCES,
            'authorization_source': source,
        },
        status_code=200,
    )


@router.post('/agents')
async def create_agent(request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = await _apply_request_authorization({'Accept': 'application/json', 'Content-Type': 'application/json'}, request, user)

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Invalid JSON body: {exc}')
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail='JSON body must be an object')

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(upstream_url, json=body, headers=headers) as response:
                payload = await response.json(content_type=None)
                if response.status == 422 and _is_workspace_missing_error(payload):
                    fallback_body = dict(body)
                    fallback_body['workspace'] = _derive_workspace_from_name(str(body.get('name') or ''))
                    log.warning(
                        'BOXEDAI create fallback: retrying with derived workspace=%s user_id=%s',
                        fallback_body['workspace'],
                        getattr(user, 'id', None),
                    )
                    async with session.post(upstream_url, json=fallback_body, headers=headers) as retry_response:
                        retry_payload = await retry_response.json(content_type=None)
                        return JSONResponse(content=retry_payload, status_code=retry_response.status)
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

    headers = await _apply_request_authorization({'Accept': 'application/json'}, request, user)

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(upstream_url, headers=headers) as response:
                payload = await response.json(content_type=None)
                if isinstance(payload, dict):
                    items = payload.get('items')
                    log.info(
                        'BOXEDAI agents list upstream_status=%s items_count=%s default_agent_id=%s',
                        response.status,
                        len(items) if isinstance(items, list) else None,
                        payload.get('default_agent_id'),
                    )
                else:
                    log.info(
                        'BOXEDAI agents list upstream_status=%s payload_type=%s',
                        response.status,
                        type(payload).__name__,
                    )
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

    headers = await _apply_request_authorization({'Accept': 'application/json'}, request, user)

    query_items = dict(request.query_params)
    query = urlencode(query_items)
    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}"
    if query:
        upstream_url = f"{upstream_url}?{query}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(upstream_url, headers=headers) as response:
                payload = await response.json(content_type=None)
                if isinstance(payload, dict):
                    items = payload.get('items')
                    log.info(
                        'BOXEDAI agents list upstream_status=%s items_count=%s default_agent_id=%s',
                        response.status,
                        len(items) if isinstance(items, list) else None,
                        payload.get('default_agent_id'),
                    )
                else:
                    log.info(
                        'BOXEDAI agents list upstream_status=%s payload_type=%s',
                        response.status,
                        type(payload).__name__,
                    )
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

    headers = await _apply_request_authorization({'Accept': 'application/json'}, request, user)

    query_items = dict(request.query_params)
    query = urlencode(query_items)
    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}/knowledge/tree"
    if query:
        upstream_url = f"{upstream_url}?{query}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(upstream_url, headers=headers) as response:
                payload = await response.json(content_type=None)
                if isinstance(payload, dict):
                    items = payload.get('items')
                    log.info(
                        'BOXEDAI agents list upstream_status=%s items_count=%s default_agent_id=%s',
                        response.status,
                        len(items) if isinstance(items, list) else None,
                        payload.get('default_agent_id'),
                    )
                else:
                    log.info(
                        'BOXEDAI agents list upstream_status=%s payload_type=%s',
                        response.status,
                        type(payload).__name__,
                    )
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

    headers = await _apply_request_authorization({'Accept': 'application/json', 'Content-Type': 'application/json'}, request, user)

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


@router.delete('/agents/{agent_id}/knowledge/folders')
async def delete_agent_knowledge_folder(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = await _apply_request_authorization({'Accept': 'application/json'}, request, user)

    item_path = request.query_params.get('path', '')
    if not item_path:
        raise HTTPException(status_code=422, detail='path query parameter is required')
    recursive_param = request.query_params.get('recursive', 'true').strip().lower()
    recursive = recursive_param not in {'false', '0', 'no'}

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}/knowledge/folders"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                upstream_url,
                headers=headers,
                params={'path': item_path, 'recursive': 'true' if recursive else 'false'},
            ) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Agent knowledge folder delete proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge folder delete upstream response error')
    except Exception as exc:
        log.exception('Agent knowledge folder delete proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge folder delete upstream error')


@router.post('/agents/{agent_id}/knowledge/files/upload')
async def upload_agent_knowledge_file(
    agent_id: str,
    request: Request,
    file: UploadFile = File(...),
    path: str = Form(default=''),
    filename: str | None = Form(default=None),
    overwrite: bool = Form(default=False),
    user=Depends(get_verified_user),
):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = await _apply_request_authorization({'Accept': 'application/json'}, request, user)

    form = aiohttp.FormData()
    form.add_field('file', await file.read(), filename=(filename or file.filename or 'upload'), content_type=file.content_type or 'application/octet-stream')
    form.add_field('path', path or '')
    if filename:
        form.add_field('filename', filename)
    form.add_field('overwrite', 'true' if overwrite else 'false')

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}/knowledge/files/upload"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(upstream_url, data=form, headers=headers) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Agent knowledge upload proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge upload upstream response error')
    except Exception as exc:
        log.exception('Agent knowledge upload proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge upload upstream error')


@router.delete('/agents/{agent_id}/knowledge/files')
async def delete_agent_knowledge_file(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = await _apply_request_authorization({'Accept': 'application/json'}, request, user)

    item_path = request.query_params.get('path', '')
    if not item_path:
        raise HTTPException(status_code=422, detail='path query parameter is required')

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}/knowledge/files"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(upstream_url, headers=headers, params={'path': item_path}) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Agent knowledge file delete proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge file delete upstream response error')
    except Exception as exc:
        log.exception('Agent knowledge file delete proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge file delete upstream error')


@router.get('/agents/{agent_id}/knowledge/files/content')
async def get_agent_knowledge_file_content(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = await _apply_request_authorization({'Accept': 'application/json'}, request, user)

    item_path = request.query_params.get('path', '')
    if not item_path:
        raise HTTPException(status_code=422, detail='path query parameter is required')

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}/knowledge/files/content"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(upstream_url, headers=headers, params={'path': item_path}) as response:
                payload = await response.json(content_type=None)
                return JSONResponse(content=payload, status_code=response.status)
    except aiohttp.ClientResponseError as exc:
        log.exception('Agent knowledge file content proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge file content upstream response error')
    except Exception as exc:
        log.exception('Agent knowledge file content proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge file content upstream error')


@router.get('/agents/{agent_id}/knowledge/files/download')
async def download_agent_knowledge_file(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = await _apply_request_authorization({'Accept': '*/*'}, request, user)

    item_path = request.query_params.get('path', '')
    if not item_path:
        raise HTTPException(status_code=422, detail='path query parameter is required')

    upstream_url = f"{OPENCLAW_OPENAI_PROXY}/api/v1/agents/{agent_id}/knowledge/files/download"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(upstream_url, headers=headers, params={'path': item_path}) as response:
                payload = await response.read()
                response_headers: dict[str, str] = {}
                content_disposition = response.headers.get('content-disposition')
                if content_disposition:
                    response_headers['content-disposition'] = content_disposition
                return Response(
                    content=payload,
                    status_code=response.status,
                    media_type=response.headers.get('content-type', 'application/octet-stream'),
                    headers=response_headers,
                )
    except aiohttp.ClientResponseError as exc:
        log.exception('Agent knowledge file download proxy upstream response error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge file download upstream response error')
    except Exception as exc:
        log.exception('Agent knowledge file download proxy upstream error: %s', exc)
        raise HTTPException(status_code=502, detail='Agent knowledge file download upstream error')


@router.patch('/agents/{agent_id}')
async def update_agent(agent_id: str, request: Request, user=Depends(get_verified_user)):
    if not OPENCLAW_OPENAI_PROXY:
        raise HTTPException(status_code=500, detail='OPENCLAW_OPENAI_PROXY is not configured')

    headers = await _apply_request_authorization({'Accept': 'application/json', 'Content-Type': 'application/json'}, request, user)

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

    headers = await _apply_request_authorization({'Accept': 'application/json'}, request, user)

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
