# Investment Projection (web)

Enter a ticker (or fetch the live price), amount, years and expected return, then
download an Excel workbook with a year-by-year table (live formulas) and a native chart.

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit page |
| `calc.py` | Validation and compound-interest maths (pure, unit tested) |
| `pricing.py` | Live price lookup via Yahoo Finance (injectable, unit tested) |
| `excel_builder.py` | Builds the .xlsx |
| `styles.py` | Glass styling (black text on light glass surfaces) |
| `.streamlit/config.toml` | Forces the light theme so default text is black |
| `tests/` | Unit and UI tests |

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Test
    pip install -r requirements-dev.txt
    python -m pytest

## Deploy
Push this whole folder to GitHub (include the `.streamlit` folder), then create the app on
share.streamlit.io with main file `app.py`.
