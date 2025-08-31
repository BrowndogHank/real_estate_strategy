#!/usr/bin/env python3
"""
Real Estate Purchase Strategy Analysis Tool
Analyzes rental vs sell strategies for home purchases
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import openpyxl
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from tabulate import tabulate

class RealEstateAnalyzer:
    def __init__(self, excel_file: str = "joint_expenses_input.xlsx"):
        self.console = Console()
        self.excel_file = excel_file
        self.current_finances = {}
        
    def load_financial_data(self) -> Dict[str, Any]:
        """Load baseline financial data from Excel file"""
        try:
            # Load Sheet1 for main financial data
            df1 = pd.read_excel(self.excel_file, sheet_name='Sheet1', header=None)
            
            # Extract income from row 2 (index 1), columns D, E, F, G (indices 3, 4, 5, 6)
            income_data = df1.iloc[1, 3:7].dropna()
            total_monthly_income = income_data.sum()
            
            # Extract expenses from column B (index 1)
            expenses = df1.iloc[:, 1].dropna()
            expense_labels = df1.iloc[:, 0].dropna()
            
            # Create expense dictionary
            expense_dict = {}
            total_expenses = 0
            
            for i, expense in enumerate(expenses):
                if isinstance(expense, (int, float)) and not pd.isna(expense):
                    if i < len(expense_labels):
                        label = str(expense_labels.iloc[i])
                        expense_dict[label] = expense
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
            
            return self.current_finances
            
        except Exception as e:
            self.console.print(f"[red]Error loading Excel file: {e}[/red]")
            sys.exit(1)
    
    def calculate_rental_strategy(self, params: Dict[str, float]) -> Dict[str, float]:
        """Calculate financial impact of rental strategy (keep current home)"""
        # New home costs
        new_home_price = params['new_home_price']
        inheritance = params['inheritance']
        rental_income = params['rental_income']
        property_tax_annual = params['property_tax']
        insurance_annual = params['insurance']
        interest_rate = params.get('interest_rate', 6.13) / 100
        
        # Calculate new mortgage amount
        down_payment = inheritance
        new_mortgage_amount = new_home_price - down_payment
        
        # Monthly mortgage payment (principal + interest)
        monthly_rate = interest_rate / 12
        num_payments = 30 * 12
        monthly_payment = (new_mortgage_amount * monthly_rate * (1 + monthly_rate)**num_payments) / \
                         ((1 + monthly_rate)**num_payments - 1)
        
        # New home monthly costs
        monthly_property_tax = property_tax_annual / 12
        monthly_insurance = insurance_annual / 12
        new_home_monthly_costs = monthly_payment + monthly_property_tax + monthly_insurance
        
        # Current home operating costs (assuming from expense breakdown)
        current_home_costs = 0
        for expense, amount in self.current_finances['expense_breakdown'].items():
            if any(keyword in expense.lower() for keyword in ['lawn', 'pool', 'maintenance', 'fpl', 'cleaning']):
                current_home_costs += amount
        
        # Calculate net impact
        additional_costs = new_home_monthly_costs + current_home_costs
        additional_income = rental_income
        net_monthly_impact = additional_income - additional_costs
        
        new_monthly_surplus = self.current_finances['monthly_surplus'] + net_monthly_impact
        
        return {
            'strategy': 'Rental Strategy',
            'new_mortgage_payment': monthly_payment,
            'new_property_tax': monthly_property_tax,
            'new_insurance': monthly_insurance,
            'new_home_total_monthly': new_home_monthly_costs,
            'current_home_operating_costs': current_home_costs,
            'rental_income': rental_income,
            'net_monthly_impact': net_monthly_impact,
            'new_monthly_surplus': new_monthly_surplus,
            'annual_surplus': new_monthly_surplus * 12
        }
    
    def calculate_sell_strategy(self, params: Dict[str, float]) -> Dict[str, float]:
        """Calculate financial impact of sell strategy (sell current home)"""
        new_home_price = params['new_home_price']
        inheritance = params['inheritance']
        sale_price = params['sale_price']
        property_tax_annual = params['property_tax']
        insurance_annual = params['insurance']
        interest_rate = params.get('interest_rate', 6.13) / 100
        
        # Calculate new mortgage amount
        total_down_payment = inheritance + sale_price
        new_mortgage_amount = max(0, new_home_price - total_down_payment)
        
        # Monthly mortgage payment
        if new_mortgage_amount > 0:
            monthly_rate = interest_rate / 12
            num_payments = 30 * 12
            monthly_payment = (new_mortgage_amount * monthly_rate * (1 + monthly_rate)**num_payments) / \
                             ((1 + monthly_rate)**num_payments - 1)
        else:
            monthly_payment = 0
        
        # New home monthly costs
        monthly_property_tax = property_tax_annual / 12
        monthly_insurance = insurance_annual / 12
        new_home_monthly_costs = monthly_payment + monthly_property_tax + monthly_insurance
        
        # Remove current home costs (no longer owned)
        current_home_savings = 0
        for expense, amount in self.current_finances['expense_breakdown'].items():
            if any(keyword in expense.lower() for keyword in ['lawn', 'pool', 'maintenance', 'fpl', 'cleaning']):
                current_home_savings += amount
        
        # Calculate net impact
        net_monthly_impact = current_home_savings - new_home_monthly_costs
        new_monthly_surplus = self.current_finances['monthly_surplus'] + net_monthly_impact
        
        return {
            'strategy': 'Sell Strategy',
            'new_mortgage_payment': monthly_payment,
            'new_property_tax': monthly_property_tax,
            'new_insurance': monthly_insurance,
            'new_home_total_monthly': new_home_monthly_costs,
            'current_home_savings': current_home_savings,
            'net_monthly_impact': net_monthly_impact,
            'new_monthly_surplus': new_monthly_surplus,
            'annual_surplus': new_monthly_surplus * 12
        }
    
    def calculate_risk_scenarios(self, rental_results: Dict, sell_results: Dict, params: Dict) -> Dict:
        """Calculate risk scenarios for both strategies"""
        scenarios = {}
        
        # Rental strategy risks
        scenarios['rental_risks'] = {
            'vacancy_3_months': {
                'description': '3 months vacancy per year',
                'annual_impact': -(params['rental_income'] * 3),
                'new_annual_surplus': rental_results['annual_surplus'] - (params['rental_income'] * 3)
            },
            'major_repairs': {
                'description': '$10,000 major repairs',
                'annual_impact': -10000,
                'new_annual_surplus': rental_results['annual_surplus'] - 10000
            },
            'lower_rent': {
                'description': '20% lower rental income',
                'monthly_impact': -(params['rental_income'] * 0.2),
                'annual_impact': -(params['rental_income'] * 0.2 * 12),
                'new_annual_surplus': rental_results['annual_surplus'] - (params['rental_income'] * 0.2 * 12)
            }
        }
        
        # Sell strategy risks
        scenarios['sell_risks'] = {
            'lower_sale_price': {
                'description': '$50,000 lower sale price',
                'impact_description': 'Higher mortgage payment',
                'additional_mortgage': 50000,
                'additional_monthly_payment': self._calculate_payment_increase(50000, params.get('interest_rate', 6.13)),
                'annual_impact': -(self._calculate_payment_increase(50000, params.get('interest_rate', 6.13)) * 12)
            },
            'closing_costs': {
                'description': '$15,000 in closing/selling costs',
                'annual_impact': -15000,
                'impact_description': 'One-time cost (amortized over 5 years: $3,000/year)'
            }
        }
        
        return scenarios
    
    def _calculate_payment_increase(self, additional_mortgage: float, interest_rate: float) -> float:
        """Calculate additional monthly payment for additional mortgage amount"""
        monthly_rate = (interest_rate / 100) / 12
        num_payments = 30 * 12
        return (additional_mortgage * monthly_rate * (1 + monthly_rate)**num_payments) / \
               ((1 + monthly_rate)**num_payments - 1)
    
    def display_current_finances(self):
        """Display current financial position from Excel data"""
        finances = self.current_finances
        
        panel = Panel.fit(
            f"Monthly Income: ${finances['monthly_income']:,.2f}\n"
            f"Monthly Expenses: ${finances['monthly_expenses']:,.2f}\n"
            f"Monthly Surplus: ${finances['monthly_surplus']:,.2f}\n"
            f"Annual Surplus: ${finances['monthly_surplus'] * 12:,.2f}",
            title="Current Financial Position",
            border_style="blue"
        )
        self.console.print(panel)
    
    def display_comparison(self, rental_results: Dict, sell_results: Dict):
        """Display side-by-side strategy comparison"""
        table = Table(title="Strategy Comparison")
        table.add_column("Metric", style="cyan")
        table.add_column("Rental Strategy", style="green")
        table.add_column("Sell Strategy", style="yellow")
        
        # Key metrics comparison
        metrics = [
            ("New Mortgage Payment", f"${rental_results['new_mortgage_payment']:,.2f}", 
             f"${sell_results['new_mortgage_payment']:,.2f}"),
            ("Property Tax (Monthly)", f"${rental_results['new_property_tax']:,.2f}", 
             f"${sell_results['new_property_tax']:,.2f}"),
            ("Insurance (Monthly)", f"${rental_results['new_insurance']:,.2f}", 
             f"${sell_results['new_insurance']:,.2f}"),
            ("New Home Total Monthly", f"${rental_results['new_home_total_monthly']:,.2f}", 
             f"${sell_results['new_home_total_monthly']:,.2f}"),
            ("Current Home Impact", f"${rental_results['current_home_operating_costs']:,.2f} (costs)", 
             f"${sell_results['current_home_savings']:,.2f} (savings)"),
            ("Rental Income", f"${rental_results['rental_income']:,.2f}", "N/A"),
            ("Net Monthly Impact", f"${rental_results['net_monthly_impact']:,.2f}", 
             f"${sell_results['net_monthly_impact']:,.2f}"),
            ("New Monthly Surplus", f"${rental_results['new_monthly_surplus']:,.2f}", 
             f"${sell_results['new_monthly_surplus']:,.2f}"),
            ("Annual Surplus", f"${rental_results['annual_surplus']:,.2f}", 
             f"${sell_results['annual_surplus']:,.2f}")
        ]
        
        for metric, rental_val, sell_val in metrics:
            table.add_row(metric, rental_val, sell_val)
        
        self.console.print(table)
    
    def display_risk_analysis(self, scenarios: Dict):
        """Display risk scenario analysis"""
        # Rental risks table
        rental_table = Table(title="Rental Strategy Risk Scenarios")
        rental_table.add_column("Risk Scenario", style="cyan")
        rental_table.add_column("Annual Impact", style="red")
        rental_table.add_column("New Annual Surplus", style="yellow")
        
        for risk, data in scenarios['rental_risks'].items():
            rental_table.add_row(
                data['description'],
                f"${data['annual_impact']:,.2f}",
                f"${data['new_annual_surplus']:,.2f}"
            )
        
        self.console.print(rental_table)
        self.console.print()
        
        # Sell risks table
        sell_table = Table(title="Sell Strategy Risk Scenarios")
        sell_table.add_column("Risk Scenario", style="cyan")
        sell_table.add_column("Impact Description", style="magenta")
        sell_table.add_column("Annual Impact", style="red")
        
        for risk, data in scenarios['sell_risks'].items():
            sell_table.add_row(
                data['description'],
                data.get('impact_description', data['description']),
                f"${data['annual_impact']:,.2f}"
            )
        
        self.console.print(sell_table)
    
    def generate_recommendation(self, rental_results: Dict, sell_results: Dict) -> str:
        """Generate recommendation based on analysis"""
        rental_surplus = rental_results['annual_surplus']
        sell_surplus = sell_results['annual_surplus']
        
        if rental_surplus > sell_surplus:
            difference = rental_surplus - sell_surplus
            return f"RECOMMEND: Rental Strategy - ${difference:,.2f} better annually"
        else:
            difference = sell_surplus - rental_surplus
            return f"RECOMMEND: Sell Strategy - ${difference:,.2f} better annually"
    
    def export_to_markdown(self, rental_results: Dict, sell_results: Dict, 
                          scenarios: Dict, params: Dict, filename: str = "analysis_results.md"):
        """Export detailed results to markdown file"""
        content = f"""# Real Estate Strategy Analysis Results

## Input Parameters
- New Home Price: ${params['new_home_price']:,.2f}
- Inheritance: ${params['inheritance']:,.2f}
- Current Home Sale Price: ${params['sale_price']:,.2f}
- Expected Rental Income: ${params['rental_income']:,.2f}
- Property Tax (Annual): ${params['property_tax']:,.2f}
- Insurance (Annual): ${params['insurance']:,.2f}
- Interest Rate: {params.get('interest_rate', 6.13)}%

## Current Financial Position
- Monthly Income: ${self.current_finances['monthly_income']:,.2f}
- Monthly Expenses: ${self.current_finances['monthly_expenses']:,.2f}
- Monthly Surplus: ${self.current_finances['monthly_surplus']:,.2f}

## Strategy Comparison

### Rental Strategy Results
- New Mortgage Payment: ${rental_results['new_mortgage_payment']:,.2f}
- Property Tax (Monthly): ${rental_results['new_property_tax']:,.2f}
- Insurance (Monthly): ${rental_results['new_insurance']:,.2f}
- Current Home Operating Costs: ${rental_results['current_home_operating_costs']:,.2f}
- Rental Income: ${rental_results['rental_income']:,.2f}
- **New Monthly Surplus: ${rental_results['new_monthly_surplus']:,.2f}**
- **Annual Surplus: ${rental_results['annual_surplus']:,.2f}**

### Sell Strategy Results
- New Mortgage Payment: ${sell_results['new_mortgage_payment']:,.2f}
- Property Tax (Monthly): ${sell_results['new_property_tax']:,.2f}
- Insurance (Monthly): ${sell_results['new_insurance']:,.2f}
- Current Home Savings: ${sell_results['current_home_savings']:,.2f}
- **New Monthly Surplus: ${sell_results['new_monthly_surplus']:,.2f}**
- **Annual Surplus: ${sell_results['annual_surplus']:,.2f}**

## Risk Analysis

### Rental Strategy Risks
"""
        for risk, data in scenarios['rental_risks'].items():
            content += f"- {data['description']}: ${data['annual_impact']:,.2f} impact, New surplus: ${data['new_annual_surplus']:,.2f}\n"
        
        content += "\n### Sell Strategy Risks\n"
        for risk, data in scenarios['sell_risks'].items():
            content += f"- {data['description']}: {data.get('impact_description', data['description'])}, ${data['annual_impact']:,.2f} impact\n"
        
        content += f"\n## Recommendation\n{self.generate_recommendation(rental_results, sell_results)}\n"
        
        with open(filename, 'w') as f:
            f.write(content)
        
        self.console.print(f"[green]Results exported to {filename}[/green]")

def main():
    parser = argparse.ArgumentParser(description="Real Estate Purchase Strategy Analysis")
    parser.add_argument("--new-home-price", type=float, required=True,
                       help="New home purchase price")
    parser.add_argument("--inheritance", type=float, required=True,
                       help="Expected inheritance amount")
    parser.add_argument("--sale-price", type=float, required=True,
                       help="Current home estimated sale price")
    parser.add_argument("--rental-income", type=float, required=True,
                       help="Expected monthly rental income")
    parser.add_argument("--property-tax", type=float, required=True,
                       help="New home annual property tax")
    parser.add_argument("--insurance", type=float, required=True,
                       help="New home annual insurance")
    parser.add_argument("--interest-rate", type=float, default=6.13,
                       help="Mortgage interest rate (default: 6.13%%)")
    parser.add_argument("--excel-file", type=str, default="joint_expenses_input.xlsx",
                       help="Excel file with baseline financial data")
    parser.add_argument("--export", type=str,
                       help="Export results to markdown file")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.excel_file).exists():
        print(f"Error: Excel file '{args.excel_file}' not found")
        sys.exit(1)
    
    # Create analyzer and run analysis
    analyzer = RealEstateAnalyzer(args.excel_file)
    
    # Load financial data
    analyzer.load_financial_data()
    
    # Prepare parameters
    params = {
        'new_home_price': args.new_home_price,
        'inheritance': args.inheritance,
        'sale_price': args.sale_price,
        'rental_income': args.rental_income,
        'property_tax': args.property_tax,
        'insurance': args.insurance,
        'interest_rate': args.interest_rate
    }
    
    # Calculate strategies
    rental_results = analyzer.calculate_rental_strategy(params)
    sell_results = analyzer.calculate_sell_strategy(params)
    risk_scenarios = analyzer.calculate_risk_scenarios(rental_results, sell_results, params)
    
    # Display results
    analyzer.console.print("\n")
    analyzer.display_current_finances()
    analyzer.console.print("\n")
    analyzer.display_comparison(rental_results, sell_results)
    analyzer.console.print("\n")
    analyzer.display_risk_analysis(risk_scenarios)
    analyzer.console.print("\n")
    
    # Generate and display recommendation
    recommendation = analyzer.generate_recommendation(rental_results, sell_results)
    panel = Panel.fit(recommendation, title="Recommendation", border_style="green")
    analyzer.console.print(panel)
    
    # Export if requested
    if args.export:
        analyzer.export_to_markdown(rental_results, sell_results, risk_scenarios, params, args.export)

if __name__ == "__main__":
    main()