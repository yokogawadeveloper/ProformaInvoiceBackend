import copy, re
import pandas as pd, numpy as np
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status

# from .models import proformaItemMaster, proformaItem
from excelupload.models import  proformaItemMaster, proformaItem
from orderack.models import orderAcknowledgement, orderAcknowledgementHistory

pattern = re.compile(r"^(\w+)(,\s*\w+)*$")


def data_crud(obj, val, user):

    global unit_price
    proforma_item = ['OAItemNo', 'item_no', 'material_desc', 'qty', 'uom',
                     'unit_price', 'unit_type', 'total_price', 'total_type', 'part_name', 'cust_part_no',
                     'cust_part_sl_no', 'hsn', 'dis_percent', 'dis_amt', 'item_val_with_dis', 'mat_ready_date',
                     'pf_percent', 'pf_amount', 'item_val_with_pf', 'freight_percent', 'freight_amount',
                     'exclude_gst_amt', 'sgst_percent', 'sgst_amt', 'cgst_percent', 'cgst_amt', 'igst_percent',
                     'igst_amt', 'item_value_with_gst']

    proforma_master = ['doc_no', 'doc_date', 'supplier', 'telephone', 'website', 'sold_to_code',
                       'sold_to_address', 'ship_to_code', 'ship_to_address', 'end_user_code', 'end_user_address',
                       'bill_to_code', 'bill_to_address', 'cus_ref_desc', 'cus_delivery_date', 'inco_terms',
                       'sales_office', 'yil_contact_person', 'approver', 'section', 'email', 'telephone', 'po_no',
                       'po_date', 'indent_no', 'remarks','payment_terms', 'doc_ref_no', 'total_item_value']

    df = pd.DataFrame(columns=proforma_item)
    dfm = pd.DataFrame(columns=proforma_master)

    copy_col_list = copy.deepcopy(val)

    count = 0
    count_dfm = 0

    for i in range(len(val)):
        if val[i] == 120:
            if i != 0:
                count += 1
            df.loc[count, 'OAItemNo'] = obj.loc[i, 'col_0']
            df.loc[count, 'item_no'] = obj.loc[i, 'col_31']
            df.loc[count, 'material_desc'] = obj.loc[i, 'col_32']
            if pattern.match(str(obj.loc[i, 'col_33'])) is not None:
                obj.loc[i, 'col_33'] = int(str(obj.loc[i, 'col_33']).replace(',', ''))
            df.loc[count, 'qty'] = obj.loc[i, 'col_33']
            df.loc[count, 'uom'] = obj.loc[i, 'col_34']
            if pd.isna(obj.loc[i, 'col_35']):
                obj.loc[i, 'col_35'] = '0.00'
            for char in str(obj.loc[i, 'col_35']):
                if char.isdigit():
                    unit_price = str(obj.loc[i, 'col_35'])
                    df.loc[count, 'unit_price'] = "".join(unit_price.split(","))
                else:
                    unit_price = 0
            if unit_price == 'nan':
                df.loc[count, 'unit_price'] = 0
            df.loc[count, 'unit_type'] = obj.loc[i, 'col_36']
            total_price = str(obj.loc[i, 'col_37'])
            df.loc[count, 'total_price'] = "".join(total_price.split(","))
            if total_price == 'nan':
                df.loc[count, 'total_price'] = 0
            df.loc[count, 'total_type'] = obj.loc[i, 'col_38']
            df.loc[count, 'part_name'] = obj.loc[i, 'col_39']

            copy_col_list.remove(val[i])

        elif val[i] == 180:
            item_value_with_gst = str(obj.loc[i, 'col_60'])
            df.loc[count, 'item_value_with_gst'] = "".join(item_value_with_gst.split(','))

            dfm.loc[count_dfm, 'doc_no'] = obj.loc[i, 'col_2']

            if not pd.isna(obj.loc[i, 'col_4']):
                dt_col_4 = obj.loc[i, 'col_4'].split(".")
                dt_col_4 = "".join(dt_col_4)
                dfm.loc[count_dfm, 'doc_date'] = datetime.strptime(dt_col_4, '%d%m%Y').date()
                dfm.loc[count_dfm, 'doc_date'] = dfm.loc[count_dfm, 'doc_date'].strftime("%Y-%m-%d")
            else:
                dfm.loc[count_dfm, 'doc_date'] = obj.loc[i, 'col_4']

            dfm.loc[count_dfm, 'supplier'] = obj.loc[i, 'col_5']
            dfm.loc[count_dfm, 'telephone'] = obj.loc[i, 'col_6']
            dfm.loc[count_dfm, 'website'] = obj.loc[i, 'col_7']
            dfm.loc[count_dfm, 'sold_to_code'] = obj.loc[i, 'col_8']
            dfm.loc[count_dfm, 'sold_to_address'] = obj.loc[i, 'col_9']
            dfm.loc[count_dfm, 'ship_to_code'] = obj.loc[i, 'col_10']
            dfm.loc[count_dfm, 'ship_to_address'] = obj.loc[i, 'col_11']
            dfm.loc[count_dfm, 'end_user_code'] = obj.loc[i, 'col_12']
            dfm.loc[count_dfm, 'end_user_address'] = obj.loc[i, 'col_13']
            dfm.loc[count_dfm, 'bill_to_code'] = obj.loc[i, 'col_14']
            dfm.loc[count_dfm, 'bill_to_address'] = obj.loc[i, 'col_15']
            dfm.loc[count_dfm, 'cus_ref_desc'] = obj.loc[i, 'col_16']

            if not pd.isna(obj.loc[i, 'col_17']):
                dt_col_17 = obj.loc[i, 'col_17'].split(".")
                dt_col_17 = "".join(dt_col_17)
                dfm.loc[count_dfm, 'cus_delivery_date'] = datetime.strptime(dt_col_17, '%d%m%Y').date()
                dfm.loc[count_dfm, 'cus_delivery_date'] = dfm.loc[count_dfm, 'cus_delivery_date'].strftime("%Y-%m-%d")
            else:
                dfm.loc[count_dfm, 'cus_delivery_date'] = obj.loc[i, 'col_17']

            dfm.loc[count_dfm, 'inco_terms'] = obj.loc[i, 'col_18']
            dfm.loc[count_dfm, 'sales_office'] = obj.loc[i, 'col_19']
            dfm.loc[count_dfm, 'yil_contact_person'] = obj.loc[i, 'col_20']
            dfm.loc[count_dfm, 'approver'] = obj.loc[i, 'col_21']
            dfm.loc[count_dfm, 'section'] = obj.loc[i, 'col_22']
            dfm.loc[count_dfm, 'email'] = obj.loc[i, 'col_23']
            dfm.loc[count_dfm, 'telephone'] = obj.loc[i, 'col_24']
            dfm.loc[count_dfm, 'po_no'] = obj.loc[i, 'col_25']

            if not pd.isna(obj.loc[i, 'col_26']):
                dt_col_26 = obj.loc[i, 'col_26'].split(".")
                dt_col_26 = "".join(dt_col_26)
                dfm.loc[count_dfm, 'po_date'] = datetime.strptime(dt_col_26, '%d%m%Y').date()
                dfm.loc[count_dfm, 'po_date'] = dfm.loc[count_dfm, 'po_date'].strftime("%Y-%m-%d")
            else:
                dfm.loc[count_dfm, 'po_date'] = obj.loc[i, 'col_26']

            dfm.loc[count_dfm, 'indent_no'] = obj.loc[i, 'col_27']
            dfm.loc[count_dfm, 'remarks'] = obj.loc[i, 'col_28']
            dfm.loc[count_dfm, 'payment_terms'] = obj.loc[i, 'col_29']
            dfm.loc[count_dfm, 'doc_ref_no'] = obj.loc[i, 'col_30']
            dfm.loc[count_dfm, 'total_item_value'] = obj.loc[i, 'col_31'].fill(0)

            copy_col_list.remove(val[i])

        else:
            if val[i] == 130:
                if "Customer Part No. :" in obj.loc[i, 'col_41']:
                    df.loc[count, 'cust_part_no'] = obj.loc[i, 'col_41']
                elif "Customer PO Sl. No. :" in obj.loc[i, 'col_41']:
                    df.loc[count, 'cust_part_sl_no'] = obj.loc[i, 'col_41']
                copy_col_list.remove(val[i])

            elif val[i] == 140:
                df.loc[count, 'hsn'] = obj.loc[i, 'col_42']
                copy_col_list.remove(val[i])

            elif val[i] == 150:
                if "Discount" in obj.loc[i, 'col_53']:
                    df.loc[count, 'dis_percent'] = 0
                    if not pd.isna(obj.loc[i, 'col_54']):
                        df.loc[count, 'dis_percent'] = np.abs(obj.loc[i, 'col_54'])

                    dis_amt = str(obj.loc[i, 'col_55'])
                    dis_amt = "".join(dis_amt.split("-"))
                    df.loc[count, 'dis_amt'] = "".join(dis_amt.split(","))
                if "P&F" in obj.loc[i, 'col_53']:
                    df.loc[count, 'pf_percent'] = float(obj.loc[i, 'col_54'])
                    pf_amount = str(obj.loc[i, 'col_55'])
                    df.loc[count, 'pf_amount'] = "".join(pf_amount.split(","))
                if "Freight" in obj.loc[i, 'col_53']:
                    df.loc[count, 'freight_percent'] = float(obj.loc[i, 'col_54'])
                    freight_amount = str(obj.loc[i, 'col_55'])
                    df.loc[count, 'freight_amount'] = "".join(freight_amount.split(","))
                copy_col_list.remove(val[i])

            elif val[i] == 160:
                exclude_gst_amt = str(obj.loc[i, 'col_56'])
                df.loc[count, 'exclude_gst_amt'] = "".join(exclude_gst_amt.split(","))
                copy_col_list.remove(val[i])

            elif val[i] == 170:
                if "CGST" in obj.loc[i, 'col_57']:
                    df.loc[count, 'cgst_percent'] = float(obj.loc[i, 'col_58'])
                    cgst_amt = str(obj.loc[i, 'col_59'])
                    df.loc[count, 'cgst_amt'] = "".join(cgst_amt.split(","))
                if "SGST" in obj.loc[i, 'col_57']:
                    df.loc[count, 'sgst_percent'] = float(obj.loc[i, 'col_58'])
                    sgst_amt = str(obj.loc[i, 'col_59'])
                    df.loc[count, 'sgst_amt'] = "".join(sgst_amt.split(","))
                if "IGST" in obj.loc[i, 'col_57']:
                    df.loc[count, 'igst_percent'] = float(obj.loc[i, 'col_58'])
                    igst_amt = str(obj.loc[i, 'col_59'])
                    df.loc[count, 'igst_amt'] = "".join(igst_amt.split(","))
                copy_col_list.remove(val[i])

            elif val[i] == 190:
                dt_col_40 = obj.loc[i, 'col_40'].split(".")
                dt_col_40 = "".join(dt_col_40)
                df.loc[count, 'mat_ready_date'] = datetime.strptime(dt_col_40, '%d%m%Y').date()
                df.loc[count, 'mat_ready_date'] = df.loc[count, 'mat_ready_date'].strftime("%Y-%m-%d")
                copy_col_list.remove(val[i])

            elif val[i] == 110:
                copy_col_list.remove(val[i])

    if val:
        val.clear()
        val = copy_col_list

        if not val:

            doc_no_filter = proformaItemMaster.objects.filter(DocNo=dfm.loc[0, 'doc_no'])
            if doc_no_filter.exists():
                doc_no_filter.filter(DocNo=dfm.loc[0, 'doc_no']).update(DeleteFlag=True, DeletedBy=user.id)
                proforma_master = doc_no_filter.filter(DocNo=dfm.loc[0, 'doc_no']).values('ProformaID')[0]
                proformaItem.objects.filter(
                    ProformaID=proforma_master['ProformaID']).update(DeleteFlag=True, DeletedBy_id=user.id)
                orderAcknowledgement.objects.filter(
                    ProformaID_id=proforma_master['ProformaID']).update(DeleteFlag=True, DeletedBy_id=user.id)
                orderAcknowledgementHistory.objects.filter(
                    ProformaID=proforma_master['ProformaID']).update(DeleteFlag=True, DeletedBy_id=user.id)

            dfm = dfm.where(dfm.notna(), None)
            df = df.where(df.notna(), None)

            row_iter = dfm.iterrows()
            row_iter1 = df.iterrows()

            master_objs = [

                proformaItemMaster(

                    DocNo=row['doc_no'], DocDate=row['doc_date'], Supplier=row['supplier'],
                    SupTelephone=row['telephone'],
                    Website=row['website'], SoldtoCode=row['sold_to_code'], SoldToAddress=row['sold_to_address'],
                    Shiptocode=row['ship_to_code'], Shiptoaddress=row['ship_to_address'],
                    EndUserCode=row['end_user_code'], EndUserAddress=row['end_user_address'],
                    Billtocode=row['bill_to_code'], Billtoaddress=row['bill_to_address'], CusRefDesc=row['cus_ref_desc'],
                    CusDeliverydate=row['cus_delivery_date'], Incoterms=row['inco_terms'],
                    SalesOffice=row['sales_office'], YilContactperson=row['yil_contact_person'],
                    Approver=row['approver'],
                    Section=row['section'], Email=row['email'],
                    Telephone=row['telephone'], PONo=row['po_no'], PoDate=row['po_date'], IndentNo=row['indent_no'],
                    Remarks=row['remarks'], PaymentTerms=row['payment_terms'],
                    DocrefNo=row['doc_ref_no'], TotalItemvalue=row['total_item_value'], SubmittedBy=user,

                )

                for index, row in row_iter

            ]

            proformaItemMaster.objects.bulk_create(master_objs)

            pk = proformaItemMaster.objects.latest('ProformaID').pk

            objs = [

                proformaItem(

                    OAItemNo=row['OAItemNo'], ItemNo=row['item_no'], MaterialDesc=row['material_desc'],
                    Qtymodels=row['qty'],
                    UOM=row['uom'], UnitPrice=row['unit_price'], UnitType=row['unit_type'],
                    TotalPrice=row['total_price'], TotalType=row['total_type'], PartName=row['part_name'],
                    CusPartNo=row['cust_part_no'], CusPartSlno=row['cust_part_sl_no'], HSN=row['hsn'],
                    DiscountPercent=row['dis_percent'], DiscountAmount=row['dis_amt'],
                    ItemValuewithDiscount=row['exclude_gst_amt'],
                    PFpercent=row['pf_percent'], PFAmount=row['pf_amount'],
                    FreightPercent=row['freight_percent'], FreightAmount=row['freight_amount'],
                    MatReadyDate=row['mat_ready_date'], ItemValuewithPF=row['exclude_gst_amt'],
                    SGSTpercent=row['sgst_percent'], SGSTAmount=row['sgst_amt'],
                    CGSTPercent=row['cgst_percent'], CGSTAmount=row['cgst_amt'],
                    IGSTPercent=row['igst_percent'], IGSTAmount=row['igst_amt'],
                    ItemValuewithGST=row['item_value_with_gst'], ProformaID_id=pk,
                    SubmittedBy=user

                )

                for index, row in row_iter1

            ]

            proformaItem.objects.bulk_create(objs)

            return Response({"value": True, "message": "File has uploaded", "id": pk}, status=status.HTTP_201_CREATED)
    else:
        return Response({'message': 'Bad request', 'status': status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)




