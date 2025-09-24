"""
WeasyPrint PDF Generation Microservice
A FastAPI-based service that converts HTML to PDF using WeasyPrint
"""

import os
import logging
from typing import Optional
from io import BytesIO
import hashlib
import hmac

from fastapi import FastAPI, HTTPException, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import weasyprint
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.environ.get('WEASYPRINT_API_KEY', 'default-dev-key-change-in-production')
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')

# Initialize FastAPI app
app = FastAPI(
    title="WeasyPrint PDF Service",
    description="High-fidelity PDF generation service using WeasyPrint",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class PDFRequest(BaseModel):
    """Request model for PDF generation"""
    htmlContent: str
    customCss: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "htmlContent": "<html><body><h1>Hello World</h1></body></html>",
                "customCss": "body { font-family: Arial; }"
            }
        }


def verify_api_key(authorization: Optional[str] = None) -> bool:
    """Verify API key from Authorization header"""
    if not authorization:
        return False
    
    try:
        # Expected format: "Bearer <api_key>"
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return False
        
        provided_key = parts[1]
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(provided_key, API_KEY)
    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        return False


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "WeasyPrint PDF Service",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test WeasyPrint functionality
        test_html = "<html><body>Test</body></html>"
        test_doc = weasyprint.HTML(string=test_html)
        test_pdf = test_doc.write_pdf()
        
        return {
            "status": "healthy",
            "weasyprint": "functional",
            "pdf_generation": "working"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/generate-pdf")
async def generate_pdf(
    request: PDFRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Generate PDF from HTML content
    
    Args:
        request: PDFRequest containing HTML content and optional CSS
        authorization: Bearer token for API authentication
    
    Returns:
        Binary PDF content
    """
    
    # Verify API key (skip in development if no auth header provided)
    if authorization and not verify_api_key(authorization):
        logger.warning("Invalid API key provided")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        logger.info("Starting PDF generation")
        
        # Prepare HTML content with optional CSS
        html_content = request.htmlContent
        
        if request.customCss:
            # Inject custom CSS into the HTML
            css_tag = f"<style>{request.customCss}</style>"
            if "</head>" in html_content:
                html_content = html_content.replace("</head>", f"{css_tag}</head>")
            elif "<body>" in html_content:
                html_content = html_content.replace("<body>", f"<head>{css_tag}</head><body>")
            else:
                html_content = f"<html><head>{css_tag}</head><body>{html_content}</body></html>"
        
        # Generate PDF using WeasyPrint
        logger.info("Parsing HTML")
        html = weasyprint.HTML(string=html_content)
        
        logger.info("Generating PDF")
        pdf_bytes = html.write_pdf()
        
        logger.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
        
        # Return PDF as binary response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=document.pdf",
                "Content-Length": str(len(pdf_bytes))
            }
        )
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )


@app.post("/generate-pdf-base64")
async def generate_pdf_base64(
    request: PDFRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Generate PDF from HTML content and return as base64
    Alternative endpoint for clients that prefer base64 encoding
    """
    import base64
    
    if authorization and not verify_api_key(authorization):
        logger.warning("Invalid API key provided")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        html_content = request.htmlContent
        
        if request.customCss:
            css_tag = f"<style>{request.customCss}</style>"
            if "</head>" in html_content:
                html_content = html_content.replace("</head>", f"{css_tag}</head>")
            elif "<body>" in html_content:
                html_content = html_content.replace("<body>", f"<head>{css_tag}</head><body>")
            else:
                html_content = f"<html><head>{css_tag}</head><body>{html_content}</body></html>"
        
        html = weasyprint.HTML(string=html_content)
        pdf_bytes = html.write_pdf()
        
        # Encode to base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return {
            "pdf": pdf_base64,
            "size": len(pdf_bytes),
            "encoding": "base64"
        }
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )


if __name__ == "__main__":
    # Run with uvicorn when executed directly
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting WeasyPrint service on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )