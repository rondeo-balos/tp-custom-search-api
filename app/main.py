from fastapi import FastAPI, HTTPException, Depends, Query as QueryParam, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Optional
from app.config import settings
from app.models import SearchResponse
from app.scraper import scraper
from app.cache import cache_manager
from app.rate_limiter import rate_limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TP Custom Search API",
    description="Google Custom Search API compatible endpoint using Playwright",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency: API Key authentication
async def verify_api_key(key: Optional[str] = QueryParam(None, alias="key")):
    """Verify API key if authentication is enabled"""
    if settings.enable_auth:
        if not key or key != settings.api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
    return key


# Dependency: Rate limiting
async def check_rate_limit(
    key: Optional[str] = QueryParam(None, alias="key"),
    x_forwarded_for: Optional[str] = Header(None)
):
    """Check rate limit for client"""
    if not settings.rate_limit_enabled:
        return
    
    # Use API key as identifier, fallback to IP
    client_id = key or x_forwarded_for or "anonymous"
    
    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "code": 429,
                    "message": "Rate limit exceeded",
                    "status": "RESOURCE_EXHAUSTED"
                }
            }
        )


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Starting TP Custom Search API")
    await scraper.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down TP Custom Search API")
    await scraper.close()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "TP Custom Search API",
        "version": "1.0.0",
        "description": "Google Custom Search API compatible endpoint",
        "endpoints": {
            "search": "/customsearch/v1",
            "health": "/health",
            "stats": "/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "tp-custom-search-api"
    }


@app.get("/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get API statistics"""
    return {
        "cache": cache_manager.get_stats(),
        "rate_limit": {
            "enabled": settings.rate_limit_enabled,
            "calls": settings.rate_limit_calls,
            "period": settings.rate_limit_period
        }
    }


@app.get("/customsearch/v1", response_model=SearchResponse)
async def custom_search(
    q: str = QueryParam(..., description="Search query"),
    cx: Optional[str] = QueryParam(None, description="Custom search engine ID"),
    key: Optional[str] = QueryParam(None, description="API key"),
    num: Optional[int] = QueryParam(10, ge=1, le=10, description="Number of results"),
    start: Optional[int] = QueryParam(1, ge=1, le=91, description="Start index"),
    lr: Optional[str] = QueryParam(None, description="Language restriction"),
    safe: Optional[str] = QueryParam("off", description="Safe search"),
    dateRestrict: Optional[str] = QueryParam(None, description="Date restriction"),
    _verify_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Custom Search API endpoint (compatible with Google Custom Search API v1)
    
    Query Parameters:
    - q: Search query (required)
    - cx: Custom search engine ID (optional, for compatibility)
    - key: API key (required if authentication enabled)
    - num: Number of results to return (1-10, default: 10)
    - start: Starting index of results (1-91, default: 1)
    - lr: Language restriction (e.g., 'lang_en')
    - safe: Safe search level ('off', 'medium', 'high')
    - dateRestrict: Date restriction (e.g., 'd7' for last 7 days)
    """
    try:
        # Check cache
        cache_key = cache_manager.get_key(q, {
            'num': num,
            'start': start,
            'lr': lr,
            'safe': safe
        })
        
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached result for query: {q}")
            return JSONResponse(content=cached_result)
        
        # Perform search
        logger.info(f"Performing search for query: {q}")
        result = await scraper.search_google(
            query=q,
            num_results=num,
            start_index=start,
            language=lr,
            safe=safe
        )
        
        # Cache result
        cache_manager.set(cache_key, result)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": 500,
                    "message": f"Search failed: {str(e)}",
                    "status": "INTERNAL"
                }
            }
        )


@app.post("/cache/clear")
async def clear_cache(api_key: str = Depends(verify_api_key)):
    """Clear search cache"""
    cache_manager.clear()
    return {"message": "Cache cleared successfully"}


@app.get("/debug/searxng")
async def debug_searxng(
    q: str = QueryParam(..., description="Search query"),
    api_key: str = Depends(verify_api_key)
):
    """Debug endpoint to see raw SearXNG response"""
    import httpx
    import os
    
    searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{searxng_url}/search",
                params={'q': q, 'format': 'json', 'language': 'en'}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
