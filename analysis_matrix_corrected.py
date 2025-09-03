#!/usr/bin/env python3
"""
Real Estate Strategy Analysis Matrix - FINAL CORRECTED VERSION
Properly handles that $9,434 includes ALL expenses including HELOC
Both strategies pay off HELOC first
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
        if principal <= 0:
            return 0
        if rate == 0:
            return principal / (years * 12)
        
        monthly_rate = rate / 12 / 100
        num_payments = years * 12
        
        payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                 ((1 + monthly_rate)**num_payments - 1)
        return payment
    
    def calculate_heloc_payment(self, balance, rate, years=10):
        """Calculate HELOC payment (10-year term)"""
        return self.calculate_mortgage_payment(balance, rate, years)
    
    def calculate_rental_strategy(self, new_home_price, interest_rate, rental_income):
        """Calculate monthly surplus for rental strategy"""
        
        # Calculate what HELOC payment was (to remove from base)
        heloc_payment = self.calculate_heloc_payment(
            self.constants['heloc_balance'], 
            self.constants['heloc_rate']
        )
        
        # Base expenses = Total - PITI - operating - utilities - HELOC
        # Since we're breaking these out separately
        base_expenses = (self.constants['total_monthly_expenses'] - 
                        self.constants['current_piti'] - 
                        self.constants['current_home_operating'] - 
                        self.constants['current_home_utilities'] -
                        heloc_payment)
        
        # ALWAYS pay off HELOC first with available cash
        cash_after_heloc = self.constants['total_liquid_cash'] - self.constants['heloc_balance']
        
        # New home financing
        down_payment = min(cash_after_heloc, new_home_price)
        loan_amount = max(0, new_home_price - down_payment)
        
        # New mortgage payment
        new_mortgage_pi = self.calculate_mortgage_payment(loan_amount, interest_rate)
        
        # New property tax and insurance
        property_tax_monthly = (new_home_price * 0.018) / 12
        insurance_monthly = self.constants['new_home_insurance'] / 12
        new_piti = new_mortgage_pi + property_tax_monthly + insurance_monthly
        
        # Calculate total monthly expenses
        # Base + current home costs + new home costs - NO HELOC (paid off)
        total_expenses = (
            base_expenses +
            self.constants['current_piti'] + # Current mortgage continues
            self.constants['current_home_operating'] +  # Current operating continues
            #self.constants['current_home_utilities'] +  # Current utilities continue
            # NO HELOC payment - it's paid off
            new_piti +  # New home PITI
            self.constants['new_home_operating'] +  # New home operating
            self.constants['new_home_utilities']  # New home utilities
        )
        
        # Total income includes rental
        total_income = self.constants['monthly_income'] + rental_income
        
        monthly_surplus = total_income - total_expenses
        
        return monthly_surplus, cash_after_heloc
    
    def calculate_sell_strategy(self, new_home_price, interest_rate):
        """Calculate monthly surplus for sell strategy"""
        
        # Calculate what HELOC payment was (to remove from base)
        heloc_payment = self.calculate_heloc_payment(
            self.constants['heloc_balance'], 
            self.constants['heloc_rate']
        )
        
        # Base expenses = Total - PITI - operating - utilities - HELOC
        base_expenses = (self.constants['total_monthly_expenses'] - 
                        self.constants['current_piti'] - 
                        self.constants['current_home_operating'] - 
                        self.constants['current_home_utilities'] -
                        heloc_payment)
        
        # Calculate sale proceeds
        gross_proceeds = self.constants['current_home_sale_price']
        selling_costs = gross_proceeds * self.constants['selling_cost_percentage']
        net_proceeds = gross_proceeds - selling_costs
        
        # Pay off all liens including HELOC
        total_liens = self.constants['total_liens'] + self.constants['heloc_balance']
        cash_from_sale = net_proceeds - total_liens
        
        # Total cash for new home
        total_cash = cash_from_sale + self.constants['total_liquid_cash']
        
        # New home financing
        down_payment = min(total_cash, new_home_price)
        loan_amount = max(0, new_home_price - down_payment)
        remaining_cash = max(0, total_cash - down_payment)
        
        # New mortgage payment
        new_mortgage_pi = self.calculate_mortgage_payment(loan_amount, interest_rate)
        
        # New property tax and insurance
        property_tax_monthly = (new_home_price * 0.018) / 12
        insurance_monthly = self.constants['new_home_insurance'] / 12
        new_piti = new_mortgage_pi + property_tax_monthly + insurance_monthly
        
        # Total monthly expenses (no current home costs, no HELOC)
        total_expenses = (
            base_expenses +
            new_piti +
            self.constants['new_home_operating'] +
            self.constants['new_home_utilities']
        )
        
        monthly_surplus = self.constants['monthly_income'] - total_expenses
        
        return monthly_surplus, remaining_cash

def generate_analysis_matrix():
    """Generate comprehensive analysis matrix"""
    
    # Constants - $9,434 INCLUDES everything
    constants = {
        'current_home_sale_price': 700000,
        'total_liens': 330000,  # Primary mortgage balance only
        'heloc_balance': 30000,  # Separate from mortgage
        'heloc_rate': 9.0,
        'current_piti': 2490,
        'current_home_operating': 390,
        'current_home_utilities': 360,
        'total_liquid_cash': 353000,
        'monthly_income': 12000,
        'total_monthly_expenses': 9434,  # INCLUDES EVERYTHING (PITI, operating, utilities, HELOC, etc.)
        'new_home_insurance': 8000,  # Annual
        'new_home_operating': 390,
        'new_home_utilities': 400,
        'selling_cost_percentage': 0.07
    }
    
    analyzer = FinancialAnalyzer(constants)
    
    # Calculate and display baseline verification
    heloc_payment = analyzer.calculate_heloc_payment(constants['heloc_balance'], constants['heloc_rate'])
    
    # Calculate base living expenses (everything except housing and HELOC)
    base_expenses = (constants['total_monthly_expenses'] - 
                    constants['current_piti'] - 
                    constants['current_home_operating'] - 
                    constants['current_home_utilities'] -
                    heloc_payment)
    
    print("\n" + "=" * 50)
    print("BASELINE FINANCIAL VERIFICATION")
    print("=" * 50)
    print(f"Monthly Income: ${constants['monthly_income']:,}")
    print(f"Total Monthly Expenses: ${constants['total_monthly_expenses']:,}")
    print(f"Current Monthly Surplus: ${constants['monthly_income'] - constants['total_monthly_expenses']:,}")
    print("\nExpense Breakdown:")
    print(f"  Current PITI: ${constants['current_piti']:,}")
    print(f"  Current Operating: ${constants['current_home_operating']:,}")
    print(f"  Current Utilities: ${constants['current_home_utilities']:,}")
    print(f"  HELOC Payment (10-yr): ${heloc_payment:.0f}")
    print(f"  Subtotal Housing+HELOC: ${constants['current_piti'] + constants['current_home_operating'] + constants['current_home_utilities'] + heloc_payment:,.0f}")
    print(f"  Other Living Expenses: ${base_expenses:,.0f}")
    print(f"  TOTAL: ${base_expenses + constants['current_piti'] + constants['current_home_operating'] + constants['current_home_utilities'] + heloc_payment:,.0f}")
    
    print("\nKey Assumptions:")
    print(f"  • HELOC ({constants['heloc_balance']:,} @ {constants['heloc_rate']}%) paid off FIRST in both strategies")
    print(f"  • Rental strategy: Uses remaining ${constants['total_liquid_cash'] - constants['heloc_balance']:,} for down payment")
    print(f"  • Sell strategy: Gets ~${(constants['current_home_sale_price'] * 0.93 - constants['total_liens'] - constants['heloc_balance']):,.0f} from sale + ${constants['total_liquid_cash']:,} cash")
    print("=" * 50)
    
    # Analysis ranges
    home_prices = range(650000, 905000, 5000)
    interest_rates = np.arange(5.0, 8.05, 0.05)
    rental_incomes = range(3500, 5300, 50)
    
    results = []
    
    print(f"\nGenerating analysis matrix...")
    print(f"Home prices: {len(home_prices)} values (${min(home_prices):,} to ${max(home_prices):,})")
    print(f"Interest rates: {len(interest_rates)} values ({min(interest_rates):.2f}% to {max(interest_rates):.2f}%)")
    print(f"Rental incomes: {len(rental_incomes)} values (${min(rental_incomes):,} to ${max(rental_incomes):,})")
    print(f"Total scenarios: {len(home_prices) * len(interest_rates) * len(rental_incomes):,}\n")
    
    scenario_count = 0
    total_scenarios = len(home_prices) * len(interest_rates) * len(rental_incomes)
    
    # Track best scenarios
    best_rental_scenario = None
    best_rental_advantage = float('-inf')
    rental_wins = 0
    
    for price in home_prices:
        for rate in interest_rates:
            for rental in rental_incomes:
                scenario_count += 1
                if scenario_count % 10000 == 0:
                    print(f"Processing scenario {scenario_count:,}/{total_scenarios:,}")
                
                rental_surplus, rental_cash = analyzer.calculate_rental_strategy(price, rate, rental)
                sell_surplus, sell_cash = analyzer.calculate_sell_strategy(price, rate)
                
                rental_advantage = rental_surplus - sell_surplus
                
                if rental_advantage > 0:
                    rental_wins += 1
                
                if rental_advantage > best_rental_advantage:
                    best_rental_advantage = rental_advantage
                    best_rental_scenario = {
                        'price': price,
                        'rate': rate,
                        'rental': rental,
                        'rental_surplus': rental_surplus,
                        'sell_surplus': sell_surplus,
                        'advantage': rental_advantage
                    }
                
                results.append({
                    'home_price': price,
                    'interest_rate': rate,
                    'rental_income': rental,
                    'rental_monthly_excess': rental_surplus,
                    'sell_monthly_excess': sell_surplus,
                    'rental_remaining_cash': rental_cash,
                    'sell_remaining_cash': sell_cash,
                    'rental_advantage': rental_advantage
                })
    
    df = pd.DataFrame(results)

    # Add rental traffic light based on rental advantage thresholds
    # Green: advantage >= -300; Yellow: -600 <= advantage < -300; else Red
    conditions = [
        df['rental_advantage'] >= -300,
        (df['rental_advantage'] >= -600) & (df['rental_advantage'] < -300),
    ]
    choices = ['Green', 'Yellow']
    df['rental_traffic_light'] = np.select(conditions, choices, default='Red')
    
    # Display results
    print("\n" + "=" * 50)
    print("BEST SCENARIO FOR RENTAL STRATEGY")
    print("=" * 50)
    if best_rental_scenario:
        print(f"Home Price: ${best_rental_scenario['price']:,}")
        print(f"Interest Rate: {best_rental_scenario['rate']:.2f}%")
        print(f"Rental Income: ${best_rental_scenario['rental']:,}")
        print(f"Rental Monthly Surplus: ${best_rental_scenario['rental_surplus']:,.0f}")
        print(f"Sell Monthly Surplus: ${best_rental_scenario['sell_surplus']:,.0f}")
        print(f"Rental Advantage: ${best_rental_scenario['advantage']:,.0f}/month")
        
        if best_rental_scenario['advantage'] > 0:
            print(f"\n✅ RENTAL STRATEGY WINS in this scenario!")
            print(f"Annual advantage: ${best_rental_scenario['advantage'] * 12:,.0f}")
        else:
            print(f"\n❌ Sell strategy still better by ${-best_rental_scenario['advantage']:,.0f}/month")
    print("=" * 50)
    
    # Show a sample detailed calculation for verification
    print("\n" + "=" * 50)
    print("SAMPLE CALCULATION VERIFICATION")
    print("(Best case: $650k @ 5.0% with $5,250 rental)")
    print("=" * 50)
    
    # Recalculate for transparency
    heloc_pmt = analyzer.calculate_heloc_payment(30000, 9.0)
    base = 9434 - 2490 - 390 - 360 - heloc_pmt
    
    print("\nRENTAL STRATEGY:")
    print(f"  Base expenses: ${base:,.0f}")
    print(f"  + Current PITI: ${2490:,.0f}")
    print(f"  + Current operating: ${390:,.0f}")
    print(f"  + Current utilities: ${360:,.0f}")
    print(f"  + HELOC: $0 (paid off)")
    rental_down = 353000 - 30000
    rental_loan = 650000 - rental_down
    rental_pi = analyzer.calculate_mortgage_payment(rental_loan, 5.0)
    print(f"  + New mortgage ({rental_loan:,} @ 5%): ${rental_pi:,.0f}")
    print(f"  + New prop tax: ${650000 * 0.018 / 12:,.0f}")
    print(f"  + New insurance: ${8000/12:,.0f}")
    print(f"  + New operating: ${390:,.0f}")
    print(f"  + New utilities: ${400:,.0f}")
    rental_exp = base + 2490 + 390 + 360 + rental_pi + 650000*0.018/12 + 8000/12 + 390 + 400
    print(f"  = Total expenses: ${rental_exp:,.0f}")
    print(f"  Income: $12,000 + $5,250 = ${17250:,.0f}")
    print(f"  Surplus: ${17250 - rental_exp:,.0f}")
    
    print("\nSELL STRATEGY:")
    print(f"  Base expenses: ${base:,.0f}")
    sell_proceeds = 700000 * 0.93 - 330000 - 30000
    sell_cash = sell_proceeds + 353000
    sell_down = min(sell_cash, 650000)
    sell_loan = max(0, 650000 - sell_down)
    if sell_loan > 0:
        sell_pi = analyzer.calculate_mortgage_payment(sell_loan, 5.0)
    else:
        sell_pi = 0
    print(f"  + New mortgage ({sell_loan:,} @ 5%): ${sell_pi:,.0f}")
    print(f"  + New prop tax: ${650000 * 0.018 / 12:,.0f}")
    print(f"  + New insurance: ${8000/12:,.0f}")
    print(f"  + New operating: ${390:,.0f}")
    print(f"  + New utilities: ${400:,.0f}")
    sell_exp = base + sell_pi + 650000*0.018/12 + 8000/12 + 390 + 400
    print(f"  = Total expenses: ${sell_exp:,.0f}")
    print(f"  Income: ${12000:,.0f}")
    print(f"  Surplus: ${12000 - sell_exp:,.0f}")
    print("=" * 50)
    
    return df

def main():
    parser = argparse.ArgumentParser(description='Generate corrected real estate strategy analysis matrix')
    parser.add_argument('--output', '-o', default='analysis_matrix_final.csv', 
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
        print(f"\n" + "=" * 50)
        print("SUMMARY STATISTICS")
        print("=" * 50)
        print(f"Total scenarios analyzed: {len(df):,}")
        
        print(f"\nRental Strategy Monthly Surplus:")
        print(f"  Min: ${df['rental_monthly_excess'].min():,.0f}")
        print(f"  Max: ${df['rental_monthly_excess'].max():,.0f}")
        print(f"  Mean: ${df['rental_monthly_excess'].mean():,.0f}")
        
        print(f"\nSell Strategy Monthly Surplus:")
        print(f"  Min: ${df['sell_monthly_excess'].min():,.0f}")
        print(f"  Max: ${df['sell_monthly_excess'].max():,.0f}")
        print(f"  Mean: ${df['sell_monthly_excess'].mean():,.0f}")
        
        print(f"\nRental Advantage (Rental - Sell):")
        print(f"  Min: ${df['rental_advantage'].min():,.0f}")
        print(f"  Max: ${df['rental_advantage'].max():,.0f}")
        print(f"  Mean: ${df['rental_advantage'].mean():,.0f}")
        
        rental_preferred = (df['rental_advantage'] > 0).sum()
        sell_preferred = (df['rental_advantage'] <= 0).sum()
        
        print(f"\n📊 Strategy Preference:")
        print(f"  Rental preferred: {rental_preferred:,} scenarios ({rental_preferred/len(df)*100:.1f}%)")
        print(f"  Sell preferred: {sell_preferred:,} scenarios ({sell_preferred/len(df)*100:.1f}%)")
        
        if rental_preferred > 0:
            print(f"\n✅ Found {rental_preferred:,} scenarios where rental strategy wins!")
            # Show a few examples where rental wins
            rental_wins = df[df['rental_advantage'] > 0].nlargest(5, 'rental_advantage')
            print("\nTop 5 rental-favorable scenarios:")
            for _, row in rental_wins.iterrows():
                print(f"  ${row['home_price']:,.0f} @ {row['interest_rate']:.2f}% with ${row['rental_income']:,.0f} rent = +${row['rental_advantage']:,.0f}/mo")
        print("=" * 50)

if __name__ == "__main__":
    main()
