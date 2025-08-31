#!/usr/bin/env python3

# Debug script to trace rental calculation step by step
import json

def calculate_monthly_payment(principal: float, rate: float, years: int = 30) -> float:
    """Calculate monthly payment for a loan"""
    if principal <= 0:
        return 0
    monthly_rate = rate / 100 / 12
    num_payments = years * 12
    if monthly_rate == 0:
        return principal / num_payments
    return (principal * monthly_rate * (1 + monthly_rate)**num_payments) / \
           ((1 + monthly_rate)**num_payments - 1)

# Input parameters from your command
new_home_price = 865000
inheritance = 353000  # total-liquid-cash
bonus_cash = 30000
rental_income = 5000
property_tax = 25000
insurance = 10000
interest_rate = 6.13
current_home_operating_costs = 390
liens_json = '[{"balance": 330000, "rate": 2.875, "type": "mortgage", "monthly_payment": 2490}, {"balance": 23000, "rate": 9.0, "type": "heloc", "monthly_payment": 317}]'
liens = json.loads(liens_json)
monthly_income = 12000
total_monthly_expenses = 9434
current_surplus = monthly_income - total_monthly_expenses

print("=== RENTAL STRATEGY CALCULATION DEBUG ===")
print(f"Starting current surplus: ${current_surplus:,.2f}")
print()

# Step 1: Debt elimination
print("Step 1: Debt Elimination")
print(f"Initial inheritance: ${inheritance:,.2f}")
remaining_liens = []
available_cash = inheritance

# Pay off HELOC (9% > 6% threshold)
heloc = next((lien for lien in liens if lien['rate'] > 6.0), None)
if heloc:
    print(f"Paying off HELOC: ${heloc['balance']:,.2f} at {heloc['rate']}%")
    available_cash -= heloc['balance']
    print(f"Remaining cash after HELOC payoff: ${available_cash:,.2f}")
    
    # Keep mortgage (2.875% < 6% threshold)
    remaining_liens = [lien for lien in liens if lien['rate'] <= 6.0]
else:
    remaining_liens = liens

available_cash += bonus_cash
print(f"Available cash after adding bonus: ${available_cash:,.2f}")
print()

# Step 2: Calculate remaining debt payments
print("Step 2: Remaining Debt Payments")
total_remaining_debt_payment = 0
for lien in remaining_liens:
    payment = lien.get('monthly_payment', calculate_monthly_payment(lien['balance'], lien['rate']))
    total_remaining_debt_payment += payment
    print(f"  {lien['type']}: ${lien['balance']:,.2f} at {lien['rate']}% = ${payment:,.2f}/month")

print(f"Total remaining debt payment: ${total_remaining_debt_payment:,.2f}")
print()

# Step 3: New home purchase
print("Step 3: New Home Purchase")
min_down_payment = new_home_price * 0.03
down_payment = max(min_down_payment, available_cash)
if down_payment > new_home_price:
    down_payment = new_home_price

new_mortgage_amount = max(0, new_home_price - down_payment)
new_mortgage_payment = calculate_monthly_payment(new_mortgage_amount, interest_rate)

print(f"Down payment: ${down_payment:,.2f}")
print(f"New mortgage amount: ${new_mortgage_amount:,.2f}")
print(f"New mortgage payment: ${new_mortgage_payment:,.2f}")
print()

# Step 4: Monthly costs
print("Step 4: Monthly Costs")
monthly_property_tax = property_tax / 12
monthly_insurance = insurance / 12
new_home_piti = new_mortgage_payment + monthly_property_tax + monthly_insurance

print(f"New mortgage payment: ${new_mortgage_payment:,.2f}")
print(f"Property tax (monthly): ${monthly_property_tax:,.2f}")
print(f"Insurance (monthly): ${monthly_insurance:,.2f}")
print(f"New home PITI: ${new_home_piti:,.2f}")
print()

# Step 5: Current home costs and income
print("Step 5: Current Home Impact")
current_mortgage_payment = 0  # Not provided, defaults to 0
total_current_debt_payment = sum(lien.get('monthly_payment', calculate_monthly_payment(lien['balance'], lien['rate'])) 
                               for lien in liens)

print(f"Current home operating costs: ${current_home_operating_costs:,.2f}")
print(f"Rental income: ${rental_income:,.2f}")
print(f"Total current debt payment (before payoff): ${total_current_debt_payment:,.2f}")
print(f"Current mortgage payment: ${current_mortgage_payment:,.2f}")
print()

# Step 6: Net calculation - THIS IS WHERE THE BUG LIKELY IS
print("Step 6: Net Monthly Impact Calculation")
debt_payment_savings = total_current_debt_payment - total_remaining_debt_payment
print(f"Debt payment savings: ${debt_payment_savings:,.2f}")

net_new_housing_cost = new_home_piti + total_remaining_debt_payment + current_home_operating_costs - rental_income
print(f"Net new housing cost: ${new_home_piti:,.2f} + ${total_remaining_debt_payment:,.2f} + ${current_home_operating_costs:,.2f} - ${rental_income:,.2f} = ${net_new_housing_cost:,.2f}")

net_monthly_impact = net_new_housing_cost - current_mortgage_payment
print(f"Net monthly impact: ${net_new_housing_cost:,.2f} - ${current_mortgage_payment:,.2f} = ${net_monthly_impact:,.2f}")

new_monthly_surplus = current_surplus - net_monthly_impact
print(f"New monthly surplus: ${current_surplus:,.2f} - ${net_monthly_impact:,.2f} = ${new_monthly_surplus:,.2f}")
print()

print("=== POTENTIAL ISSUE ANALYSIS ===")
print("The calculation seems to be:")
print("1. Adding ALL new costs (PITI + remaining debt + operating costs)")
print("2. Subtracting rental income")
print("3. But not properly accounting for the fact that current debt payments")
print("   are already built into the current surplus calculation")
print()
print("Manual calculation approach might be:")
print(f"Current surplus: ${current_surplus:,.2f}")
print(f"+ Rental income: ${rental_income:,.2f}")
print(f"+ Debt payment savings: ${debt_payment_savings:,.2f}")
print(f"- New home PITI: ${new_home_piti:,.2f}")
print(f"- Current home operating: ${current_home_operating_costs:,.2f}")
print()

manual_surplus = current_surplus + rental_income + debt_payment_savings - new_home_piti - current_home_operating_costs
print(f"Manual calculation result: ${manual_surplus:,.2f}")