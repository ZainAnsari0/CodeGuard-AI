"""
CodeGuard AI - AI API Endpoints
AI service status, health checks, and vulnerability explanation.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.base import ResponseSchema
from app.models.user import User
from app.api.dependencies import get_current_user
from app.ai.fallback_chain import ai_chain
from app.ai.parser import LLMOutputParser
from app.ai.prompts.manager import PromptManager
from app.ai.ollama_client import ollama_client

router = APIRouter()

# Singleton instances — avoids re-initializing on every request
_prompt_manager = PromptManager()
_output_parser = LLMOutputParser()


class ExplainRequest(BaseModel):
    """Request body for AI explain endpoint."""
    vulnerability_type: str
    severity: str = "medium"
    cwe_id: Optional[str] = None
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None
    language: str = "python"


@router.get("/status", response_model=dict)
async def get_ai_status():
    """Get AI service status including Ollama availability."""
    health = await ollama_client.check_health()
    return {
        "service": "CodeGuard AI",
        "ollama": health,
        "providers": [p.name for p in ai_chain.providers],
    }


@router.get("/ollama-health", response_model=dict)
async def ollama_health():
    """Check Ollama server health and available models."""
    from fastapi import HTTPException
    result = await ollama_client.check_health()
    if not result["available"]:
        raise HTTPException(
            status_code=503,
            detail={
                "available": False,
                "error": result["error"],
                "message": "Ollama server is not reachable. Start it with: ollama serve",
            },
        )
    return result


@router.post("/explain", response_model=ResponseSchema)
async def explain_finding(
    request: ExplainRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Explain a vulnerability finding using the AI fallback chain."""
    prompt = _prompt_manager.render_template(
        "explanation",
        {
            "vulnerability_type": request.vulnerability_type,
            "severity": request.severity,
            "cwe_id": request.cwe_id or "",
            "language": request.language,
            "code_snippet": request.code_snippet or "",
        },
    )

    result = await ai_chain.generate(
        prompt=prompt,
        finding=request.model_dump(),
    )

    raw_response = result.get("response", "")
    try:
        explanation = _output_parser.parse_explanation(raw_response)
        explanation_data = explanation.model_dump() if hasattr(explanation, "model_dump") else explanation
    except Exception:
        explanation_data = {"raw_explanation": raw_response}

    explanation_data["provider_used"] = result.get("provider_used", "unknown")

    return ResponseSchema(
        message="Explanation generated",
        data=explanation_data,
    )