# Research: System Modernization & Refactoring

## Problem
The original monolithic dashboard made adding new features slow and prone to UI regressions. Additionally, network instability and SSL issues often broke the data acquisition layer.

## Decisions
1. **Modularization**: Break `src/dashboard.py` into `src/views/` and `src/components/`.
    - **Rationale**: Separation of concerns. Layout logic stays in the main app; specific UI pieces are isolated.
2. **Robustness**: Implement a unified `_get_response_sync` in `DataSource` base class.
    - **Rationale**: DRY principle for error handling and SSL fallback.
3. **Caching**: Move from streamlit-only cache to a database-backed "Cache-Aside" strategy.
    - **Rationale**: Persists analysis across sessions and allows for complex TTL logic.

## Technical Findings
- `curl_cffi` is superior to `requests` for sites like Finviz which use Cloudflare.
- SSL issues are common in certain dev environments; `verify=False` is a necessary (though risky) fallback for public financial data.
