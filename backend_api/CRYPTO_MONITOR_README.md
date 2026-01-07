# Cryptocurrency Asset Migration Monitoring System

## Overview

This is an enhanced Python monitoring script for tracking ADA (Cardano) and NIGHT (Midnight) cryptocurrency metrics to support asset migration testing and decision-making.

## Key Improvements Over Original

### 1. **Robust Error Handling**
- Exponential backoff retry logic for API calls
- Comprehensive exception handling
- Graceful degradation when data is unavailable
- Rate limit detection and handling

### 2. **Structured Logging**
- Professional logging instead of print statements
- Both console and file logging
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Timestamped entries for audit trail

### 3. **Data Persistence**
- Historical data tracking (90-day rolling window)
- JSON-based storage for easy analysis
- Trend analysis capabilities
- Report generation and archival

### 4. **Comprehensive Metrics**
- All four test cases (TC-01 through TC-04) implemented
- Edge case detection (zombie chain, DUST inflation risks)
- Weighted scoring system (40/30/20/10 split)
- Historical volatility analysis

### 5. **Production-Ready Design**
- Configurable via dataclass-based configuration
- Scheduling-ready with built-in interval support
- Clean separation of concerns (API, data, testing, reporting)
- Type hints throughout for better code quality

### 6. **Better Reporting**
- Structured JSON reports for programmatic consumption
- Detailed verdict matrix (85/60/40 score thresholds)
- Actionable recommendations based on scoring
- Historical trend visualization

## Installation

```bash
cd backend_api
pip install -r requirements.txt
```

## Usage

### Single Execution Mode

Run a single monitoring cycle:

```bash
python src/crypto_monitor.py
```

This will:
1. Fetch current ADA and NIGHT prices from CoinGecko
2. Execute all test cases (TC-01 through TC-04)
3. Check for edge cases
4. Generate verdict and recommendation
5. Save report to `monitoring_data/latest_report.json`
6. Append to historical data in `monitoring_data/price_history.json`

### Scheduled Mode

Run continuously with 24-hour intervals:

```bash
python src/crypto_monitor.py --schedule
```

Run with custom interval (e.g., every 12 hours):

```bash
python src/crypto_monitor.py --schedule 12
```

### Integration with Task Scheduler

**Linux/macOS (cron):**

```bash
# Run daily at 9:00 AM
0 9 * * * cd /path/to/backend_api && python src/crypto_monitor.py
```

**Windows (Task Scheduler):**

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to daily
4. Action: Start a program
5. Program: `python`
6. Arguments: `src/crypto_monitor.py`
7. Start in: `C:\path\to\backend_api`

## Configuration

All configuration is managed through the `MonitorConfig` dataclass at the top of the script. Key parameters:

```python
@dataclass
class MonitorConfig:
    # API Configuration
    api_base_url: str = "https://api.coingecko.com/api/v3"
    api_timeout: int = 30
    max_retries: int = 3
    
    # Test Criteria Thresholds
    target_ratio: float = 0.25      # TC-01: NIGHT/ADA ratio target
    tvl_monthly_growth: float = 15.0 # TC-02: Required TVL growth %
    stability_threshold: float = 15.0 # TC-04: Max 24h volatility %
    
    # Volume Analysis
    min_volume_ratio: float = 0.05   # NIGHT must be >5% of ADA volume
```

You can customize by modifying these values or creating a configuration file.

## Test Cases

### TC-01: Exchange Rate Pressure Test (40% weight)
- **Pass Criteria**: NIGHT/ADA ratio >= 0.25
- **Warning Level**: Ratio >= 0.20 (sell pressure detected)
- **Fail**: Ratio < 0.20 (excessive sell pressure)

### TC-02: Ecosystem Growth Test (30% weight)
- **Pass Criteria**: TVL growth >15% monthly, 3+ active ZK dApps
- **Current Implementation**: Uses volume ratio as proxy
- **Note**: Full implementation requires additional data sources

### TC-03: Founder Engagement Test (20% weight)
- **Pass Criteria**: Stable YouTube engagement, reduced X noise
- **Current Implementation**: Manual review required
- **Note**: Requires social media monitoring tools

### TC-04: Token Unlock Stability Test (10% weight)
- **Pass Criteria**: 24h volatility <15%, no drops >30%
- **Includes**: Historical 7-day volatility analysis
- **Critical**: Detects cascade risk conditions

## Verdict Matrix

The script generates verdicts based on total score:

| Score | Verdict | Recommendation |
|-------|---------|----------------|
| 85-100 | PASS (Highly Stable) | Aggressive swap: 20-30% ADA → NIGHT |
| 60-84 | CONDITIONAL PASS | Conservative swap: 10% ADA → NIGHT |
| 40-59 | RE-TEST REQUIRED | Hold position, airdrop only |
| <40 | FAIL (Critical Bug) | Risk avoidance, consider swap back |

## Edge Case Detection

### Zombie Chain Warning
Triggers when NIGHT volume falls below 5% of ADA volume:
- Indicates insufficient liquidity
- Blocks achievement of 7-8x gain targets
- Automatically downgrades verdict

### Volume Trend Analysis
Monitors 7-day volume trends:
- Alerts on >30% volume decline
- Early warning for liquidity issues

## Output Files

All output is saved to the `monitoring_data/` directory:

### `latest_report.json`
Complete monitoring report with:
- Timestamp and test environment
- Current ADA and NIGHT metrics
- All test case results with detailed scoring
- Final verdict and recommendation
- Edge case warnings

### `price_history.json`
Historical data (90-day rolling window):
- Timestamp-indexed entries
- Price, volume, and ratio data
- Used for trend analysis

### `crypto_monitor.log`
Detailed execution log:
- DEBUG level: API calls, data parsing
- INFO level: Test results, verdicts
- WARNING level: Edge cases, retry attempts
- ERROR level: Failures and exceptions

## Example Output

```
======================================================================
Starting Midnight Asset Migration Monitoring Cycle
======================================================================
Current NIGHT/ADA Ratio: 0.2847
ADA Price: $1.0523 | NIGHT Price: $0.2996
----------------------------------------------------------------------
Executing Test Cases
----------------------------------------------------------------------
[TC-01] Exchange Rate Pressure Test: PASS (Score: 40/40)
[TC-02] Ecosystem Growth Test: CONDITIONAL (Score: 18/30)
[TC-03] Founder Engagement Test: MANUAL_REVIEW (Score: 20/20)
[TC-04] Token Unlock Stability Test: PASS (Score: 10/10)
----------------------------------------------------------------------
Edge Case Analysis
----------------------------------------------------------------------
⚠️ WARNING: NIGHT volume dropped 22.3% below 7-day average. Liquidity declining.
======================================================================
FINAL VERDICT: CONDITIONAL PASS
Total Score: 88/100 (downgraded due to edge case)
Recommendation: ⚠ CONSERVATIVE SWAP: Migrate only 10% of ADA holdings to NIGHT. 
Maintain flexibility for market changes.
======================================================================
```

## API Rate Limits

CoinGecko free tier limits:
- 10-50 calls/minute
- Script implements exponential backoff
- Automatic retry on 429 status
- Configurable timeout and retry settings

## Extending the Script

### Adding Custom Test Cases

```python
def execute_tc05_custom_metric(self, ...):
    """Your custom test case logic"""
    score = 0
    status = "FAIL"
    
    # Your logic here
    
    return TestCaseResult(
        test_id="TC-05",
        name="Custom Metric Test",
        status=status,
        score=score,
        weight=custom_weight,
        details={...},
        pass_criteria="Your criteria"
    )
```

### Integrating Additional Data Sources

The script is designed for easy extension:

1. Add new client classes following `CoinGeckoClient` pattern
2. Implement retry logic and error handling
3. Update `TestExecutor` to consume new data
4. Modify scoring weights as needed

## Troubleshooting

### "Failed to fetch cryptocurrency data"
- Check internet connection
- Verify CoinGecko API is accessible
- Review rate limit status
- Check logs for detailed error messages

### "midnight-3 not found in response"
- Verify CoinGecko asset ID is correct
- NIGHT may not be listed yet on CoinGecko
- Update `night_id` in config when available

### No historical trend data
- Normal for first run
- Data accumulates over time
- Requires at least 2 data points for trends

## Best Practices

1. **Run Daily**: Execute at consistent times for reliable trends
2. **Monitor Logs**: Review `crypto_monitor.log` regularly
3. **Archive Reports**: Keep reports for compliance/audit trail
4. **Manual Verification**: Always verify TC-03 manually via social media
5. **Cross-Reference**: Compare with other market data sources

## Security Notes

- No API keys required for CoinGecko free tier
- All data stored locally in JSON format
- No sensitive information in logs
- Consider .gitignore for `monitoring_data/` if version controlling

## Future Enhancements

Potential improvements:
- Integration with Midnight TVL data sources
- Real-time WebSocket price feeds
- Email/SMS alerting on critical conditions
- Dashboard UI for visualization
- Machine learning-based trend prediction
- Multi-asset portfolio optimization

## Support

For issues or questions:
1. Check logs in `monitoring_data/crypto_monitor.log`
2. Review CoinGecko API documentation
3. Verify asset IDs are current
4. Test with simplified config first

## License

This script is provided as-is for personal use in cryptocurrency asset monitoring and decision-making.

---

**Important Disclaimer**: This monitoring script is a tool for data analysis and does not constitute financial advice. Always conduct your own research and consult with financial professionals before making investment decisions.
