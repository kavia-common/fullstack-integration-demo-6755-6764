# Cryptocurrency Asset Migration Monitoring System

## Overview

This is an enhanced Python monitoring script for tracking ADA (Cardano) and NIGHT (Midnight) cryptocurrency metrics to support asset migration testing and decision-making.

## 🚀 New Features in v2.0

### 1. **Configuration File Support**
- JSON-based configuration for easy customization
- No code changes needed to adjust thresholds
- Separate configuration for alerts, API, and data storage

### 2. **Technical Indicators**
- 7-day and 30-day Simple Moving Averages (SMA)
- 14-period Relative Strength Index (RSI)
- 7-day volatility calculations
- Volume trend analysis

### 3. **CSV Export**
- Export historical data for external analysis
- Compatible with Excel, Google Sheets, and data analysis tools
- One-command export: `python src/crypto_monitor.py --export`

### 4. **Alert System**
- Threshold-based alerting
- Slack webhook integration
- Configurable alert conditions
- Email notification support (requires SMTP setup)

### 5. **Performance Optimizations**
- API response caching (60-second duration)
- Reduced redundant API calls
- Faster historical data processing
- Optimized data retention management

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
- Historical data tracking (configurable retention period)
- JSON-based storage for easy analysis
- Trend analysis capabilities
- Report generation and archival

### 4. **Comprehensive Metrics**
- All four test cases (TC-01 through TC-04) implemented
- Edge case detection (zombie chain, DUST inflation risks)
- Weighted scoring system (40/30/20/10 split)
- Historical volatility analysis

### 5. **Production-Ready Design**
- Configurable via JSON configuration file
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

## Configuration

### Using config.json (Recommended)

Create or edit `config.json` in the `backend_api` directory:

```json
{
  "api": {
    "base_url": "https://api.coingecko.com/api/v3",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 5
  },
  "assets": {
    "ada_id": "cardano",
    "night_id": "midnight-3"
  },
  "thresholds": {
    "target_ratio": 0.25,
    "ratio_sell_pressure": 0.20,
    "tvl_monthly_growth": 15.0,
    "min_zk_dapps": 3,
    "stability_threshold": 15.0,
    "crash_threshold": 30.0,
    "min_volume_ratio": 0.05
  },
  "weights": {
    "tc01_weight": 40,
    "tc02_weight": 30,
    "tc03_weight": 20,
    "tc04_weight": 10
  },
  "alerts": {
    "enabled": true,
    "email_notifications": false,
    "slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "alert_on_score_below": 60
  },
  "data": {
    "data_dir": "monitoring_data",
    "history_file": "price_history.json",
    "report_file": "latest_report.json",
    "history_retention_days": 90
  },
  "logging": {
    "log_level": "INFO",
    "log_file": "crypto_monitor.log",
    "console_output": true
  }
}
```

### Custom Configuration File

```bash
python src/crypto_monitor.py --config /path/to/custom_config.json
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
3. Calculate technical indicators
4. Check for edge cases
5. Generate verdict and recommendation
6. Save report to `monitoring_data/latest_report.json`
7. Append to historical data in `monitoring_data/price_history.json`

### Scheduled Mode

Run continuously with 24-hour intervals:

```bash
python src/crypto_monitor.py --schedule
```

Run with custom interval (e.g., every 12 hours):

```bash
python src/crypto_monitor.py --schedule 12
```

### Export Historical Data

Export to CSV for analysis:

```bash
python src/crypto_monitor.py --export
```

This creates `monitoring_data/monitoring_export.csv` with:
- Timestamps
- ADA and NIGHT prices
- Volume data
- Ratios
- Scores and verdicts

### Combined Options

```bash
# Use custom config and schedule
python src/crypto_monitor.py --config my_config.json --schedule 6

# Export with custom config
python src/crypto_monitor.py --config my_config.json --export
```

### Integration with Task Scheduler

**Linux/macOS (cron):**

```bash
# Run daily at 9:00 AM
0 9 * * * cd /path/to/backend_api && python src/crypto_monitor.py

# Run every 6 hours
0 */6 * * * cd /path/to/backend_api && python src/crypto_monitor.py
```

**Windows (Task Scheduler):**

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to daily or custom interval
4. Action: Start a program
5. Program: `python`
6. Arguments: `src/crypto_monitor.py`
7. Start in: `C:\path\to\backend_api`

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

## Technical Indicators

### Simple Moving Averages (SMA)
- **7-Day SMA**: Short-term price trend
- **30-Day SMA**: Medium-term price trend
- **Cross Analysis**: 7-day crossing above 30-day indicates bullish momentum

### Relative Strength Index (RSI)
- **Range**: 0-100
- **Overbought**: RSI > 70
- **Oversold**: RSI < 30
- **Neutral**: 30-70

### Volatility
- **7-Day Volatility**: Percentage standard deviation of price
- **Interpretation**: 
  - <10%: Low volatility (stable)
  - 10-20%: Moderate volatility
  - >20%: High volatility (risky)

### Volume Trend
- **Increasing**: Recent 3-day average > previous 4-day average
- **Decreasing**: Vice versa
- **Significance**: Increasing volume with price rise = strong trend

## Alert System

### Configuration

Enable alerts in `config.json`:

```json
{
  "alerts": {
    "enabled": true,
    "alert_on_score_below": 60,
    "slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "email_notifications": false
  }
}
```

### Slack Integration

1. Create a Slack webhook:
   - Go to https://api.slack.com/messaging/webhooks
   - Create a new webhook for your workspace
   - Copy the webhook URL

2. Add to config.json:
   ```json
   "slack_webhook": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
   ```

3. Alerts will be sent when score drops below threshold

### Alert Triggers

Alerts are triggered when:
- Total score falls below configured threshold (default: 60)
- Critical edge cases are detected
- Significant market changes occur

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
- Technical indicators
- Final verdict and recommendation
- Edge case warnings

### `price_history.json`
Historical data (configurable retention period):
- Timestamp-indexed entries
- Price, volume, and ratio data
- Used for trend analysis and technical indicators

### `monitoring_export.csv`
Exported data for analysis:
- Timestamp, prices, volumes
- Ratios and scores
- Verdicts
- Compatible with Excel and data analysis tools

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
----------------------------------------------------------------------
Technical Indicators (NIGHT)
----------------------------------------------------------------------
  7-Day SMA: $0.2912
  30-Day SMA: $0.2785
  RSI (14): 58.34
  7-Day Volatility: 12.45%
  Volume Trend: Decreasing
----------------------------------------------------------------------
Historical Trend Analysis (30-day)
----------------------------------------------------------------------
  Data Points: 30
  Avg Ratio: 0.2756
  Range: 0.2401 - 0.3012
  Volatility: 0.0156
  Trend: INCREASING
======================================================================
```

## API Rate Limits

CoinGecko free tier limits:
- 10-50 calls/minute
- Script implements exponential backoff
- Automatic retry on 429 status
- 60-second response caching
- Configurable timeout and retry settings

## Performance Optimization

### API Caching
- Responses cached for 60 seconds
- Reduces redundant API calls
- Faster execution on repeated runs

### Data Retention
- Configurable retention period (default: 90 days)
- Automatic cleanup of old data
- Optimized storage and processing

### Batch Operations
- Single API call for multiple assets
- Efficient JSON serialization
- Minimized I/O operations

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
4. Modify scoring weights in configuration

### Custom Technical Indicators

Add to `DataManager.calculate_technical_indicators()`:

```python
# Example: MACD indicator
if len(prices) >= 26:
    ema_12 = self._calculate_ema(prices[-12:], 12)
    ema_26 = self._calculate_ema(prices[-26:], 26)
    indicators.macd = ema_12 - ema_26
```

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

### Configuration not loading
- Verify JSON syntax is valid
- Check file path is correct
- Review logs for parsing errors
- Use default config as template

### Alerts not working
- Verify `enabled` is `true` in config
- Check Slack webhook URL is correct
- Test webhook manually with curl
- Review logs for alert errors

## Best Practices

1. **Run Regularly**: Execute at consistent times for reliable trends
2. **Monitor Logs**: Review `crypto_monitor.log` regularly
3. **Archive Reports**: Keep reports for compliance/audit trail
4. **Manual Verification**: Always verify TC-03 manually via social media
5. **Cross-Reference**: Compare with other market data sources
6. **Use Configuration**: Customize via config.json instead of code changes
7. **Export Data**: Regular exports for backup and analysis
8. **Set Alerts**: Configure threshold-based alerts for critical conditions

## Security Notes

- No API keys required for CoinGecko free tier
- All data stored locally in JSON format
- No sensitive information in logs
- Consider .gitignore for `monitoring_data/` if version controlling
- Slack webhook URLs should be kept secure
- Use environment variables for sensitive configuration

## Future Enhancements

Potential improvements:
- Integration with Midnight TVL data sources
- Real-time WebSocket price feeds
- Email/SMS alerting with SMTP configuration
- Dashboard UI for visualization (Web/Desktop)
- Machine learning-based trend prediction
- Multi-asset portfolio optimization
- Advanced technical indicators (MACD, Bollinger Bands)
- Social sentiment analysis for TC-03
- Automated trading recommendations

## Support

For issues or questions:
1. Check logs in `monitoring_data/crypto_monitor.log`
2. Review CoinGecko API documentation
3. Verify asset IDs are current
4. Test with simplified config first
5. Check configuration file syntax
6. Review this README for solutions

## Version History

### v2.0 (Current)
- Added configuration file support
- Implemented technical indicators
- Added CSV export functionality
- Integrated alert system
- Performance optimizations
- Enhanced documentation

### v1.0
- Initial release
- Basic monitoring functionality
- Test cases TC-01 through TC-04
- Historical data tracking
- Edge case detection

## License

This script is provided as-is for personal use in cryptocurrency asset monitoring and decision-making.

---

**Important Disclaimer**: This monitoring script is a tool for data analysis and does not constitute financial advice. Always conduct your own research and consult with financial professionals before making investment decisions. Cryptocurrency investments carry significant risk.
