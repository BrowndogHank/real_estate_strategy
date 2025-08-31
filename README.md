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
  --new-home-price 425000 \
  --inheritance 180000 \
  --sale-price 320000 \
  --rental-income 2800 \
  --property-tax 8500 \
  --insurance 3200
```

### With Export to Markdown
```bash
python home_analyzer.py \
  --new-home-price 425000 \
  --inheritance 180000 \
  --sale-price 320000 \
  --rental-income 2800 \
  --property-tax 8500 \
  --insurance 3200 \
  --export my_analysis.md
```

### All Parameters
```bash
python home_analyzer.py \
  --new-home-price 425000 \
  --inheritance 180000 \
  --sale-price 320000 \
  --rental-income 2800 \
  --property-tax 8500 \
  --insurance 3200 \
  --interest-rate 5.25 \
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
| `--interest-rate` | No | Mortgage interest rate (%) | 5.75 |
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
│ Monthly Income: $12,500.00   │
│ Monthly Expenses: $16,850.42 │
│ Monthly Surplus: $-4,350.42  │
│ Annual Surplus: $-52,204.96  │
╰──────────────────────────────╯

                   Strategy Comparison                    
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Metric                 ┃ Rental Strategy ┃ Sell Strategy     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ New Monthly Surplus    │ $-5,842.18      │ $-6,925.73        │
│ Annual Surplus         │ $-70,106.14     │ $-83,108.82       │
└────────────────────────┴─────────────────┴───────────────────┘

╭──────────────────── Recommendation ─────────────────────╮
│ RECOMMEND: Rental Strategy - $13,002.68 better annually │
╰─────────────────────────────────────────────────────────╯
```

## Risk Scenarios Analyzed

### Rental Strategy Risks
- Vacancy periods (2 months/year)
- Major repairs ($7,500)
- Lower rental income (15% reduction)

### Sell Strategy Risks  
- Lower sale price ($25,000 less)
- Closing/selling costs ($8,500)

## Contributing

Feel free to submit issues and enhancement requests!