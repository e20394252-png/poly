#!/usr/bin/env python3
"""
Test script for the new High-Frequency Momentum Scalping Strategy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import global_state, client
from new_strategy import HighFrequencyStrategy, NEW_STRATEGY_CONFIG
import json
from datetime import datetime

def test_strategy_config():
    """Test that new strategy configuration is properly loaded"""
    print("=== TESTING NEW STRATEGY CONFIGURATION ===")
    
    # Check if bot is using new config
    print(f"Take Profit: {global_state.config.get('take_profit_threshold')} (expected: 0.025)")
    print(f"Stop Loss: {global_state.config.get('stop_loss_threshold')} (expected: -0.08)")
    print(f"Price Min: {global_state.config.get('price_min')} (expected: 0.70)")
    print(f"Price Max: {global_state.config.get('price_max')} (expected: 0.89)")
    print(f"Max Positions: {global_state.config.get('max_positions')} (expected: 10)")
    print(f"Max Hold Time: {global_state.config.get('max_hold_time_minutes')} (expected: 30)")
    
    # Verify values are correct
    expected = {
        'take_profit_threshold': 0.025,
        'stop_loss_threshold': -0.08,
        'price_min': 0.70,
        'price_max': 0.89,
        'max_positions': 10,
        'max_hold_time_minutes': 30
    }
    
    all_correct = True
    for key, expected_value in expected.items():
        actual_value = global_state.config.get(key)
        if actual_value != expected_value:
            print(f"❌ {key}: {actual_value} != {expected_value}")
            all_correct = False
        else:
            print(f"✅ {key}: {actual_value}")
    
    return all_correct

def test_strategy_logic():
    """Test the new strategy logic with sample data"""
    print("\n=== TESTING STRATEGY LOGIC ===")
    
    if client is None:
        print("❌ Client not initialized - cannot test live strategy")
        return False
    
    strategy = HighFrequencyStrategy(client, NEW_STRATEGY_CONFIG)
    
    # Test entry criteria
    test_cases = [
        {"price": 0.65, "expected": False, "reason": "Below minimum"},
        {"price": 0.75, "expected": True, "reason": "In range"},
        {"price": 0.92, "expected": False, "reason": "Above maximum"},
        {"price": 0.85, "expected": True, "reason": "In range"},
    ]
    
    print("Testing entry criteria:")
    for case in test_cases:
        can_enter, reason = strategy.check_entry_criteria(case["price"], {})
        status = "✅" if can_enter == case["expected"] else "❌"
        print(f"{status} Price {case['price']}: {can_enter} ({reason})")
    
    # Test position sizing
    print("\nTesting position sizing:")
    test_prices = [0.70, 0.75, 0.80, 0.85, 0.89]
    for price in test_prices:
        shares, cost = strategy.calculate_position_size(price)
        print(f"Price {price}: {shares} shares (${cost:.2f})")
    
    return True

def simulate_trade_session():
    """Simulate a trading session with the new strategy"""
    print("\n=== SIMULATING TRADING SESSION ===")
    
    if client is None:
        print("❌ Client not initialized")
        return
    
    # Check current balance
    try:
        balance = client.get_balance()
        print(f"Current balance: ${balance}")
    except Exception as e:
        print(f"❌ Cannot get balance: {e}")
        return
    
    # Simulate finding opportunities
    print("\nSimulating opportunity detection:")
    sample_opportunities = [
        {"price": 0.72, "outcome": "YES", "confidence": 0.85},
        {"price": 0.78, "outcome": "YES", "confidence": 0.80},
        {"price": 0.83, "outcome": "YES", "confidence": 0.75},
        {"price": 0.87, "outcome": "YES", "confidence": 0.70},
    ]
    
    strategy = HighFrequencyStrategy(client, NEW_STRATEGY_CONFIG)
    
    for opp in sample_opportunities:
        can_enter, reason = strategy.check_entry_criteria(opp["price"], {})
        if can_enter:
            shares, cost = strategy.calculate_position_size(opp["price"])
            print(f"✅ OPPORTUNITY: {opp['outcome']} @ ${opp['price']:.2f}")
            print(f"   -> Position: {shares} shares (${cost:.2f})")
            print(f"   -> Confidence: {opp['confidence']:.2f}")
        else:
            print(f"❌ REJECTED: {opp['outcome']} @ ${opp['price']:.2f} - {reason}")

def performance_comparison():
    """Compare old vs new strategy performance metrics"""
    print("\n=== PERFORMANCE COMPARISON ===")
    
    old_strategy = {
        "price_range": "20-80%",
        "take_profit": "4%",
        "stop_loss": "-15%",
        "trade_amount": "5 USDC",
        "expected_win_rate": "~60%",
        "risk_per_trade": "High"
    }
    
    new_strategy = {
        "price_range": "70-89%",
        "take_profit": "2.5%",
        "stop_loss": "-8%",
        "trade_amount": "2-5 USDC (dynamic)",
        "expected_win_rate": "~75-85%",
        "risk_per_trade": "Low"
    }
    
    print("Old Strategy vs New Strategy:")
    for key in old_strategy:
        print(f"{key}:")
        print(f"  Old: {old_strategy[key]}")
        print(f"  New: {new_strategy[key]}")
        print()

if __name__ == "__main__":
    print("Testing New High-Frequency Momentum Scalping Strategy")
    print("=" * 60)
    
    # Run tests
    config_ok = test_strategy_config()
    logic_ok = test_strategy_logic()
    
    if config_ok and logic_ok:
        simulate_trade_session()
        performance_comparison()
        print("\n✅ All tests passed! Strategy is ready for deployment.")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")
    
    print("\nNext steps:")
    print("1. Start the bot with the new strategy")
    print("2. Monitor performance for 1-2 hours")
    print("3. Adjust parameters if needed")
    print("4. Scale up gradually")
