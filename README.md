# Real Estate Purchase Strategy Analyzer

A Python CLI tool that analyzes real estate purchase strategies by comparing rental vs sell approaches using your current financial data from Excel.

## Features

- **Excel Integration**: Automatically loads your current financial baseline from `joint_expenses_input.xlsx`
- **Dual Strategy Analysis**: Compares keeping current home as rental vs selling it
- **Risk Analysis**: Evaluates scenarios like vacancy periods, major repairs, and market fluctuations
- **Rich Output**: Beautiful formatted tables and summaries in the terminal
- **Export Capability**: Save detailed results to markdown files
- **Flexible Parameters**: Customize home prices, inheritance, interest rates, and more

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
  --new-home-price 865000 \
  --inheritance 353000 \
  --sale-price 700000 \
  --rental-income 5000 \
  --property-tax 25000 \
  --insurance 10000
```

### With Export to Markdown
```bash
python home_analyzer.py \
  --new-home-price 865000 \
  --inheritance 353000 \
  --sale-price 700000 \
  --rental-income 5000 \
  --property-tax 25000 \
  --insurance 10000 \
  --export my_analysis.md
```

### All Parameters
```bash
python home_analyzer.py \
  --new-home-price 865000 \
  --inheritance 353000 \
  --sale-price 700000 \
  --rental-income 5000 \
  --property-tax 25000 \
  --insurance 10000 \
  --interest-rate 6.5 \
  --excel-file custom_expenses.xlsx \
  --export detailed_results.md
```

## Command Line Arguments

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `--new-home-price` | Yes | New home purchase price | - |
| `--inheritance` | Yes | Expected inheritance amount | - |
| `--sale-price` | Yes | Current home estimated sale price | - |
| `--rental-income` | Yes | Expected monthly rental income | - |
| `--property-tax` | Yes | New home annual property tax | - |
| `--insurance` | Yes | New home annual insurance | - |
| `--interest-rate` | No | Mortgage interest rate (%) | 6.13 |
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

The tool automatically identifies current home operating costs (lawn, pool, maintenance, utilities) from the expense labels.

## Output

The tool provides:

1. **Current Financial Position**: Your baseline income, expenses, and surplus
2. **Strategy Comparison Table**: Side-by-side comparison of rental vs sell approaches
3. **Risk Analysis**: Impact of various negative scenarios on each strategy
4. **Clear Recommendation**: Which strategy is financially better and by how much
5. **Optional Markdown Export**: Detailed report saved to file

## Example Output

```
╭─ Current Financial Position ─╮
│ Monthly Income: $24,000.00   │
│ Monthly Expenses: $34,722.73 │
│ Monthly Surplus: $-10,722.73 │
│ Annual Surplus: $-128,672.76 │
╰──────────────────────────────╯

                   Strategy Comparison                    
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Metric                 ┃ Rental Strategy ┃ Sell Strategy     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ New Monthly Surplus    │ $-12,153.02     │ $-13,238.40       │
│ Annual Surplus         │ $-145,836.22    │ $-158,860.76      │
└────────────────────────┴─────────────────┴───────────────────┘

╭──────────────────── Recommendation ─────────────────────╮
│ RECOMMEND: Rental Strategy - $13,024.54 better annually │
╰─────────────────────────────────────────────────────────╯
```

## Risk Scenarios Analyzed

### Rental Strategy Risks
- Vacancy periods (3 months/year)
- Major repairs ($10,000)
- Lower rental income (20% reduction)

### Sell Strategy Risks  
- Lower sale price ($50,000 less)
- Closing/selling costs ($15,000)

## Contributing

Feel free to submit issues and enhancement requests!