import uuid

import requests
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from schemas import ChatRequest, Location

router = APIRouter(prefix="/api/chat", tags=["chat"])


def run_orca(request: Request, message: str, conversation_id: str, location):
    try:
        return request.app.state.orca.run(message, conversation_id, location)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream data provider unavailable: {exc}") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Request processing failed: {exc}") from exc


@router.post("")
def chat(req: ChatRequest, request: Request):
    conversation_id = req.conversation_id or f"conv_{uuid.uuid4().hex[:10]}"
    result = run_orca(request, req.message, conversation_id, req.location)
    return result.model_dump()


@router.websocket("/ws/{conversation_id}")
async def chat_ws(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            message = str(payload.get("message", "")).strip()
            if not message:
                await websocket.send_json({"error": "message is required"})
                continue
            try:
                loc = Location.model_validate(payload["location"]) if payload.get("location") else None
            except Exception as exc:
                await websocket.send_json({"error": f"Invalid location: {exc}"})
                continue
            try:
                result = run_orca(websocket.app, message, conversation_id, loc)
            except HTTPException as exc:
                await websocket.send_json({"error": exc.detail})
                continue
            await websocket.send_json(result.model_dump())
    except WebSocketDisconnect:
        pass
