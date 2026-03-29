"""
New High-Frequency Momentum Scalping Strategy for Polymarket
Optimized for frequent small profitable trades
"""

import os
import time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, PartialCreateOrderOptions, BalanceAllowanceParams, AssetType
from py_clob_client.order_builder.constants import BUY, SELL

# Load environment variables
load_dotenv()

# New Strategy Configuration
NEW_STRATEGY_CONFIG = {
    # Entry criteria - high probability but still volatile
    "price_min": 0.70,          # 70% minimum probability
    "price_max": 0.89,          # 89% maximum probability (still room for movement)
    
    # Profit targets - small but frequent
    "take_profit_threshold": 0.025,   # 2.5% take profit
    "stop_loss_threshold": -0.08,      # -8% stop loss (strict risk control)
    
    # Position sizing for high frequency
    "trade_amount_usdc": 2.5,          # Smaller positions for more trades
    "max_positions": 10,               # Limit concurrent positions
    
    # Timing for high frequency
    "poll_interval_seconds": 7,        # Check every 7 seconds
    "max_hold_time_minutes": 30,       # Exit positions after 30 mins max
    
    # Risk management
    "max_daily_trades": 100,           # Daily trade limit
    "max_daily_loss": 20.0,            # Stop trading if lose $20 in a day
    
    # Market filters
    "min_liquidity_score": 0.5,        # Only trade liquid markets
    "min_volume_24h": 1000.0,          # Minimum daily volume
}

class HighFrequencyStrategy:
    def __init__(self, client, config=NEW_STRATEGY_CONFIG):
        self.client = client
        self.config = config
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        self.active_positions = []
        
    def reset_daily_counters(self):
        """Reset daily counters at midnight"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset_date = today
            
    def check_entry_criteria(self, price, market_data):
        """Check if market meets entry criteria for high-frequency strategy"""
        # Price range check
        if not (self.config["price_min"] <= price <= self.config["price_max"]):
            return False, f"Price {price:.3f} not in range {self.config['price_min']}-{self.config['price_max']}"
            
        # Liquidity check (if available)
        if "volume_24h" in market_data and market_data["volume_24h"] < self.config["min_volume_24h"]:
            return False, f"Insufficient volume: {market_data['volume_24h']}"
            
        # Daily limits check
        self.reset_daily_counters()
        if self.daily_trades >= self.config["max_daily_trades"]:
            return False, f"Daily trade limit reached: {self.daily_trades}"
            
        if self.daily_pnl <= -self.config["max_daily_loss"]:
            return False, f"Daily loss limit reached: ${self.daily_pnl:.2f}"
            
        # Position limit check
        if len(self.active_positions) >= self.config["max_positions"]:
            return False, f"Max positions reached: {len(self.active_positions)}"
            
        return True, "Entry criteria met"
        
    def calculate_position_size(self, price):
        """Calculate optimal position size for high-frequency trading"""
        base_amount = self.config["trade_amount_usdc"]
        
        # Adjust size based on confidence (higher price = smaller position for safety)
        confidence_multiplier = 1.0 - (price - self.config["price_min"]) / (self.config["price_max"] - self.config["price_min"])
        adjusted_amount = base_amount * (0.7 + 0.3 * confidence_multiplier)  # Range: 70-100% of base
        
        # Calculate shares
        shares = round(adjusted_amount / price, 2)
        return shares, adjusted_amount
        
    def should_exit_position(self, position, current_price):
        """Determine if position should be closed based on strategy rules"""
        entry_price = position["entry_price"]
        entry_time = position["entry_time"]
        
        # Calculate PnL percentage
        pnl_pct = (current_price - entry_price) / entry_price
        
        # Take profit
        if pnl_pct >= self.config["take_profit_threshold"]:
            return True, f"Take profit: {pnl_pct:+.2%}"
            
        # Stop loss
        if pnl_pct <= self.config["stop_loss_threshold"]:
            return True, f"Stop loss: {pnl_pct:+.2%}"
            
        # Max hold time
        hold_time = datetime.now() - entry_time
        if hold_time > timedelta(minutes=self.config["max_hold_time_minutes"]):
            return True, f"Max hold time reached: {hold_time}"
            
        return False, "Hold position"
        
    def execute_trade(self, token_id, price, shares, side):
        """Execute trade with proper error handling and logging"""
        try:
            # Update allowance
            allowance_params = BalanceAllowanceParams(
                asset_type=AssetType.COLLATERAL,
                amount=str(10000)  # Large allowance
            )
            self.client.update_balance_allowance(allowance_params)
            
            # Create order
            order_args = OrderArgs(
                price=price,
                size=shares,
                side=side,
                token_id=token_id,
                order_type=OrderType.LIMIT
            )
            
            # Place order
            order = self.client.create_order(order_args)
            
            # Update daily counters
            self.daily_trades += 1
            
            return True, order
            
        except Exception as e:
            error_msg = f"Trade execution failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return False, error_msg
            
    def get_market_sentiment(self, token_id):
        """Analyze market sentiment for momentum trading"""
        try:
            # Get orderbook for liquidity analysis
            orderbook = self.client.get_order_book(token_id)
            
            # Calculate spread and liquidity score
            if hasattr(orderbook, 'bids') and hasattr(orderbook, 'asks') and orderbook.bids and orderbook.asks:
                best_bid = float(orderbook.bids[0].price)
                best_ask = float(orderbook.asks[0].price)
                spread = best_ask - best_bid
                
                # Simple liquidity score based on spread
                liquidity_score = max(0, 1 - (spread / best_bid))
                
                # Get recent price movement (if available)
                try:
                    midpoint = self.client.get_midpoint(token_id)
                    current_price = float(midpoint.get('midpoint', 0))
                except:
                    current_price = 0
                    
                return {
                    "liquidity_score": liquidity_score,
                    "spread": spread,
                    "current_price": current_price,
                    "best_bid": best_bid,
                    "best_ask": best_ask
                }
        except Exception as e:
            print(f"[DEBUG] Sentiment analysis failed: {e}")
            
        return {"liquidity_score": 0.5, "current_price": 0}  # Default values

# Integration function to replace current strategy
def implement_new_strategy():
    """Function to integrate new strategy into existing bot"""
    print("=== IMPLEMENTING HIGH-FREQUENCY MOMENTUM SCALPING STRATEGY ===")
    print(f"Configuration: {NEW_STRATEGY_CONFIG}")
    print("Key improvements:")
    print("- Higher probability entry range (70-89%)")
    print("- Smaller, faster profits (2.5% TP)")
    print("- Strict risk control (-8% SL)")
    print("- Increased trade frequency (7s intervals)")
    print("- Better position sizing")
    
    return NEW_STRATEGY_CONFIG

if __name__ == "__main__":
    implement_new_strategy()
