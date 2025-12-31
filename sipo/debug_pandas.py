
import pandas as pd
import datetime

def test_pandas_behavior():
    dates = [f'2025-12-{i:02d}' for i in range(1, 32)]
    df = pd.DataFrame({'Fecha': dates})
    
    # Simulate _robust_date_parsing logic
    # Initial parse with dayfirst=True
    df['Fecha_parsed'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
    
    print("Parsing result for Dec 1-31 with dayfirst=True (ISO strings):")
    print(df.head(15))
    print("NaT count:", df['Fecha_parsed'].isna().sum())
    
    # Now check what happens if it's DD/MM/YYYY
    dates_es = [f'{i:02d}/12/2025' for i in range(1, 32)]
    df_es = pd.DataFrame({'Fecha': dates_es})
    df_es['Fecha_parsed'] = pd.to_datetime(df_es['Fecha'], dayfirst=True, errors='coerce')
    print("\nParsing result for Dec 1-31 with dayfirst=True (ES strings):")
    print(df_es.head(15))
    print("NaT count:", df_es['Fecha_parsed'].isna().sum())

    # Range check simulation
    start = pd.to_datetime('01/12/2025') # Jan 12th if dayfirst=False (default)
    print(f"\nDefault start date from '01/12/2025': {start}")
    
    start_correct = pd.to_datetime('01/12/2025', dayfirst=True)
    print(f"Correct start date from '01/12/2025': {start_correct}")

if __name__ == "__main__":
    test_pandas_behavior()
