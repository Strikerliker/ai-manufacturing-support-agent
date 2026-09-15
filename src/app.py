from __future__ import annotations

import json
import os
from typing import Any

from rag import Passage, chunk_markdown, citations, fallback_answer, format_context, requires_escalation, retrieve

SERVICE_NAME = "ai-manufacturing-support-agent"
KNOWLEDGE_BUCKET = os.getenv("KNOWLEDGE_BUCKET", "")
KNOWLEDGE_PREFIX = os.getenv("KNOWLEDGE_PREFIX", "knowledge/")
MODEL_ID = os.getenv("MODEL_ID", "amazon.nova-lite-v1:0")
MAX_QUESTION_CHARS = int(os.getenv("MAX_QUESTION_CHARS", "2000"))
MIN_RETRIEVAL_SCORE = float(os.getenv("MIN_RETRIEVAL_SCORE", "0.08"))
TOP_K = int(os.getenv("TOP_K", "4"))


def response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
        },
        "body": json.dumps(body),
    }


def parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body")
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Request body must be valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Request body must be a JSON object.")
    return parsed


def validate_question(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("question must be a string.")
    question = value.strip()
    if not question:
        raise ValueError("question is required.")
    if len(question) > MAX_QUESTION_CHARS:
        raise ValueError(f"question exceeds the {MAX_QUESTION_CHARS}-character limit.")
    return question


def get_s3_client() -> Any:
    import boto3

    return boto3.client("s3")


def get_bedrock_client() -> Any:
    import boto3

    return boto3.client("bedrock-runtime")


def load_knowledge_from_s3() -> list[Passage]:
    if not KNOWLEDGE_BUCKET:
        raise RuntimeError("KNOWLEDGE_BUCKET is not configured.")

    s3 = get_s3_client()
    token: str | None = None
    passages: list[Passage] = []

    while True:
        kwargs: dict[str, Any] = {"Bucket": KNOWLEDGE_BUCKET, "Prefix": KNOWLEDGE_PREFIX}
        if token:
            kwargs["ContinuationToken"] = token
        page = s3.list_objects_v2(**kwargs)
        for item in page.get("Contents", []):
            key = str(item.get("Key") or "")
            if not key.lower().endswith(".md"):
                continue
            obj = s3.get_object(Bucket=KNOWLEDGE_BUCKET, Key=key)
            text = obj["Body"].read().decode("utf-8")
            source = key.rsplit("/", 1)[-1]
            passages.extend(chunk_markdown(source, text))

        if not page.get("IsTruncated"):
            break
        token = page.get("NextContinuationToken")
        if not token:
            break

    return passages


def invoke_grounded_model(question: str, context: str) -> str:
    client = get_bedrock_client()
    result = client.converse(
        modelId=MODEL_ID,
        system=[
            {
                "text": (
                    "You are a manufacturing IT support assistant. Answer only from the approved "
                    "support context provided. Do not invent ERP transactions, permissions, safety "
                    "steps, or production changes. If the context is insufficient, say the approved "
                    "procedure does not contain enough information and recommend escalation. Keep "
                    "the response concise, operationally useful, and distinguish checks from changes."
                )
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            f"QUESTION:\n{question}\n\nAPPROVED SUPPORT CONTEXT:\n{context}\n\n"
                            "Answer the question using only the approved context."
                        )
                    }
                ],
            }
        ],
        inferenceConfig={"maxTokens": 900, "temperature": 0.1},
    )
    blocks = result.get("output", {}).get("message", {}).get("content", [])
    answer = "".join(block.get("text", "") for block in blocks if isinstance(block, dict)).strip()
    if not answer:
        raise RuntimeError("The model returned an empty response.")
    return answer


def answer_question(question: str, passages: list[Passage]) -> dict[str, Any]:
    matches = retrieve(
        question,
        passages,
        top_k=TOP_K,
        min_score=MIN_RETRIEVAL_SCORE,
    )
    escalation = requires_escalation(question)

    if not matches:
        return {
            "answer": fallback_answer(),
            "citations": [],
            "grounded": False,
            "escalation_required": True,
        }

    answer = invoke_grounded_model(question, format_context(matches))
    return {
        "answer": answer,
        "citations": citations(matches),
        "grounded": True,
        "escalation_required": escalation,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    request_context = event.get("requestContext", {})
    http = request_context.get("http", {})
    method = str(http.get("method", "")).upper()
    path = str(event.get("rawPath") or http.get("path") or "")

    if method == "GET" and path == "/health":
        return response(200, {"status": "ok", "service": SERVICE_NAME})

    if method != "POST" or path != "/support":
        return response(404, {"error": "not_found"})

    try:
        payload = parse_body(event)
        question = validate_question(payload.get("question"))
        passages = load_knowledge_from_s3()
        result = answer_question(question, passages)
    except ValueError as exc:
        return response(400, {"error": "invalid_request", "message": str(exc)})
    except Exception:
        return response(
            502,
            {
                "error": "support_service_unavailable",
                "message": "The support agent could not complete the request.",
            },
        )

    request_id = getattr(context, "aws_request_id", None) if context else None
    return response(
        200,
        {
            "service": SERVICE_NAME,
            "model": MODEL_ID,
            "request_id": request_id,
            **result,
        },
    )
