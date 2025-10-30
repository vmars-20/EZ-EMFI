# Moku Deployment Debugging Session - DS1140-PD
**Date:** 2025-01-28
**Issue:** Oscilloscope getting stuck during deployment, causing timeouts

---

## Problem Summary

When deploying DS1140-PD with multi-instrument configuration (Oscilloscope + CloudCompile), the deployment would hang indefinitely or timeout when configuring the Oscilloscope in Slot 1. This prevented CloudCompile from being deployed to Slot 2.

## Symptoms

1. **Moku GUI showed only Oscilloscope in Slot 1**
   - Slot 2 (CloudCompile) never appeared
   - User consistently reported CloudCompile not showing up

2. **Deployment hung on "Deploying instruments... Slot 1: Oscilloscope"**
   - No progress for 30+ seconds
   - Eventually timed out with `ReadTimeoutError`

3. **Specific API call that timed out:**
   ```
   HTTPConnectionPool(host='192.168.13.159', port=80): Read timed out. (read timeout=30)
   File "/Users/vmars20/EZ-EMFI/tools/moku_go.py", line 321, in deploy
       osc.set_timebase(*timebase)
   ```

4. **Subsequent API calls also timed out**
   - `set_control()` calls failed
   - Device became unresponsive to all API requests

## Root Cause Analysis

### How I Figured It Out

1. **Observed deployment script behavior:**
   - Script printed "Slot 1: Oscilloscope" but never printed "✓ Deployed to slot 1"
   - This meant `set_instrument()` succeeded but subsequent configuration failed

2. **Enabled debug logging:**
   ```bash
   MOKU_LOG_LEVEL=DEBUG uv run python tools/moku_go.py deploy ...
   ```
   - Confirmed the hang was in oscilloscope configuration, not connection

3. **Examined stack trace carefully:**
   - Timeout occurred in `osc.set_timebase(*timebase)` call
   - This was AFTER `set_instrument()` succeeded
   - Line 321 in moku_go.py: the settings configuration step

4. **Checked config file:**
   ```json
   "settings": {
     "timebase": [-0.005, 0.005]
   }
   ```
   - This triggered `set_timebase()` call after oscilloscope deployment

5. **Tested without timebase setting:**
   - Removed the `settings` block from config
   - Deployment succeeded immediately!
   - CloudCompile appeared in Slot 2 ✓

## Solution

### Immediate Fix

**Remove oscilloscope settings from deployment config:**

```json
"1": {
  "instrument": "Oscilloscope"
},
```

Instead of:
```json
"1": {
  "instrument": "Oscilloscope",
  "settings": {
    "timebase": [-0.005, 0.005]
  }
},
```

### Why This Works

- `set_instrument()` is a fast operation (just deploys the instrument)
- `set_timebase()` requires the instrument to be fully initialized and responsive
- If the Moku is in a busy state (from previous deployments), `set_timebase()` can hang
- By skipping timebase configuration, deployment completes quickly
- Timebase can be set manually via GUI after deployment

### Long-Term Recommendations

1. **Always check Moku state before deployment:**
   - Test with a simple API call first
   - If slow/unresponsive, power cycle before deploying

2. **Use force_connect=True:**
   - Already doing this, which helps take ownership from stuck sessions

3. **Separate deployment from configuration:**
   - Deploy instruments first (fast)
   - Configure settings afterward (can retry if needed)

4. **Add timeout handling to moku_go.py:**
   - Catch `ReadTimeoutError` during settings configuration
   - Print helpful message suggesting power cycle
   - Continue with deployment even if settings fail

## When Moku Becomes Unresponsive

**Symptoms:**
- All API calls timeout after 30 seconds
- Web GUI may be slow or unresponsive
- Subsequent scripts fail immediately

**Solution:**
1. Power cycle the Moku hardware (unplug, wait 10s, plug back in)
2. Wait for Moku to fully boot (~30-60 seconds)
3. Test connectivity: `ping 192.168.13.159`
4. Redeploy configuration

## Debugging Checklist for Future Issues

When deployment hangs:

1. **Enable debug logging:**
   ```bash
   MOKU_LOG_LEVEL=DEBUG uv run python tools/moku_go.py ...
   ```

2. **Check which step hangs:**
   - Look for the last printed message
   - Check if it's connection, deployment, or configuration

3. **Examine stack trace:**
   - Find the exact API call that timed out
   - Note which instrument (slot number)
   - Check if it's a deployment call or settings call

4. **Simplify configuration:**
   - Remove all `settings` blocks
   - Try deploying with minimal config
   - Add settings back one at a time

5. **Test Moku responsiveness:**
   - Try accessing web GUI
   - Run a simple API call (e.g., just connect and disconnect)
   - If everything times out → power cycle needed

## Code Reference

**File:** `tools/moku_go.py`
**Lines:** 314-324 (oscilloscope deployment with settings)

```python
elif slot_config.instrument == 'Oscilloscope':
    console.print(f"  Slot {slot_num}: Oscilloscope")
    osc = moku.set_instrument(slot_num, Oscilloscope)  # ← This succeeds

    # Apply settings if provided
    if 'timebase' in slot_config.settings:
        timebase = slot_config.settings['timebase']
        osc.set_timebase(*timebase)  # ← This can hang!
        console.print(f"    Timebase: {timebase}")

    console.print(f"  ✓ Deployed to slot {slot_num}")
```

## Successful Deployment

After removing timebase setting:

```
[2/3] Deploying instruments...
  Slot 1: Oscilloscope
  ✓ Deployed to slot 1          ← Success!
  Slot 2: CloudCompile
    Bitstream: DS1140_bits.tar
  ✓ Deployed to slot 2          ← Success!

[3/3] Configuring routing...
  ✓ Configured 4 connection(s)
```

## Key Takeaway

**The problem wasn't the oscilloscope deployment itself** - it was the settings configuration that followed. The deployment worked, but configuring it hung. This is why removing the settings block fixed the issue.

This is a common pattern with the Moku API:
- **Deployment operations** (set_instrument) are usually fast
- **Configuration operations** (set_timebase, set_frontend, etc.) can hang if device is busy
- **Routing operations** (set_connections) are usually reliable

Always configure instruments AFTER verifying they're responsive, not as part of the deployment step.

---

**Status:** Issue resolved by removing timebase configuration from deployment config.
**Next Steps:** Power cycle Moku before testing, then use simplified deployment config.
