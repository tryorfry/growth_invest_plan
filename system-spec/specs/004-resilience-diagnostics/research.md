# Research: Spec 004 - Resilience & Performance

## Objectives
- Reduce analysis latency from ~45s back to ~15-20s.
- Gracefully handle consistently failing or blocked data sources (SSL, 403 Forbidden).
- Improve diagnostics to surface backend health to the user.

## Findings
- **Macrotrends**: Consistently 403ing in the current environment. Each failure triggers retries and timeouts, adding ~30s of dead time.
- **News Sentiment**: Uses standard `requests` which fails on SSL intercepted environments.
- **Circuit Breaker**: A mechanism is needed to "mute" a source after repeated failures.

## Latency Breakdown (Estimated)
| Source | Normal | Blocked/Failing | Impact |
| --- | --- | --- | --- |
| technical | 2-5s | 15s (timeout) | Medium |
| fundamental | 1s | 5s | Low |
| news | 1s | 15s (SSL retry) | Medium |
| macrotrends | 3s | 30s (403 + retries) | High |
| earnings | 5s | 15s | Medium |

## Proposed Solution
- Implement `DataSource.check_circuit()` to skip failing sources.
- Mark sources as "Broken" immediately on 403 Forbidden.
- Refactor `NewsSentimentSource` to use the `DataSource` base.
