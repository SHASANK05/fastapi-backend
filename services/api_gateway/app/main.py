import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException, status
from jose import JWTError, jwt

SECRET_KEY = os.getenv("JWT_SECRET", "supersecretshopeasejwtkey2026")
ALGORITHM = "HS256"

SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000"),
    "users": os.getenv("USER_SERVICE_URL", "http://user_service:8000"),
    "products": os.getenv("PRODUCT_SERVICE_URL", "http://product_service:8000"),
    "orders": os.getenv("ORDER_SERVICE_URL", "http://order_service:8000"),
    "payments": os.getenv("PAYMENT_SERVICE_URL", "http://payment_service:8000"),
}

app = FastAPI(title="ShopEase API Gateway", version="1.0.0")

def is_public_route(path: str, method: str) -> bool:
    clean_path = path.rstrip("/")
    if clean_path in ["/api/v1/auth/login", "/api/v1/auth/register"]:
        return True
    if clean_path.startswith("/api/v1/products") and method.upper() == "GET":
        return True
    if clean_path in ["", "/", "/health", "/docs", "/openapi.json"]:
        return True
    return False

@app.get("/")
def root():
    return {"service": "API Gateway", "status": "operational", "port": 8000}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.api_route("/api/v1/{service_name}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.api_route("/api/v1/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def reverse_proxy(service_name: str, request: Request, path: str = ""):
    if service_name not in SERVICES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service '{service_name}' not recognized")

    target_base = SERVICES[service_name]
    target_url = f"{target_base}/api/v1/{service_name}" + (f"/{path}" if path else "")
    
    in_headers = {k.lower(): v for k, v in request.headers.items()}
    in_headers.pop("host", None)
    in_headers.pop("content-length", None)

    full_path = f"/api/v1/{service_name}" + (f"/{path}" if path else "")
    
    if not is_public_route(full_path, request.method):
        auth_header = in_headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Missing or invalid Authorization header"
            )
        
        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            role = payload.get("role")
            if user_id is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
            
            in_headers["x-user-id"] = str(user_id)
            in_headers["x-user-role"] = str(role)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    body = await request.body()
    query_params = request.url.query

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            upstream_res = await client.request(
                method=request.method,
                url=target_url,
                params=query_params if query_params else None,
                content=body if body else None,
                headers=in_headers
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail=f"Downstream service unreachable: {str(exc)}"
            )

    excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
    response_headers = {k: v for k, v in upstream_res.headers.items() if k.lower() not in excluded_headers}
    return Response(
        content=upstream_res.content,
        status_code=upstream_res.status_code,
        headers=response_headers,
        media_type=upstream_res.headers.get("content-type")
    )
