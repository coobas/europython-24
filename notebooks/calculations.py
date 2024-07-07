import pandas as pd

def load_data() -> pd.DataFrame:
    return pd.DataFrame({"A": range(5)})

def a_mean(df: pd.DataFrame) -> float:
    return df["A"].mean()
