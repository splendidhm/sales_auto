# AGENTS.md — Affiliate Automation Hub

## Verified implementation snapshot (2026-10-13)

- Phase 1 through the template-first Naver pilot are implemented: offline CLI/mock collection, SQLite v3, blog/channel settings, a 4-week/12-post calendar, deterministic templates, duplicate warnings, local review/approval, publication packages and manual Naver URL records.
- Blog workflow is `planned -> research -> draft -> reviewed -> approved -> packaged -> published`. Only approved/package-ready items appear in This Week. Product/link/body changes invalidate approval and return linked plans to draft.
- Affiliate use is explicit per content plan. Informational plans omit an existing affiliate link and disclosure from export. Affiliate plans require channel status `shopping_connect_ready`, a confirmed Shopping Connect link, disclosure and review.
- Product categories: living/storage and robot vacuums. Updates that omit category preserve the existing category. Invalid URL ports and malformed hosts return application validation errors.
- Verification: 28 unittest tests passed, loopback Streamlit health returned HTTP 200, and the current isolated robot-vacuum scenario passed 12 checks without changing the production DB. No actual Naver publication or paid API use.
- Core modules: db/migrations, editorial, publishing, service, runtime and cli in src/affiliate_hub. app.py is the local UI; scripts/test_robot_workflow.py reproduces the retained robot test.
- Current source-of-truth handoff: HANDOFF.md. Skill/tool usage audit: SKILLS_USED.md. Reproduction instructions: README.md.
- Repository requested by owner: https://github.com/splendidhm/sales_auto.git; branch main; initial delivery commit message: 쇼핑커넥트 블로그 자동화. This request explicitly authorizes committing/pushing this delivery; it is not blanket authorization for future pushes.
- Never commit runtime databases, exports, logs, .venv, .env or secrets. Reproduce test artifacts from the scripts on a new checkout.
- The production DB was backed up and migrated from v2 to v3. Blog settings and the 12 plans remain empty until the owner enters the real Naver blog URL. Next milestone is the first manually published pilot post, followed by grounded AI drafts and cost controls after provider/key/budget setup.

## 1. Mission and operating context
Build a maintainable, Windows-first, Python-based affiliate content automation system. Prioritize Naver Shopping Connect, then add Coupang Partners. Start with a separate Naver Blog about living/storage products; add a separate WordPress site after validation. Require factual review and human approval before any eventual publication.

**Current known facts**
- Owner uses a Windows PC and plans to develop with Codex.
- Coupang Partners membership: **not yet registered**; no API credentials may be assumed.
- Existing HPL website: local sibling `HPL_auto` is Next.js, with code-managed economic/data articles and no observed CMS publishing endpoint. Keep HPL separate; live deployment parity is unverified.
- Target channels: Naver Blog first (manual posting), separate WordPress later. Instagram is outside initial scope.
- A dedicated Naver Blog has been created, but its real name/URL is not stored in the app yet. Brand Connect and Shopping Connect are not yet linked. No API keys. Review budget: 15–30 minutes daily; recurring cost cap KRW 50,000/month.
- Windows Task Scheduler is the initial runtime; hosting/cloud may be added later.
- Local manual editorial UI and schema v3 now exist. Read HANDOFF.md for actual verification; do not infer live integrations from the architecture.

## 2. Non-negotiable engineering rules
1. **Inspect first:** Check repository files, Git status, Python version, existing tests and configuration before editing. Preserve user work; do not overwrite working code without reason.
2. **Plan in increments:** Deliver a small working vertical slice with tests before expanding. Prefer simple, clear modules and typed Python. Avoid unnecessary microservices, Redis, Kubernetes, Celery, or cloud dependencies in MVP.
3. **Truthful status:** Never report a feature as implemented or tested unless verified. Distinguish mocks/stubs from real API integrations and hypothetical business metrics from real analytics.
4. **No invented integrations:** Check official current API docs/permissions before implementation. Coupang Partners API access may require final approval; distinguish it from Coupang Wing seller API. Never assume a public Naver Blog write API. Instagram publishing needs authorized Meta permissions and eligible accounts. Confirm the existing website stack before selecting its publisher adapter.
5. **Compliant publishing:** No attempts to evade anti-bot defenses, CAPTCHAs, rate limits, login controls, or platform terms. No spam, misleading testimonials, scraped/reused copyrighted images, fabricated discounts/prices/reviews, or undisclosed affiliate compensation. Use review/approval gates prior to publication. Prefer manual draft export where an authorized posting interface is unavailable.
6. **Protect credentials:** Keep API tokens in environment variables or `.env` locally; `.env`, logs, databases, virtualenvs, and any personal data must not enter Git. Supply `.env.example` with placeholders only. Do not echo tokens to console or logs. Use least privilege.
7. **Operational safety:** Idempotent jobs, explicit exit codes, bounded exponential backoff only for transient errors, sensible timeouts, per-job locking/concurrency control, structured logs, and durable job state. Do not re-post when retrying an uncertain publish result; reconcile first.
8. **Windows robustness:** Use `pathlib`, a project-specific virtual environment, explicit working directories, and `python -m ...` entrypoints. Avoid reliance on activated shells or interactive desktops for scheduled tasks. Document sleep/power/user-session limitations.
9. **Data quality:** Record data source, observed timestamp, and validity; distinguish verified facts from AI-generated assertions. Avoid silently treating stale prices as current. Store only necessary data, and support retention/cleanup.
10. **Test before handoff:** Run unit tests plus CLI smoke tests. Report exact commands, outcomes, remaining issues, and files changed. If a test cannot run, state why.
11. **Communication:** Explain commands and operational decisions in Korean; code, identifiers, docstrings, and commit messages can use clear English. Prefer concise, reproducible instructions.

## 3. Target architecture

```text
Windows Task Scheduler
   -> CLI orchestration / job runner
      -> mock provider now; manual Shopping Connect inputs then authorized API adapters
      -> SQLite product and content store
      -> scoring and selection
      -> AI draft generation (later)
      -> factual/compliance checks + human approval
      -> Naver draft export now; separate WordPress adapter later
      -> attribution-aware reports and execution logs
Local Streamlit review UI -> manual products, revision-specific review/approval and publication records
```

Keep business logic separate from API clients, persistence, and CLI. Provider interfaces must support multiple sources. Do not confuse Naver search APIs with Shopping Connect link generation or Blog publishing. Public creator APIs are not verified; manual input is the default until official access is established.

Suggested *target* layout (adapt to repository reality; not all folders must be created in Phase 1):

```text
affiliate-hub/
  AGENTS.md
  HANDOFF.md
  pyproject.toml
  .env.example
  .gitignore
  README.md
  src/affiliate_hub/
    __init__.py
    cli.py
    config.py
    db.py
    models.py
    jobs/
      collect.py
    providers/
      base.py
      mock.py
      coupang.py                 # only once authorized and documented
    scoring/
    content/
    publishers/
    reports/
  tests/
  scripts/
    run_collect.cmd
  data/                         # ignored
  logs/                         # ignored
```

Prefer a package using `src` layout and one CLI entrypoint rather than many unrelated scripts. Python >=3.12 is preferred if available; inspect local compatibility first. SQLite is sufficient for MVP. Avoid adding dependencies for features not yet built.

## 4. Phase 1 acceptance criteria (offline, no Coupang account needed)
- CLI exposes `init-db`, `collect --provider mock`, `products`, `status` (exact naming can vary if documented).
- Mock provider returns exactly three clearly fictional test products with stable IDs; **never label mock output as Coupang data**.
- First collection inserts 3 rows; second collection inserts 0 new rows and updates/skips existing 3, without growing the product count.
- SQLite initialized automatically; tables include `products` and `job_runs` (or equivalent), with useful uniqueness and timestamps.
- Logs written to `logs/`; failures return nonzero exit status and are identifiable from logs/status.
- Windows scheduling documentation includes program path, argument list, working directory, overlap policy, retry policy, and how to test manually.
- Unit tests cover insert/upsert behavior, repeated collection, and failure exit/logging behavior. Do not claim that Task Scheduler ran unless tested on Windows.
- `.gitignore` excludes `.env`, `.venv/`, `data/`, `logs/`, caches, and secrets. `.env.example` has no real secrets.
- Template drafts and Markdown export are offline mock exercises, explicitly marked not for publication. Export never marks a draft published or approved.
- Standard-library unittest is the offline test runner; tests are also pytest-compatible. No package download is required for phase 1.

## 5. Data and publishing model (forward compatibility)
Minimum conceptual entities: `products`, `affiliate_links`, `content_drafts`, `publications`, `performance`, `job_runs`. Separate **source product ID** from internal ID; keep source, fetch time, price currency, and availability freshness. Content lifecycle: `draft -> reviewed -> approved -> queued -> published` (and `failed`/`needs_recheck`). Never auto-approve AI content. Do not imply item-level commissions if reporting only provides aggregate attribution.

## 6. Implementation policy for later phases
- **Phase 2:** Manual real product/source/link input, local Streamlit review screen, Naver manual export and publication URL recording. Verify creator enrollment requirements; lack of approval must not block informational content preparation.
- **Phase 3:** Shopping Connect links only after authorized enrollment; AI grounded drafts, costs, disclosure checks, revisions and mandatory human approval. Never invent an API integration.
- **Phase 4:** Separate WordPress via official REST API and application credentials after a 4-week/12-post pilot, review within 30 minutes/day for the last 2 weeks, and total recurring cost within KRW 50,000/month. These are internal operating gates, not platform enrollment rules.
- **Phase 5:** Coupang membership/API verification and adapter; attribution-aware performance reports, scheduler hardening, daily backups with 30-day retention and restore tests. No invented item-level attribution.
- User authorized phase 2. Keep future live integrations, paid API calls and actual publication outside this implementation.
- Schema v2/v3 migrations are additive: legacy content_drafts preserve v1 snapshots; editorial_state + draft_revisions are authoritative for real content, while blog_settings + content_plans hold channel operations. Never read legacy status/title as the current state of a real draft.
- All UI writes use Hub.mutate and the same OS lock as CLI. Changing product facts/links or draft text invalidates approval. Review/approval/export must check the current revision and product version.
- Streamlit must bind to loopback only. No public hosting or remote authentication has been implemented.

## 7. Codex completion protocol
For every iteration:
1. Briefly describe findings and implementation plan.
2. Implement the smallest coherent change.
3. Run available checks and show results.
4. Update `HANDOFF.md` with verified state, commands, blockers, and next actions.
5. Summarize delivered files and any assumptions or approvals needed from the owner.

**Avoid destructive Git operations and pushing to remote without explicit user instruction.** Prefer a feature branch when an existing stable repository is present. Do not automatically publish real affiliate content, post on accounts, or spend paid API credits without explicit approval.
