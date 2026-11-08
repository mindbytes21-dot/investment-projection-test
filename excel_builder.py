"""
Excel builder for the Investment Projection tool (no GUI dependencies).

build_workbook(...) accepts a file path OR a file-like object (e.g. io.BytesIO),
so it works both on a desktop and inside a web app.
"""

from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo


def build_workbook(ticker, price, amount, years, annual_rate_pct, comp_per_year, path):
    """Create the Excel file. Table cells are formulas that reference the Inputs sheet."""
    wb = Workbook()
    wb.calculation.fullCalcOnLoad = True  # make Excel calculate formulas on open

    # ---- shared styles ----
    navy = "1F3864"
    header_fill = PatternFill("solid", fgColor=navy)
    header_font = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
    input_font = Font(color="0000FF", name="Calibri", size=11)  # blue = editable input
    label_font = Font(bold=True, name="Calibri", size=11)
    thin = Side(style="thin", color="D0D7E5")
    box = Border(left=thin, right=thin, top=thin, bottom=thin)
    money = '"$"#,##0.00'
    pct = "0.0%"

    # ================= Inputs sheet =================
    ws_in = wb.active
    ws_in.title = "Inputs"
    ws_in.sheet_view.showGridLines = False

    ws_in["A1"] = f"Investment Projection: {ticker}"
    ws_in["A1"].font = Font(bold=True, size=16, color=navy)
    ws_in["A2"] = "Blue cells are inputs you can change. Everything else recalculates."
    ws_in["A2"].font = Font(italic=True, color="666666")

    rows = [
        ("Ticker", ticker, None),
        ("Current price per share", float(price), money),
        ("Amount invested today", float(amount), money),
        ("Shares purchased", "=B5/B4", '#,##0.0000'),
        ("Time horizon (years)", int(years), "0"),
        ("Expected annual return", annual_rate_pct / 100.0, pct),
        ("Compounding periods per year", int(comp_per_year), "0"),
    ]
    for i, (label, value, fmt) in enumerate(rows, start=3):
        ws_in.cell(row=i, column=1, value=label).font = label_font
        c = ws_in.cell(row=i, column=2, value=value)
        c.border = box
        c.alignment = Alignment(horizontal="right")
        if fmt:
            c.number_format = fmt
        if label != "Shares purchased":
            c.font = input_font
        ws_in.cell(row=i, column=1).border = box

    last = years + 2  # last data row on the Projection sheet
    ws_in["A11"] = "Results"
    ws_in["A11"].font = Font(bold=True, size=13, color=navy)
    results = [
        ("Projected value", f"=Projection!D{last}", money),
        ("Total gain", f"=Projection!F{last}", money),
        ("Total return", f"=Projection!G{last}", pct),
        ("Implied price per share", f"=Projection!H{last}", money),
    ]
    for i, (label, formula, fmt) in enumerate(results, start=12):
        ws_in.cell(row=i, column=1, value=label).font = label_font
        c = ws_in.cell(row=i, column=2, value=formula)
        c.number_format = fmt
        c.border = box
        c.alignment = Alignment(horizontal="right")
        ws_in.cell(row=i, column=1).border = box

    ws_in["A17"] = ("Disclaimer: what-if illustration only. Assumes a constant return, "
                    "no fees, taxes or inflation.")
    ws_in["A17"].font = Font(italic=True, color="888888", size=9)
    ws_in.column_dimensions["A"].width = 34
    ws_in.column_dimensions["B"].width = 20

    # ================= Projection sheet =================
    ws = wb.create_sheet("Projection")
    headers = ["Year", "Start Value ($)", "Growth ($)", "End Value ($)",
               "Amount Invested ($)", "Total Gain ($)", "Total Return (%)",
               "Implied Share Price ($)"]
    ws.append(headers)

    for year in range(0, years + 1):
        r = year + 2
        end_formula = f"=Inputs!$B$5*(1+Inputs!$B$8/Inputs!$B$9)^(Inputs!$B$9*A{r})"
        start_formula = f"=D{r}" if year == 0 else f"=D{r - 1}"
        ws.append([
            year,
            start_formula,
            f"=D{r}-B{r}",
            end_formula,
            "=Inputs!$B$5",
            f"=D{r}-E{r}",
            f"=F{r}/E{r}",
            f"=D{r}/Inputs!$B$6",
        ])

    # formatting
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 32
    for r in range(2, last + 1):
        ws.cell(row=r, column=1).alignment = Alignment(horizontal="center")
        for col in (2, 3, 4, 5, 6, 8):
            ws.cell(row=r, column=col).number_format = money
        ws.cell(row=r, column=7).number_format = pct
    widths = [8, 17, 15, 17, 19, 16, 16, 22]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + i)].width = w
    ws.freeze_panes = "A2"

    table = Table(displayName="ProjectionTable", ref=f"A1:H{last}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(table)

    # ---- native Excel line chart ----
    chart = LineChart()
    chart.title = f"{ticker}: projected growth at {annual_rate_pct:g}% per year"
    chart.height = 11
    chart.width = 22
    chart.y_axis.title = "Portfolio value ($)"
    chart.x_axis.title = "Years"
    chart.y_axis.numFmt = '"$"#,##0'
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    chart.legend.position = "b"

    chart.add_data(Reference(ws, min_col=4, min_row=1, max_row=last), titles_from_data=True)
    chart.add_data(Reference(ws, min_col=5, min_row=1, max_row=last), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=last))

    growth_series, invested_series = chart.series
    growth_series.marker.symbol = "circle"
    growth_series.marker.size = 6
    growth_series.graphicalProperties.line.solidFill = "1F77B4"
    growth_series.graphicalProperties.line.width = 28575
    growth_series.smooth = False
    invested_series.graphicalProperties.line.solidFill = "7F7F7F"
    invested_series.graphicalProperties.line.dashStyle = "dash"
    invested_series.graphicalProperties.line.width = 22225
    invested_series.smooth = False

    ws.add_chart(chart, "J2")

    wb.save(path)
    return path


def projected_value(amount, years, annual_rate_pct, comp_per_year):
    return amount * (1 + annual_rate_pct / 100 / comp_per_year) ** (comp_per_year * years)
