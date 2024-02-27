import os

from rest_framework.views import APIView
from rest_framework import viewsets

from rest_framework.response import Response
from django.core.files.storage import default_storage

import os.path
import pandas as pd
from rest_framework.decorators import action
from django.db.models import Q
from rest_framework import permissions


from .serializer import proformaItemSerializer, proformaItemMasterSerializer, proformaMasterSerializer
from .models import proformaItem, proformaItemMaster
from .dataframe import data_crud



class DataCrud(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    def post(self, request, Format=None):
        if True:
            for file in request.FILES:
                file_name = default_storage.delete(os.path.abspath('static/inputFiles/{}.csv'.format(file)))
                file_name = default_storage.save(os.path.abspath('static/inputFiles/{}.csv'.format(file)),
                                                 request.FILES[file])

            col_names = ["col_" + str(i) for i in range(83)]
            prod_list = pd.read_csv(os.path.abspath('static/inputFiles/prod_line_item.csv'), sep='\t', names=col_names)
            # prod_list = prod_list.to_dict('records')
            # # save prod_list into a excel file
            # df = pd.DataFrame(prod_list)
            # df.to_excel(os.path.abspath('static/inputFiles/prod_line_item_output.xlsx'), index=False)

            
            # return Response({
            #     "status": True,
            # })

            df = pd.DataFrame(prod_list)
            df_list = df["col_0"].tolist()

            data = data_crud(df, df_list, request.user)

        return Response(data.data)


class proformaItemMasterViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = proformaItemMaster.objects.all()
    serializer_class = proformaItemMasterSerializer

    def get_queryset(self):
        query_set = self.queryset.exclude(DeleteFlag=True)
        return query_set

    def list(self, request, *args, **kwargs):
        # query_params = request.query_params.dict()
        # offset = int(query_params.pop('offset', 0))
        # end = int(query_params.pop('end', 5))
        queryset = self.get_queryset()
        # queryset = queryset[offset:end]
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        total_records = queryset.count()
        return Response({'records': serializer.data, 'totalRecords': total_records})

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(ProformaID=kwargs['pk']).first()
        serializer = self.serializer_class(queryset)
        serializer = {"records": serializer.data}
        if queryset is None:
            serializer = {"records": "No data available", "status": False}
        return Response(serializer)

    @action(methods=['post'], detail=False, url_path='doc_no')
    def getProformaDocNo(self, request):
        data = request.data
        doc_no_filter = proformaItemMaster.objects.filter(DocNo=data)
        if doc_no_filter:
            return Response({"value": True})
        else:
            return Response({"value": False})

    # @action(methods=['get'], detail=False, url_path='print_aoitem/(?P<id>[0-9]+)')
    # def OAItem_generatePDFWithLogo(self, request, id):
    #     proforma_instance = proformaItemMaster.objects.get(pk=id)
    #     proforma_serializer = proformaItemMasterSerializer(proforma_instance, context={'request': request})
    #     data = proforma_serializer.data
    #
    #     order_ack = orderAcknowledgement.objects.filter(ProformaID=id).last()
    #     order_ack_serializer = orderAcknowledgementSerializer(order_ack, context={'request': request})
    #     order_ack_data = order_ack_serializer.data
    #
    #     filename = "OrderItem__%s.pdf" % proforma_instance.ProformaID
    #     content = "inline; filename='%s'" % filename
    #
    #     data['DocNo'] = str(proforma_serializer.data['DocNo'])
    #     data['DocDate'] = datetime.datetime.strptime(str(proforma_serializer.data['DocDate']), '%Y-%m-%d').date()
    #     data['DocDate'] = data['DocDate'].strftime("%d/%m/%Y")
    #     data['PONo'] = str(proforma_serializer.data['PONo'])
    #     data['PoDate'] = datetime.datetime.strptime(str(proforma_serializer.data['PoDate']), '%Y-%m-%d').date()
    #     data['PoDate'] = data['PoDate'].strftime("%d/%m/%Y")
    #     data['SoldtoCode'] = proforma_serializer.data['SoldtoCode']
    #     data['SoldToAddress'] = proforma_serializer.data['SoldToAddress']
    #     data['SoldToAddress'] = data['SoldToAddress'].replace('\u000b', '\n')
    #     data['Shiptocode'] = proforma_serializer.data['Shiptocode']
    #     data['Shiptoaddress'] = proforma_serializer.data['Shiptoaddress']
    #     data['Shiptoaddress'] = data['Shiptoaddress'].replace('\u000b', '\n')
    #     data['EndUserCode'] = proforma_serializer.data['EndUserCode']
    #     data['EndUserAddress'] = proforma_serializer.data['EndUserAddress']
    #     data['EndUserAddress'] = data['EndUserAddress'].replace('\u000b', '\n')
    #
    #     if data['Billtocode'] is not None:
    #         data['Billtocode'] = proforma_serializer.data['Billtocode']
    #         data['Billtoaddress'] = proforma_serializer.data['Billtoaddress']
    #         data['Billtoaddress'] = data['Billtoaddress'].replace('\u000b', '\n')
    #
    #     indent_no = proforma_serializer.data['IndentNo']
    #     indent_char_list = ["D", "H", "J", "K", "V", "M", "E", "B", "N", "U", "C", "P", "G", "L", "S"]
    #     sale_office_list = ["Delhi", "Hyderabad", "Bangladesh", "Kolkata", "Vizag", "Mumbai", "Cochin", "Baroda",
    #                         "Nagpur", "Bhutan", "Chennai", "Pune", "Surat", "Bangalore", "Corporate Sales"]
    #     global sales_office
    #     sales_office = ""
    #
    #     if indent_no:
    #         for index, value in enumerate(indent_char_list):
    #             if indent_no[1].upper() == value:
    #                 sales_office = sale_office_list[index]
    #
    #     data['Sales_Office'] = sales_office
    #
    #     data['Discount_Percent'] = proforma_serializer.data['items'][0]['DiscountPercent']
    #     data['PF_Percent'] = proforma_serializer.data['items'][0]['PFpercent']
    #     data['Freight_Percent'] = proforma_serializer.data['items'][0]['FreightPercent']
    #
    #     data['IGST_Percent'] = proforma_serializer.data['items'][0]['IGSTPercent']
    #     data['CGST_Percent'] = proforma_serializer.data['items'][0]['CGSTPercent']
    #     data['SGST_Percent'] = proforma_serializer.data['items'][0]['SGSTpercent']
    #
    #     data['PaymentTerms'] = proforma_serializer.data['PaymentTerms']
    #
    #     discount, pf, freight, cgst, sgst, igst, = 0, 0, 0, 0, 0, 0
    #     cgstp, sgstp, igstp = 0, 0, 0
    #     subtotal, total = 0, 0
    #
    #     for element in data['items']:
    #         if element['DiscountAmount'] is not None:
    #             discount += element['DiscountAmount']
    #         if element['PFAmount'] is not None:
    #             pf += element['PFAmount']
    #         if element['FreightAmount'] is not None:
    #             freight += element['FreightAmount']
    #         if element['TotalPrice'] is not None:
    #             subtotal += element['TotalPrice']
    #         if element['ItemValuewithGST'] is not None:
    #             total += element['ItemValuewithGST']
    #         if element['CGSTAmount'] is not None:
    #             cgst += element['CGSTAmount']
    #             cgstp = element['CGSTPercent']
    #         if element['SGSTAmount'] is not None:
    #             sgst += element['SGSTAmount']
    #             sgstp = element['SGSTpercent']
    #         if element['IGSTAmount'] is not None:
    #             igst += element['IGSTAmount']
    #             igstp = element['IGSTPercent']
    #
    #     data['TotalDiscount'] = discount
    #     data['TotalPf'] = pf
    #     data['TotalFreight'] = freight
    #     data['TotalCGST'] = cgst
    #     data['TotalSGST'] = sgst
    #     data['TotalIGST'] = igst
    #
    #     data['CGST_Percent'] = cgstp
    #     data['SGST_Percent'] = sgstp
    #     data['IGST_Percent'] = igstp
    #
    #     data['SubTotal'] = subtotal
    #     data['TotalAmount'] = total
    #
    #     if data['PaymentTerms'] is None:
    #         data['PaymentTerms'] = ""
    #     else:
    #         if "Payment Terms:" in data['PaymentTerms']:
    #             data['PaymentTerms'] = data['PaymentTerms'].split('Payment Terms:')
    #             data['PaymentTerms'] = data['PaymentTerms'][1]
    #
    #     if len(data['items']) != 0:
    #         data['MaterialReadinessDate'] = str(data['items'][0]['MatReadyDate'])
    #         data['MaterialReadinessDate'] = datetime.datetime.strptime(str(data['MaterialReadinessDate']), '%Y-%m-%dT%H:%M:%SZ').date()
    #         data['MaterialReadinessDate'] = data['MaterialReadinessDate'].strftime("%d/%m/%Y")
    #
    #     data['length'] = len(data['items'])
    #
    #     data['PIpdf'] = 'with'
    #     data['Party_Address'] = 'OAItemwithPDF'
    #
    #     if data['Billtoaddress'] is not None:
    #         x = proforma_serializer.data['Billtoaddress']
    #         x = x.split(",")
    #         x = x[0].split(".")
    #         if len(x) == 1:
    #             x = x[0].split("\u000b")
    #         else:
    #             x = x[1].split("\u000b")
    #         data['Consignee'] = x[0]
    #     else:
    #         x = proforma_serializer.data['Shiptoaddress']
    #         x = x.split(",")
    #         x = x[0].split(".")
    #         if len(x) == 1:
    #             x = x[0].split("\u000b")
    #         else:
    #             x = x[1].split("\u000b")
    #         data['Consignee'] = x[0]
    #
    #     path = os.path.abspath('static/images/header-image.png/')
    #     with open(path, "rb") as image_file:
    #         encoded_string = base64.b64encode(image_file.read()).decode('ascii')
    #         image64 = 'data:image/png;base64,{}'.format(encoded_string)
    #
    #         data['pdf_header_logo'] = image64
    #
    #     pdf_response = PDFTemplateResponse(
    #         request=request,
    #         template='oaitem.html',
    #         filename=filename,
    #         context=data,
    #         cmd_options={
    #             'title': filename,
    #             'margin-top': '50',
    #             'print-media-type': True
    #         },
    #         header_template = 'header_template.html',
    #
    #     )
    #     return pdf_response

    # @action(methods=['get'], detail=False, url_path='print_aoitem/(?P<id>[0-9]+)')
    # def OAItem_generatePDFWithLogo(self, request, id):
    #     proforma_instance = proformaItemMaster.objects.get(pk=id)
    #     proforma_serializer = proformaItemMasterSerializer(proforma_instance, context={'request': request})
    #     data = proforma_serializer.data
    #
    #     order_ack = orderAcknowledgement.objects.filter(ProformaID=id).last()
    #     order_ack_serializer = orderAcknowledgementSerializer(order_ack, context={'request': request})
    #     order_ack_data = order_ack_serializer.data
    #
    #     filename = "OrderItem__%s.pdf" % proforma_instance.ProformaID
    #     content = "inline; filename='%s'" % filename
    #
    #     data['DocNo'] = str(proforma_serializer.data['DocNo'])
    #     data['DocDate'] = datetime.datetime.strptime(str(proforma_serializer.data['DocDate']), '%Y-%m-%d').date()
    #     data['DocDate'] = data['DocDate'].strftime("%d/%m/%Y")
    #     data['PONo'] = str(proforma_serializer.data['PONo'])
    #     data['PoDate'] = datetime.datetime.strptime(str(proforma_serializer.data['PoDate']), '%Y-%m-%d').date()
    #     data['PoDate'] = data['PoDate'].strftime("%d/%m/%Y")
    #
    #     data['SoldtoCode'] = proforma_serializer.data['SoldtoCode']
    #     data['SoldToAddress'] = proforma_serializer.data['SoldToAddress']
    #     if data['SoldToAddress'] is not None:
    #         data['SoldToAddress_head'] = data['SoldToAddress'].replace('\u000b', '\n')
    #     else:
    #         data['SoldToAddress_head'] = ""
    #
    #     data['Shiptocode'] = proforma_serializer.data['Shiptocode']
    #     data['Shiptoaddress'] = proforma_serializer.data['Shiptoaddress']
    #     if data['Shiptoaddress'] is not None:
    #         data['Shiptoaddress_head'] = data['Shiptoaddress'].replace('\u000b', '\n')
    #     else:
    #         data['Shiptoaddress_head'] = ""
    #
    #     data['EndUserCode'] = proforma_serializer.data['EndUserCode']
    #     data['EndUserAddress'] = proforma_serializer.data['EndUserAddress']
    #     if data['EndUserAddress'] is not None:
    #         data['EndUserAddress_head'] = data['EndUserAddress'].replace('\u000b', '\n')
    #     else:
    #         data['EndUserAddress_head'] = ""
    #
    #     data['Billtocode'] = proforma_serializer.data['Billtocode']
    #     data['Billtoaddress'] = proforma_serializer.data['Billtoaddress']
    #     if data['Billtoaddress'] is not None:
    #         data['Billtoaddress_head'] = data['Billtoaddress'].replace('\u000b', '\n')
    #     else:
    #         data['Billtoaddress_head'] = ""
    #
    #     data['Party_Address'] = order_ack_data['Party_Address']
    #
    #     data['unitType'] = data['items'][0]['TotalType']
    #
    #     indent_no = proforma_serializer.data['IndentNo']
    #     indent_char_list = ["D", "H", "J", "K", "V", "M", "E", "B", "N", "U", "C", "P", "G", "L", "S"]
    #     sale_office_list = ["Delhi", "Hyderabad", "Bangladesh", "Kolkata", "Vizag", "Mumbai", "Cochin", "Baroda",
    #                         "Nagpur", "Bhutan", "Chennai", "Pune", "Surat", "Bangalore", "Corporate Sales"]
    #     global sales_office
    #     sales_office = ""
    #
    #     if indent_no:
    #         for index, value in enumerate(indent_char_list):
    #             if indent_no[1].upper() == value:
    #                 sales_office = sale_office_list[index]
    #
    #     data['Sales_Office'] = sales_office
    #
    #     data['Discount_Percent'] = proforma_serializer.data['items'][0]['DiscountPercent']
    #     data['PF_Percent'] = proforma_serializer.data['items'][0]['PFpercent']
    #     data['Freight_Percent'] = proforma_serializer.data['items'][0]['FreightPercent']
    #
    #     data['length'] = len(order_ack_data['order'])
    #
    #     data['order'] = order_ack_data['order']
    #
    #     data['Type'] = data['order'][0]['Type']
    #
    #     itemno = data['items']
    #     global itemval
    #     total_order_IGST, total_order_CGST, total_order_SGST = 0, 0, 0
    #     for i in itemno:
    #         for index, j in enumerate(data['order']):
    #             if i['ProformaItemid'] == j['ProformaItemid']:
    #                 j['ItemNo'] = i['ItemNo']
    #                 if j['PI_IGST'] is not None:
    #                     total_order_IGST += j['PI_IGST']
    #                 if j['PI_CGST'] is not None:
    #                     total_order_CGST += j['PI_CGST']
    #                 if j['PI_SGST'] is not None:
    #                     total_order_SGST += j['PI_SGST']
    #                 if j['ItemNo'] is not None:
    #                     itemval = index
    #                 if j['TotalAmount'] != 0:
    #                     data['order'][itemval]['TotalAmount'] = int(data['order'][itemval]['PI_Qty'] * data['order'][itemval]['UnitPrice'])
    #                     if j['ItemNo'] is None:
    #                         j['TotalAmount'] = 0
    #
    #     data['total_order_IGST'] = total_order_IGST
    #     data['total_order_CGST'] = total_order_CGST
    #     data['total_order_SGST'] = total_order_SGST
    #
    #     data['PaymentTerms'] = proforma_serializer.data['PaymentTerms']
    #
    #     if data['PaymentTerms'] is None:
    #         data['PaymentTerms'] = ""
    #     else:
    #         if "Payment Terms:" in data['PaymentTerms']:
    #             data['PaymentTerms'] = data['PaymentTerms'].split('Payment Terms:')
    #             data['PaymentTerms'] = data['PaymentTerms'][1]
    #
    #     if len(data['items']) != 0:
    #         data['MaterialReadinessDate'] = str(data['items'][0]['MatReadyDate'])
    #         data['MaterialReadinessDate'] = datetime.datetime.strptime(str(data['MaterialReadinessDate']), '%Y-%m-%dT%H:%M:%SZ').date()
    #         data['MaterialReadinessDate'] = data['MaterialReadinessDate'].strftime("%d/%m/%Y")
    #
    #     loop = proforma_serializer.data['items']
    #
    #     # data['IGST_Percent'] = proforma_serializer.data['items'][0]['IGSTPercent']
    #     IGST_Percent = proforma_serializer.data['items'][0]['IGSTPercent']
    #     if IGST_Percent is not None:
    #         if IGST_Percent.is_integer() is True:
    #             data['IGST_Percent'] = int(IGST_Percent)
    #         elif IGST_Percent.is_integer() is not True:
    #             data['IGST_Percent'] = IGST_Percent
    #         else:
    #             data['IGST_Percent'] = None
    #     else:
    #         data['IGST_Percent'] = None
    #         for index, value in enumerate(loop):
    #             if value['ItemNo'] is None and value['IGSTPercent']:
    #                 data['IGST_Percent'] = value['IGSTPercent']
    #                 break
    #
    #         if data['Type'] == 'M' or data['Type'] == 'A':
    #             if data['IGST_Percent'] is not None:
    #                 data['TotalAmount'] = order_ack_data['TotalUnitPrice']
    #                 data['TotalUnitPrice'] = float(order_ack_data['TotalUnitPrice']) - float(total_order_IGST)
    #
    #     # data['CGST_Percent'] = proforma_serializer.data['items'][0]['CGSTPercent']
    #     CGST_Percent = proforma_serializer.data['items'][0]['CGSTPercent']
    #     if CGST_Percent is not None:
    #         if CGST_Percent.is_integer() is True:
    #             data['CGST_Percent'] = int(CGST_Percent)
    #         elif CGST_Percent.is_integer() is not True:
    #             data['CGST_Percent'] = CGST_Percent
    #         else:
    #             data['CGST_Percent'] = None
    #     else:
    #         data['CGST_Percent'] = None
    #         for index, value in enumerate(loop):
    #             if value['ItemNo'] is None and value['CGSTPercent']:
    #                 data['CGST_Percent'] = value['CGSTPercent']
    #                 break
    #
    #     # data['SGST_Percent'] = proforma_serializer.data['items'][0]['SGSTpercent']
    #     SGST_Percent = proforma_serializer.data['items'][0]['SGSTpercent']
    #     if SGST_Percent is not None:
    #         if SGST_Percent.is_integer() is True:
    #             data['SGST_Percent'] = int(SGST_Percent)
    #         elif SGST_Percent.is_integer() is not True:
    #             data['SGST_Percent'] = SGST_Percent
    #         else:
    #             data['SGST_Percent'] = None
    #     else:
    #         data['SGST_Percent'] = None
    #         for index, value in enumerate(loop):
    #             if value['ItemNo'] is None and value['SGSTpercent']:
    #                 data['SGST_Percent'] = value['SGSTpercent']
    #                 break
    #
    #         if data['Type'] == 'M' or data['Type'] == 'A':
    #             if data['CGST_Percent'] is not None and data['SGST_Percent'] is not None:
    #                 data['TotalAmount'] = order_ack_data['TotalUnitPrice']
    #                 total_gst = total_order_CGST + total_order_SGST
    #                 data['TotalUnitPrice'] = float(order_ack_data['TotalUnitPrice']) - float(total_gst)
    #
    #     data['PIpdf'] = 'with'
    #
    #     data['TotalUnitPrice'] = order_ack_data['TotalUnitPrice']
    #     data['TotalAmount'] = order_ack_data['']
    #
    #     if data['Party_Address'] == 'shiptoparty':
    #         data['Shiptoaddress'] = proforma_serializer.data['Shiptoaddress']
    #         x = data['Shiptoaddress'].split(",")
    #         if x is not None:
    #             x = x[0].split("\u000b")
    #         else:
    #             x = '-'
    #         data['Consignee'] = x[0]
    #     elif data['Party_Address'] == 'soldtoparty':
    #         data['SoldToAddress'] = proforma_serializer.data['SoldToAddress']
    #         x = data['SoldToAddress'].split(",")
    #         if x is not None:
    #             x = x[0].split("\u000b")
    #         else:
    #             x = '-'
    #         data['Consignee'] = x[0]
    #     elif data['Party_Address'] == 'enduseraddress':
    #         data['EndUserAddress'] = proforma_serializer.data['EndUserAddress']
    #         x = data['EndUserAddress'].split(",")
    #         if x is not None:
    #             x = x[0].split("\u000b")
    #         else:
    #             x = '-'
    #         data['Consignee'] = x[0]
    #     elif data['Party_Address'] == 'billtoparty':
    #         x = proforma_serializer.data['Billtoaddress']
    #         x = x.split(",")
    #         if x is not None:
    #             x = x[0].split("\u000b")
    #         else:
    #             x = '-'
    #         data['Consignee'] = x[0]
    #
    #     path = os.path.abspath('static/images/header-image.png/')
    #     with open(path, "rb") as image_file:
    #         encoded_string = base64.b64encode(image_file.read()).decode('ascii')
    #         image64 = 'data:image/png;base64,{}'.format(encoded_string)
    #
    #         data['pdf_header_logo'] = image64
    #
    #     data['PI_TotalDiscount'] = order_ack_data['PI_TotalDiscount']
    #     data['PI_TotalPf'] = order_ack_data['PI_TotalPf']
    #     data['PI_TotalFreight'] = order_ack_data['PI_TotalFreight']
    #
    #     data['PI_TotalCGST'] = order_ack_data['PI_TotalCGST']
    #     data['PI_TotalSGST'] = order_ack_data['PI_TotalSGST']
    #     data['PI_TotalIGST'] = order_ack_data['PI_TotalIGST']
    #
    #     data['TotalAmount'] = order_ack_data['TotalAmount']
    #     data['TotalAmountWithTCS'] = order_ack_data['TotalAmountWithTCS']
    #
    #     pdf_response = PDFTemplateResponse(
    #         request=request,
    #         template='oaitem.html',
    #         filename=filename,
    #         context=data,
    #         cmd_options={
    #             'title': filename,
    #             'margin-top': '50',
    #             'print-media-type': True
    #         },
    #         header_template = 'header_template.html',
    #
    #     )
    #     return pdf_response


class proformaMasterViewSet(viewsets.ModelViewSet):
    # permission_classes = (permissions.IsAuthenticated, )
    queryset = proformaItemMaster.objects.all()
    serializer_class = proformaMasterSerializer

    def get_queryset(self):
        query_set = self.queryset.exclude(DeleteFlag=True)
        return query_set

    def list(self, request, *args, **kwargs):
        query_set = self.get_queryset()
        query_params = request.query_params.dict()
        if query_params:
            if query_params['so_no'] != '' or query_params['startDate'] != '' or query_params['endDate'] != '':

                so_no = query_params['so_no']
                start_date = query_params['startDate']
                end_date = query_params['endDate']

                query_set = query_set.filter(Q(DocNo__exact=so_no) |
                                             Q(DocDate__range=[start_date, end_date]))
        serializer = self.serializer_class(query_set, many=True, context={'request': request})
        serializer_data = serializer.data
        return Response({'records': serializer_data})


class proformaItemViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = proformaItem.objects.all()
    serializer_class = proformaItemSerializer

    def get_queryset(self):
        query_set = self.queryset.exclude(DeleteFlag=True)
        return query_set

    def list(self, request, *args, **kwargs):
        # query_params = request.query_params.dict()
        # offset = int(query_params.pop('offset', 0))
        # end = int(query_params.pop('end', 5))
        queryset = self.get_queryset()
        # queryset = queryset[offset:end]
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        total_records = queryset.count()
        return Response({'records': serializer.data, 'totalRecords': total_records})

    @action(methods=['get'], detail=False, url_path='retrieve_item/(?P<id>[0-9]+)')
    def retrieve_item(self, request, id):
        queryset = proformaItem.objects.filter(ProformaItemid=id)
        serializer = self.serializer_class(queryset, context={'request': request})
        return Response(serializer.data)
