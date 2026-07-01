# CloudPilot AI — Production Readiness Checklist

Status: Demo/hackathon-grade app. This doc lists everything needed to take it to production, in priority order. Boxes already fixed in code are marked ✅.

---

## Phase 0 — Correctness bugs (fix before anything else)

- [x] ✅ `graph.py` missing `import re` → silent NameError swallowed by broad except, killed AI summary parsing whenever LLM returned markdown-fenced JSON. **Fixed.**
- [x] ✅ `/api/v1/recent` returned `"Running"` for completed tasks (reversed label). **Fixed.**
- [x] ✅ `useAnalysisStream.ts` / `useInfrastructureStream.ts` — `onerror` read `status` from a stale closure, so real mid-stream connection drops never surfaced as errors (user just sees an infinite spinner). Fixed with `statusRef`. **Fixed.**
- [ ] Broad `except: pass` / `except Exception: pass` blocks throughout (`scanner.py`, `graph.py`, `infra_graph.py`) swallow every error silently. Fine as a *fallback* mechanism, but you currently have **zero visibility** when LLM calls fail — add structured logging (see Observability) inside every except block, don't just `pass`.

## Phase 1 — Stop the UI lying (fake/simulated pieces)

- [ ] **`DeploymentStepsCard.tsx`** — shows "Build & Push Docker Image", "Provision Infrastructure", "Deploy Application", "Setup Monitoring" as if real AWS deployment is happening. The backend **never deploys anything** — it only generates IaC files for the user to run themselves. Either:
  - (a) Remove this card entirely and replace with a clear "Download → run `terraform apply` yourself" CTA, or
  - (b) Build the real thing: an actual deployment agent that calls AWS APIs (ECS/App Runner/Amplify) via boto3/Terraform Cloud, with real per-step status.
- [ ] **`RecentDeploymentsCard.tsx`** — hardcoded array, not wired to `/api/v1/recent`. Wire it up or remove the card.
- [ ] **`CostEstimator`** — static heuristic table (e.g., ECS = flat $25/mo), not live AWS pricing. Label it explicitly as "Estimated" in the UI (already says this in places, make sure it's consistent everywhere cost appears), or integrate the real [AWS Price List API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-price-list-query-api.html).
- [ ] Any other "confidence_score" / "validation_score" numbers the LLM invents — these are LLM opinions, not measured facts. Consider relabeling in the UI as "AI confidence" not "score" to set correct user expectations.

## Phase 2 — Security & abuse prevention

- [ ] **No auth on `/analyze` or `/infrastructure/generate`.** Anyone can hit your public API and make your server clone arbitrary GitHub repos. Add API keys, JWT auth, or at minimum a per-IP rate limiter (`slowapi` for FastAPI).
- [ ] **CORS `allow_origins=["*"]` + `allow_credentials=True`** — browsers reject this combo anyway once you add cookies/auth; restrict to your actual frontend domain(s) via env var.
- [ ] **No clone size/timeout limits.** A malicious or huge repo URL can hang a worker or fill disk. Add:
  - `git clone --depth 1` timeout (subprocess timeout or `GIT_HTTP_LOW_SPEED_LIMIT`/`GIT_HTTP_LOW_SPEED_TIME`)
  - max repo size check before/after clone, abort + cleanup if exceeded
- [ ] **SSRF risk in URL validation** — `GitService.validate_and_parse_url` only checks the string looks like a github.com URL; it doesn't stop something like `github.com/../../internal-service` tricks or redirect abuse during clone. Low risk with GitPython but worth a review.
- [ ] **Secrets** — `OPENAI_API_KEY` via `.env` is fine locally; in production use AWS Secrets Manager / SSM Parameter Store, inject at container start, never bake into the image.
- [ ] **Generated `.env.example` files are LLM output** — add a server-side check that generated content never contains anything that looks like a real key pattern (`sk-`, `AKIA`, etc.) before it's zipped and served, as a defense-in-depth backstop against prompt injection from a malicious repo's README/code confusing the LLM.
- [ ] **Zip download endpoint (`/download/{generation_id}`)** has no ownership check — any caller who knows/guesses a UUID can download another user's generated infra files. Not trivial to guess (UUID4), but add a session/user binding if you add auth.

## Phase 3 — Data layer & scaling

- [ ] **In-memory dicts (`analysis_tasks`, `infra_generations`) are not production storage.**
  - Restarting the backend loses all in-flight and historical tasks.
  - Won't work behind a load balancer with >1 backend instance (task lives only in the instance that created it).
  - Fix: move to Redis (fast, good for SSE polling reads) or Postgres (durable, good for the "recent" history feature).
- [ ] **No TTL / cleanup.** Tasks accumulate forever → unbounded memory growth. Add expiry (e.g., 24h) and a background reaper, or `EXPIRE` if using Redis.
- [ ] **SSE polling via `asyncio.sleep(0.3)` loop per open connection** — fine at small scale, but every open stream is a live coroutine polling a dict every 300ms. At real concurrency this doesn't scale well; consider pub/sub (Redis Streams/Pub-Sub) so the stream endpoint is notified instead of polling.

## Phase 4 — Reliability

- [ ] **`BackgroundTasks` (FastAPI's built-in) run in the same process/worker.** If the worker restarts mid-analysis, the task silently disappears with no retry. For production, move long-running pipeline execution to a real task queue (Celery, Arq, or Temporal) with retries and dead-letter handling.
- [ ] **No timeout on LLM calls** (`call_llm` in `infra_graph.py`) — a hung OpenAI request could stall a pipeline node indefinitely. Add `request_timeout` to `ChatOpenAI` and a max retry count.
- [ ] **No idempotency** — resubmitting the same repo URL always clones + runs the full pipeline again. Consider caching scan results per repo+commit for some TTL.

## Phase 5 — Observability

- [ ] No structured logging anywhere — only in-memory "agent logs" meant for the UI, not real backend logs. Add proper `logging` (or `structlog`) with request IDs correlated to `task_id`/`generation_id`.
- [ ] No metrics (request counts, pipeline duration, LLM latency/cost, failure rate). Add Prometheus metrics or push to CloudWatch.
- [ ] No error tracking (Sentry or similar) — right now failures just vanish into `except: pass`.
- [ ] No health/readiness distinction — `/health` always returns healthy even if OpenAI is unreachable or disk is full. Add real dependency checks.

## Phase 6 — Testing & CI/CD for the app itself

- [ ] `pytest` is in `requirements.txt` but there are **no test files** in the repo. Add at minimum:
  - Unit tests for `GitService.validate_and_parse_url` (this regex logic is exactly the kind of thing that breaks on edge cases)
  - Unit tests for `HeuristicScanner` against fixture repos
  - Integration test for the full analyze pipeline against a small known public repo
- [ ] No CI pipeline for CloudPilot AI itself (ironic, given it generates CI/CD for others). Add GitHub Actions: lint (ruff/eslint), typecheck (mypy/tsc), test, build.
- [ ] No Dockerfile for CloudPilot AI's own backend/frontend — you're generating Dockerfiles for other repos but don't have one for shipping this app itself.

## Phase 7 — Frontend polish

- [ ] No React error boundaries — a component throwing (e.g., malformed SSE JSON edge case) can blank the whole page.
- [ ] `EventSource` doesn't support custom headers — if you add auth (Phase 2), you'll need to either pass a token via query param (less secure, log-leakage risk) or switch to `fetch` + `ReadableStream` for SSE with proper `Authorization` headers.
- [ ] No loading/empty states audit pass — verify every card degrades gracefully when its data is partial/missing (e.g., LLM fallback path returns fewer checklist items than UI expects).

---

## Suggested order of attack

1. Phase 0 (done) + Phase 1 (stop misleading users) — 1–2 days
2. Phase 2 security basics (auth + rate limit + CORS lockdown) — 1–2 days, non-negotiable before any public deploy
3. Phase 3 data layer (Redis/Postgres swap) — 2–3 days, blocks real multi-instance scaling
4. Phase 5 observability — do in parallel with Phase 3, cheap and high value
5. Phase 4 (task queue) and Phase 6 (tests/CI) — before calling it "v1.0"
6. Phase 7 — ongoing polish

Nenu ee list lo ఏదైనా phase ni next code చేయమంటే cheppu — starting point గా Phase 2 (auth + rate limiting) suggest chesta, ఎందుకంటే అది public గా deploy చేసేముందు non-negotiable.
