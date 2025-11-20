"""Technical analysis utilities for support/resistance detection."""

from decimal import Decimal
from typing import List, Tuple, Dict, Optional
import math

from ..models.market_data import PriceData


class SupportResistanceLevel:
    """Represents a support or resistance level."""

    def __init__(self, price: Decimal, level_type: str, strength: float, touches: int):
        self.price = price
        self.level_type = level_type  # 'support' or 'resistance'
        self.strength = strength  # 0.0 to 1.0
        self.touches = touches  # Number of times price touched this level


class TechnicalAnalyzer:
    """Technical analysis utilities for price data."""

    @staticmethod
    def find_support_resistance_levels(
        price_data: List[PriceData],
        lookback_period: int = 20,
        min_touches: int = 2,
        price_tolerance_percent: float = 0.5
    ) -> Dict[str, List[SupportResistanceLevel]]:
        """
        Identify support and resistance levels using pivot point analysis.

        Args:
            price_data: List of price data (should be sorted by timestamp)
            lookback_period: Number of periods to look back/forward for pivot identification
            min_touches: Minimum number of touches required for a valid level
            price_tolerance_percent: Price tolerance for grouping similar levels

        Returns:
            Dictionary with 'support' and 'resistance' level lists
        """
        if len(price_data) < lookback_period * 2:
            return {"support": [], "resistance": []}

        # Sort by timestamp to ensure chronological order
        sorted_data = sorted(price_data, key=lambda x: x.timestamp)

        # Find pivot highs and lows
        pivot_highs = TechnicalAnalyzer._find_pivot_highs(sorted_data, lookback_period)
        pivot_lows = TechnicalAnalyzer._find_pivot_lows(sorted_data, lookback_period)

        # Group similar price levels
        resistance_levels = TechnicalAnalyzer._group_price_levels(
            pivot_highs, price_tolerance_percent, min_touches, "resistance"
        )
        support_levels = TechnicalAnalyzer._group_price_levels(
            pivot_lows, price_tolerance_percent, min_touches, "support"
        )

        # Calculate strength scores
        current_price = sorted_data[-1].close_price if sorted_data else Decimal("0")

        for level in resistance_levels:
            level.strength = TechnicalAnalyzer._calculate_level_strength(
                level, current_price, sorted_data, "resistance"
            )

        for level in support_levels:
            level.strength = TechnicalAnalyzer._calculate_level_strength(
                level, current_price, sorted_data, "support"
            )

        # Sort by strength (strongest first)
        resistance_levels.sort(key=lambda x: x.strength, reverse=True)
        support_levels.sort(key=lambda x: x.strength, reverse=True)

        return {
            "support": support_levels[:5],  # Top 5 support levels
            "resistance": resistance_levels[:5]  # Top 5 resistance levels
        }

    @staticmethod
    def _find_pivot_highs(price_data: List[PriceData], lookback: int) -> List[Tuple[Decimal, int]]:
        """Find pivot high points in price data."""
        pivot_highs = []

        for i in range(lookback, len(price_data) - lookback):
            current_high = price_data[i].high_price
            is_pivot_high = True

            # Check if current high is higher than surrounding highs
            for j in range(i - lookback, i + lookback + 1):
                if j != i and price_data[j].high_price >= current_high:
                    is_pivot_high = False
                    break

            if is_pivot_high:
                pivot_highs.append((current_high, i))

        return pivot_highs

    @staticmethod
    def _find_pivot_lows(price_data: List[PriceData], lookback: int) -> List[Tuple[Decimal, int]]:
        """Find pivot low points in price data."""
        pivot_lows = []

        for i in range(lookback, len(price_data) - lookback):
            current_low = price_data[i].low_price
            is_pivot_low = True

            # Check if current low is lower than surrounding lows
            for j in range(i - lookback, i + lookback + 1):
                if j != i and price_data[j].low_price <= current_low:
                    is_pivot_low = False
                    break

            if is_pivot_low:
                pivot_lows.append((current_low, i))

        return pivot_lows

    @staticmethod
    def _group_price_levels(
        pivots: List[Tuple[Decimal, int]],
        tolerance_percent: float,
        min_touches: int,
        level_type: str
    ) -> List[SupportResistanceLevel]:
        """Group similar price levels together."""
        if not pivots:
            return []

        levels = []
        tolerance = tolerance_percent / 100

        # Sort pivots by price
        sorted_pivots = sorted(pivots, key=lambda x: x[0])

        i = 0
        while i < len(sorted_pivots):
            current_price = sorted_pivots[i][0]
            group = [sorted_pivots[i]]

            # Find all pivots within tolerance of current price
            j = i + 1
            while j < len(sorted_pivots):
                pivot_price = sorted_pivots[j][0]
                price_diff = abs(float(pivot_price - current_price)) / float(current_price)

                if price_diff <= tolerance:
                    group.append(sorted_pivots[j])
                    j += 1
                else:
                    break

            # Only create level if minimum touches requirement is met
            if len(group) >= min_touches:
                # Calculate average price of the group
                avg_price = sum(pivot[0] for pivot in group) / len(group)

                level = SupportResistanceLevel(
                    price=avg_price,
                    level_type=level_type,
                    strength=0.0,  # Will be calculated later
                    touches=len(group)
                )
                levels.append(level)

            i = j

        return levels

    @staticmethod
    def _calculate_level_strength(
        level: SupportResistanceLevel,
        current_price: Decimal,
        price_data: List[PriceData],
        level_type: str
    ) -> float:
        """Calculate the strength of a support/resistance level."""
        strength = 0.0

        # Base strength from number of touches
        touch_strength = min(level.touches / 5.0, 1.0)  # Max at 5 touches
        strength += touch_strength * 0.4

        # Proximity to current price (closer levels are more relevant)
        price_distance = abs(float(level.price - current_price)) / float(current_price)
        proximity_strength = max(0, 1.0 - price_distance * 10)  # Decay over 10%
        strength += proximity_strength * 0.3

        # Recency of touches (more recent touches are stronger)
        recency_strength = TechnicalAnalyzer._calculate_recency_strength(
            level, price_data, level_type
        )
        strength += recency_strength * 0.3

        return min(strength, 1.0)

    @staticmethod
    def _calculate_recency_strength(
        level: SupportResistanceLevel,
        price_data: List[PriceData],
        level_type: str
    ) -> float:
        """Calculate strength based on recency of level touches."""
        tolerance = 0.005  # 0.5% tolerance
        recent_touches = 0
        total_periods = len(price_data)

        # Look for touches in recent data (last 25% of data)
        recent_start = int(total_periods * 0.75)

        for i in range(recent_start, total_periods):
            price_range = (price_data[i].low_price, price_data[i].high_price)
            level_price = level.price

            # Check if level was touched
            if level_type == "support":
                if (level_price >= price_range[0] * (1 - tolerance) and
                    level_price <= price_range[1] * (1 + tolerance)):
                    recent_touches += 1
            else:  # resistance
                if (level_price >= price_range[0] * (1 - tolerance) and
                    level_price <= price_range[1] * (1 + tolerance)):
                    recent_touches += 1

        return min(recent_touches / 3.0, 1.0)  # Max at 3 recent touches

    @staticmethod
    def calculate_fibonacci_levels(
        price_data: List[PriceData],
        swing_high: Optional[Decimal] = None,
        swing_low: Optional[Decimal] = None
    ) -> Dict[str, Decimal]:
        """Calculate Fibonacci retracement levels."""
        if not price_data:
            return {}

        # Auto-detect swing high/low if not provided
        if swing_high is None or swing_low is None:
            sorted_data = sorted(price_data, key=lambda x: x.timestamp)
            recent_data = sorted_data[-50:] if len(sorted_data) >= 50 else sorted_data

            swing_high = max(d.high_price for d in recent_data)
            swing_low = min(d.low_price for d in recent_data)

        # Fibonacci ratios
        fib_ratios = {
            "0.0": 0.0,
            "23.6": 0.236,
            "38.2": 0.382,
            "50.0": 0.500,
            "61.8": 0.618,
            "78.6": 0.786,
            "100.0": 1.0
        }

        price_range = swing_high - swing_low
        fib_levels = {}

        for level_name, ratio in fib_ratios.items():
            fib_price = swing_high - (price_range * Decimal(str(ratio)))
            fib_levels[f"Fib_{level_name}"] = fib_price

        return fib_levels

    @staticmethod
    def identify_chart_patterns(price_data: List[PriceData]) -> List[Dict]:
        """Identify basic chart patterns."""
        if len(price_data) < 20:
            return []

        patterns = []
        sorted_data = sorted(price_data, key=lambda x: x.timestamp)

        # Simple trend identification
        recent_prices = [d.close_price for d in sorted_data[-20:]]

        # Calculate trend slope
        if len(recent_prices) >= 10:
            x_values = list(range(len(recent_prices)))
            y_values = [float(p) for p in recent_prices]

            # Simple linear regression
            n = len(recent_prices)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

            if slope > 0.5:
                patterns.append({
                    "type": "uptrend",
                    "strength": min(slope / 2.0, 1.0),
                    "description": "Strong upward trend detected"
                })
            elif slope < -0.5:
                patterns.append({
                    "type": "downtrend",
                    "strength": min(abs(slope) / 2.0, 1.0),
                    "description": "Strong downward trend detected"
                })
            else:
                patterns.append({
                    "type": "sideways",
                    "strength": 1.0 - abs(slope),
                    "description": "Sideways/consolidation pattern"
                })

        return patterns