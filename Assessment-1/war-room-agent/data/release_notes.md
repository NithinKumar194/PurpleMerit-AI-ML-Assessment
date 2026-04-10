# Release Notes — SmartPay v2.0 (Unified Checkout)

## Launch Date
2026-03-29

## Feature Summary
SmartPay v2.0 is a complete redesign of the checkout and payment experience.
Key changes include a new payment SDK, async report generation engine,
and a full dashboard UI redesign.

## Changes Shipped
- Migrated payment processor to PayCore SDK v3.1.2 (previously v2.8.0)
- New async report generation engine replacing synchronous renderer
- Dashboard rebuilt in React 18 (previously React 16)
- Saved payment method storage migrated to new encrypted vault
- Checkout flow reduced from 5 steps to 3 steps

## Known Risks at Launch (Accepted by PM)
1. BUG-4421: PayCore SDK v3.1.2 has an unresolved race condition under
   high concurrency (>200 simultaneous transactions). Risk accepted as
   "low probability in production." Status: OPEN, no fix ETA.

2. Async report engine not load-tested beyond 500 concurrent users.
   Production peak is estimated at 800-1200 concurrent users.

3. Saved settings migration script completed on 94.2% of accounts.
   Remaining 5.8% (~12,000 users) may experience preference loss on
   first login post-update.

4. React 18 upgrade introduces concurrent rendering — not fully tested
   on Android WebView versions below 90.

## Rollback Plan
- Payment: Revert to PayCore SDK v2.8.0 (estimated 45 minutes)
- UI: Docker image tagged v1.9.3 available for immediate redeploy
- Database: No schema changes — rollback is non-destructive
- Estimated full rollback time: 90 minutes

## Success Criteria (Defined by PM pre-launch)
- Crash rate: must stay below 1.0%
- Payment success rate: must stay above 95%
- Support ticket volume: must stay below 100/day
- Funnel completion: must stay above 50%
- D1 Retention: must stay above 40%