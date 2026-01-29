# Rate Limiting & Double Trigger Fixes

## Changes Made (Jan 29, 2026)

### Problem 1: Double Trigger Bug
**Issue**: `pynput` hotkey listener could fire multiple times for a single keypress, causing duplicate API calls.

**Solution**: Enhanced debounce protection in `main.py`:
- Already had `is_processing` flag check
- Added user notification when hotkey is pressed while processing
- Shows "Busy" notification to inform user to wait

### Problem 2: API Rate Limiting (429 Errors)
**Issue**: Gemini API free tier limits to 20 requests/day. App crashed on rate limit errors.

**Solution**: Implemented exponential backoff retry logic in both files:

#### Files Modified:
1. **`gemini_client.py`** (main app)
2. **`service_runner.py`** (services)

#### Retry Strategy:
- **Max retries**: 5 attempts
- **Base delay**: 1 second
- **Backoff pattern**: 1s → 2s → 4s → 8s → 16s (exponential: `2^attempt`)
- **Total max wait**: ~31 seconds before giving up

#### Error Handling:
- **429 (Rate Limit)**: Automatic retry with exponential backoff
- **Other 4xx errors**: Immediate failure with descriptive error
- **Network/other errors**: Retry with same backoff strategy
- **After max retries**: Clear user-friendly error message

### Code Changes Summary

#### 1. `gemini_client.py`
```python
# Added imports
import time
from google.genai.errors import ClientError

# Modified _process_text method
- Wrapped API call in retry loop (max 5 attempts)
- Catches ClientError for 429 handling
- Implements exponential backoff: delay = base_delay * (2 ** attempt)
- Logs retry attempts and delays
- User-friendly error messages
```

#### 2. `service_runner.py`
```python
# Added imports
import time
from google.genai.errors import ClientError

# Modified _process_text method in StandaloneGeminiClient
- Same retry logic as main app
- Ensures services don't crash on rate limits
- Logs all retry attempts to service.log
```

#### 3. `main.py`
```python
# Enhanced hotkey handler
- Added notification when hotkey pressed during processing
- Shows "Busy" alert: "Please wait, processing previous request..."
- Improved logging for debounce events
```

### Benefits

1. **Resilience**: App gracefully handles temporary API issues
2. **User Experience**: Clear feedback when rate limited
3. **No Crashes**: Automatic retry for transient failures
4. **Smart Waiting**: Exponential backoff prevents API hammering
5. **Transparency**: All retries logged for debugging

### Testing

To test the fixes:

1. **Rate limit handling**: Make 20 requests quickly, then observe retry behavior
2. **Double trigger**: Press hotkey rapidly multiple times
3. **Network issues**: Disconnect/reconnect during processing

### Free Tier Limits

**Gemini API Free Tier**:
- 20 requests per day per model
- Resets every 24 hours
- Consider upgrading if you need more: https://ai.google.dev/pricing

### Logs

Check logs for retry attempts:
- Main app: `altgrammarly.log`
- Services: `service.log`

Look for: `⚠️ Rate limit hit (429). Retrying in Xs...`
