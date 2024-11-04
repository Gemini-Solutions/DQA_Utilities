import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import datetime as dt
import random

# 1. Generate Ticker Symbols and Random Dates
tickers = [f'TICKER{i+1}' for i in range(1000)]
issue_dates = [dt.date(2000, 1, 1) + dt.timedelta(days=random.randint(0, 365 * 20)) for _ in range(1000)]
maturity_dates = [issue_date + dt.timedelta(days=random.randint(365, 365 * 10)) for issue_date in issue_dates]

# 2. Define Columns and Create Sample DataFrames
columns = ["Ticker", "Issue Date", "Maturity Date", "Coupon Rate", "Credit Rating", "Price", "Yield", "Volume"]
credit_ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC']

data1 = pd.DataFrame({
    "Ticker": tickers,
    "Issue Date": issue_dates,
    "Maturity Date": maturity_dates,
    "Coupon Rate": np.random.uniform(1.5, 5.0, 1000),
    "Credit Rating": [random.choice(credit_ratings) for _ in range(1000)],
    "Price": np.random.uniform(90, 110, 1000),
    "Yield": np.random.uniform(0.5, 3.5, 1000),
    "Volume": np.random.randint(1000, 5000, 1000)
})

# Duplicate data1 to data2 and introduce random differences
data2 = data1.copy()
for _ in range(150):  # Introduce 150 random modifications in data2
    idx = random.randint(0, 999)
    col = random.choice(columns)
    if col in ["Price", "Yield", "Volume", "Coupon Rate"]:
        data2.at[idx, col] = float(data2.at[idx, col]) + np.random.normal(0, 5)
    elif col in ["Issue Date", "Maturity Date"]:
        data2.at[idx, col] = data2.at[idx, col] + dt.timedelta(days=random.randint(-10, 10))
    elif col == "Credit Rating":
        data2.at[idx, col] = random.choice(credit_ratings)
    elif col == "Ticker":
        data2.at[idx, col] = f"TICKER{random.randint(1, 1000)}"

# 3. Save data1 and data2 as CSV files
data1.to_csv("left_file.csv", index=False)
data2.to_csv("right_file.csv", index=False)

# 4. Load CSV files into DataFrames
left_df = pd.read_csv("left_file.csv", parse_dates=["Issue Date", "Maturity Date"])
right_df = pd.read_csv("right_file.csv", parse_dates=["Issue Date", "Maturity Date"])

# 5. Convert DataFrames to PyArrow Tables for comparison
left_table = pa.Table.from_pandas(left_df)
right_table = pa.Table.from_pandas(right_df)

# 6. Compare Columns and Identify Differences
diff_report = {"Column": [], "Mismatch Count": []}

for col in left_table.column_names:
    left_column = left_table[col]
    right_column = right_table[col]

    # Find mismatches using PyArrow's not_equal function
    mismatches = pc.not_equal(left_column, right_column)
    mismatch_indices = pc.filter(pa.array(range(len(left_column))), mismatches)

    if mismatch_indices.length() > 0:
        diff_report["Column"].append(col)
        diff_report["Mismatch Count"].append(mismatch_indices.length())

# 7. Create Comparison Summary DataFrame
diff_df = pd.DataFrame(diff_report)
diff_df.to_csv("comparison_summary.csv", index=False)

# Add the left and right source data for reference
with pd.ExcelWriter("comparison_summary_csv.xlsx") as writer:
    diff_df.to_excel(writer, sheet_name="Summary", index=False)
    left_df.to_excel(writer, sheet_name="Left Source", index=False)
    right_df.to_excel(writer, sheet_name="Right Source", index=False)

print("Comparison complete. Results saved in 'comparison_summary.csv' and 'comparison_summary.xlsx'.")
