import os
from datetime import datetime
import numpy as np
import pandas as pd
from rest_framework.response import Response


# change by gautam 2021-07-20
def dataListToExcel(data):
    col = ["SL.NO.", "MONTH", "DIVISION", "BU HEAD", "P M", "LOCATION", "CUSTOMER CODE",
           "CUSTOMER NAME", "SO NO/FAK", "PO NO", "PO Date", "PI NO", "PI DATE", "PI VALUE(INR)", "RECEIVED AMT(INR)",
           "RECD ON",
           "Balance in(INR)", "PI ADVANCE", "PI RETENTION", "PI TOTAL", "PI VALUE(USD)", "PI VALUE(BDT)", "CATEGORY",
           "DESCRIPTION", "REMARKS", "JOB CODE",
           "WBS", "BG NO/DT", "PI BASIC VALUE", "PAYMENT TERMS", "MATERIAL READINESS DATE", "DELETED REMARKS",
           "DELETED STATUS"]

    pi_total_value_inr = 0
    pi_total_value_usd = 0
    pi_total_value_bdt = 0

    df = pd.DataFrame(columns=col)
    summary_head = []
    div_arr = []
    count = 0

    for index, value in enumerate(data):
        if value['deleted_pi'] is True:
            styler = df.style
            styler.background_gradient({'background-color : yellow'})

        df.loc[index, "SL.NO."] = count + 1
        df.loc[index, "MONTH"] = datetime.strptime(value['submitDate'], '%d-%m-%Y').date()
        df.loc[index, "MONTH"] = df.loc[index, "MONTH"].strftime("%d-%b-%y")
        df.loc[index, "DIVISION"] = value['divisionName']
        df.loc[index, "BU HEAD"] = value['buHead']
        df.loc[index, "P M"] = value['pmName']
        df.loc[index, "LOCATION"] = value['regionName']
        df.loc[index, "CUSTOMER CODE"] = value['customerCode']
        df.loc[index, "CUSTOMER NAME"] = value['customerName']
        df.loc[index, "SO NO/FAK"] = value['docNo']
        df.loc[index, "PO NO"] = value['poNo']  # Adding PO No
        df.loc[index, "PO Date"] = datetime.strptime(value['poDate'], '%Y-%m-%d').date()  # Corrected date format
        df.loc[index, "PI NO"] = value['pi_no']
        df.loc[index, "PI DATE"] = datetime.strptime(value['submitDate'], '%d-%m-%Y').date()
        df.loc[index, "PI DATE"] = df.loc[index, "PI DATE"].strftime("%d/%m/%Y")
        df.loc[index, "PI VALUE(INR)"] = value['pi_total']
        df.loc[index, "RECEIVED AMT(INR)"] = 0
        df.loc[index, "RECD ON"] = '-'
        df.loc[index, "Balance in(INR)"] = value['balance_value']
        df.loc[index, "PI ADVANCE"] = value['pi_advance']
        df.loc[index, "PI RETENTION"] = value['pi_retention']
        df.loc[index, "PI TOTAL"] = value['pi_value_inr']
        df.loc[index, "PI VALUE(USD)"] = value['pi_value_usd']
        df.loc[index, "PI VALUE(BDT)"] = value['pi_value_bdt']
        df.loc[index, "CATEGORY"] = value['categoryName']
        df.loc[index, "DESCRIPTION"] = ','.join([str(elem) for elem in value['description']])
        df.loc[index, "REMARKS"] = value['remarks']
        df.loc[index, "JOB CODE"] = value['jobcode']
        df.loc[index, "WBS"] = value['wbs']
        df.loc[index, "BG NO/DT"] = value['bgno_dt']
        df.loc[index, "PI BASIC VALUE"] = ""
        df.loc[index, "PAYMENT TERMS"] = value['payment_terms']
        df.loc[index, "MATERIAL READINESS DATE"] = value['mat_ready_date']
        df.loc[index, "DELETED REMARKS"] = value['deleted_remarks']
        df.loc[index, "DELETED STATUS"] = value['delete_status']

        pi_total_value_inr += value['pi_value_inr']
        pi_total_value_usd += value['pi_value_usd']
        pi_total_value_bdt += value['pi_value_bdt']
        count += 1
        # For summary
        month_val = datetime.strptime(value['submitDate'], '%d-%m-%Y').date()
        summary_head.append(month_val.strftime("%b-%y"))
        div_arr.append(value['divisionName'])
    # for excel
    writer = pd.ExcelWriter(os.path.abspath('static/{}.xlsx'.format("proforma_report")), engine='xlsxwriter')
    sheet_name = "PI UPTO - " + df['MONTH'].iloc[-1]
    df.to_excel(writer, sheet_name=sheet_name, startrow=4, index=False, header=True)
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    org = "YOKOGAWA INDIA LIMITED"
    pi_status = "PI - COLLECTION LIST FR " + df["MONTH"][0] + ' - ' + df['MONTH'].iloc[-1]
    worksheet.write(1, 1, org)
    worksheet.write(2, 1, pi_status)
    worksheet.write(2, 11, pi_total_value_inr)
    worksheet.write(2, 15, pi_total_value_usd)
    worksheet.write(2, 16, pi_total_value_bdt)
    worksheet.freeze_panes(5, 1)
    # formatting the Excel
    format1 = workbook.add_format({})
    format2 = workbook.add_format({"bg_color": "#669731"})
    format3 = workbook.add_format({"align": "center", "bold": True})
    # worksheet set column
    worksheet.set_column('A:A', 10, format3)
    worksheet.set_column('B:B', 18, format1)
    worksheet.set_column('C:C', 18, format1)
    worksheet.set_column('D:D', 18, format1)
    worksheet.set_column('E:E', 18, format1)
    worksheet.set_column('F:F', 18, format1)
    worksheet.set_column('G:G', 18, format1)
    worksheet.set_column('H:H', 18, format1)
    worksheet.set_column('I:I', 18, format1)
    worksheet.set_column('J:J', 18, format1)
    worksheet.set_column('K:K', 18, format1)
    worksheet.set_column('L:L', 18, format1)
    worksheet.set_column('M:M', 18, format1)
    worksheet.set_column('N:N', 18, format1)
    worksheet.set_column('O:O', 18, format1)
    worksheet.set_column('P:P', 18, format1)
    worksheet.set_column('Q:Q', 18, format1)
    worksheet.set_column('R:R', 18, format1)
    worksheet.set_column('S:S', 18, format1)
    worksheet.set_column('T:T', 18, format1)
    worksheet.set_column('U:U', 18, format1)
    worksheet.set_column('V:V', 18, format1)
    worksheet.set_column('W:W', 18, format1)
    worksheet.set_column('X:X', 18, format1)
    worksheet.set_column('Y:Y', 18, format1)
    worksheet.set_column('Z:Z', 18, format1)
    worksheet.set_column('AA:AA', 18, format1)
    worksheet.set_column('AB:AB', 18, format1)
    worksheet.set_column('AC:AC', 18, format1)
    worksheet.set_column('AD:AD', 18, format1)
    worksheet.set_column('AE:AE', 18, format1)

    worksheet.conditional_format('B4:R4', {'type': 'no_blanks', 'format': format1})
    worksheet.conditional_format('B2', {"type": "formula", "criteria": '=($B$2="y")', "format": format2})
    number_rows = len(df.index) + 4
    format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    worksheet.conditional_format("$A$4:$AE$%d" % (number_rows),
                                 {"type": "formula",
                                  "criteria": '=INDIRECT("AE"&ROW())="Deleted"',
                                  "format": format
                                  }
                                 )

    summary_head = list(dict.fromkeys(summary_head))
    summary_head.insert(0, "Row Labels")
    summary_head.append("Grand Total")

    division = list(dict.fromkeys(div_arr))

    # Summary Report
    # df_rp = pd.DataFrame(columns=summary_head)

    df_sam = pd.DataFrame(data)
    df_rp = df_sam.filter(['divisionName', 'regionName', 'submitDate', 'pi_value_inr']).dropna()
    df_rp = pd.pivot_table(df_rp, values='pi_value_inr', index=['divisionName', 'regionName'], columns=['submitDate'],
                           aggfunc=np.sum)
    writer.save()
    return Response(True)
