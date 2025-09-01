# Real Estate Purchase Strategy Analyzer

A Python CLI tool that analyzes real estate purchase strategies by comparing rental vs sell approaches using your current financial data from Excel.

## Features

- **Excel Integration**: Automatically loads your current financial baseline from `joint_expenses_input.xlsx`
- **Dual Strategy Analysis**: Compares keeping current home as rental vs selling it
- **Risk Analysis**: Evaluates scenarios like vacancy periods, major repairs, and market fluctuations
- **Rich Output**: Beautiful formatted tables and summaries in the terminal
- **Export Capability**: Save detailed results to markdown files
- **Flexible Parameters**: Customize home prices, inheritance, interest rates, operating costs, utilities, and more
- **Granular Cost Tracking**: Separate tracking for operating costs (lawn, maintenance) and utilities (electric, gas, water) for both current and new homes

## Installation

1. Create and activate conda environment:
```bash
conda create -n real_estate_strategy python=3.11 -y
conda activate real_estate_strategy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python home_analyzer.py \
  --new-home-price 425000 \
  --total-liquid-cash 85000 \
  --sale-price 350000 \
  --rental-income 2750 \
  --property-tax 8400 \
  --insurance 3200 \
  --monthly-income 8500 \
  --total-monthly-expenses 6200
```

### With Export to Markdown
```bash
python home_analyzer.py \
  --new-home-price 385000 \
  --total-liquid-cash 75000 \
  --sale-price 325000 \
  --rental-income 2400 \
  --property-tax 7500 \
  --insurance 2800 \
  --monthly-income 7800 \
  --total-monthly-expenses 5500 \
  --export property_analysis.md
```

### Advanced Usage with Operating Costs and Utilities
```bash
python home_analyzer.py \
  --new-home-price 465000 \
  --total-liquid-cash 95000 \
  --sale-price 375000 \
  --rental-income 2900 \
  --property-tax 9200 \
  --insurance 3400 \
  --current-home-operating-costs 320 \
  --current-home-utilities 285 \
  --new-home-operating-costs 350 \
  --new-home-utilities 240 \
  --interest-rate 7.25 \
  --monthly-income 8200 \
  --total-monthly-expenses 5800 \
  --export comprehensive_analysis.md
```

### With Current Home Liens and Debt Strategy
```bash
python home_analyzer.py \
  --new-home-price 445000 \
  --total-liquid-cash 85000 \
  --sale-price 365000 \
  --rental-income 2650 \
  --property-tax 8800 \
  --insurance 3100 \
  --current-home-liens '[{"balance": 225000, "rate": 3.5, "type": "mortgage"}, {"balance": 15000, "rate": 9.25, "type": "heloc"}]' \
  --pay-off-high-rate-first \
  --high-rate-threshold 5.5 \
  --monthly-income 7500 \
  --total-monthly-expenses 5200 \
  --export complete_strategy.md
```

## Command Line Arguments

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `--new-home-price` | Yes | New home purchase price | - |
| `--total-liquid-cash` | Yes | Total inheritance/liquid cash available | - |
| `--sale-price` | Yes | Current home estimated sale price | - |
| `--rental-income` | Yes | Expected monthly rental income | - |
| `--property-tax` | Yes | New home annual property tax | - |
| `--insurance` | Yes | New home annual insurance | - |
| `--interest-rate` | No | Mortgage interest rate (%) | 6.13 |
| `--current-home-liens` | No | JSON string of current liens | - |
| `--current-mortgage-payment` | No | Current monthly mortgage payment (PITI) | Auto-detected |
| `--current-home-operating-costs` | No | Current home monthly operating costs | Auto-detected |
| `--current-home-utilities` | No | Current home monthly utilities | Auto-detected |
| `--new-home-operating-costs` | No | New home monthly operating costs | 0 |
| `--new-home-utilities` | No | New home monthly utilities | 0 |
| `--selling-cost-percentage` | No | Selling cost percentage | 7% |
| `--bonus-cash` | No | Additional cash (e.g., bonuses) | 0 |
| `--liquid-savings` | No | Additional liquid savings for sell strategy | 0 |
| `--monthly-income` | No | Monthly income (alternative to Excel) | - |
| `--total-monthly-expenses` | No | Monthly expenses (alternative to Excel) | - |
| `--excel-file` | No | Excel file with financial data | joint_expenses_input.xlsx |
| `--export` | No | Export results to markdown file | - |

## Excel File Requirements

The tool expects an Excel file with the following structure:

### Sheet1 (Main Financial Data)
- **Row 2, Columns D-G**: Income data (will be summed for total monthly income)
- **Column A**: Expense item labels
- **Column B**: Expense amounts

### Sheet2 (Additional Personal Expenses) - Optional
- **Column A**: Personal expense labels  
- **Column B**: Personal expense amounts

The tool automatically identifies current home operating costs (lawn, pool, maintenance) and utilities (electric, gas, water, sewer) from the expense labels. You can override these auto-detected values using the corresponding command-line parameters.

## Output

The tool provides:

1. **Current Financial Position**: Your baseline income, expenses, and surplus
2. **Detailed Strategy Comparison Table**: Comprehensive side-by-side comparison including mortgage rates, operating costs, utilities, and debt management
3. **Risk Analysis**: Impact of various negative scenarios on each strategy
4. **Clear Recommendation**: Which strategy is financially better and by how much
5. **Enhanced Cost Breakdown**: Separate tracking of operating costs and utilities for accurate analysis
6. **Optional Markdown Export**: Detailed report saved to file

## Example Output

```
╭─ Current Financial Position ─╮
│ Monthly Income: $8,500.00    │
│ Monthly Expenses: $6,200.00  │
│ Monthly Surplus: $2,300.00   │
│ Annual Surplus: $27,600.00   │
╰──────────────────────────────╯

╭── Strategy Summary ──╮
│ Rental:  $1,685/mo   │
│ Sell:    $895/mo     │
│ Diff:     +$790/mo  │
│ Rental preferred     │
╰──────────────────────╯

╭────────────────────────── 🎯 Final Recommendation ───────────────────────────╮
│ RENTAL STRATEGY PREFERRED - $9,480 better annually                           │
│                                                                              │
│ ✅ Even in worst-case rental scenarios, still outperforms selling            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Risk Scenarios Analyzed

### Rental Strategy Risks
- Vacancy periods (1-6 months/year)
- Major repairs ($5,000-$15,000)
- Reduced rental income (10-20% reduction)
- Property management fees (8-12%)
- Tenant damage/eviction costs ($3,000)

### Sell Strategy Risks  
- Lower sale price ($25,000-$100,000 less)
- Higher selling costs (up to 10% vs 7% baseline)
- Market timing delays (6 months additional costs)
- Moving and transition costs ($8,000)

## Contributing

Feel free to submit issues and enhancement requests!