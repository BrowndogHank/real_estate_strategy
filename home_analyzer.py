#!/usr/bin/env python3
"""
Real Estate Purchase Strategy Analysis Tool
Analyzes rental vs sell strategies for home purchases with comprehensive debt handling
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List
import pandas as pd
import openpyxl
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from tabulate import tabulate

class RealEstateAnalyzer:
    def __init__(self, monthly_income: float = None, total_monthly_expenses: float = None, excel_file: str = None):
        self.console = Console()
        self.excel_file = excel_file
        self.current_finances = {}
        self.use_parameters = monthly_income is not None and total_monthly_expenses is not None
        if self.use_parameters:
            self.current_finances = {
                'monthly_income': monthly_income,
                'monthly_expenses': total_monthly_expenses,
                'monthly_surplus': monthly_income - total_monthly_expenses,
                'expense_breakdown': {}
            }
        
    def load_financial_data(self) -> Dict[str, Any]:
        """Load baseline financial data from Excel file or use provided parameters"""
        if self.use_parameters:
            return self.current_finances
            
        if not self.excel_file:
            self.console.print(f"[red]Error: Either provide monthly income/expenses parameters or specify an Excel file[/red]")
            sys.exit(1)
            
        try:
            # Load Sheet1 for main financial data
            df1 = pd.read_excel(self.excel_file, sheet_name='Sheet1', header=None)
            
            # Extract income from row 2 (index 1), columns D, E, F, G (indices 3, 4, 5, 6)
            income_data = df1.iloc[1, 3:7].dropna()
            total_monthly_income = income_data.sum()
            
            # Extract expenses from column B (index 1)
            expenses = df1.iloc[:, 1].dropna()
            expense_labels = df1.iloc[:, 0].dropna()
            
            # Create expense dictionary - filter out non-expense items
            expense_dict = {}
            total_expenses = 0
            
            # Define exclusions for items that aren't monthly expenses
            exclude_keywords = ['savings', 'total', 'after bills', 'current principle and intrest', 
                              'current taxes and insurance', 'income']
            
            for i, expense in enumerate(expenses):
                if isinstance(expense, (int, float)) and not pd.isna(expense):
                    if i < len(expense_labels):
                        label = str(expense_labels.iloc[i]).lower()
                        original_label = str(expense_labels.iloc[i])
                        
                        # Skip items that aren't actual monthly expenses
                        if any(keyword in label for keyword in exclude_keywords):
                            continue
                            
                        # Skip extremely large values that are likely data entry errors
                        if expense > 5000:  # No single monthly expense should be over $5000
                            continue
                            
                        expense_dict[original_label] = expense
                        total_expenses += expense
            
            # Load Sheet2 for additional personal expenses
            try:
                df2 = pd.read_excel(self.excel_file, sheet_name='Sheet2', header=None)
                sheet2_expenses = df2.iloc[:, 1].dropna()
                sheet2_labels = df2.iloc[:, 0].dropna()
                
                for i, expense in enumerate(sheet2_expenses):
                    if isinstance(expense, (int, float)) and not pd.isna(expense):
                        if i < len(sheet2_labels):
                            label = f"Personal_{sheet2_labels.iloc[i]}"
                            expense_dict[label] = expense
                            total_expenses += expense
            except:
                pass  # Sheet2 might not exist or be accessible
            
            self.current_finances = {
                'monthly_income': total_monthly_income,
                'monthly_expenses': total_expenses,
                'monthly_surplus': total_monthly_income - total_expenses,
                'expense_breakdown': expense_dict
            }
            
            # Auto-detect current mortgage payment
            current_mortgage_payment = 0
            for expense_name, amount in expense_dict.items():
                if any(keyword in expense_name.lower() for keyword in ['mortgage', 'home loan', 'principal', 'interest']):
                    current_mortgage_payment += amount
            
            self.current_finances['current_mortgage_payment'] = current_mortgage_payment
            
            return self.current_finances
            
        except Exception as e:
            self.console.print(f"[red]Error loading Excel file: {e}[/red]")
            sys.exit(1)
    
    def parse_liens(self, liens_json: str) -> List[Dict]:
        """Parse liens from JSON string"""
        try:
            return json.loads(liens_json)
        except json.JSONDecodeError:
            self.console.print(f"[red]Error parsing liens JSON: {liens_json}[/red]")
            return []
    
    def calculate_monthly_payment(self, principal: float, rate: float, years: int = 30) -> float:
        """Calculate monthly payment for a loan"""
        if principal <= 0:
            return 0
        monthly_rate = rate / 100 / 12
        num_payments = years * 12
        if monthly_rate == 0:
            return principal / num_payments
        return (principal * monthly_rate * (1 + monthly_rate)**num_payments) / \
               ((1 + monthly_rate)**num_payments - 1)
    
    def eliminate_high_rate_debt(self, liens: List[Dict], inheritance: float, 
                                high_rate_threshold: float) -> Tuple[List[Dict], float]:
        """Pay off high-rate debt first, return remaining liens and cash"""
        remaining_cash = inheritance
        remaining_liens = []
        eliminated_debt = []
        
        # Sort liens by rate (highest first)
        liens_by_rate = sorted(liens, key=lambda x: x['rate'], reverse=True)
        
        for lien in liens_by_rate:
            if lien['rate'] > high_rate_threshold and remaining_cash > 0:
                if remaining_cash >= lien['balance']:
                    # Pay off completely
                    remaining_cash -= lien['balance']
                    eliminated_debt.append(lien)
                    self.console.print(f"[green]Paying off {lien['type']} (${lien['balance']:,.2f} at {lien['rate']:.3f}%)[/green]")
                else:
                    # Partial payment
                    paid_amount = remaining_cash
                    remaining_balance = lien['balance'] - paid_amount
                    remaining_cash = 0
                    updated_lien = lien.copy()
                    updated_lien['balance'] = remaining_balance
                    # Recalculate monthly payment for remaining balance
                    if 'monthly_payment' not in updated_lien:
                        updated_lien['monthly_payment'] = self.calculate_monthly_payment(
                            remaining_balance, lien['rate']
                        )
                    else:
                        # Proportionally reduce payment
                        payment_ratio = remaining_balance / lien['balance']
                        updated_lien['monthly_payment'] = lien['monthly_payment'] * payment_ratio
                    remaining_liens.append(updated_lien)
                    self.console.print(f"[yellow]Partially paying down {lien['type']} by ${paid_amount:,.2f}[/yellow]")
            else:
                remaining_liens.append(lien)
        
        return remaining_liens, remaining_cash
    
    def calculate_rental_strategy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate financial impact of rental strategy (keep current home)"""
        # Extract parameters
        new_home_price = params['new_home_price']
        inheritance = params['inheritance']
        bonus_cash = params.get('bonus_cash', 0)
        rental_income = params['rental_income']
        property_tax_annual = params['property_tax']
        insurance_annual = params['insurance']
        interest_rate = params.get('interest_rate', 6.13)
        liens = params.get('liens', [])
        current_mortgage_payment = params.get('current_mortgage_payment', 0)
        current_home_operating_costs = params.get('current_home_operating_costs', 0)
        pay_off_high_rate_first = params.get('pay_off_high_rate_first', True)
        high_rate_threshold = params.get('high_rate_threshold', 6.0)
        
        # Handle debt elimination strategy
        remaining_liens = liens.copy()
        available_cash = inheritance
        
        if pay_off_high_rate_first:
            remaining_liens, available_cash = self.eliminate_high_rate_debt(
                liens, inheritance, high_rate_threshold
            )
        
        available_cash += bonus_cash  # Add bonus cash after debt payoff
        
        # Calculate remaining monthly debt payments
        total_remaining_debt_payment = 0
        for lien in remaining_liens:
            if 'monthly_payment' in lien:
                total_remaining_debt_payment += lien['monthly_payment']
            else:
                total_remaining_debt_payment += self.calculate_monthly_payment(
                    lien['balance'], lien['rate']
                )
        
        # New home purchase
        min_down_payment = new_home_price * 0.03  # 3% minimum
        down_payment = max(min_down_payment, available_cash)
        if down_payment > new_home_price:
            down_payment = new_home_price  # 100% cash purchase
        
        new_mortgage_amount = max(0, new_home_price - down_payment)
        new_mortgage_payment = self.calculate_monthly_payment(new_mortgage_amount, interest_rate)
        
        # Monthly costs
        monthly_property_tax = property_tax_annual / 12
        monthly_insurance = insurance_annual / 12
        new_home_piti = new_mortgage_payment + monthly_property_tax + monthly_insurance
        
        # Auto-detect current home operating costs from Excel if not provided
        if current_home_operating_costs == 0 and self.current_finances.get('expense_breakdown'):
            for expense, amount in self.current_finances['expense_breakdown'].items():
                if any(keyword in expense.lower() for keyword in 
                      ['lawn', 'pool', 'maintenance', 'fpl', 'cleaning', 'utilities']):
                    current_home_operating_costs += amount
        
        # Auto-detect current mortgage payment if not provided
        if current_mortgage_payment == 0:
            current_mortgage_payment = self.current_finances.get('current_mortgage_payment', 0)
        
        # Calculate incremental impact on current budget
        # The current surplus already includes current debt payments and mortgage
        # We need to calculate the net change from current state
        
        total_current_debt_payment = sum(lien.get('monthly_payment', self.calculate_monthly_payment(lien['balance'], lien['rate'])) 
                                       for lien in liens)
        
        # Calculate the net monthly impact by considering:
        # 1. Current debt payments are already in the current budget (subtract them as they're current outflow)
        # 2. Remaining debt payments are new ongoing costs (add them as new outflow)  
        # 3. New home costs are additional (add them as new outflow)
        # 4. Rental income is new income (subtract as it reduces net cost)
        # 5. Current home operating costs continue (add as ongoing cost, though they're already in current budget)
        
        # The correct approach: Start with current surplus, then add income and subtract new/continuing costs
        # Current surplus already has: current_debt_payments + current_mortgage_payment + operating_costs built in
        # So we need: current_surplus + rental_income - new_home_piti - (remaining_debt - current_debt) - (0 if operating costs already in surplus)
        
        # If current_home_operating_costs are provided explicitly, they may not be in the current_surplus
        # But current debt payments ARE in the current_surplus, so we need to handle the transition
        
        net_monthly_impact = (new_home_piti + 
                             total_remaining_debt_payment +
                             current_home_operating_costs -
                             rental_income -
                             (current_mortgage_payment + total_current_debt_payment))
        
        # Apply the incremental change to current surplus
        new_monthly_surplus = self.current_finances['monthly_surplus'] - net_monthly_impact
        
        # Calculate debt payment savings for reporting
        debt_payment_savings = total_current_debt_payment - total_remaining_debt_payment
        
        # Calculate net new housing cost for reporting purposes (this is what the new costs would be without considering current payments)
        net_new_housing_cost = new_home_piti + total_remaining_debt_payment + current_home_operating_costs - rental_income
        
        return {
            'strategy': 'Rental Strategy',
            'inheritance_used': inheritance - available_cash + bonus_cash,
            'down_payment': down_payment,
            'new_mortgage_amount': new_mortgage_amount,
            'new_mortgage_payment': new_mortgage_payment,
            'new_property_tax': monthly_property_tax,
            'new_insurance': monthly_insurance,
            'new_home_piti': new_home_piti,
            'remaining_debt_payment': total_remaining_debt_payment,
            'current_mortgage_payment': current_mortgage_payment,
            'current_home_operating_costs': current_home_operating_costs,
            'rental_income': rental_income,
            'net_new_housing_cost': net_new_housing_cost,
            'net_monthly_impact': net_monthly_impact,
            'new_monthly_surplus': new_monthly_surplus,
            'annual_surplus': new_monthly_surplus * 12,
            'remaining_liens': remaining_liens,
            'debt_eliminated': len(liens) - len(remaining_liens),
            'debt_payment_savings': debt_payment_savings,
            'total_current_debt_payment': total_current_debt_payment,
            'loan_to_value': (new_mortgage_amount / new_home_price * 100) if new_home_price > 0 else 0
        }
    
    def calculate_sell_strategy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate financial impact of sell strategy (sell current home)"""
        # Extract parameters
        new_home_price = params['new_home_price']
        total_liquid_cash = params['inheritance']  # This is total liquid cash (inheritance + savings combined)
        bonus_cash = params.get('bonus_cash', 0)
        sale_price = params['sale_price']
        property_tax_annual = params['property_tax']
        insurance_annual = params['insurance']
        interest_rate = params.get('interest_rate', 6.13)
        liens = params.get('liens', [])
        current_mortgage_payment = params.get('current_mortgage_payment', 0)
        current_home_operating_costs = params.get('current_home_operating_costs', 0)
        selling_cost_percentage = params.get('selling_cost_percentage', 7.0) / 100
        
        # Calculate sale proceeds
        total_lien_balance = sum(lien['balance'] for lien in liens)
        selling_costs = sale_price * selling_cost_percentage
        net_proceeds = sale_price - total_lien_balance - selling_costs
        
        # Total available cash: net proceeds + all liquid cash + bonus cash
        total_available_cash = net_proceeds + total_liquid_cash + bonus_cash
        
        # Calculate down payment and new mortgage
        down_payment = min(total_available_cash, new_home_price)
        new_mortgage_amount = max(0, new_home_price - down_payment)
        new_mortgage_payment = self.calculate_monthly_payment(new_mortgage_amount, interest_rate)
        
        # Monthly costs
        monthly_property_tax = property_tax_annual / 12
        monthly_insurance = insurance_annual / 12
        new_home_piti = new_mortgage_payment + monthly_property_tax + monthly_insurance
        
        # Auto-detect costs that will be eliminated
        eliminated_operating_costs = current_home_operating_costs
        if eliminated_operating_costs == 0 and self.current_finances.get('expense_breakdown'):
            for expense, amount in self.current_finances['expense_breakdown'].items():
                if any(keyword in expense.lower() for keyword in 
                      ['lawn', 'pool', 'maintenance', 'fpl', 'cleaning', 'utilities']):
                    eliminated_operating_costs += amount
        
        # Auto-detect current mortgage payment if not provided
        if current_mortgage_payment == 0:
            current_mortgage_payment = self.current_finances.get('current_mortgage_payment', 0)
        
        # Calculate total current debt payments that will be eliminated
        total_current_debt_payments = sum(
            lien.get('monthly_payment', self.calculate_monthly_payment(lien['balance'], lien['rate'])) 
            for lien in liens
        )
        
        # Calculate net impact: all eliminated expenses minus new home PITI
        # Eliminated: current mortgage + current debt payments + operating costs
        eliminated_expenses = current_mortgage_payment + total_current_debt_payments + eliminated_operating_costs
        
        # Net impact: positive means additional cost, negative means savings
        net_monthly_impact = new_home_piti - eliminated_expenses
        new_monthly_surplus = self.current_finances['monthly_surplus'] - net_monthly_impact
        
        return {
            'strategy': 'Sell Strategy',
            'sale_price': sale_price,
            'total_lien_balance': total_lien_balance,
            'selling_costs': selling_costs,
            'net_proceeds': net_proceeds,
            'total_available_cash': total_available_cash,
            'down_payment': down_payment,
            'new_mortgage_amount': new_mortgage_amount,
            'new_mortgage_payment': new_mortgage_payment,
            'new_property_tax': monthly_property_tax,
            'new_insurance': monthly_insurance,
            'new_home_piti': new_home_piti,
            'eliminated_mortgage_payment': current_mortgage_payment,
            'eliminated_debt_payments': total_current_debt_payments,
            'eliminated_operating_costs': eliminated_operating_costs,
            'eliminated_expenses': eliminated_expenses,
            'net_monthly_impact': net_monthly_impact,
            'new_monthly_surplus': new_monthly_surplus,
            'annual_surplus': new_monthly_surplus * 12,
            'loan_to_value': (new_mortgage_amount / new_home_price * 100) if new_home_price > 0 else 0
        }
    
    def calculate_risk_scenarios(self, rental_results: Dict, sell_results: Dict, params: Dict) -> Dict:
        """Calculate comprehensive risk scenarios for both strategies"""
        scenarios = {}
        rental_income = params['rental_income']
        
        # Enhanced rental strategy risks
        scenarios['rental_risks'] = {
            'vacancy_1_month': {
                'description': '1 month vacancy per year',
                'monthly_impact': -rental_income,
                'annual_impact': -rental_income,
                'new_annual_surplus': rental_results['annual_surplus'] - rental_income
            },
            'vacancy_3_months': {
                'description': '3 months vacancy per year',
                'monthly_impact': -(rental_income * 3 / 12),
                'annual_impact': -(rental_income * 3),
                'new_annual_surplus': rental_results['annual_surplus'] - (rental_income * 3)
            },
            'vacancy_6_months': {
                'description': '6 months vacancy per year',
                'monthly_impact': -(rental_income * 6 / 12),
                'annual_impact': -(rental_income * 6),
                'new_annual_surplus': rental_results['annual_surplus'] - (rental_income * 6)
            },
            'reduced_rent_10': {
                'description': '10% rent reduction',
                'monthly_impact': -(rental_income * 0.1),
                'annual_impact': -(rental_income * 0.1 * 12),
                'new_annual_surplus': rental_results['annual_surplus'] - (rental_income * 0.1 * 12)
            },
            'reduced_rent_20': {
                'description': '20% rent reduction',
                'monthly_impact': -(rental_income * 0.2),
                'annual_impact': -(rental_income * 0.2 * 12),
                'new_annual_surplus': rental_results['annual_surplus'] - (rental_income * 0.2 * 12)
            },
            'major_repair_5k': {
                'description': '$5,000 major repair',
                'annual_impact': -5000,
                'new_annual_surplus': rental_results['annual_surplus'] - 5000
            },
            'major_repair_10k': {
                'description': '$10,000 major repair',
                'annual_impact': -10000,
                'new_annual_surplus': rental_results['annual_surplus'] - 10000
            },
            'major_repair_15k': {
                'description': '$15,000 major repair',
                'annual_impact': -15000,
                'new_annual_surplus': rental_results['annual_surplus'] - 15000
            },
            'property_mgmt_8': {
                'description': '8% property management fee',
                'monthly_impact': -(rental_income * 0.08),
                'annual_impact': -(rental_income * 0.08 * 12),
                'new_annual_surplus': rental_results['annual_surplus'] - (rental_income * 0.08 * 12)
            },
            'property_mgmt_12': {
                'description': '12% property management fee',
                'monthly_impact': -(rental_income * 0.12),
                'annual_impact': -(rental_income * 0.12 * 12),
                'new_annual_surplus': rental_results['annual_surplus'] - (rental_income * 0.12 * 12)
            },
            'tenant_damage': {
                'description': 'Tenant damage/eviction ($3,000)',
                'annual_impact': -3000,
                'new_annual_surplus': rental_results['annual_surplus'] - 3000
            }
        }
        
        # Enhanced sell strategy risks
        scenarios['sell_risks'] = {
            'lower_sale_25k': {
                'description': '$25,000 lower sale price',
                'impact_description': 'Higher mortgage payment',
                'additional_mortgage': 25000,
                'additional_monthly_payment': self._calculate_payment_increase(25000, params.get('interest_rate', 6.13)),
                'annual_impact': -(self._calculate_payment_increase(25000, params.get('interest_rate', 6.13)) * 12),
                'new_annual_surplus': sell_results['annual_surplus'] - (self._calculate_payment_increase(25000, params.get('interest_rate', 6.13)) * 12)
            },
            'lower_sale_50k': {
                'description': '$50,000 lower sale price',
                'impact_description': 'Higher mortgage payment',
                'additional_mortgage': 50000,
                'additional_monthly_payment': self._calculate_payment_increase(50000, params.get('interest_rate', 6.13)),
                'annual_impact': -(self._calculate_payment_increase(50000, params.get('interest_rate', 6.13)) * 12),
                'new_annual_surplus': sell_results['annual_surplus'] - (self._calculate_payment_increase(50000, params.get('interest_rate', 6.13)) * 12)
            },
            'lower_sale_100k': {
                'description': '$100,000 lower sale price',
                'impact_description': 'Higher mortgage payment',
                'additional_mortgage': 100000,
                'additional_monthly_payment': self._calculate_payment_increase(100000, params.get('interest_rate', 6.13)),
                'annual_impact': -(self._calculate_payment_increase(100000, params.get('interest_rate', 6.13)) * 12),
                'new_annual_surplus': sell_results['annual_surplus'] - (self._calculate_payment_increase(100000, params.get('interest_rate', 6.13)) * 12)
            },
            'higher_selling_costs_10': {
                'description': '10% selling costs (vs 7% baseline)',
                'additional_cost': params['sale_price'] * 0.03,  # 3% additional
                'annual_impact': -(params['sale_price'] * 0.03),
                'impact_description': 'Reduced cash available (amortized over 10 years)',
                'new_annual_surplus': sell_results['annual_surplus'] - (params['sale_price'] * 0.03 / 10)
            },
            'market_timing': {
                'description': 'Market timing - 6 month delay',
                'impact_description': 'Additional 6 months current home costs',
                'additional_cost': (params.get('current_mortgage_payment', 0) + params.get('current_home_operating_costs', 0)) * 6,
                'annual_impact': -((params.get('current_mortgage_payment', 0) + params.get('current_home_operating_costs', 0)) * 6),
                'new_annual_surplus': sell_results['annual_surplus'] - ((params.get('current_mortgage_payment', 0) + params.get('current_home_operating_costs', 0)) * 6)
            },
            'moving_costs': {
                'description': 'Moving and transition costs',
                'additional_cost': 8000,
                'annual_impact': -8000,
                'impact_description': 'One-time cost (amortized over 5 years: $1,600/year)',
                'new_annual_surplus': sell_results['annual_surplus'] - 1600
            }
        }
        
        return scenarios
    
    def _calculate_payment_increase(self, additional_mortgage: float, interest_rate: float) -> float:
        """Calculate additional monthly payment for additional mortgage amount"""
        return self.calculate_monthly_payment(additional_mortgage, interest_rate)
    
    def validate_inputs(self, params: Dict[str, Any]) -> List[str]:
        """Validate input parameters and return list of warnings/errors"""
        warnings = []
        
        # Check if inheritance covers minimum down payment
        min_down_payment = params['new_home_price'] * 0.03
        if params['inheritance'] + params.get('bonus_cash', 0) < min_down_payment:
            warnings.append(f"WARNING: Total cash (${params['inheritance'] + params.get('bonus_cash', 0):,.2f}) may not cover minimum down payment (${min_down_payment:,.2f})")
        
        # Check rental income vs operating costs
        current_home_costs = params.get('current_home_operating_costs', 0)
        if current_home_costs > 0 and params['rental_income'] < current_home_costs * 1.5:
            warnings.append(f"WARNING: Rental income (${params['rental_income']:,.2f}) is low relative to operating costs (${current_home_costs:,.2f})")
        
        # Check debt-to-income for rental strategy
        total_debt_payment = sum(lien.get('monthly_payment', self.calculate_monthly_payment(lien['balance'], lien['rate'])) 
                               for lien in params.get('liens', []))
        new_mortgage_payment = self.calculate_monthly_payment(
            max(0, params['new_home_price'] - params['inheritance'] - params.get('bonus_cash', 0)), 
            params.get('interest_rate', 6.13)
        )
        total_housing_debt = total_debt_payment + new_mortgage_payment + params['property_tax']/12 + params['insurance']/12
        dti_ratio = (total_housing_debt / self.current_finances['monthly_income']) * 100
        
        if dti_ratio > 43:
            warnings.append(f"WARNING: Total debt-to-income ratio ({dti_ratio:.1f}%) exceeds typical lending limits (43%)")
        
        return warnings
    
    def display_current_finances(self):
        """Display current financial position from Excel data"""
        finances = self.current_finances
        
        content = f"Monthly Income: ${finances['monthly_income']:,.2f}\n"
        content += f"Monthly Expenses: ${finances['monthly_expenses']:,.2f}\n"
        content += f"Monthly Surplus: ${finances['monthly_surplus']:,.2f}\n"
        content += f"Annual Surplus: ${finances['monthly_surplus'] * 12:,.2f}"
        
        if finances.get('current_mortgage_payment', 0) > 0:
            content += f"\nCurrent Mortgage Payment: ${finances['current_mortgage_payment']:,.2f}"
        
        panel = Panel.fit(content, title="Current Financial Position", border_style="blue")
        self.console.print(panel)
    
    def display_detailed_comparison(self, rental_results: Dict, sell_results: Dict):
        """Display detailed side-by-side strategy comparison"""
        table = Table(title="Detailed Strategy Comparison")
        table.add_column("Metric", style="cyan")
        table.add_column("Rental Strategy", style="green")
        table.add_column("Sell Strategy", style="yellow")
        
        # Financial metrics comparison
        metrics = [
            ("🏠 New Home Purchase", "", ""),
            ("Down Payment", f"${rental_results['down_payment']:,.2f}", f"${sell_results['down_payment']:,.2f}"),
            ("New Mortgage Amount", f"${rental_results['new_mortgage_amount']:,.2f}", f"${sell_results['new_mortgage_amount']:,.2f}"),
            ("Loan-to-Value Ratio", f"{rental_results['loan_to_value']:.1f}%", f"{sell_results['loan_to_value']:.1f}%"),
            ("", "", ""),
            ("💰 Monthly Costs", "", ""),
            ("New Mortgage Payment", f"${rental_results['new_mortgage_payment']:,.2f}", f"${sell_results['new_mortgage_payment']:,.2f}"),
            ("Property Tax", f"${rental_results['new_property_tax']:,.2f}", f"${sell_results['new_property_tax']:,.2f}"),
            ("Insurance", f"${rental_results['new_insurance']:,.2f}", f"${sell_results['new_insurance']:,.2f}"),
            ("New Home PITI", f"${rental_results['new_home_piti']:,.2f}", f"${sell_results['new_home_piti']:,.2f}"),
            ("", "", ""),
            ("🏡 Current Home Impact", "", ""),
            ("Current Mortgage Payment", f"${rental_results['current_mortgage_payment']:,.2f} (continues)", f"${sell_results['eliminated_mortgage_payment']:,.2f} (eliminated)"),
            ("Current Debt Payments", f"${rental_results.get('total_current_debt_payment', 0):,.2f} → ${rental_results['remaining_debt_payment']:,.2f}", f"${sell_results.get('eliminated_debt_payments', 0):,.2f} (eliminated)"),
            ("Operating Costs", f"${rental_results['current_home_operating_costs']:,.2f} (continues)", f"${sell_results['eliminated_operating_costs']:,.2f} (eliminated)"),
            ("Rental Income", f"${rental_results['rental_income']:,.2f}", "N/A"),
            ("Debt Payment Savings", f"${rental_results.get('debt_payment_savings', 0):,.2f}", f"${sell_results.get('eliminated_debt_payments', 0):,.2f} (all eliminated)"),
            ("", "", ""),
            ("📊 Net Impact", "", ""),
            ("Net Monthly Impact", f"${rental_results['net_monthly_impact']:,.2f}", f"${sell_results['net_monthly_impact']:,.2f}"),
            ("New Monthly Surplus", f"${rental_results['new_monthly_surplus']:,.2f}", f"${sell_results['new_monthly_surplus']:,.2f}"),
            ("Annual Surplus", f"${rental_results['annual_surplus']:,.2f}", f"${sell_results['annual_surplus']:,.2f}")
        ]
        
        for metric, rental_val, sell_val in metrics:
            if metric.startswith(("🏠", "💰", "🏡", "📊")):
                table.add_row(Text(metric, style="bold"), "", "")
            elif metric == "":
                table.add_row("", "", "")
            else:
                table.add_row(metric, rental_val, sell_val)
        
        self.console.print(table)
        
        # Display debt elimination details for rental strategy
        if rental_results['debt_eliminated'] > 0:
            debt_panel = Panel.fit(
                f"Debt Elimination: {rental_results['debt_eliminated']} high-rate liens paid off\n"
                f"Remaining liens: {len(rental_results['remaining_liens'])}\n"
                f"Monthly debt payment reduced significantly",
                title="Rental Strategy - Debt Management",
                border_style="green"
            )
            self.console.print(debt_panel)
    
    def display_strategy_summary(self, rental_results: Dict, sell_results: Dict):
        """Display strategy summary comparison box"""
        rental_surplus = rental_results['new_monthly_surplus']
        sell_surplus = sell_results['new_monthly_surplus']
        difference = rental_surplus - sell_surplus
        
        if difference > 0:
            preferred = "Rental preferred"
            diff_text = f"+${difference:,.0f}/mo"
        else:
            preferred = "Sell preferred"
            diff_text = f"+${abs(difference):,.0f}/mo"
            
        summary_content = f"""Rental:  ${rental_surplus:,.0f}/mo
Sell:    ${sell_surplus:,.0f}/mo
Diff:     {diff_text}
{preferred}"""
        
        summary_panel = Panel.fit(
            summary_content,
            title="Strategy Summary",
            border_style="bright_blue"
        )
        self.console.print(summary_panel)
        
    def display_cash_flow_breakdown(self, rental_results: Dict, sell_results: Dict):
        """Display simplified cash flow breakdown focusing on key differences"""
        table = Table(title="Monthly Cash Flow Impact")
        table.add_column("Component", style="cyan")
        table.add_column("Rental Strategy", style="green")
        table.add_column("Sell Strategy", style="yellow")
        
        table.add_row("💰 NEW EXPENSES", "", "")
        table.add_row("  New Home PITI", f"${rental_results['new_home_piti']:,.2f}", f"${sell_results['new_home_piti']:,.2f}")
        table.add_row("  Remaining Debt Payments", f"${rental_results['remaining_debt_payment']:,.2f}", "$0 (all eliminated)")
        table.add_row("", "", "")
        
        table.add_row("🏠 CURRENT HOME", "", "")
        table.add_row("  Mortgage + Operating", f"${rental_results['current_mortgage_payment'] + rental_results['current_home_operating_costs']:,.2f} (continues)", f"${sell_results['eliminated_mortgage_payment'] + sell_results['eliminated_operating_costs']:,.2f} (eliminated)")
        table.add_row("  Rental Income", f"-${rental_results['rental_income']:,.2f}", "N/A")
        table.add_row("  Debt Payments", f"${rental_results.get('debt_payment_savings', 0):,.2f} (saved)", f"${sell_results.get('eliminated_debt_payments', 0):,.2f} (eliminated)")
        table.add_row("", "", "")
        
        table.add_row("📊 NET RESULT", "", "")
        table.add_row("  Monthly Impact", f"${rental_results['net_monthly_impact']:,.2f} additional cost", f"${sell_results['net_monthly_impact']:,.2f} net change")
        table.add_row("  New Monthly Surplus", f"[bold]${rental_results['new_monthly_surplus']:,.2f}[/bold]", f"[bold]${sell_results['new_monthly_surplus']:,.2f}[/bold]")
        
        self.console.print(table)
    
    def display_risk_analysis(self, scenarios: Dict):
        """Display comprehensive risk scenario analysis"""
        # Rental risks table
        rental_table = Table(title="Rental Strategy Risk Scenarios")
        rental_table.add_column("Risk Scenario", style="cyan")
        rental_table.add_column("Annual Impact", style="red")
        rental_table.add_column("New Annual Surplus", style="yellow")
        rental_table.add_column("Severity", style="magenta")
        
        for risk, data in scenarios['rental_risks'].items():
            # Determine severity based on impact
            impact = abs(data['annual_impact'])
            if impact < 5000:
                severity = "Low"
            elif impact < 15000:
                severity = "Medium"
            else:
                severity = "High"
            
            rental_table.add_row(
                data['description'],
                f"${data['annual_impact']:,.2f}",
                f"${data['new_annual_surplus']:,.2f}",
                severity
            )
        
        self.console.print(rental_table)
        self.console.print()
        
        # Sell risks table
        sell_table = Table(title="Sell Strategy Risk Scenarios")
        sell_table.add_column("Risk Scenario", style="cyan")
        sell_table.add_column("Impact Description", style="magenta")
        sell_table.add_column("Annual Impact", style="red")
        sell_table.add_column("New Annual Surplus", style="yellow")
        
        for risk, data in scenarios['sell_risks'].items():
            sell_table.add_row(
                data['description'],
                data.get('impact_description', data['description']),
                f"${data['annual_impact']:,.2f}",
                f"${data.get('new_annual_surplus', 'N/A')}"
            )
        
        self.console.print(sell_table)
    
    def generate_recommendation(self, rental_results: Dict, sell_results: Dict, scenarios: Dict) -> str:
        """Generate comprehensive recommendation based on analysis"""
        rental_surplus = rental_results['annual_surplus']
        sell_surplus = sell_results['annual_surplus']
        
        # Base recommendation
        if rental_surplus > sell_surplus:
            difference = rental_surplus - sell_surplus
            base_rec = f"RENTAL STRATEGY PREFERRED - ${difference:,.2f} better annually"
            
            # Risk analysis for rental
            worst_case_rental = min([data['new_annual_surplus'] for data in scenarios['rental_risks'].values()])
            if worst_case_rental > sell_surplus:
                risk_assessment = f"✅ Even in worst-case rental scenarios (${worst_case_rental:,.2f}), still outperforms selling"
            else:
                risk_assessment = f"⚠️ Rental worst-case scenario (${worst_case_rental:,.2f}) underperforms selling - consider risk tolerance"
        else:
            difference = sell_surplus - rental_surplus
            base_rec = f"SELL STRATEGY PREFERRED - ${difference:,.2f} better annually"
            
            # Risk analysis for sell
            risk_assessment = "✅ Selling eliminates rental property risks but locks in current market conditions"
        
        return f"{base_rec}\n\n{risk_assessment}"
    
    def export_to_markdown(self, rental_results: Dict, sell_results: Dict, 
                          scenarios: Dict, params: Dict, filename: str = "analysis_results.md"):
        """Export comprehensive results to markdown file"""
        content = f"""# Real Estate Strategy Analysis Results

## Input Parameters
- **New Home Price:** ${params['new_home_price']:,.2f}
- **Total Inheritance:** ${params['inheritance']:,.2f}
- **Bonus Cash:** ${params.get('bonus_cash', 0):,.2f}
- **Current Home Sale Price:** ${params['sale_price']:,.2f}
- **Expected Rental Income:** ${params['rental_income']:,.2f}
- **Property Tax (Annual):** ${params['property_tax']:,.2f}
- **Insurance (Annual):** ${params['insurance']:,.2f}
- **Interest Rate:** {params.get('interest_rate', 6.13):.2f}%
- **Selling Cost Percentage:** {params.get('selling_cost_percentage', 7.0):.1f}%
- **Pay Off High-Rate Debt First:** {'Yes' if params.get('pay_off_high_rate_first', True) else 'No'}
- **High-Rate Threshold:** {params.get('high_rate_threshold', 6.0):.1f}%

## Current Financial Position
- **Monthly Income:** ${self.current_finances['monthly_income']:,.2f}
- **Monthly Expenses:** ${self.current_finances['monthly_expenses']:,.2f}
- **Monthly Surplus:** ${self.current_finances['monthly_surplus']:,.2f}
- **Annual Surplus:** ${self.current_finances['monthly_surplus'] * 12:,.2f}

## Current Home Liens
"""
        if params.get('liens'):
            for i, lien in enumerate(params['liens'], 1):
                content += f"{i}. **{lien['type'].title()}:** ${lien['balance']:,.2f} at {lien['rate']:.3f}% (Monthly: ${lien.get('monthly_payment', self.calculate_monthly_payment(lien['balance'], lien['rate'])):,.2f})\n"
        else:
            content += "No liens specified\n"
        
        content += f"""
## Strategy Comparison

### 🟢 Rental Strategy Results
- **Down Payment:** ${rental_results['down_payment']:,.2f}
- **New Mortgage Amount:** ${rental_results['new_mortgage_amount']:,.2f}
- **Loan-to-Value:** {rental_results['loan_to_value']:.1f}%
- **New Mortgage Payment:** ${rental_results['new_mortgage_payment']:,.2f}
- **Property Tax (Monthly):** ${rental_results['new_property_tax']:,.2f}
- **Insurance (Monthly):** ${rental_results['new_insurance']:,.2f}
- **New Home PITI:** ${rental_results['new_home_piti']:,.2f}
- **Remaining Debt Payment:** ${rental_results['remaining_debt_payment']:,.2f}
- **Current Home Operating Costs:** ${rental_results['current_home_operating_costs']:,.2f}
- **Rental Income:** ${rental_results['rental_income']:,.2f}
- **Debt Eliminated:** {rental_results['debt_eliminated']} liens
- **Net Monthly Impact:** ${rental_results['net_monthly_impact']:,.2f}
- **New Monthly Surplus:** ${rental_results['new_monthly_surplus']:,.2f}
- **NEW ANNUAL SURPLUS:** ${rental_results['annual_surplus']:,.2f}

### 🟡 Sell Strategy Results
- **Sale Price:** ${sell_results['sale_price']:,.2f}
- **Total Lien Balance:** ${sell_results['total_lien_balance']:,.2f}
- **Selling Costs:** ${sell_results['selling_costs']:,.2f}
- **Net Proceeds:** ${sell_results['net_proceeds']:,.2f}
- **Total Available Cash:** ${sell_results['total_available_cash']:,.2f}
- **Down Payment:** ${sell_results['down_payment']:,.2f}
- **New Mortgage Amount:** ${sell_results['new_mortgage_amount']:,.2f}
- **Loan-to-Value:** {sell_results['loan_to_value']:.1f}%
- **New Mortgage Payment:** ${sell_results['new_mortgage_payment']:,.2f}
- **Property Tax (Monthly):** ${sell_results['new_property_tax']:,.2f}
- **Insurance (Monthly):** ${sell_results['new_insurance']:,.2f}
- **New Home PITI:** ${sell_results['new_home_piti']:,.2f}
- **Eliminated Expenses:** ${sell_results['eliminated_expenses']:,.2f}
- **Net Monthly Impact:** ${sell_results['net_monthly_impact']:,.2f}
- **New Monthly Surplus:** ${sell_results['new_monthly_surplus']:,.2f}
- **NEW ANNUAL SURPLUS:** ${sell_results['annual_surplus']:,.2f}

## Risk Analysis

### Rental Strategy Risks
"""
        for risk, data in scenarios['rental_risks'].items():
            content += f"- **{data['description']}:** ${data['annual_impact']:,.2f} impact → ${data['new_annual_surplus']:,.2f} annual surplus\n"
        
        content += "\n### Sell Strategy Risks\n"
        for risk, data in scenarios['sell_risks'].items():
            content += f"- **{data['description']}:** {data.get('impact_description', '')} → ${data['annual_impact']:,.2f} impact\n"
        
        content += f"\n## 🎯 Recommendation\n{self.generate_recommendation(rental_results, sell_results, scenarios)}\n"
        
        # Add 5-year and 10-year projections
        content += f"""
## Long-term Projections

### 5-Year Analysis
- **Rental Strategy 5-Year Surplus:** ${rental_results['annual_surplus'] * 5:,.2f}
- **Sell Strategy 5-Year Surplus:** ${sell_results['annual_surplus'] * 5:,.2f}
- **Difference:** ${(rental_results['annual_surplus'] - sell_results['annual_surplus']) * 5:,.2f}

### 10-Year Analysis
- **Rental Strategy 10-Year Surplus:** ${rental_results['annual_surplus'] * 10:,.2f}
- **Sell Strategy 10-Year Surplus:** ${sell_results['annual_surplus'] * 10:,.2f}
- **Difference:** ${(rental_results['annual_surplus'] - sell_results['annual_surplus']) * 10:,.2f}

*Note: These projections assume constant income, expenses, and rental rates. Actual results may vary due to inflation, market changes, and property appreciation.*
"""
        
        with open(filename, 'w') as f:
            f.write(content)
        
        self.console.print(f"[green]Comprehensive analysis exported to {filename}[/green]")

def main():
    parser = argparse.ArgumentParser(description="Comprehensive Real Estate Purchase Strategy Analysis")
    
    # Core parameters
    parser.add_argument("--new-home-price", type=float, required=True,
                       help="New home purchase price")
    parser.add_argument("--total-liquid-cash", dest="inheritance", type=float, required=True,
                       help="Total inheritance/liquid cash available")
    parser.add_argument("--sale-price", type=float, required=True,
                       help="Current home estimated sale price")
    parser.add_argument("--rental-income", type=float, required=True,
                       help="Expected monthly rental income")
    parser.add_argument("--property-tax", type=float, required=True,
                       help="New home annual property tax")
    parser.add_argument("--insurance", type=float, required=True,
                       help="New home annual insurance")
    
    # New financial parameters
    parser.add_argument("--current-home-liens", type=str,
                       help='JSON string of current liens: [{"balance": 330000, "rate": 2.875, "type": "mortgage"}, {"balance": 23000, "rate": 9.0, "type": "heloc"}]')
    parser.add_argument("--current-mortgage-payment", type=float, default=0,
                       help="Current total monthly mortgage payment (PITI)")
    parser.add_argument("--selling-cost-percentage", type=float, default=7.0,
                       help="Selling cost percentage (default: 7%)")
    parser.add_argument("--bonus-cash", type=float, default=0,
                       help="Additional cash (e.g., March 2026 bonus)")
    parser.add_argument("--liquid-savings", type=float, default=0,
                       help="Additional liquid savings available for sell strategy")
    
    # Strategy options
    parser.add_argument("--pay-off-high-rate-first", action="store_true", default=True,
                       help="Pay off highest rate liens first with inheritance")
    parser.add_argument("--high-rate-threshold", type=float, default=6.0,
                       help="Liens above this rate get paid off first (default: 6.0%)")
    
    # Optional parameters
    parser.add_argument("--interest-rate", type=float, default=6.13,
                       help="Mortgage interest rate (default: 6.13%)")
    parser.add_argument("--monthly-income", type=float,
                       help="Current monthly income (alternative to Excel file)")
    parser.add_argument("--total-monthly-expenses", type=float,
                       help="Current total monthly expenses (alternative to Excel file)")
    parser.add_argument("--current-home-operating-costs", type=float, default=0,
                       help="Current home monthly operating costs (lawn, maintenance, utilities, etc.)")
    parser.add_argument("--excel-file", type=str,
                       help="Excel file with baseline financial data (alternative to manual input)")
    parser.add_argument("--export", type=str,
                       help="Export results to markdown file")
    
    args = parser.parse_args()
    
    # Validate inputs
    use_manual_input = args.monthly_income is not None and args.total_monthly_expenses is not None
    use_excel_input = args.excel_file is not None
    
    if not use_manual_input and not use_excel_input:
        print("Error: Either provide --monthly-income and --total-monthly-expenses, or specify --excel-file")
        sys.exit(1)
        
    if use_excel_input and not Path(args.excel_file).exists():
        print(f"Error: Excel file '{args.excel_file}' not found")
        sys.exit(1)
    
    # Create analyzer and run analysis
    if use_manual_input:
        analyzer = RealEstateAnalyzer(monthly_income=args.monthly_income, 
                                    total_monthly_expenses=args.total_monthly_expenses)
    else:
        analyzer = RealEstateAnalyzer(excel_file=args.excel_file)
    
    # Load financial data
    analyzer.load_financial_data()
    
    # Parse liens if provided
    liens = []
    if args.current_home_liens:
        liens = analyzer.parse_liens(args.current_home_liens)
    
    # Prepare parameters
    params = {
        'new_home_price': args.new_home_price,
        'inheritance': args.inheritance,
        'bonus_cash': args.bonus_cash,
        'sale_price': args.sale_price,
        'rental_income': args.rental_income,
        'property_tax': args.property_tax,
        'insurance': args.insurance,
        'interest_rate': args.interest_rate,
        'liens': liens,
        'current_mortgage_payment': args.current_mortgage_payment,
        'current_home_operating_costs': args.current_home_operating_costs,
        'selling_cost_percentage': args.selling_cost_percentage,
        'liquid_savings': args.liquid_savings,
        'pay_off_high_rate_first': args.pay_off_high_rate_first,
        'high_rate_threshold': args.high_rate_threshold
    }
    
    # Validate inputs
    warnings = analyzer.validate_inputs(params)
    if warnings:
        for warning in warnings:
            analyzer.console.print(f"[yellow]{warning}[/yellow]")
        analyzer.console.print()
    
    # Calculate strategies
    rental_results = analyzer.calculate_rental_strategy(params)
    sell_results = analyzer.calculate_sell_strategy(params)
    risk_scenarios = analyzer.calculate_risk_scenarios(rental_results, sell_results, params)
    
    # Display results
    analyzer.console.print("\n")
    analyzer.display_current_finances()
    analyzer.console.print("\n")
    analyzer.display_strategy_summary(rental_results, sell_results)
    analyzer.console.print("\n")
    analyzer.display_detailed_comparison(rental_results, sell_results)
    analyzer.console.print("\n")
    analyzer.display_cash_flow_breakdown(rental_results, sell_results)
    analyzer.console.print("\n")
    analyzer.display_risk_analysis(risk_scenarios)
    analyzer.console.print("\n")
    
    # Generate and display recommendation
    recommendation = analyzer.generate_recommendation(rental_results, sell_results, risk_scenarios)
    panel = Panel.fit(recommendation, title="🎯 Final Recommendation", border_style="green")
    analyzer.console.print(panel)
    
    # Export if requested
    if args.export:
        analyzer.export_to_markdown(rental_results, sell_results, risk_scenarios, params, args.export)

if __name__ == "__main__":
    main()