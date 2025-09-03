#!/usr/bin/env python3
"""
Real Estate Strategy Analysis Matrix
Analyzes rental vs sell strategies across multiple scenarios
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import argparse
from datetime import datetime

class FinancialAnalyzer:
    def __init__(self, constants):
        self.constants = constants
        
    def calculate_mortgage_payment(self, principal, rate, years=30):
        """Calculate monthly mortgage payment (P&I only)"""
        if rate == 0:
            return principal / (years * 12)
        
        monthly_rate = rate / 12 / 100
        num_payments = years * 12
        
        payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                 ((1 + monthly_rate)**num_payments - 1)
        return payment
    
    def calculate_rental_strategy(self, new_home_price, interest_rate, rental_income):
        """Calculate monthly surplus for rental strategy"""
        # Start with current monthly surplus
        current_surplus = self.constants['monthly_income'] - self.constants['total_monthly_expenses']
        
        # Pay off high-rate debt (HELOC) first with available cash
        cash_for_debt_payoff = min(self.constants['heloc_balance'], self.constants['total_liquid_cash'])
        remaining_cash_after_debt = self.constants['total_liquid_cash'] - cash_for_debt_payoff
        
        # Calculate debt payment savings (HELOC elimination)
        heloc_payment_savings = self.calculate_mortgage_payment(
            self.constants['heloc_balance'], self.constants['heloc_rate']
        )
        
        # New home financing
        down_payment = remaining_cash_after_debt  # Use remaining cash as down payment
        loan_amount = new_home_price - down_payment
        
        # New mortgage P&I
        new_mortgage_pi = self.calculate_mortgage_payment(loan_amount, interest_rate)
        
        # New property tax and insurance
        property_tax_monthly = (new_home_price * 0.018) / 12
        insurance_monthly = self.constants['new_home_insurance'] / 12
        
        # Total new PITI
        new_piti = new_mortgage_pi + property_tax_monthly + insurance_monthly
        
        # Calculate net monthly impact
        new_costs = new_piti + self.constants['new_home_operating'] + self.constants['new_home_utilities']
        rental_income_net = rental_income - self.constants['current_home_operating'] - self.constants['current_home_utilities']
        debt_savings = heloc_payment_savings
        
        # New monthly surplus
        monthly_surplus = current_surplus - new_costs + rental_income_net + debt_savings
        
        return monthly_surplus, new_home_price - down_payment
    
    def calculate_sell_strategy(self, new_home_price, interest_rate):
        """Calculate monthly surplus for sell strategy"""
        # Start with current monthly surplus  
        current_surplus = self.constants['monthly_income'] - self.constants['total_monthly_expenses']
        
        # Sale proceeds
        sale_proceeds = self.constants['current_home_sale_price'] * (1 - self.constants['selling_cost_percentage'])
        
        # Pay off all liens (mortgage + HELOC)
        remaining_proceeds = sale_proceeds - self.constants['total_liens'] - self.constants['heloc_balance']
        
        # New home financing
        available_for_down = remaining_proceeds + self.constants['total_liquid_cash']
        down_payment = available_for_down  # Use all available cash
        loan_amount = max(0, new_home_price - down_payment)
        
        # New mortgage P&I (if any loan needed)
        new_mortgage_pi = self.calculate_mortgage_payment(loan_amount, interest_rate) if loan_amount > 0 else 0
        
        # New property tax and insurance
        property_tax_monthly = (new_home_price * 0.018) / 12
        insurance_monthly = self.constants['new_home_insurance'] / 12
        
        # Total new PITI
        new_piti = new_mortgage_pi + property_tax_monthly + insurance_monthly
        
        # Calculate net monthly impact
        new_costs = new_piti + self.constants['new_home_operating'] + self.constants['new_home_utilities']
        eliminated_costs = (self.constants['current_piti'] + 
                          self.constants['current_home_operating'] + 
                          self.constants['current_home_utilities'])
        
        # New monthly surplus
        monthly_surplus = current_surplus - new_costs + eliminated_costs
        
        return monthly_surplus, max(0, available_for_down - down_payment)

def generate_analysis_matrix():
    """Generate comprehensive analysis matrix"""
    
    # Constants
    constants = {
        'current_home_sale_price': 700000,
        'total_liens': 330000,  # Primary mortgage only (HELOC tracked separately)
        'heloc_balance': 30000,
        'heloc_rate': 9.0,
        'current_piti': 2490,
        'current_home_operating': 390,
        'current_home_utilities': 360,
        'total_liquid_cash': 353000,
        'monthly_income': 12000,
        'total_monthly_expenses': 8684,  # 9434 - 390 - 360
        'base_monthly_expenses': 8684,  # 9434 - 360 - 390
        'new_home_insurance': 8000,
        'new_home_operating': 390,
        'new_home_utilities': 400,
        'selling_cost_percentage': 0.07
    }
    
    # Analysis ranges
    home_prices = range(650000, 905000, 5000)  # 650k to 900k in 5k steps
    interest_rates = np.arange(5.0, 8.05, 0.05)  # 5.0% to 8.0% in 0.05% steps
    rental_incomes = range(3500, 5300, 50)  # 3500 to 5250 in 50 steps
    
    analyzer = FinancialAnalyzer(constants)
    results = []
    
    print(f"Generating analysis matrix...")
    print(f"Home prices: {len(home_prices)} values ({min(home_prices):,} to {max(home_prices):,})")
    print(f"Interest rates: {len(interest_rates)} values ({min(interest_rates):.2f}% to {max(interest_rates):.2f}%)")
    print(f"Rental incomes: {len(rental_incomes)} values ({min(rental_incomes):,} to {max(rental_incomes):,})")
    print(f"Total scenarios: {len(home_prices) * len(interest_rates) * len(rental_incomes):,}")
    
    scenario_count = 0
    total_scenarios = len(home_prices) * len(interest_rates) * len(rental_incomes)
    
    for price in home_prices:
        for rate in interest_rates:
            for rental in rental_incomes:
                scenario_count += 1
                if scenario_count % 100 == 0:
                    print(f"Processing scenario {scenario_count:,}/{total_scenarios:,}")
                
                rental_excess, rental_cash = analyzer.calculate_rental_strategy(price, rate, rental)
                sell_excess, sell_cash = analyzer.calculate_sell_strategy(price, rate)
                
                results.append({
                    'home_price': price,
                    'interest_rate': rate,
                    'rental_income': rental,
                    'rental_monthly_excess': rental_excess,
                    'sell_monthly_excess': sell_excess,
                    'rental_remaining_cash': rental_cash,
                    'sell_remaining_cash': sell_cash,
                    'rental_advantage': rental_excess - sell_excess
                })
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description='Generate real estate strategy analysis matrix')
    parser.add_argument('--output', '-o', default='analysis_matrix.csv', 
                       help='Output CSV filename')
    parser.add_argument('--summary', '-s', action='store_true',
                       help='Show summary statistics')
    
    args = parser.parse_args()
    
    # Generate analysis
    df = generate_analysis_matrix()
    
    # Save results
    output_path = Path(args.output)
    df.to_csv(output_path, index=False)
    print(f"\nAnalysis complete! Results saved to: {output_path}")
    
    # Show summary if requested
    if args.summary:
        print(f"\nSummary Statistics:")
        print(f"Total scenarios analyzed: {len(df):,}")
        print(f"\nRental Strategy Monthly Excess:")
        print(f"  Min: ${df['rental_monthly_excess'].min():,.0f}")
        print(f"  Max: ${df['rental_monthly_excess'].max():,.0f}")
        print(f"  Mean: ${df['rental_monthly_excess'].mean():,.0f}")
        
        print(f"\nSell Strategy Monthly Excess:")
        print(f"  Min: ${df['sell_monthly_excess'].min():,.0f}")
        print(f"  Max: ${df['sell_monthly_excess'].max():,.0f}")
        print(f"  Mean: ${df['sell_monthly_excess'].mean():,.0f}")
        
        print(f"\nRental Advantage (Rental - Sell):")
        print(f"  Min: ${df['rental_advantage'].min():,.0f}")
        print(f"  Max: ${df['rental_advantage'].max():,.0f}")
        print(f"  Mean: ${df['rental_advantage'].mean():,.0f}")
        
        rental_preferred = (df['rental_advantage'] > 0).sum()
        print(f"\nScenarios where rental is preferred: {rental_preferred:,} ({rental_preferred/len(df)*100:.1f}%)")

if __name__ == "__main__":
    main()