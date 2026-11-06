# Performance Checklist

Quick reference checklist for backend, data, cloud, and frontend performance. Use alongside `code-review-and-quality`.

## Database & Query Performance

- [ ] No N+1 query patterns (use batch loading, joins, or eager loading)
- [ ] List endpoints and BigQuery/SQL queries are bounded and paginated (never unbounded `SELECT *`)
- [ ] Query plans inspected (`EXPLAIN ANALYZE` or BigQuery slot execution graph) before and after index/partition changes
- [ ] Composite indexes ordered by equality predicates first, then range/sort columns
- [ ] One connection pool or SDK client per process/worker, not re-instantiated per request

## API, Concurrency & Agent Latency

- [ ] No blocking synchronous I/O (`requests.get`, `time.sleep`, `subprocess.run`) inside `async def` event loops
- [ ] Independent downstream RPCs or subagent fan-outs run concurrently (`asyncio.gather` / parallel tool calls) rather than serially
- [ ] Explicit timeouts and bounded retry with exponential backoff + jitter configured on all external network calls
- [ ] Streaming responses or chunked progress used for long-running LLM generation paths

## Caching & State

- [ ] Cached operations measured as expensive first
- [ ] Cache keys include all variance dimensions (tenant, user, locale, model version, permissions)
- [ ] Bounded memory ceiling (`maxsize` / TTL eviction) set on all in-memory caches (no unbounded dicts/lists)
- [ ] Stampede protection (request coalescing or `stale-while-revalidate`) on hot keys

## Frontend & Portal Rendering

- [ ] Core Web Vitals targets: LCP <= 2.5s, INP <= 200ms, CLS <= 0.1
- [ ] Images use modern formats (WebP/AVIF) with explicit `width` and `height`
- [ ] Bundle size kept minimal; heavy libraries loaded on demand or cached with pinned versions
- [ ] Long lists virtualized and DOM reads/writes batched to prevent layout thrashing
