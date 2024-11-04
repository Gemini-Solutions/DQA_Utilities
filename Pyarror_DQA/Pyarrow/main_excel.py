import pandas as pd
import numpy as np
from datetime import date, timedelta
import pyarrow as pa
import pyarrow.compute as pc

# Sample data generation
num_securities = 1000
tickers = [f"TICKER{i}" for i in range(1, num_securities + 1)]

# Generate random dates for issue and maturity
start_date = date(2000, 1, 1)
issue_dates = [start_date + timedelta(days=np.random.randint(0, 365 * 20)) for _ in range(num_securities)]
maturity_dates = [issue_date + timedelta(days=np.random.randint(365 * 5, 365 * 30)) for issue_date in issue_dates]

# Define columns
columns = ["Ticker", "Issuer Name", "Issue Date", "Maturity Date", "Coupon Rate (%)", "Credit Rating",
           "Interest Rate", "Price", "Yield (%)", "Volume", "Bid Price", "Ask Price"]

# Data for the left and right files
data1 = pd.DataFrame({
    "Ticker": tickers,
    "Issuer Name": [f"Issuer {i}" for i in range(1, num_securities + 1)],
    "Issue Date": issue_dates,
    "Maturity Date": maturity_dates,
    "Coupon Rate (%)": np.random.uniform(0, 10, num_securities),
    "Credit Rating": np.random.choice(["AAA", "AA", "A", "BBB", "BB", "B", "CCC"], num_securities),
    "Interest Rate": np.random.uniform(0, 5, num_securities),
    "Price": np.random.uniform(80, 120, num_securities),
    "Yield (%)": np.random.uniform(0.5, 8, num_securities),
    "Volume": np.random.randint(1000, 100000, num_securities),
    "Bid Price": np.random.uniform(80, 120, num_securities),
    "Ask Price": np.random.uniform(80, 120, num_securities)
})

data2 = data1.copy()

# Introduce random differences with correct type casting
for _ in range(150):  # Change 150 random entries
    idx = np.random.choice(data2.index)
    col = np.random.choice(columns[1:])
    if pd.api.types.is_numeric_dtype(data2[col]):
        data2.at[idx, col] = float(data2.at[idx, col]) + np.random.normal(0, 5)
    elif pd.api.types.is_datetime64_any_dtype(data2[col]):
        data2.at[idx, col] = data2.at[idx, col] + timedelta(days=np.random.randint(1, 365))
    else:
        data2.at[idx, col] = f"Issuer {np.random.randint(1, num_securities + 1)}" if col == "Issuer Name" else np.random.choice(["AAA", "AA", "A", "BBB", "BB", "B", "CCC"])

# Save to Excel files
data1.to_excel("left_file.xlsx", index=False)
data2.to_excel("right_file.xlsx", index=False)

# Load the Excel files into pyarrow tables
left_df = pd.read_excel("left_file.xlsx")
right_df = pd.read_excel("right_file.xlsx")

# Ensure consistent data types
for col in ["Issue Date", "Maturity Date"]:
    left_df[col] = pd.to_datetime(left_df[col], errors='coerce')
    right_df[col] = pd.to_datetime(right_df[col], errors='coerce')

# Convert to pyarrow tables
left_table = pa.Table.from_pandas(left_df)
right_table = pa.Table.from_pandas(right_df)

# Compare the two tables column by column
diff_report = []

for col in columns:
    left_column = left_table.column(col)
    right_column = right_table.column(col)
    
    # Find rows with mismatches in this column
    mismatches = pc.not_equal(left_column, right_column)
    mismatch_indices = pc.filter(pa.array(range(len(left_column))), mismatches)
    
    if mismatch_indices.length() > 0:  # Use .length() instead of .size
        diff_report.append({
            "Column": col,
            "Mismatch Count": mismatch_indices.length()
        })

# Create a DataFrame to summarize the comparison
diff_df = pd.DataFrame(diff_report)

# Save the comparison summary to Excel
with pd.ExcelWriter("comparison_summary.xlsx") as writer:
    diff_df.to_excel(writer, sheet_name="Summary", index=False)
    left_df.to_excel(writer, sheet_name="Left Source", index=False)
    right_df.to_excel(writer, sheet_name="Right Source", index=False)

print("Comparison summary saved to 'comparison_summary.xlsx'")
