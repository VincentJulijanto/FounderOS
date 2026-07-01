# FounderOS backend — Hugging Face Spaces (Docker SDK), Decision #8.
# A long-running container holds the ~90–240s debate run that serverless can't.
# Listens on 7860 (HF Docker default) and bakes the seed vault into the image so a
# cold instance already has sample company history to demo against.

FROM python:3.11-slim

WORKDIR /app

# 1. Dependencies first, as their own layer, so installs cache across rebuilds.
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 2. Application code (backend is a PEP 420 namespace package — no __init__.py).
COPY backend/ ./backend/

# 3. Bake the seed vault into the image at the path VAULT_PATH points at. This is
#    what makes "a returning company that remembers" work on a fresh instance.
COPY vault/ /app/vault/

# 4. Non-secret runtime defaults. Secrets (QWEN_API_KEY) and env-specific values
#    (ALLOWED_ORIGINS) come from Space variables, never baked into the image.
#    Path is configuration (Decision #8): the same image runs locally and on the Space.
ENV VAULT_PATH=/app/vault \
    USE_MOCK_LLM=true \
    PYTHONUNBUFFERED=1

# 5. Port must match app_port: 7860 in the Space README frontmatter.
EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
