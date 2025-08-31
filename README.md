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
  --new-home-price 565000 \
  --total-liquid-cash 250000 \
  --sale-price 485000 \
  --rental-income 3450 \
  --property-tax 12500 \
  --insurance 4200
```

### With Export to Markdown
```bash
python home_analyzer.py \
  --new-home-price 485000 \
  --total-liquid-cash 195000 \
  --sale-price 375000 \
  --rental-income 2950 \
  --property-tax 9800 \
  --insurance 3850 \
  --export property_analysis.md
```

### Advanced Usage with Operating Costs and Utilities
```bash
python home_analyzer.py \
  --new-home-price 675000 \
  --total-liquid-cash 325000 \
  --sale-price 520000 \
  --rental-income 3800 \
  --property-tax 14200 \
  --insurance 4750 \
  --current-home-operating-costs 520 \
  --current-home-utilities 385 \
  --new-home-operating-costs 480 \
  --new-home-utilities 320 \
  --interest-rate 7.25 \
  --export comprehensive_analysis.md
```

### With Current Home Liens and Debt Strategy
```bash
python home_analyzer.py \
  --new-home-price 545000 \
  --total-liquid-cash 275000 \
  --sale-price 425000 \
  --rental-income 3200 \
  --property-tax 11800 \
  --insurance 4100 \
  --current-home-liens '[{"balance": 285000, "rate": 3.125, "type": "mortgage"}, {"balance": 18500, "rate": 8.75, "type": "heloc"}]' \
  --pay-off-high-rate-first \
  --high-rate-threshold 5.5 \
  --excel-file family_finances.xlsx \
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
│ Monthly Income: $14,750.00   │
│ Monthly Expenses: $11,425.85 │
│ Monthly Surplus: $3,324.15   │
│ Annual Surplus: $39,889.80   │
╰──────────────────────────────╯

                   Strategy Comparison                    
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Metric                 ┃ Rental Strategy ┃ Sell Strategy     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ New Monthly Surplus    │ $1,847.92       │ $825.44           │
│ Annual Surplus         │ $22,175.04      │ $9,905.28         │
└────────────────────────┴─────────────────┴───────────────────┘

╭──────────────────── Recommendation ─────────────────────╮
│ RECOMMEND: Rental Strategy - $12,269.76 better annually │
╰─────────────────────────────────────────────────────────╯
```

## Risk Scenarios Analyzed

### Rental Strategy Risks
- Vacancy periods (3 months/year)
- Major repairs ($12,000)
- Lower rental income (20% reduction)

### Sell Strategy Risks  
- Lower sale price ($35,000 less)
- Closing/selling costs ($15,200)

## Contributing

Feel free to submit issues and enhancement requests!