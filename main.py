from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
import httpx
import logging

# Initialize the FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a route to capture all paths under /ollama-endpoint/{path:path}
@app.api_route("/ollama-endpoint/{path:path}", methods=["POST"])
async def forward_to_ollama(request: Request, path: str):
    print("Request received")
    try:
        # Construct the full URL for the locally running Ollama instance
        ollama_url = f"http://0.0.0.0:11434/{path}"
        logger.info(f"Forwarding request to: {ollama_url}")

        # Prepare headers
        headers = dict(request.headers)
        headers["Content-Type"] = "application/json"

        # Forward the request to Ollama
        async with httpx.AsyncClient() as client:
            if request.method == "POST":
                request_payload = await request.json()
                response = await client.post(ollama_url, headers=headers, json=request_payload)
            else:
                logger.error(f"BAD REQUEST. Not a POST request. Request Method found to be: {request.method}")
                raise HTTPException(status_code=500, detail=f"BAD REQUEST. Not a POST request. Request Method found to be: {request.method}")
            
        # Handle Ollama response using iter_lines
        response.encoding = "utf-8"
        async def stream_response():
            async for chunk in response.aiter_lines():
                yield chunk + '\n'  # Ensure each chunk ends with newline

        return StreamingResponse(stream_response(), status_code=response.status_code)

    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP status error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Define a route for the health check
@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)