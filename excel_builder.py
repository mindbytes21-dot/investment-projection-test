"""
Excel builder for the Investment Projection tool (no UI dependencies).

build_workbook(...) accepts a file path OR a file-like object (e.g. io.BytesIO),
so it works on a desktop and inside a web app.

Workbook layout
  Inputs      assumptions (blue = editable) and a results summary
  Projection  year-by-year table (live formulas) plus a native Excel line chart
"""

from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo

from calc import MAX_YEARS, normalize_ticker

# Cell addresses on the Inputs sheet: the single source of truth for every formula.
PRICE_CELL, AMOUNT_CELL, SHARES_CELL = "B4", "B5", "B6"
YEARS_CELL, RATE_CELL, COMP_CELL = "B7", "B8", "B9"

NAVY = "1F3864"
MONEY = '"$"#,##0.00'
PRICE_FMT = '"$"#,##0.00##'      # shows up to 4 decimals for sub-dollar prices
PCT = "0.0%"


def _ref(cell):
    """'B5' -> 'Inputs!$B$5' (absolute reference to the Inputs sheet)."""
    return f"Inputs!${cell[0]}${cell[1:]}"


def build_workbook(ticker, price, amount, years, annual_rate_pct, comp_per_year, target):
    """Create the workbook and save it to `target` (path or file-like). Returns target."""
    ticker = normalize_ticker(ticker)  # also blocks formula-injection such as "=1+1"
    if not (price > 0 and amount > 0 and comp_per_year >= 1 and 1 <= years <= MAX_YEARS):
        raise ValueError("Invalid projection inputs.")
    years = int(years)

    wb = Workbook()
    wb.calculation.fullCalcOnLoad = True  # make Excel calculate formulas on open

    header_fill = PatternFill("solid", fgColor=NAVY)
    header_font = Font(bold=True, color="FFFFFF", size=11)
    input_font = Font(color="0000FF", size=11)   # blue = cell you can edit
    plain_font = Font(color="000000", size=11)
    label_font = Font(bold=True, size=11)
    thin = Side(style="thin", color="D0D7E5")
    box = Border(left=thin, right=thin, top=thin, bottom=thin)

    # ================= Inputs sheet =================
    ws_in = wb.active
    ws_in.title = "Inputs"
    ws_in.sheet_view.showGridLines = False

    ws_in["A1"] = f"Investment Projection: {ticker}"
    ws_in["A1"].font = Font(bold=True, size=16, color=NAVY)
    ws_in["A2"] = "Blue cells are inputs you can change. Everything else recalculates."
    ws_in["A2"].font = Font(italic=True, color="666666")

    # (label, value, number format, editable?)
    rows = [
        ("Ticker", ticker, None, False),
        ("Current price per share", float(price), PRICE_FMT, True),
        ("Amount invested today", float(amount), MONEY, True),
        ("Shares purchased", f"={AMOUNT_CELL}/{PRICE_CELL}", "#,##0.0000", False),
        ("Time horizon (years, fixed)", years, "0", False),
        ("Expected annual return", annual_rate_pct / 100.0, PCT, True),
        ("Compounding periods per year", int(comp_per_year), "0", True),
    ]
    for i, (label, value, fmt, editable) in enumerate(rows, start=3):
        lab = ws_in.cell(row=i, column=1, value=label)
        lab.font = label_font
        lab.border = box
        cell = ws_in.cell(row=i, column=2, value=value)
        cell.border = box
        cell.alignment = Alignment(horizontal="right")
        cell.font = input_font if editable else plain_font
        if fmt:
            cell.number_format = fmt

    last = years + 2  # last data row on the Projection sheet
    ws_in["A11"] = "Results"
    ws_in["A11"].font = Font(bold=True, size=13, color=NAVY)
    results = [
        ("Projected value", f"=Projection!D{last}", MONEY),
        ("Total gain", f"=Projection!F{last}", MONEY),
        ("Total return", f"=Projection!G{last}", PCT),
        ("Implied price per share", f"=Projection!H{last}", PRICE_FMT),
    ]
    for i, (label, formula, fmt) in enumerate(results, start=12):
        lab = ws_in.cell(row=i, column=1, value=label)
        lab.font = label_font
        lab.border = box
        cell = ws_in.cell(row=i, column=2, value=formula)
        cell.number_format = fmt
        cell.border = box
        cell.alignment = Alignment(horizontal="right")

    ws_in["A17"] = ("Disclaimer: what-if illustration only. Assumes a constant return, "
                    "no fees, taxes or inflation. Not financial advice.")
    ws_in["A17"].font = Font(italic=True, color="888888", size=9)
    ws_in.column_dimensions["A"].width = 34
    ws_in.column_dimensions["B"].width = 20

    # ================= Projection sheet =================
    ws = wb.create_sheet("Projection")
    headers = ["Year", "Start Value ($)", "Growth ($)", "End Value ($)",
               "Amount Invested ($)", "Total Gain ($)", "Total Return (%)",
               "Implied Share Price ($)"]
    ws.append(headers)

    amount_ref, rate_ref = _ref(AMOUNT_CELL), _ref(RATE_CELL)
    comp_ref, shares_ref = _ref(COMP_CELL), _ref(SHARES_CELL)
    for year in range(0, years + 1):
        r = year + 2
        ws.append([
            year,
            f"=D{r}" if year == 0 else f"=D{r - 1}",
            f"=D{r}-B{r}",
            f"={amount_ref}*(1+{rate_ref}/{comp_ref})^({comp_ref}*A{r})",
            f"={amount_ref}",
            f"=D{r}-E{r}",
            f"=F{r}/E{r}",
            f"=D{r}/{shares_ref}",
        ])

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 32
    for r in range(2, last + 1):
        ws.cell(row=r, column=1).alignment = Alignment(horizontal="center")
        for col in (2, 3, 4, 5, 6):
            ws.cell(row=r, column=col).number_format = MONEY
        ws.cell(row=r, column=7).number_format = PCT
        ws.cell(row=r, column=8).number_format = PRICE_FMT
    for letter, width in zip("ABCDEFGH", [8, 17, 15, 17, 19, 16, 16, 22]):
        ws.column_dimensions[letter].width = width
    ws.freeze_panes = "A2"

    table = Table(displayName="ProjectionTable", ref=f"A1:H{last}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(table)

    # ---- native Excel line chart ----
    chart = LineChart()
    chart.title = f"{ticker}: projected growth at {annual_rate_pct:g}% per year"
    chart.height, chart.width = 11, 22
    chart.y_axis.title = "Portfolio value ($)"
    chart.x_axis.title = "Years"
    chart.y_axis.numFmt = '"$"#,##0'
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    chart.legend.position = "b"
    chart.add_data(Reference(ws, min_col=4, min_row=1, max_row=last), titles_from_data=True)
    chart.add_data(Reference(ws, min_col=5, min_row=1, max_row=last), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=last))

    value_series, invested_series = chart.series
    value_series.marker.symbol = "circle"
    value_series.marker.size = 6
    value_series.graphicalProperties.line.solidFill = "1F77B4"
    value_series.graphicalProperties.line.width = 28575
    value_series.smooth = False
    invested_series.graphicalProperties.line.solidFill = "7F7F7F"
    invested_series.graphicalProperties.line.dashStyle = "dash"
    invested_series.graphicalProperties.line.width = 22225
    invested_series.smooth = False
    ws.add_chart(chart, "J2")

    wb.save(target)
    return target
