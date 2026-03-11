# Plan: Two Changes

## Change 1: Fix text overflow in all chat views
**Problem:** In the 4 views that have chat panels (Policy Q&A, Claims, Coverage Upgrade, Damage Assessment), the agent's text output flows underneath the conversation/input bar at the bottom.

**Fix:** Update `ChatPanel.tsx` to move the input bar outside the scroll area, so messages stop cleanly above it with a subtle gradient fade. This single fix improves all 4 chat views.

## Change 2: Create a new Dashboard view (6th view)
**Keep all 5 existing views exactly as they are:**
1. Home (The Portal — voice orb)
2. Policy Q&A (The Editorial — asymmetric split)
3. Claims (The Command Center — header band + photo workspace)
4. Coverage Upgrade (The Showcase — reverse editorial split)
5. Damage Assessment (The Scanner — scan grid + photo upload)

**Add a 6th view: Dashboard (The Ledger)**
- A personal dashboard for the customer
- Shows: policy status, coverage cards, claims history with status badges and costs
- Unique constellation/network background (different from all other views)
- Fetches data from the API using the customer's policy number
- Agent navigates here when user says "show me my dashboard", "summary of my claims", etc.
- VoiceNav + Home button in the nav bar (same pattern as other views)
