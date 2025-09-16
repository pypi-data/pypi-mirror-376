import os
import pandas as pd
from pathlib import Path
import webbrowser

class SimpleViewer:
    """Standalone version to test CSV → HTML rendering"""

    def _render_results_table(self, csv_path):
        df = self.read_csv_to_dataframe(csv_path)
        if df is not None:
            html_table = self.dataframe_to_html(df)
            self.save_html_file(html_table)
        else:
            print("No data available to display.")

    def read_csv_to_dataframe(self, csv_path):
        try:
            df = pd.read_csv(csv_path, sep=',', usecols=lambda col: col != 'Unnamed: 0')
            print("DataFrame loaded:\n", df)
            return df
        except pd.errors.ParserError as e:
            print(f"Error reading CSV: {e}")
            return None
        except FileNotFoundError:
            print(f"CSV file not found: {csv_path}")
            return None

    def dataframe_to_html(self, df):
        html_table = df.to_html(classes='table table-striped', index=False)
        styled_html = f"""
        <style>
            .table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .table th, .table td {{
                text-align: center;
                padding: 8px;
                border: 1px solid #ddd;
            }}
        </style>
        {html_table}
        """
        return styled_html

    def save_html_file(self, html_content):
        html_path = "toxCSM_detailedInfo.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
        html_file = Path(html_path).resolve()
        print(f"HTML saved at: {html_file}")
        webbrowser.open(f'file://{html_file}')


# ------------------------
# Create minimal CSV for testing
csv_path = "/home/bpueche/ScipionUserData/projects/test/Runs/001279_ProtChemToxCSM/extra/toxCSM_detailedInfo.csv"
if not os.path.exists(csv_path):
    import csv
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Value"])
        writer.writerow(["Test1", 123])
        writer.writerow(["Test2", 456])
    print(f"Test CSV created at {csv_path}")

# Instantiate viewer and run
viewer = SimpleViewer()
viewer._render_results_table(csv_path)
