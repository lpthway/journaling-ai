# Expert Questions - System Architecture Decisions

## Q1: Should we migrate the frontend to use the optimized `/insights/cached` endpoint instead of the legacy `/entries/analytics/*` endpoints?
**Default if unknown:** Yes (the optimized system is specifically designed for better performance and already exists)

## Q2: Do you want to preserve backward compatibility with the current `/entries/analytics/*` API endpoints during the transition?
**Default if unknown:** Yes (gradual migration is safer than breaking changes)

## Q3: Should entries have their sentiment/mood analysis computed and stored at creation time rather than on-demand?
**Default if unknown:** Yes (pre-computation eliminates the expensive processing during analytics requests)

## Q4: Is it acceptable to migrate from the current JSON file caching to Redis-based caching for better performance and reliability?
**Default if unknown:** Yes (Redis is already available and more suitable for production caching)

## Q5: Should we implement incremental analytics updates (only process new/changed entries) rather than full recomputation?
**Default if unknown:** Yes (incremental updates maintain real-time accuracy with better performance)