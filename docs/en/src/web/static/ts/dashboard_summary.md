# dashboard_summary.ts

> 📅 Last Updated: 2026/06/05

## Purpose

Explains how the summary panel mixes backend graph-level remaining-time estimates with frontend aggregation of node status counters.

## Key Points

- The backend provides total remaining time only.
- The frontend aggregates success, pending, failed, duplicated, and active-node counts from `nodeStatuses`.
