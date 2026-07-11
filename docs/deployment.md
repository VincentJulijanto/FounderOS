# FounderOS — Deployment

The single deployment reference both lanes read. Records **Decision #8**: the backend runs on
**Hugging Face Spaces (Docker SDK)**, the frontend on **Vercel Hobby**. See the rationale in
`docs/architecture.md` § Deployment; the standing ownership split is in `CLAUDE.md`.

> **Reference doc.** The Dockerfile spec below is now **implemented** at the repo root: `Dockerfile`
> (+ `.dockerignore`), the Space README lives at `SPACE_README.md` (place it at the Space root as
> `README.md`), and the baked seed vault is `vault/` (two sample companies with `.md` history). The
> spec stays here as the rationale for what that file must do.

---

## Why this shape (the short version)

- The full 8-agent debate takes **~90–240s per run**. HF Spaces runs a **persistent container with
  no per-request function timeout**, so a 240s run completes.
- **Not Vercel for the backend** — serverless function timeouts can't hold a 240s run, and the
  ephemeral serverless filesystem can't hold the vault's markdown write-back.
- **Not Railway or Render** — both gate the usable tier behind payment. **HF free CPU Basic (2 vCPU
  / 16 GB) needs no card and no trial clock.**
- Frontend stays on **Vercel Hobby** (Next.js), pointed at the backend via one env var.

---

## (a) Hugging Face Space setup (backend)

1. **Create a Space** → SDK: **Docker** → hardware: **CPU Basic (free, 2 vCPU / 16 GB)**.
2. **A Space is its own git repo.** It needs **its own `README.md` with YAML frontmatter** that
   configures the Space — this is **distinct from the project `README.md`** at the repo root. The
   Space README frontmatter must declare the Docker SDK and the app port:

   ```yaml
   ---
   title: FounderOS API
   emoji: 🧭
   colorFrom: indigo
   colorTo: yellow
   sdk: docker
   app_port: 7860
   pinned: false
   ---
   ```

   > `app_port: 7860` must match the port the container listens on (HF Docker default). If the two
   > disagree, the Space serves nothing.

3. **Get the code onto the Space.** Either push the backend to the Space's git remote, or connect
   the Space to this GitHub repo. The image is built from the `Dockerfile` at the Space root.
4. **The container runs `uvicorn` on `7860`** and serves the FastAPI app.
5. **The seed vault is copied into the image at build time** (see the Dockerfile spec) so a fresh
   instance already has sample company history to demo against.
6. **Set the Space secrets/variables** (Settings → Variables and secrets): `QWEN_API_KEY` (secret),
   `USE_MOCK_LLM`, `VAULT_PATH`, `ALLOWED_ORIGINS`. See [§ (c)](#c-environment-variables).

---

## (b) Dockerfile SPEC (prose only — Lane A writes the actual file)

The image must:

1. **Start from a slim Python base** matching the backend's Python version.
2. **Install dependencies first** — copy `backend/requirements.txt` and install, as its own layer,
   so dependency installs cache across rebuilds.
3. **Copy the backend application** into the image (e.g. under `/app`).
4. **Bake the seed vault** into the image — copy the sample company vault folders (a couple of
   companies, each with `.md` decision history) to the path `VAULT_PATH` points at (e.g.
   `/app/vault`). This is what makes "a returning company that remembers" work on a cold instance.
5. **Set the runtime env defaults** that aren't secrets — e.g. `VAULT_PATH=/app/vault`. Secrets
   (`QWEN_API_KEY`) and env-specific values (`ALLOWED_ORIGINS`) come from Space variables, not the
   image.
6. **Expose / listen on port `7860`** (must match `app_port` in the Space README).
7. **Launch uvicorn** bound to `0.0.0.0:7860` serving the FastAPI app
   (`backend.main:app` — confirm the import path against the final module layout).

> Do **not** hardcode the vault path or CORS origins into the image — both are read from env so the
> same image runs locally, on the Space, and (future) against a synced vault. See
> [§ vault posture](#vault-persistence-posture).

---

## (c) Environment variables

**Backend** (Space variables / local `.env`)

| Var | Purpose | Example |
|---|---|---|
| `VAULT_PATH` | Filesystem root of the per-company vault. **Env-configurable, never hardcoded.** | `/app/vault` |
| `ALLOWED_ORIGINS` | CORS allow-list. **Must include the Vercel domain and localhost.** | `https://founderos.vercel.app,http://localhost:3000` |
| `QWEN_API_KEY` | DashScope key. Empty → mock mode. | *(secret)* |
| `USE_MOCK_LLM` | `true` runs keyless with mock fixtures. | `false` in live demo |
| *(port)* | Container listens here; matches Space `app_port`. | `7860` |

**Frontend** (Vercel project env)

| Var | Purpose | Example |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL. The frontend **must** read this and **never hardcode** the backend URL. | `https://<user>-founderos.hf.space` |

**Required CORS origins:** the backend's `ALLOWED_ORIGINS` must list every frontend origin that will
call it — the Vercel production domain (and any Vercel preview domains you demo from) plus
`http://localhost:3000` for dev. A tunnel demo (below) calls from the same frontend origins, so no
extra backend CORS entry is needed unless you also serve the frontend from a new origin.

**Ownership:** Lane A owns `VAULT_PATH` + `ALLOWED_ORIGINS` + the Dockerfile; Lane B owns
`NEXT_PUBLIC_API_BASE_URL` wiring. Both lanes depend on this contract (watchlisted in `CLAUDE.md`).

---

## (d) Local + tunnel alternative (low-setup live demo)

Same backend code, different host — good for a live demo when a laptop can stay on.

1. Run the backend locally (mock or live):
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
2. Expose it with a public tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:8000      # Cloudflare Tunnel
   # or:
   ngrok http 8000                                     # ngrok
   ```
3. Point the frontend at the printed public URL by setting **`NEXT_PUBLIC_API_BASE_URL`** to it
   (Vercel env for a deployed frontend, or `.env.local` for a local `npm run dev`).
4. Ensure the backend's `ALLOWED_ORIGINS` includes whatever origin the frontend is served from.

Locally, `VAULT_PATH` can point at a checked-out vault folder (e.g. the seed vault) so write-back
persists to disk between runs on your machine.

---

## (e) Vercel frontend

Nothing changes about the frontend build. Only:

1. In the Vercel project, set **`NEXT_PUBLIC_API_BASE_URL`** to the backend URL — the **HF Space
   URL**, the **tunnel URL**, or `http://localhost:8000` in dev.
2. Redeploy so the value is baked into the client bundle (`NEXT_PUBLIC_*` vars are read at build
   time).
3. Confirm the backend's `ALLOWED_ORIGINS` includes the Vercel domain.

---

## Vault persistence posture

The HF free-tier container filesystem (including `/data`) is **ephemeral**. Acceptable for the
hackathon: a demo runs inside **one live instance**, so `write_back` persists **within the
session**; only a restart/redeploy resets it — which we don't do mid-demo. The **seed vault baked
into the image** means a returning sample company already has history on a cold start.

> **Future-only (not this phase):** for cross-restart persistence, push the vault to a **HF Dataset
> repo** via the `huggingface_hub` library. **Do not reintroduce Postgres** — vault-only stands
> (Decision #1).

---

## Pre-demo checklist

- [ ] Space README frontmatter has `sdk: docker` and `app_port: 7860`.
- [ ] Image builds; container serves on `7860`.
- [ ] Seed vault present in the image at `VAULT_PATH`.
- [ ] Space secrets set: `QWEN_API_KEY`, `USE_MOCK_LLM`, `VAULT_PATH`, `ALLOWED_ORIGINS`.
- [ ] `ALLOWED_ORIGINS` includes the Vercel domain + `http://localhost:3000`.
- [ ] Vercel `NEXT_PUBLIC_API_BASE_URL` points at the live backend; frontend redeployed.
- [ ] One end-to-end run completes (allow up to ~240s in live mode).
- [ ] Fallback: local + Cloudflare Tunnel ready in case the Space is cold/slow.
