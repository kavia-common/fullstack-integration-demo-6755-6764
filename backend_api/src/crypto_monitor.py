"""
Cryptocurrency Asset Migration Monitoring Script

This script monitors ADA (Cardano) and NIGHT (Midnight) cryptocurrency metrics
to support asset migration testing and decision-making based on predefined criteria.

Features:
- Robust API error handling with exponential backoff retry logic
- Structured logging for production monitoring
- Historical data tracking with JSON persistence
- Comprehensive test case validation (TC-01 through TC-04)
- Scheduling-ready design with configurable intervals
- Detailed metrics and reporting

PUBLIC_INTERFACE
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


# ============================================================================
# CONFIGURATION
# ============================================================================

class TestVerdict(Enum):
    """Test verdict categories based on scoring matrix"""
    HIGHLY_STABLE = "PASS (Highly Stable)"
    CONDITIONAL_PASS = "CONDITIONAL PASS"
    RETEST_REQUIRED = "RE-TEST REQUIRED"
    CRITICAL_BUG = "FAIL (Critical Bug)"


@dataclass
class MonitorConfig:
    """Configuration parameters for the monitoring script"""
    # API Configuration
    api_base_url: str = "https://api.coingecko.com/api/v3"
    api_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    
    # Asset IDs (CoinGecko format)
    ada_id: str = "cardano"
    night_id: str = "midnight-3"
    
    # Test Criteria Thresholds (TC-01 through TC-04)
    target_ratio: float = 0.25  # TC-01: NIGHT/ADA ratio threshold
    ratio_sell_pressure: float = 0.20  # TC-01: Critical sell pressure level
    tvl_monthly_growth: float = 15.0  # TC-02: Required TVL growth percentage
    min_zk_dapps: int = 3  # TC-02: Minimum active ZK dApps
    stability_threshold: float = 15.0  # TC-04: Max acceptable 24h volatility (%)
    crash_threshold: float = 30.0  # TC-04: Critical price drop threshold (%)
    
    # Volume Analysis (Edge Case Detection)
    min_volume_ratio: float = 0.05  # NIGHT volume must be >5% of ADA volume
    
    # Test Weights for Scoring
    tc01_weight: int = 40  # Ratio pressure test weight
    tc02_weight: int = 30  # Ecosystem growth test weight
    tc03_weight: int = 20  # Founder engagement test weight
    tc04_weight: int = 10  # Unlock stability test weight
    
    # Data Storage
    data_dir: str = "monitoring_data"
    history_file: str = "price_history.json"
    report_file: str = "latest_report.json"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "crypto_monitor.log"


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(config: MonitorConfig) -> logging.Logger:
    """
    Configure structured logging for the monitoring script
    
    PUBLIC_INTERFACE
    """
    logger = logging.getLogger("CryptoMonitor")
    logger.setLevel(getattr(logging, config.log_level))
    
    # Console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler for persistent logs
    log_path = Path(config.data_dir) / config.log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s'
    )
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class CryptoMetrics:
    """Comprehensive metrics for a cryptocurrency asset"""
    asset_id: str
    timestamp: str
    price_usd: float
    volume_24h: float
    price_change_24h: float
    market_cap: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TestCaseResult:
    """Result of an individual test case"""
    test_id: str
    name: str
    status: str
    score: int
    weight: int
    details: Dict
    pass_criteria: str


@dataclass
class MonitoringReport:
    """Complete monitoring report with all test results"""
    timestamp: str
    test_environment: str
    ada_metrics: CryptoMetrics
    night_metrics: CryptoMetrics
    current_ratio: float
    test_results: List[TestCaseResult]
    total_score: int
    verdict: str
    recommendation: str
    edge_case_warnings: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'test_environment': self.test_environment,
            'ada_metrics': self.ada_metrics.to_dict(),
            'night_metrics': self.night_metrics.to_dict(),
            'current_ratio': self.current_ratio,
            'test_results': [
                {
                    'test_id': tc.test_id,
                    'name': tc.name,
                    'status': tc.status,
                    'score': tc.score,
                    'weight': tc.weight,
                    'details': tc.details,
                    'pass_criteria': tc.pass_criteria
                }
                for tc in self.test_results
            ],
            'total_score': self.total_score,
            'verdict': self.verdict,
            'recommendation': self.recommendation,
            'edge_case_warnings': self.edge_case_warnings
        }


# ============================================================================
# API CLIENT WITH RETRY LOGIC
# ============================================================================

class CoinGeckoClient:
    """
    Robust CoinGecko API client with retry logic and rate limiting
    
    PUBLIC_INTERFACE
    """
    
    def __init__(self, config: MonitorConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Crypto Monitor Bot)',
            'Accept': 'application/json'
        })
    
    def get_crypto_data(self, asset_ids: List[str]) -> Optional[Dict]:
        """
        Fetch cryptocurrency data with exponential backoff retry
        
        Args:
            asset_ids: List of CoinGecko asset IDs
            
        Returns:
            Dictionary with asset data or None on failure
            
        PUBLIC_INTERFACE
        """
        url = f"{self.config.api_base_url}/simple/price"
        params = {
            "ids": ",".join(asset_ids),
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_market_cap": "true"
        }
        
        for attempt in range(1, self.config.max_retries + 1):
            try:
                self.logger.debug(f"API request attempt {attempt}/{self.config.max_retries}")
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.api_timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # Validate response structure
                if not self._validate_response(data, asset_ids):
                    raise ValueError("Invalid API response structure")
                
                self.logger.info(f"Successfully fetched data for {len(asset_ids)} assets")
                return data
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"API timeout on attempt {attempt}")
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"HTTP error on attempt {attempt}: {e}")
                if e.response.status_code == 429:  # Rate limit
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    self.logger.warning(f"Rate limited. Waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed on attempt {attempt}: {e}")
            except ValueError as e:
                self.logger.error(f"Data validation failed: {e}")
                return None
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt}: {e}")
            
            if attempt < self.config.max_retries:
                wait_time = self.config.retry_delay * attempt
                self.logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        self.logger.error("All retry attempts failed")
        return None
    
    def _validate_response(self, data: Dict, expected_ids: List[str]) -> bool:
        """Validate API response contains expected data"""
        if not isinstance(data, dict):
            return False
        
        for asset_id in expected_ids:
            if asset_id not in data:
                self.logger.error(f"Missing data for asset: {asset_id}")
                return False
            
            asset_data = data[asset_id]
            required_fields = ['usd', 'usd_24h_vol', 'usd_24h_change']
            for field in required_fields:
                if field not in asset_data:
                    self.logger.error(f"Missing field '{field}' for {asset_id}")
                    return False
        
        return True


# ============================================================================
# DATA PERSISTENCE
# ============================================================================

class DataManager:
    """
    Manages historical data persistence and retrieval
    
    PUBLIC_INTERFACE
    """
    
    def __init__(self, config: MonitorConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.data_path = Path(config.data_dir)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_path / config.history_file
        self.report_file = self.data_path / config.report_file
    
    def save_metrics(self, metrics: Dict):
        """
        Append current metrics to historical data
        
        PUBLIC_INTERFACE
        """
        try:
            history = self.load_history()
            history.append(metrics)
            
            # Keep only last 90 days of data
            if len(history) > 90:
                history = history[-90:]
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            self.logger.info(f"Saved metrics to {self.history_file}")
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
    
    def load_history(self) -> List[Dict]:
        """
        Load historical metrics data
        
        PUBLIC_INTERFACE
        """
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load history: {e}")
        
        return []
    
    def save_report(self, report: MonitoringReport):
        """
        Save the latest monitoring report
        
        PUBLIC_INTERFACE
        """
        try:
            with open(self.report_file, 'w') as f:
                json.dump(report.to_dict(), f, indent=2)
            
            self.logger.info(f"Saved report to {self.report_file}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
    
    def get_historical_trend(self, days: int = 30) -> Dict:
        """
        Calculate historical trends over specified period
        
        PUBLIC_INTERFACE
        """
        history = self.load_history()
        if len(history) < 2:
            return {'trend': 'insufficient_data', 'data_points': len(history)}
        
        recent_data = history[-days:] if len(history) >= days else history
        
        ratios = [entry.get('current_ratio', 0) for entry in recent_data]
        if not ratios:
            return {'trend': 'no_ratio_data'}
        
        avg_ratio = sum(ratios) / len(ratios)
        min_ratio = min(ratios)
        max_ratio = max(ratios)
        
        # Calculate volatility
        if len(ratios) > 1:
            variance = sum((r - avg_ratio) ** 2 for r in ratios) / len(ratios)
            volatility = variance ** 0.5
        else:
            volatility = 0
        
        return {
            'data_points': len(recent_data),
            'avg_ratio': round(avg_ratio, 4),
            'min_ratio': round(min_ratio, 4),
            'max_ratio': round(max_ratio, 4),
            'volatility': round(volatility, 4),
            'trend': 'increasing' if ratios[-1] > ratios[0] else 'decreasing'
        }


# ============================================================================
# TEST CASE EXECUTION
# ============================================================================

class TestExecutor:
    """
    Executes all test cases and generates scoring
    
    PUBLIC_INTERFACE
    """
    
    def __init__(self, config: MonitorConfig, logger: logging.Logger, data_manager: DataManager):
        self.config = config
        self.logger = logger
        self.data_manager = data_manager
    
    def execute_tc01_ratio_pressure(
        self, 
        current_ratio: float, 
        ada_price: float, 
        night_price: float
    ) -> TestCaseResult:
        """
        TC-01: Exchange Rate Pressure Test
        
        Validates that NIGHT/ADA ratio meets threshold requirements
        
        PUBLIC_INTERFACE
        """
        score = 0
        status = "FAIL"
        
        if current_ratio >= self.config.target_ratio:
            score = self.config.tc01_weight
            status = "PASS"
        elif current_ratio >= self.config.ratio_sell_pressure:
            score = int(self.config.tc01_weight * 0.5)
            status = "WARNING"
        
        details = {
            'current_ratio': round(current_ratio, 4),
            'target_ratio': self.config.target_ratio,
            'sell_pressure_level': self.config.ratio_sell_pressure,
            'ada_price': round(ada_price, 4),
            'night_price': round(night_price, 4),
            'interpretation': (
                "Strong position - ratio above target" if status == "PASS"
                else "Moderate sell pressure detected" if status == "WARNING"
                else "Critical - excessive sell pressure"
            )
        }
        
        return TestCaseResult(
            test_id="TC-01",
            name="Exchange Rate Pressure Test",
            status=status,
            score=score,
            weight=self.config.tc01_weight,
            details=details,
            pass_criteria=f"Ratio >= {self.config.target_ratio} with converging volatility"
        )
    
    def execute_tc02_ecosystem_growth(
        self, 
        night_volume: float, 
        ada_volume: float
    ) -> TestCaseResult:
        """
        TC-02: Ecosystem Growth Test
        
        Evaluates Midnight ecosystem development indicators
        Note: TVL and dApp count require additional data sources
        
        PUBLIC_INTERFACE
        """
        score = 0
        status = "MANUAL_REVIEW"
        
        # Volume comparison as proxy for ecosystem activity
        volume_ratio = night_volume / ada_volume if ada_volume > 0 else 0
        
        # Simplified scoring based on available data
        if volume_ratio >= 0.10:  # 10% of ADA volume indicates healthy ecosystem
            score = self.config.tc02_weight
            status = "PASS"
        elif volume_ratio >= 0.05:
            score = int(self.config.tc02_weight * 0.6)
            status = "CONDITIONAL"
        
        details = {
            'night_24h_volume': round(night_volume, 2),
            'ada_24h_volume': round(ada_volume, 2),
            'volume_ratio': round(volume_ratio, 4),
            'note': 'Full TVL and dApp metrics require additional data sources',
            'interpretation': (
                "Healthy ecosystem activity" if status == "PASS"
                else "Moderate activity levels" if status == "CONDITIONAL"
                else "Requires manual verification of TVL and dApp count"
            )
        }
        
        return TestCaseResult(
            test_id="TC-02",
            name="Ecosystem Growth Test",
            status=status,
            score=score,
            weight=self.config.tc02_weight,
            details=details,
            pass_criteria=f"TVL growth >{self.config.tvl_monthly_growth}% monthly, {self.config.min_zk_dapps}+ active ZK dApps"
        )
    
    def execute_tc03_founder_engagement(self) -> TestCaseResult:
        """
        TC-03: Founder Engagement Test
        
        Monitors Charles Hoskinson's engagement quality
        Note: Requires external social media monitoring
        
        PUBLIC_INTERFACE
        """
        # This test requires external data sources (YouTube, X/Twitter)
        # Return placeholder result indicating manual review needed
        
        details = {
            'data_source': 'External - YouTube & X/Twitter analytics required',
            'metrics_needed': [
                'YouTube deep-dive frequency',
                'X platform engagement quality',
                'Community sentiment analysis'
            ],
            'note': 'Manual review recommended via social media monitoring tools'
        }
        
        return TestCaseResult(
            test_id="TC-03",
            name="Founder Engagement Test",
            status="MANUAL_REVIEW",
            score=self.config.tc03_weight,  # Give full credit pending manual review
            weight=self.config.tc03_weight,
            details=details,
            pass_criteria="Stable YouTube engagement, reduced X platform noise"
        )
    
    def execute_tc04_unlock_stability(
        self, 
        price_change_24h: float,
        historical_data: List[Dict]
    ) -> TestCaseResult:
        """
        TC-04: Token Unlock Stability Test
        
        Monitors price stability after unlock events
        
        PUBLIC_INTERFACE
        """
        score = 0
        status = "FAIL"
        
        # Check 24h volatility
        volatility_ok = abs(price_change_24h) < self.config.stability_threshold
        
        # Check for crash conditions
        no_crash = price_change_24h > -self.config.crash_threshold
        
        if volatility_ok and no_crash:
            score = self.config.tc04_weight
            status = "PASS"
        elif no_crash:
            score = int(self.config.tc04_weight * 0.5)
            status = "WARNING"
        
        # Analyze historical volatility if data available
        historical_volatility = "N/A"
        if len(historical_data) >= 7:
            recent_changes = [
                entry.get('night_metrics', {}).get('price_change_24h', 0)
                for entry in historical_data[-7:]
            ]
            avg_volatility = sum(abs(c) for c in recent_changes) / len(recent_changes)
            historical_volatility = round(avg_volatility, 2)
        
        details = {
            'price_change_24h': round(price_change_24h, 2),
            'stability_threshold': self.config.stability_threshold,
            'crash_threshold': self.config.crash_threshold,
            'historical_7d_avg_volatility': historical_volatility,
            'interpretation': (
                "Price stable - no unlock stress detected" if status == "PASS"
                else "Moderate volatility observed" if status == "WARNING"
                else "Critical instability - potential cascade risk"
            )
        }
        
        return TestCaseResult(
            test_id="TC-04",
            name="Token Unlock Stability Test",
            status=status,
            score=score,
            weight=self.config.tc04_weight,
            details=details,
            pass_criteria=f"24h volatility <{self.config.stability_threshold}%, no drops >{self.config.crash_threshold}%"
        )
    
    def check_edge_cases(
        self, 
        night_volume: float, 
        ada_volume: float
    ) -> List[str]:
        """
        Check for critical edge cases that could invalidate migration
        
        PUBLIC_INTERFACE
        """
        warnings = []
        
        # Edge Case 1: Zombie chain - insufficient liquidity
        volume_ratio = night_volume / ada_volume if ada_volume > 0 else 0
        if volume_ratio < self.config.min_volume_ratio:
            warnings.append(
                f"⚠️ CRITICAL: NIGHT volume is only {volume_ratio*100:.2f}% of ADA volume "
                f"(threshold: {self.config.min_volume_ratio*100}%). "
                "Potential 'zombie chain' - insufficient liquidity for target gains."
            )
        
        # Edge Case 2: Volume trend analysis
        historical = self.data_manager.load_history()
        if len(historical) >= 7:
            recent_volumes = [
                entry.get('night_metrics', {}).get('volume_24h', 0)
                for entry in historical[-7:]
            ]
            if recent_volumes:
                avg_volume = sum(recent_volumes) / len(recent_volumes)
                current_vs_avg = (night_volume / avg_volume - 1) * 100 if avg_volume > 0 else 0
                
                if current_vs_avg < -30:
                    warnings.append(
                        f"⚠️ WARNING: NIGHT volume dropped {abs(current_vs_avg):.1f}% "
                        "below 7-day average. Liquidity declining."
                    )
        
        return warnings


# ============================================================================
# MAIN MONITOR
# ============================================================================

class CryptoMonitor:
    """
    Main monitoring orchestrator
    
    PUBLIC_INTERFACE
    """
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()
        self.logger = setup_logging(self.config)
        self.api_client = CoinGeckoClient(self.config, self.logger)
        self.data_manager = DataManager(self.config, self.logger)
        self.test_executor = TestExecutor(self.config, self.logger, self.data_manager)
    
    def execute_monitoring_cycle(self) -> Optional[MonitoringReport]:
        """
        Execute complete monitoring cycle with all tests
        
        Returns:
            MonitoringReport object or None on failure
            
        PUBLIC_INTERFACE
        """
        self.logger.info("=" * 70)
        self.logger.info("Starting Midnight Asset Migration Monitoring Cycle")
        self.logger.info("=" * 70)
        
        # Fetch current data
        data = self.api_client.get_crypto_data([self.config.ada_id, self.config.night_id])
        if not data:
            self.logger.error("Failed to fetch cryptocurrency data")
            return None
        
        # Parse metrics
        try:
            ada_metrics = self._parse_metrics(data[self.config.ada_id], self.config.ada_id)
            night_metrics = self._parse_metrics(data[self.config.night_id], self.config.night_id)
        except Exception as e:
            self.logger.error(f"Failed to parse metrics: {e}")
            return None
        
        # Calculate ratio
        current_ratio = night_metrics.price_usd / ada_metrics.price_usd
        
        self.logger.info(f"Current NIGHT/ADA Ratio: {current_ratio:.4f}")
        self.logger.info(f"ADA Price: ${ada_metrics.price_usd} | NIGHT Price: ${night_metrics.price_usd}")
        
        # Load historical data for trend analysis
        historical_data = self.data_manager.load_history()
        
        # Execute all test cases
        self.logger.info("-" * 70)
        self.logger.info("Executing Test Cases")
        self.logger.info("-" * 70)
        
        test_results = []
        
        # TC-01: Ratio Pressure Test
        tc01 = self.test_executor.execute_tc01_ratio_pressure(
            current_ratio, ada_metrics.price_usd, night_metrics.price_usd
        )
        test_results.append(tc01)
        self.logger.info(f"[{tc01.test_id}] {tc01.name}: {tc01.status} (Score: {tc01.score}/{tc01.weight})")
        
        # TC-02: Ecosystem Growth Test
        tc02 = self.test_executor.execute_tc02_ecosystem_growth(
            night_metrics.volume_24h, ada_metrics.volume_24h
        )
        test_results.append(tc02)
        self.logger.info(f"[{tc02.test_id}] {tc02.name}: {tc02.status} (Score: {tc02.score}/{tc02.weight})")
        
        # TC-03: Founder Engagement Test
        tc03 = self.test_executor.execute_tc03_founder_engagement()
        test_results.append(tc03)
        self.logger.info(f"[{tc03.test_id}] {tc03.name}: {tc03.status} (Score: {tc03.score}/{tc03.weight})")
        
        # TC-04: Unlock Stability Test
        tc04 = self.test_executor.execute_tc04_unlock_stability(
            night_metrics.price_change_24h, historical_data
        )
        test_results.append(tc04)
        self.logger.info(f"[{tc04.test_id}] {tc04.name}: {tc04.status} (Score: {tc04.score}/{tc04.weight})")
        
        # Calculate total score
        total_score = sum(tc.score for tc in test_results)
        
        # Check edge cases
        self.logger.info("-" * 70)
        self.logger.info("Edge Case Analysis")
        self.logger.info("-" * 70)
        edge_warnings = self.test_executor.check_edge_cases(
            night_metrics.volume_24h, ada_metrics.volume_24h
        )
        
        for warning in edge_warnings:
            self.logger.warning(warning)
        
        if not edge_warnings:
            self.logger.info("✓ No critical edge cases detected")
        
        # Generate verdict and recommendation
        verdict, recommendation = self._generate_verdict(total_score, edge_warnings)
        
        # Create report
        report = MonitoringReport(
            timestamp=datetime.now().isoformat(),
            test_environment="Midnight Kūkolu Phase (Stable Mainnet Preview)",
            ada_metrics=ada_metrics,
            night_metrics=night_metrics,
            current_ratio=current_ratio,
            test_results=test_results,
            total_score=total_score,
            verdict=verdict,
            recommendation=recommendation,
            edge_case_warnings=edge_warnings
        )
        
        # Print final verdict
        self.logger.info("=" * 70)
        self.logger.info(f"FINAL VERDICT: {verdict}")
        self.logger.info(f"Total Score: {total_score}/100")
        self.logger.info(f"Recommendation: {recommendation}")
        self.logger.info("=" * 70)
        
        # Persist data
        self.data_manager.save_metrics({
            'timestamp': report.timestamp,
            'current_ratio': current_ratio,
            'ada_metrics': ada_metrics.to_dict(),
            'night_metrics': night_metrics.to_dict(),
            'total_score': total_score,
            'verdict': verdict
        })
        self.data_manager.save_report(report)
        
        # Print historical trend
        trend = self.data_manager.get_historical_trend()
        if trend.get('data_points', 0) > 1:
            self.logger.info("-" * 70)
            self.logger.info("Historical Trend Analysis (30-day)")
            self.logger.info(f"  Data Points: {trend['data_points']}")
            self.logger.info(f"  Avg Ratio: {trend.get('avg_ratio', 'N/A')}")
            self.logger.info(f"  Range: {trend.get('min_ratio', 'N/A')} - {trend.get('max_ratio', 'N/A')}")
            self.logger.info(f"  Volatility: {trend.get('volatility', 'N/A')}")
            self.logger.info(f"  Trend: {trend.get('trend', 'N/A').upper()}")
        
        return report
    
    def _parse_metrics(self, data: Dict, asset_id: str) -> CryptoMetrics:
        """Parse API response into CryptoMetrics object"""
        return CryptoMetrics(
            asset_id=asset_id,
            timestamp=datetime.now().isoformat(),
            price_usd=data['usd'],
            volume_24h=data['usd_24h_vol'],
            price_change_24h=data['usd_24h_change'],
            market_cap=data.get('usd_market_cap')
        )
    
    def _generate_verdict(self, total_score: int, edge_warnings: List[str]) -> Tuple[str, str]:
        """
        Generate final verdict and recommendation based on scoring matrix
        
        Scoring Matrix:
        - 85-100: PASS (Highly Stable) - Aggressive swap 20-30% ADA to NIGHT
        - 60-84: CONDITIONAL PASS - Conservative swap 10% ADA to NIGHT
        - 40-59: RE-TEST REQUIRED - Hold position, airdrop only
        - <40: FAIL (Critical Bug) - Risk avoidance, consider swap back to ADA
        """
        if edge_warnings:
            # Critical edge cases detected - downgrade verdict
            if total_score >= 85:
                total_score = 70  # Downgrade to conditional
            elif total_score >= 60:
                total_score = 50  # Downgrade to retest
        
        if total_score >= 85:
            return (
                TestVerdict.HIGHLY_STABLE.value,
                "✓ AGGRESSIVE SWAP: Migrate 20-30% of ADA holdings to NIGHT. "
                "All metrics indicate strong stability and growth potential."
            )
        elif total_score >= 60:
            return (
                TestVerdict.CONDITIONAL_PASS.value,
                "⚠ CONSERVATIVE SWAP: Migrate only 10% of ADA holdings to NIGHT. "
                "Maintain flexibility for market changes."
            )
        elif total_score >= 40:
            return (
                TestVerdict.RETEST_REQUIRED.value,
                "⏸ HOLD POSITION: Maintain current allocation. "
                "Participate via airdrop only, no additional purchases recommended."
            )
        else:
            return (
                TestVerdict.CRITICAL_BUG.value,
                "⛔ RISK AVOIDANCE: Consider swapping airdropped NIGHT back to ADA. "
                "Critical stability issues detected."
            )


# ============================================================================
# SCHEDULING AND CLI
# ============================================================================

def run_scheduled_monitoring(interval_hours: int = 24, max_runs: Optional[int] = None):
    """
    Run monitoring on a scheduled basis
    
    Args:
        interval_hours: Hours between monitoring cycles
        max_runs: Maximum number of runs (None for infinite)
        
    PUBLIC_INTERFACE
    """
    monitor = CryptoMonitor()
    run_count = 0
    
    monitor.logger.info(f"Starting scheduled monitoring (every {interval_hours} hours)")
    
    while True:
        run_count += 1
        
        try:
            report = monitor.execute_monitoring_cycle()
            
            if report:
                monitor.logger.info(f"Monitoring cycle {run_count} completed successfully")
            else:
                monitor.logger.error(f"Monitoring cycle {run_count} failed")
        
        except Exception as e:
            monitor.logger.error(f"Unexpected error in monitoring cycle {run_count}: {e}", exc_info=True)
        
        # Check if we've reached max runs
        if max_runs and run_count >= max_runs:
            monitor.logger.info(f"Reached maximum runs ({max_runs}). Exiting.")
            break
        
        # Wait for next cycle
        wait_seconds = interval_hours * 3600
        next_run = datetime.now() + timedelta(seconds=wait_seconds)
        monitor.logger.info(f"Next monitoring cycle at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        monitor.logger.info(f"Sleeping for {interval_hours} hours...")
        
        time.sleep(wait_seconds)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

# PUBLIC_INTERFACE
def main():
    """
    Main entry point for the monitoring script
    
    Usage:
        python crypto_monitor.py              # Run single cycle
        python crypto_monitor.py --schedule   # Run continuously (24h intervals)
        
    PUBLIC_INTERFACE
    """
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--schedule':
        # Scheduled mode - runs continuously
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        run_scheduled_monitoring(interval_hours=interval)
    else:
        # Single execution mode
        monitor = CryptoMonitor()
        report = monitor.execute_monitoring_cycle()
        
        if report:
            print("\n" + "=" * 70)
            print("Report saved to: monitoring_data/latest_report.json")
            print("Historical data: monitoring_data/price_history.json")
            print("Logs: monitoring_data/crypto_monitor.log")
            print("=" * 70)
            sys.exit(0)
        else:
            print("Monitoring cycle failed. Check logs for details.")
            sys.exit(1)


if __name__ == "__main__":
    main()
