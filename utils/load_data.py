import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

usaha_list = [
    'cafe','fnb','laundry','gym','fashion','stationery',
    'carwash','photostudio','barbershop','salon','bengkel','elektronik'
]

def load_data():
    df = pd.read_excel(BASE_DIR / "data" / "df_fe.xlsx")

    # safe competitor sum (ANTI ERROR)
    for u in usaha_list:
        if f"competitor_{u}" not in df.columns:
            df[f"competitor_{u}"] = 0

    df["total_competitor"] = df[
        [f"competitor_{u}" for u in usaha_list]
    ].sum(axis=1)

    return df