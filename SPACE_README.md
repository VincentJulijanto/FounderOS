---
title: FounderOS API
emoji: 🧭
colorFrom: indigo
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# FounderOS API (Hugging Face Space)

> **This file is the Hugging Face Space's `README.md`, not the project README.** When deploying to
> a Space, place this file at the Space root as `README.md`. Hugging Face reads the YAML frontmatter
> above to configure the Space — `sdk: docker` builds from the `Dockerfile` at the Space root, and
> `app_port: 7860` **must** match the port the container listens on (see the `Dockerfile`). If the
> two disagree, the Space serves nothing.

The FastAPI backend for FounderOS — an AI board that evaluates one company decision and returns a
board-ready memo. The full 7-agent debate takes ~90–240s per run, which is why this runs as a
long-running container (Decision #8) rather than serverless.

## Space variables & secrets

Set these under **Settings → Variables and secrets** (full reference: `docs/deployment.md`):

| Name | Kind | Example |
|---|---|---|
| `QWEN_API_KEY` | secret | *(DashScope key; empty → mock mode)* |
| `USE_MOCK_LLM` | variable | `false` for a live demo, `true` for keyless |
| `VAULT_PATH` | variable | `/app/vault` (matches the baked seed vault) |
| `ALLOWED_ORIGINS` | variable | `https://<your-app>.vercel.app,http://localhost:3000` |

The image ships in keyless **mock mode** by default and boots against the baked seed vault, so the
Space is demoable the moment it builds — set `QWEN_API_KEY` + `USE_MOCK_LLM=false` to go live.
