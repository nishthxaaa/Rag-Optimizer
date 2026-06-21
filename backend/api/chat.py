from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.api.state import app_state, OptimizationStatus
import json

router = APIRouter()

@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat.
    
    Message protocol:
      Client sends: {"question": "your question here"}
      Server sends: {"type": "token", "content": "word "}  (streamed)
                    {"type": "done", "content": ""}         (end of response)
                    {"type": "error", "content": "message"} (on failure)
    """
    await websocket.accept()

    try:
        while True:
            # Wait for a question from the client
            raw = await websocket.receive_text()
            data = json.loads(raw)
            question = data.get("question", "").strip()

            if not question:
                await websocket.send_json({"type": "error", "content": "Empty question."})
                continue

            # Make sure optimization is complete
            if app_state.status != OptimizationStatus.COMPLETE:
                await websocket.send_json({
                    "type": "error",
                    "content": "Optimization not complete yet. Please wait."
                })
                continue

            if app_state.winner_chain is None:
                await websocket.send_json({
                    "type": "error",
                    "content": "No winning chain loaded."
                })
                continue

            # Stream the response token by token
            try:
                async for chunk in app_state.winner_chain.astream(question):
                    if chunk:
                        await websocket.send_json({
                            "type": "token",
                            "content": chunk
                        })

                # Signal the end of the response
                await websocket.send_json({"type": "done", "content": ""})

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Error generating response: {str(e)}"
                })

    except WebSocketDisconnect:
        print("[WS] Client disconnected.")
    except Exception as e:
        print(f"[WS] Unexpected error: {e}")