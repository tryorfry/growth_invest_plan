import pandas as pd
import os
import datetime
from typing import List, Dict, Any

def export_reports_to_excel(reports: List[Dict[str, Any]], output_dir: str = "data/reports") -> str:
    """
    Exports a list of report dictionaries to a timestamped Excel spreadsheet.
    Returns the absolute path to the generated file.
    """
    if not reports:
        raise ValueError("No reports provided for export.")
        
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"automated_report_{timestamp}.xlsx"
    filepath = os.path.abspath(os.path.join(output_dir, filename))
    
    df = pd.DataFrame(reports)
    
    # Sort by Sector, then Checklist Score
    if "Sector" in df.columns and "Checklist Score" in df.columns:
        df = df.sort_values(by=["Sector", "Checklist Score"], ascending=[True, False])
        
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="All Stocks", index=False)
        
        # Create a sheet per sector
        if "Sector" in df.columns:
            sectors = df["Sector"].unique()
            for sector in sectors:
                # Max sheet name length is 31
                sheet_name = str(sector)[:31] if pd.notna(sector) else "Unknown"
                # Some invalid characters in Excel sheet names
                sheet_name = sheet_name.replace("/", "-").replace("\\", "-").replace("?", "").replace("*", "").replace("[", "").replace("]", "")
                
                sector_df = df[df["Sector"] == sector]
                sector_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
    return filepath
