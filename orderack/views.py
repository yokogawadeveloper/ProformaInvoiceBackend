import base64
import datetime
import os
from datetime import timedelta

from django.db.models import Count
from django.http import HttpResponse
from excelupload.models import proformaItem, proformaItemMaster
from excelupload.serializer import (proformaItemMasterSerializer,
                                    proformaItemSerializer)
from masterdata.models import (divisionMaster, projectManagerMaster,
                               regionMaster)
from masterdata.serializer import (divisionMasterSerializer,
                                   projectManagerMasterSerializer,
                                   regionMasterSerializer)
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from wkhtmltopdf.views import PDFTemplateResponse

from .common import generate_pi_no
from .export_to_excel import dataListToExcel
from .models import orderAcknowledgement, orderAcknowledgementHistory
from .serializer import (orderAcknowledgementHistorySerializer,
                         orderAcknowledgementSerializer, orderAckSerializer)

# Create your views here.


class orderAcknowledgementViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = orderAcknowledgement.objects.all()
    serializer_class = orderAcknowledgementSerializer

    def get_queryset(self):
        query_set = self.queryset.exclude(DeleteFlag=True).order_by('OrderAckId')
        return query_set

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_records = queryset.count()
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        serializer_data = serializer.data

        proformaId = []
        if len(serializer_data) != 0:
            for obj in serializer_data:
                proformaId.append(obj['ProformaID'])

        queryset = proformaItemMaster.objects.filter(ProformaID__in=proformaId)
        proforma_serializer = proformaItemMasterSerializer(queryset, many=True, context={'request': request})
        proforma_serializer_data = proforma_serializer.data

        return Response({'proforma': proforma_serializer_data, 'records': serializer_data, 'totalRecords': total_records})

    @action(methods=['post'], detail=False, url_path='based_on_proforma_id')
    def post_list(self, request):
        data = request.data
        queryset = self.get_queryset().filter(ProformaID_id=data['proforma_id'])
        total_records = queryset.count()
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response({'records': serializer.data, 'totalRecords': total_records})

    def create(self, request, *args, **kwargs):
        data = request.data
        count = [{'count': 1}]
        data['RevNo'] = count[0]['count']
        queryset = self.get_queryset()
        if queryset.filter(ProformaID=request.data['ProformaID']).exists():
            count = queryset.filter(ProformaID=request.data['ProformaID']).values(
                'ProformaID').annotate(count=Count('ProformaID'))
            data['RevNo'] += count[0]['count']

        new_pi = generate_pi_no()
        data['PI_NO'] = new_pi

        division_instance = divisionMaster.objects.get(DivisionId=data['DivisionId'])
        region_instance = regionMaster.objects.get(RegionId=data['RegionId'])

        division_serializer = divisionMasterSerializer(division_instance, context={'request': request})
        region_serializer = regionMasterSerializer(region_instance, context={'request': request})

        from datetime import date

        today = date.today()
        datestring = today.strftime("%Y-%m-%d")
        date = datetime.datetime.strptime(datestring, "%Y-%m-%d").date()

        global year

        if date.month > 3:
            year = date.year
        else:
            year = date.year - 1

        year = str(year)

        data['PI_CODE'] = "P" + '-' + division_serializer.data['Abbr'] + '-' + region_serializer.data['Abbr'] + '-' + year[-2:] + '-' + '%06d' % (data['PI_NO'])

        serializer = orderAcknowledgementSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'value': True, 'data': serializer.data})
        return Response(True)

    def update(self, request, *args, **kwargs):
        data = request.data

        pi_code_suffix = data['PI_CODE'].split('-')

        division_instance = divisionMaster.objects.get(DivisionId=data['DivisionId'])
        region_instance = regionMaster.objects.get(RegionId=data['RegionId'])

        division_serializer = divisionMasterSerializer(division_instance, context={'request': request})
        region_serializer = regionMasterSerializer(region_instance, context={'request': request})

        from datetime import date

        today = date.today()
        datestring = today.strftime("%Y-%m-%d")
        date = datetime.datetime.strptime(datestring, "%Y-%m-%d").date()

        global year

        if date.month > 3:
            year = date.year
        else:
            year = date.year - 1

        year = str(year)

        data['PI_CODE'] = "P" + '-' + division_serializer.data['Abbr'] + '-' + region_serializer.data['Abbr'] + '-' + year[-2:] + '-' + pi_code_suffix[-1]

        queries = self.get_queryset().filter(OrderAckId=kwargs['pk']).first()

        serializer = orderAcknowledgementSerializer(queries, data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'value': True, 'data': serializer.data})
        return Response(True)

    def retrieve(self, request, *args, **kwargs):
        query = self.get_queryset().filter(OrderAckId=kwargs['pk']).first()
        serializer = self.get_serializer(query)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='delete_item')
    def delete_item(self, request):
        data = request.data
        orderAcknowledgement.objects.filter(OrderAckId=data['order_ack_id']).update(DeleteFlag=True, DeletedBy_id=request.user.id, deleted_remarks=data['remarks'])
        orderAcknowledgementHistory.objects.filter(OrderAckId_id=data['order_ack_id']).update(DeleteFlag=True, DeletedBy_id=request.user.id)
        queryset = self.get_queryset().exclude(DeleteFlag=True)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path='retrieve_item/(?P<id>[0-9]+)')
    def retrieve_item(self, request, id):
        queryset = orderAcknowledgement.objects.filter(OrderAckId=id)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path='print_aoitem/(?P<id>[0-9]+)')
    def OAItem_generatePDFWithLogo(self, request, id):
        pi_instance = orderAcknowledgement.objects.get(pk=id)
        serializer = self.serializer_class(pi_instance, context={'request': request})
        data = serializer.data
        filename = "OrderItem__%s.pdf" % pi_instance.OrderAckId
        content = "inline; filename='%s'" % filename

        proforma_instance = proformaItemMaster.objects.get(pk=data['ProformaID'])
        proforma_serializer = proformaItemMasterSerializer(proforma_instance, context={'request': request})

        proforma_item_instance = proformaItem.objects.filter(ProformaID=data['ProformaID'])
        proforma_item_serializer = proformaItemSerializer(proforma_item_instance, many=True, context={'request': request})

        data['DocNo'] = str(proforma_serializer.data['DocNo'])
        if proforma_serializer.data['DocDate'] is not None:
            data['DocDate'] = datetime.datetime.strptime(str(proforma_serializer.data['DocDate']), '%Y-%m-%d').date()
            data['DocDate'] = data['DocDate'].strftime("%d/%m/%Y")
        else:
            data['DocDate'] = ""

        data['PONo'] = str(proforma_serializer.data['PONo'])
        if proforma_serializer.data['PoDate'] is not None:
            data['PoDate'] = datetime.datetime.strptime(str(proforma_serializer.data['PoDate']), '%Y-%m-%d').date()
            data['PoDate'] = data['PoDate'].strftime("%d/%m/%Y")
        else:
            data['PoDate'] = ""
            

        data['SoldtoCode'] = proforma_serializer.data['SoldtoCode']
        data['SoldToAddress'] = proforma_serializer.data['SoldToAddress']
        if data['SoldToAddress'] is not None:
            data['SoldToAddress_head'] = data['SoldToAddress'].replace('\u000b', '\n')
        else:
            data['SoldToAddress_head'] = ""

        data['Shiptocode'] = proforma_serializer.data['Shiptocode']
        data['Shiptoaddress'] = proforma_serializer.data['Shiptoaddress']
        if data['Shiptoaddress'] is not None:
            data['Shiptoaddress_head'] = data['Shiptoaddress'].replace('\u000b', '\n')
        else:
            data['Shiptoaddress_head'] = ""

        data['EndUserCode'] = proforma_serializer.data['EndUserCode']
        data['EndUserAddress'] = proforma_serializer.data['EndUserAddress']
        if data['EndUserAddress'] is not None:
            data['EndUserAddress_head'] = data['EndUserAddress'].replace('\u000b', '\n')
        else:
            data['EndUserAddress_head'] = ""

        data['Billtocode'] = proforma_serializer.data['Billtocode']
        data['Billtoaddress'] = proforma_serializer.data['Billtoaddress']
        if data['Billtoaddress'] is not None:
            data['Billtoaddress_head'] = data['Billtoaddress'].replace('\u000b', '\n')
        else:
            data['Billtoaddress_head'] = ""

        data['PI_date'] = datetime.datetime.strptime(str(data['SubmittedDate']), '%Y-%m-%dT%H:%M:%S.%fZ').date()
        data['PI_date'] = data['PI_date'].strftime("%d/%m/%Y")

        if proforma_serializer.data['items'][0]['TotalType'] is not None:
            data['unitType'] = proforma_serializer.data['items'][0]['TotalType']
        else:
            data['unitType'] = proforma_serializer.data['items'][1]['TotalType']

        itemno = proforma_item_serializer.data
        global itemval
        total_order_IGST, total_order_CGST, total_order_SGST = 0, 0, 0
        isgt_percent, sgst_percent, cgst_percent = 0, 0, 0
        count, item_order = 0, 0
        itemval = 0
        data['TotalUnitPriceValue'] = 0
        data['total_discount'] = 0
        
        for index, j in enumerate(data['order']):
            for i in itemno:
                if i['ProformaItemid'] == j['ProformaItemid']:
                    j['CusPartNo'] = i['CusPartNo']
                    j['CusPartSlno'] = i['CusPartSlno']
                    j['ItemNo'] = i['ItemNo']
                    item_order += 1
                    j['item_order'] = item_order
                    if j['PI_IGST'] is not None:
                        total_order_IGST += j['PI_IGST']
                        isgt_percent = j['IGST']
                        if isgt_percent == 0 and total_order_IGST == 0:
                            data['zero_IGST'] = isgt_percent
                            data['zero_IGST_value'] = total_order_IGST
                    if j['PI_CGST'] is not None:
                        total_order_CGST += j['PI_CGST']
                        cgst_percent = j['CGST']
                        if cgst_percent == 0 and total_order_CGST == 0:
                            data['zero_CGST'] = cgst_percent
                            data['zero_CGST_value'] = total_order_CGST
                    if j['PI_SGST'] is not None:
                        total_order_SGST += j['PI_SGST']
                        sgst_percent = j['SGST']
                        if sgst_percent == 0:
                            data['zero_SGST'] = sgst_percent
                            data['zero_SGST_value'] = total_order_SGST
                    if j['PI_Discount'] is not None:
                        data['total_discount'] += j['PI_Discount']
                    if j['ItemNo'] is not None:
                        itemval = index
                        count += 1
                        j['counter'] = count
                    else:
                        j['counter'] = 0
                    if j['TotalAmount'] != 0:
                        data['order'][itemval]['TotalAmount'] = float(data['order'][itemval]['PI_Qty'] * data['order'][itemval]['UnitPrice'])
                        data['TotalUnitPriceValue'] += data['order'][itemval]['TotalAmount']
                        if j['ItemNo'] is None:
                            j['TotalAmount'] = 0
                        if i['DiscountPercent'] is not None:
                            j['Discount_Percent'] = i['DiscountPercent']
                        if i['PFAmount'] is not None and i['PFAmount'] != 0:
                            if i['PFpercent'] is not None:
                                j['PF_Percent'] = i['PFpercent']
                            if total_order_IGST != 0:
                                data['order'][itemval]['TotalAmount'] = float(
                                    data['order'][itemval]['TotalAmount'] + j['PI_IGST'] + i['PFAmount'])
                            else:
                                totalgst = j['PI_CGST'] + j['PI_SGST']
                                data['order'][itemval]['TotalAmount'] = float(
                                    data['order'][itemval]['TotalAmount'] + totalgst + i['PFAmount'])
                        if i['FreightAmount'] is not None and i['FreightAmount'] != 0:
                            if i['FreightPercent'] is not None:
                                j['Freight_Percent'] = i['FreightPercent']

##        for index, j in enumerate(data['order']):
##            if j['ProformaItemid'] is not None:
##                if j['ItemNo'] is not None:
##                    count += 1
##                    j['counter'] = count
##                else:
##                    j['counter'] = 0
##            else:
##                count += 1
##                j['counter'] = count
                
        data['Type'] = data['order'][0]['Type']
        
        if total_order_IGST != 0:
            if data['PI_TotalFreight'] is not None and data['Type'] != "M":
                total = isgt_percent * data['PI_TotalFreight'] / 100
                total_order_IGST = total_order_IGST + total
        if total_order_CGST != 0:
            if data['PI_TotalFreight'] is not None and data['Type'] != "M":
                total = cgst_percent * data['PI_TotalFreight'] / 100
                total_order_CGST = total_order_CGST + total
        if total_order_SGST != 0:
            if data['PI_TotalFreight'] is not None and data['Type'] != "M":
                total = sgst_percent * data['PI_TotalFreight'] / 100
                total_order_SGST = total_order_SGST + total

        data['total_order_IGST'] = total_order_IGST
        data['total_order_CGST'] = total_order_CGST
        data['total_order_SGST'] = total_order_SGST

        indent_no = proforma_serializer.data['IndentNo']
        indent_char_list = ["D", "H", "J", "K", "V", "M", "E", "B", "N", "U", "C", "P", "G", "L", "S"]
        sale_office_list = ["Delhi", "Hyderabad", "Bangladesh", "Kolkata", "Vizag", "Mumbai", "Cochin", "Baroda",
                            "Nagpur", "Bhutan", "Chennai", "Pune", "Surat", "Bangalore", "Corporate Sales"]
        global sales_office
        sales_office = ""

        if len(indent_no) == 10:
            for index, value in enumerate(indent_char_list):
                if indent_no[1].upper() == value:
                    sales_office = sale_office_list[index]

        data['Sales_Office'] = sales_office

##        data['Discount_Percent'] = proforma_serializer.data['items'][0]['DiscountPercent']
##        data['PF_Percent'] = proforma_serializer.data['items'][0]['PFpercent']
##        data['Freight_Percent'] = proforma_serializer.data['items'][0]['FreightPercent']

        loop = proforma_serializer.data['items']

        # data['IGST_Percent'] = proforma_serializer.data['items'][0]['IGSTPercent']
        IGST_Percent = proforma_serializer.data['items'][0]['IGSTPercent']
        if IGST_Percent is not None:
            if IGST_Percent.is_integer() is True:
                data['IGST_Percent'] = int(IGST_Percent)
            elif IGST_Percent.is_integer() is not True:
                data['IGST_Percent'] = IGST_Percent
            else:
                data['IGST_Percent'] = None
        else:
            data['IGST_Percent'] = None
            for index, value in enumerate(loop):
                if value['ItemNo'] is None and value['IGSTPercent']:
                    data['IGST_Percent'] = value['IGSTPercent']
                    break

            # if data['Type'] == 'M' or data['Type'] == 'A':
            #     if data['IGST_Percent'] is not None:
            #         data['TotalAmount'] = data['TotalUnitPrice']
            #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_order_IGST)

        # data['CGST_Percent'] = proforma_serializer.data['items'][0]['CGSTPercent']
        CGST_Percent = proforma_serializer.data['items'][0]['CGSTPercent']
        if CGST_Percent is not None:
            if CGST_Percent.is_integer() is True:
                data['CGST_Percent'] = int(CGST_Percent)
            elif CGST_Percent.is_integer() is not True:
                data['CGST_Percent'] = CGST_Percent
            else:
                data['CGST_Percent'] = None
        else:
            data['CGST_Percent'] = None
            for index, value in enumerate(loop):
                if value['ItemNo'] is None and value['CGSTPercent']:
                    data['CGST_Percent'] = value['CGSTPercent']
                    break

        # data['SGST_Percent'] = proforma_serializer.data['items'][0]['SGSTpercent']
        SGST_Percent = proforma_serializer.data['items'][0]['SGSTpercent']
        if SGST_Percent is not None:
            if SGST_Percent.is_integer() is True:
                data['SGST_Percent'] = int(SGST_Percent)
            elif SGST_Percent.is_integer() is not True:
                data['SGST_Percent'] = SGST_Percent
            else:
                data['SGST_Percent'] = None
        else:
            data['SGST_Percent'] = None
            for index, value in enumerate(loop):
                if value['ItemNo'] is None and value['SGSTpercent']:
                    data['SGST_Percent'] = value['SGSTpercent']
                    break

            # if data['Type'] == 'M' or data['Type'] == 'A':
            #     if data['CGST_Percent'] is not None and data['SGST_Percent'] is not None:
            #         data['TotalAmount'] = data['TotalUnitPrice']
            #         total_gst = total_order_CGST + total_order_SGST
            #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_gst)

        data['Type'] = data['order'][0]['Type']
        if data['Type'] == 'M':
            data['PaymentTerms'] = proforma_serializer.data['PaymentTerms']
            if data['MaterialReadinessDate'] is not None:
                date = datetime.datetime.strptime(data['MaterialReadinessDate'], '%Y-%m-%d')
                data['MatReadyDate'] = date.strftime('%d/%b/%Y')
            else:
                data['MatReadyDate'] = None
        else:
            data['PaymentTerms'] = data['order'][0]['PaymentTerms']
            if data['PaymentTerms'] is None:
                data['PaymentTerms'] = proforma_serializer.data['PaymentTerms']
            data['MatReadyDate'] = None

        if data['PaymentTerms'] is None:
            data['PaymentTerms'] = ""
        else:
            if "Payment Terms:" in data['PaymentTerms']:
                data['PaymentTerms'] = data['PaymentTerms'].split('Payment Terms:')
                data['PaymentTerms'] = data['PaymentTerms'][1]

        data['length'] = len(data['order'])

        data['PIpdf'] = 'with'

        if data['ProjectManagerId'] != 0:
            projectmanager_instance = projectManagerMaster.objects.get(pk=data['ProjectManagerId'])
            projectmanager_serializer = projectManagerMasterSerializer(projectmanager_instance, context={'request': request})
            data['Project_Manager'] = projectmanager_serializer.data['EmployeeName']
        else:
            data['Project_Manager'] = ""

        data['Sale_Order_No'] = data['PI_CODE']

        if data['Party_Address'] == 'shiptoparty':
            data['Shiptoaddress'] = proforma_serializer.data['Shiptoaddress']
            if data['Shiptoaddress'] is not None:
                data['Consignee'] = data['Shiptoaddress'].replace('\u000b', '\n')
            else:
                data['Consignee'] = ""

            x = data['Shiptoaddress'].split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['cust_consignee'] = x[0]

        elif data['Party_Address'] == 'soldtoparty':
            data['SoldToAddress'] = proforma_serializer.data['SoldToAddress']
            if data['SoldToAddress'] is not None:
                data['Consignee'] = data['SoldToAddress'].replace('\u000b', '\n')
            else:
                data['Consignee'] = ""

            x = data['SoldToAddress'].split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['cust_consignee'] = x[0]

        elif data['Party_Address'] == 'enduseraddress':
            data['EndUserAddress'] = proforma_serializer.data['EndUserAddress']
            if data['EndUserAddress'] is not None:
                data['Consignee'] = data['EndUserAddress'].replace('\u000b', '\n')
            else:
                data['Consignee'] = ""

            x = data['EndUserAddress'].split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['cust_consignee'] = x[0]

        elif data['Party_Address'] == 'billtoparty':
            data['Billtoaddress'] = proforma_serializer.data['Billtoaddress']
            if data['Billtoaddress'] is not None:
                data['Consignee'] = data['Billtoaddress'].replace('\u000b', '\n')
            else:
                data['Consignee'] = ""

            x = proforma_serializer.data['Billtoaddress']
            x = x.split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['cust_consignee'] = x[0]

        from datetime import date

        today = date.today()
        datestring = today.strftime("%d-%m-%Y")
        date = datetime.datetime.strptime(datestring, "%d-%m-%Y").date()
        
        data['TodayDate'] = date.strftime('%d-%m-%Y')

        path = os.path.abspath('static/images/header-image.png/')
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('ascii')
            image64 = 'data:image/png;base64,{}'.format(encoded_string)

            data['pdf_header_logo'] = image64

        pdf_response = PDFTemplateResponse(
            request=request,
            template='oa_item.html',
            filename=filename,
            context=data,
            cmd_options={
                'title': filename,
                'margin-top': '40',
                'print-media-type': True
            },
            header_template='oa_header.html',
        )
        return pdf_response

    @action(methods=['get'], detail=False, url_path='print_with_logo/(?P<id>[0-9]+)')
    def generatePDFWithLogo(self, request, id):
        pi_instance = orderAcknowledgement.objects.get(pk=id)
        serializer = self.serializer_class(pi_instance, context={'request': request})
        data = serializer.data
        filename = "Invoice__%s.pdf" % pi_instance.OrderAckId
        content = "inline; filename='%s'" % filename

        proforma_instance = proformaItemMaster.objects.get(pk=data['ProformaID'])
        proforma_serializer = proformaItemMasterSerializer(proforma_instance, context={'request': request})

        proforma_item_instance = proformaItem.objects.filter(ProformaID=data['ProformaID'])
        proforma_item_serializer = proformaItemSerializer(proforma_item_instance, many=True, context={'request': request})

        data['DocNo'] = str(proforma_serializer.data['DocNo'])
        if proforma_serializer.data['DocDate'] is not None:
            data['DocDate'] = datetime.datetime.strptime(str(proforma_serializer.data['DocDate']), '%Y-%m-%d').date()
            data['DocDate'] = data['DocDate'].strftime("%d/%m/%Y")
        else:
            data['DocDate'] = ""

        data['PONo'] = str(proforma_serializer.data['PONo'])
        if proforma_serializer.data['PoDate'] is not None:
            data['PoDate'] = datetime.datetime.strptime(str(proforma_serializer.data['PoDate']), '%Y-%m-%d').date()
            data['PoDate'] = data['PoDate'].strftime("%d/%m/%Y")
        else:
            data['PoDate'] = ""

        data['SoldtoCode'] = proforma_serializer.data['SoldtoCode']
        data['SoldToAddress'] = proforma_serializer.data['SoldToAddress']
        if data['SoldToAddress'] is not None:
            data['SoldToAddress_head'] = data['SoldToAddress'].replace('\u000b', '\n')
        else:
            data['SoldToAddress_head'] = ""

        data['Shiptocode'] = proforma_serializer.data['Shiptocode']
        data['Shiptoaddress'] = proforma_serializer.data['Shiptoaddress']
        if data['Shiptoaddress'] is not None:
            data['Shiptoaddress_head'] = data['Shiptoaddress'].replace('\u000b', '\n')
        else:
            data['Shiptoaddress_head'] = ""

        data['EndUserCode'] = proforma_serializer.data['EndUserCode']
        data['EndUserAddress'] = proforma_serializer.data['EndUserAddress']
        if data['EndUserAddress'] is not None:
            data['EndUserAddress_head'] = data['EndUserAddress'].replace('\u000b', '\n')
        else:
            data['EndUserAddress_head'] = ""

        data['Billtocode'] = proforma_serializer.data['Billtocode']
        data['Billtoaddress'] = proforma_serializer.data['Billtoaddress']
        if data['Billtoaddress'] is not None:
            data['Billtoaddress_head'] = data['Billtoaddress'].replace('\u000b', '\n')
        else:
            data['Billtoaddress_head'] = ""

        data['PI_date'] = datetime.datetime.strptime(str(data['SubmittedDate']), '%Y-%m-%dT%H:%M:%S.%fZ').date()
        data['PI_date'] = data['PI_date'].strftime("%d/%m/%Y")

        if proforma_serializer.data['items'][0]['TotalType'] is not None:
            data['unitType'] = proforma_serializer.data['items'][0]['TotalType']
        else:
            data['unitType'] = proforma_serializer.data['items'][1]['TotalType']

        itemno = proforma_item_serializer.data
        global itemval
        total_order_IGST, total_order_CGST, total_order_SGST = 0, 0, 0
        isgt_percent, sgst_percent, cgst_percent = 0, 0, 0
        count, item_order = 0, 0
        itemval = 0
        data['TotalUnitPriceValue'] = 0
        data['total_discount'] = 0
        
        for index, j in enumerate(data['order']):
            for i in itemno:
                if i['ProformaItemid'] == j['ProformaItemid']:
                    j['CusPartNo'] = i['CusPartNo']
                    j['CusPartSlno'] = i['CusPartSlno']
                    j['ItemNo'] = i['ItemNo']
                    item_order += 1
                    j['item_order'] = item_order
                    if j['PI_IGST'] is not None:
                        total_order_IGST += j['PI_IGST']
                        isgt_percent = j['IGST']
                        if isgt_percent == 0 and total_order_IGST == 0:
                            data['zero_IGST'] = isgt_percent
                            data['zero_IGST_value'] = total_order_IGST
                    if j['PI_CGST'] is not None:
                        total_order_CGST += j['PI_CGST']
                        cgst_percent = j['CGST']
                        if cgst_percent == 0 and total_order_CGST == 0:
                            data['zero_CGST'] = cgst_percent
                            data['zero_CGST_value'] = total_order_CGST
                    if j['PI_SGST'] is not None:
                        total_order_SGST += j['PI_SGST']
                        sgst_percent = j['SGST']
                        if sgst_percent == 0:
                            data['zero_SGST'] = sgst_percent
                            data['zero_SGST_value'] = total_order_SGST
                    if j['PI_Discount'] is not None:
                        data['total_discount'] += j['PI_Discount']
                    if j['ItemNo'] is not None:
                        itemval = index
                        count += 1
                        j['counter'] = count
                    else:
                        j['counter'] = 0
                    if j['TotalAmount'] != 0:
                        data['order'][itemval]['TotalAmount'] = float(data['order'][itemval]['PI_Qty'] * data['order'][itemval]['UnitPrice'])
                        data['order'][itemval]['MultiplyUnitPrice'] = float(data['order'][itemval]['PI_Qty'] * data['order'][itemval]['UnitPrice'])
##                        if data['order'][itemval]['PI_Pf'] is not None and data['order'][itemval]['PI_Pf'] != 0:
##                            data['order'][itemval]['MultiplyUnitPrice'] = float(data['order'][itemval]['MultiplyUnitPrice'] + data['order'][itemval]['PI_Pf'])
##                        if data['order'][itemval]['PI_Freight'] is not None and data['order'][itemval]['PI_Freight'] != 0:
##                            data['order'][itemval]['MultiplyUnitPrice'] = float(data['order'][itemval]['MultiplyUnitPrice'] + data['order'][itemval]['PI_Freight'])
                        data['order'][itemval]['TotalAmount'] = data['order'][itemval]['MultiplyUnitPrice']
                        data['TotalUnitPriceValue'] += data['order'][itemval]['TotalAmount']
                        if j['ItemNo'] is None:
                            j['TotalAmount'] = 0
                        if i['DiscountPercent'] is not None:
                            j['Discount_Percent'] = i['DiscountPercent']
                        if i['PFAmount'] is not None and i['PFAmount'] != 0:
                            if i['PFpercent'] is not None:
                                j['PF_Percent'] = i['PFpercent']
                            if total_order_IGST != 0:
                                data['order'][itemval]['TotalAmount'] = float(
                                    data['order'][itemval]['TotalAmount'] + j['PI_IGST'] + i['PFAmount'])
                            else:
                                totalgst = j['PI_CGST'] + j['PI_SGST']
                                data['order'][itemval]['TotalAmount'] = float(
                                    data['order'][itemval]['TotalAmount'] + totalgst + i['PFAmount'])
                        if i['FreightAmount'] is not None and i['FreightAmount'] != 0:
                            if i['FreightPercent'] is not None:
                                j['Freight_Percent'] = i['FreightPercent']

##        for index, j in enumerate(data['order']):
##            if j['ProformaItemid'] is not None:
##                if j['ItemNo'] is not None:
##                    count += 1
##                    j['counter'] = count
##                else:
##                    j['counter'] = 0
##            else:
##                count += 1
##                j['counter'] = count
                            
        data['Type'] = data['order'][0]['Type']
        
        if total_order_IGST != 0:
            if data['PI_TotalFreight'] is not None and data['Type'] != "M":
                total = isgt_percent * data['PI_TotalFreight'] / 100
                total_order_IGST = total_order_IGST + total
        if total_order_CGST != 0:
            if data['PI_TotalFreight'] is not None and data['Type'] != "M":
                total = cgst_percent * data['PI_TotalFreight'] / 100
                total_order_CGST = total_order_CGST + total
        if total_order_SGST != 0:
            if data['PI_TotalFreight'] is not None and data['Type'] != "M":
                total = sgst_percent * data['PI_TotalFreight'] / 100
                total_order_SGST = total_order_SGST + total

        data['total_order_IGST'] = total_order_IGST
        data['total_order_CGST'] = total_order_CGST
        data['total_order_SGST'] = total_order_SGST

        if data['Party_Address'] == 'billtoparty':
            data['Billtocode'] = proforma_serializer.data['Billtocode']
            data['Billtoaddress'] = proforma_serializer.data['Billtoaddress']
            data['Billtoaddress'] = data['Billtoaddress'].replace('\u000b', '\n')

        indent_no = proforma_serializer.data['IndentNo']
        indent_char_list = ["D", "H", "J", "K", "V", "M", "E", "B", "N", "U", "C", "P", "G", "L", "S"]
        sale_office_list = ["Delhi", "Hyderabad", "Bangladesh", "Kolkata", "Vizag", "Mumbai", "Cochin", "Baroda",
                            "Nagpur", "Bhutan", "Chennai", "Pune", "Surat", "Bangalore", "Corporate Sales"]
        global sales_office
        sales_office = ""

        if indent_no:
            if len(indent_no) == 10:
                for index, value in enumerate(indent_char_list):
                    if indent_no[1].upper() == value:
                        sales_office = sale_office_list[index]

        data['Sales_Office'] = sales_office

##        data['Discount_Percent'] = proforma_serializer.data['items'][0]['DiscountPercent']
##        data['PF_Percent'] = proforma_serializer.data['items'][0]['PFpercent']
##        data['Freight_Percent'] = proforma_serializer.data['items'][0]['FreightPercent']

        loop = proforma_serializer.data['items']

        # data['IGST_Percent'] = proforma_serializer.data['items'][0]['IGSTPercent']
        IGST_Percent = proforma_serializer.data['items'][0]['IGSTPercent']
        if IGST_Percent is not None:
            if IGST_Percent.is_integer() is True:
                data['IGST_Percent'] = int(IGST_Percent)
            elif IGST_Percent.is_integer() is not True:
                data['IGST_Percent'] = IGST_Percent
            else:
                data['IGST_Percent'] = None
        else:
            data['IGST_Percent'] = None
            for index, value in enumerate(loop):
                if value['ItemNo'] is None and value['IGSTPercent']:
                    data['IGST_Percent'] = value['IGSTPercent']
                    break

            # if data['Type'] == 'M' or data['Type'] == 'A':
            #     if data['IGST_Percent'] is not None:
            #         data['TotalAmount'] = data['TotalUnitPrice']
            #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_order_IGST)

        # data['CGST_Percent'] = proforma_serializer.data['items'][0]['CGSTPercent']
        CGST_Percent = proforma_serializer.data['items'][0]['CGSTPercent']
        if CGST_Percent is not None:
            if CGST_Percent.is_integer() is True:
                data['CGST_Percent'] = int(CGST_Percent)
            elif CGST_Percent.is_integer() is not True:
                data['CGST_Percent'] = CGST_Percent
            else:
                data['CGST_Percent'] = None
        else:
            data['CGST_Percent'] = None
            for index, value in enumerate(loop):
                if value['ItemNo'] is None and value['CGSTPercent']:
                    data['CGST_Percent'] = value['CGSTPercent']
                    break

        # data['SGST_Percent'] = proforma_serializer.data['items'][0]['SGSTpercent']
        SGST_Percent = proforma_serializer.data['items'][0]['SGSTpercent']
        if SGST_Percent is not None:
            if SGST_Percent.is_integer() is True:
                data['SGST_Percent'] = int(SGST_Percent)
            elif SGST_Percent.is_integer() is not True:
                data['SGST_Percent'] = SGST_Percent
            else:
                data['SGST_Percent'] = None
        else:
            data['SGST_Percent'] = None
            for index, value in enumerate(loop):
                if value['ItemNo'] is None and value['SGSTpercent']:
                    data['SGST_Percent'] = value['SGSTpercent']
                    break

            # if data['Type'] == 'M' or data['Type'] == 'A':
            #     if data['CGST_Percent'] is not None and data['SGST_Percent'] is not None:
            #         data['TotalAmount'] = data['TotalUnitPrice']
            #         total_gst = total_order_CGST + total_order_SGST
            #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_gst)



        data['region'] = regionMaster.objects.filter(RegionId=data['RegionId']).values('RegionName')[0]['RegionName']


        data['Type'] = data['order'][0]['Type']
        if data['Type'] == 'M':
            data['PaymentTerms'] = proforma_serializer.data['PaymentTerms']
            if data['MaterialReadinessDate'] is not None:
                date = datetime.datetime.strptime(data['MaterialReadinessDate'], '%Y-%m-%d')
                data['MatReadyDate'] = date.strftime('%d/%b/%Y')
            else:
                data['MatReadyDate'] = None
        else:
            data['PaymentTerms'] = data['order'][0]['PaymentTerms']
            if data['PaymentTerms'] is None:
                data['PaymentTerms'] = proforma_serializer.data['PaymentTerms']
            data['MatReadyDate'] = None

        if data['PaymentTerms'] is None:
            data['PaymentTerms'] = ""
        else:
            if "Payment Terms:" in data['PaymentTerms']:
                data['PaymentTerms'] = data['PaymentTerms'].split('Payment Terms:')
                data['PaymentTerms'] = data['PaymentTerms'][1]

        data['length'] = len(data['order'])

        data['PIpdf'] = 'with'

        if data['ProjectManagerId'] != 0:
            projectmanager_instance = projectManagerMaster.objects.get(pk=data['ProjectManagerId'])
            projectmanager_serializer = projectManagerMasterSerializer(projectmanager_instance, context={'request': request})
            data['Project_Manager'] = projectmanager_serializer.data['EmployeeName']
        else:
            data['Project_Manager'] = ""

        data['Sale_Order_No'] = data['PI_CODE']

        # data['TotalAmount'] = data['TotalUnitPrice']
        # if data['Type'] == 'M' or data['Type'] == 'A':
        #     if data['IGST_Percent'] is not None:
        #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_order_IGST)
        #     elif data['CGST_Percent'] is not None and data['SGST_Percent'] is not None:
        #         total_gst = total_order_CGST + total_order_SGST
        #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_gst)

        if data['Party_Address'] == 'shiptoparty':
            data['Shiptoaddress'] = proforma_serializer.data['Shiptoaddress']
            x = data['Shiptoaddress'].split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['Consignee'] = x[0]
        elif data['Party_Address'] == 'soldtoparty':
            data['SoldToAddress'] = proforma_serializer.data['SoldToAddress']
            x = data['SoldToAddress'].split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['Consignee'] = x[0]
        elif data['Party_Address'] == 'enduseraddress':
            data['EndUserAddress'] = proforma_serializer.data['EndUserAddress']
            x = data['EndUserAddress'].split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['Consignee'] = x[0]
        elif data['Party_Address'] == 'billtoparty':
            x = proforma_serializer.data['Billtoaddress']
            x = x.split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['Consignee'] = x[0]

        from datetime import date

        today = date.today()
        datestring = today.strftime("%d-%m-%Y")
        date = datetime.datetime.strptime(datestring, "%d-%m-%Y").date()
        
        data['TodayDate'] = date.strftime('%d-%m-%Y')

        path = os.path.abspath('static/images/header-image.png/')
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('ascii')
            image64 = 'data:image/png;base64,{}'.format(encoded_string)

            data['pdf_header_logo'] = image64

        pdf_response = PDFTemplateResponse(
            request=request,
            template='invoice_with_logo.html',
            filename=filename,
            context=data,
            cmd_options={
                'title': filename,
                'margin-top': '40',
                'print-media-type': True
            },
            header_template='header_template.html',
            # footer_template='footer_template.html',
        )
        return pdf_response

    @action(methods=['get'], detail=False, url_path='print_without_logo/(?P<id>[0-9]+)')
    def generatePDFWithoutLogo(self, request, id):
        pi_instance = orderAcknowledgement.objects.get(pk=id)
        serializer = self.serializer_class(pi_instance, context={'request': request})
        data = serializer.data
        filename = "Invoice__%s.pdf" % pi_instance.OrderAckId
        content = "inline; filename='%s'" % filename

        proforma_instance = proformaItemMaster.objects.get(pk=data['ProformaID'])
        proforma_serializer = proformaItemMasterSerializer(proforma_instance, context={'request': request})

        proforma_item_instance = proformaItem.objects.filter(ProformaID=data['ProformaID'])
        proforma_item_serializer = proformaItemSerializer(proforma_item_instance, many=True, context={'request': request})
        
        data['DocNo'] = str(proforma_serializer.data['DocNo'])
        if proforma_serializer.data['DocDate'] is not None:
            data['DocDate'] = datetime.datetime.strptime(str(proforma_serializer.data['DocDate']), '%Y-%m-%d').date()
            data['DocDate'] = data['DocDate'].strftime("%d/%m/%Y")
        else:
            data['DocDate'] = ""

        data['PONo'] = str(proforma_serializer.data['PONo'])
        if proforma_serializer.data['PoDate'] is not None:
            data['PoDate'] = datetime.datetime.strptime(str(proforma_serializer.data['PoDate']), '%Y-%m-%d').date()
            data['PoDate'] = data['PoDate'].strftime("%d/%m/%Y")
        else:
            data['PoDate'] = ""

        data['SoldtoCode'] = proforma_serializer.data['SoldtoCode']
        data['SoldToAddress'] = proforma_serializer.data['SoldToAddress']
        if data['SoldToAddress'] is not None:
            data['SoldToAddress_head'] = data['SoldToAddress'].replace('\u000b', '\n')
        else:
            data['SoldToAddress_head'] = ""

        data['Shiptocode'] = proforma_serializer.data['Shiptocode']
        data['Shiptoaddress'] = proforma_serializer.data['Shiptoaddress']
        if data['Shiptoaddress'] is not None:
            data['Shiptoaddress_head'] = data['Shiptoaddress'].replace('\u000b', '\n')
        else:
            data['Shiptoaddress_head'] = ""

        data['EndUserCode'] = proforma_serializer.data['EndUserCode']
        data['EndUserAddress'] = proforma_serializer.data['EndUserAddress']
        if data['EndUserAddress'] is not None:
            data['EndUserAddress_head'] = data['EndUserAddress'].replace('\u000b', '\n')
        else:
            data['EndUserAddress_head'] = ""

        data['Billtocode'] = proforma_serializer.data['Billtocode']
        data['Billtoaddress'] = proforma_serializer.data['Billtoaddress']
        if data['Billtoaddress'] is not None:
            data['Billtoaddress_head'] = data['Billtoaddress'].replace('\u000b', '\n')
        else:
            data['Billtoaddress_head'] = ""

        data['PI_date'] = datetime.datetime.strptime(str(data['SubmittedDate']), '%Y-%m-%dT%H:%M:%S.%fZ').date()
        data['PI_date'] = data['PI_date'].strftime("%d/%m/%Y")

        if proforma_serializer.data['items'][0]['TotalType'] is not None:
            data['unitType'] = proforma_serializer.data['items'][0]['TotalType']
        else:
            data['unitType'] = proforma_serializer.data['items'][1]['TotalType']

        itemno = proforma_item_serializer.data
        total_order_IGST, total_order_CGST, total_order_SGST = 0, 0, 0
        isgt_percent, sgst_percent, cgst_percent = 0, 0, 0
        count, item_order = 0, 0
        itemval = 0
        data['TotalUnitPriceValue'] = 0
        data['total_discount'] = 0
        
        for index, j in enumerate(data['order']):
            for i in itemno:
                if i['ProformaItemid'] == j['ProformaItemid']:
                    j['CusPartNo'] = i['CusPartNo']
                    j['CusPartSlno'] = i['CusPartSlno']
                    j['ItemNo'] = i['ItemNo']
                    item_order += 1
                    j['item_order'] = item_order
                    if j['PI_IGST'] is not None:
                        total_order_IGST += j['PI_IGST']
                        isgt_percent = j['IGST']
                        if isgt_percent == 0 and total_order_IGST == 0:
                            data['zero_IGST'] = isgt_percent
                            data['zero_IGST_value'] = total_order_IGST
                    if j['PI_CGST'] is not None:
                        total_order_CGST += j['PI_CGST']
                        cgst_percent = j['CGST']
                        if cgst_percent == 0 and total_order_CGST == 0:
                            data['zero_CGST'] = cgst_percent
                            data['zero_CGST_value'] = total_order_CGST
                    if j['PI_SGST'] is not None:
                        total_order_SGST += j['PI_SGST']
                        sgst_percent = j['SGST']
                        if sgst_percent == 0:
                            data['zero_SGST'] = sgst_percent
                            data['zero_SGST_value'] = total_order_SGST
                    if j['PI_Discount'] is not None:
                        data['total_discount'] += j['PI_Discount']
                    if j['ItemNo'] is not None:
                        itemval = index
                        count += 1
                        j['counter'] = count
                    else:
                        j['counter'] = 0
                    if j['TotalAmount'] != 0:
                        data['order'][itemval]['TotalAmount'] = float(data['order'][itemval]['PI_Qty'] * data['order'][itemval]['UnitPrice'])
                        data['order'][itemval]['MultiplyUnitPrice'] = float(data['order'][itemval]['PI_Qty'] * data['order'][itemval]['UnitPrice'])
##                        if data['order'][itemval]['PI_Pf'] is not None and data['order'][itemval]['PI_Pf'] != 0:
##                            data['order'][itemval]['MultiplyUnitPrice'] = float(data['order'][itemval]['MultiplyUnitPrice'] + data['order'][itemval]['PI_Pf'])
##                        if data['order'][itemval]['PI_Freight'] is not None and data['order'][itemval]['PI_Freight'] != 0:
##                            data['order'][itemval]['MultiplyUnitPrice'] = float(data['order'][itemval]['MultiplyUnitPrice'] + data['order'][itemval]['PI_Freight'])
                        data['order'][itemval]['TotalAmount'] = data['order'][itemval]['MultiplyUnitPrice']
                        data['TotalUnitPriceValue'] += data['order'][itemval]['TotalAmount']
                        if j['ItemNo'] is None:
                            j['TotalAmount'] = 0
                        if i['DiscountPercent'] is not None:
                            j['Discount_Percent'] = i['DiscountPercent']
                        if i['PFAmount'] is not None and i['PFAmount'] != 0:
                            if i['PFpercent'] is not None:
                                j['PF_Percent'] = i['PFpercent']
                            if total_order_IGST != 0:
                                data['order'][itemval]['TotalAmount'] = float(
                                    data['order'][itemval]['TotalAmount'] + j['PI_IGST'] + i['PFAmount'])
                            else:
                                totalgst = j['PI_CGST'] + j['PI_SGST']
                                data['order'][itemval]['TotalAmount'] = float(
                                    data['order'][itemval]['TotalAmount'] + totalgst + i['PFAmount'])
                        if i['FreightAmount'] is not None and i['FreightAmount'] != 0:
                            if i['FreightPercent'] is not None:
                                j['Freight_Percent'] = i['FreightPercent']

##        for index, j in enumerate(data['order']):
##            if j['ProformaItemid'] is not None:
##                if j['ItemNo'] is not None:
##                    count += 1
##                    j['counter'] = count
##                else:
##                    j['counter'] = 0
##            else:
##                count += 1
##                j['counter'] = count

        data['region'] = regionMaster.objects.filter(RegionId=data['RegionId']).values('RegionName')[0]['RegionName']
            
        data['Type'] = data['order'][0]['Type']
        
        if total_order_IGST != 0:
            if data['PI_TotalFreight'] is not None and data['Type'] != "M":
                total = isgt_percent * data['PI_TotalFreight'] / 100
                total_order_IGST = total_order_IGST + total
        if total_order_CGST != 0:
            if data['PI_TotalFreight'] is not None and data['Type'] != "M":
                total = cgst_percent * data['PI_TotalFreight'] / 100
                total_order_CGST = total_order_CGST + total
        if total_order_SGST != 0:
            if data['PI_TotalFreight'] is not None and data['Type'] != "M":
                total = sgst_percent * data['PI_TotalFreight'] / 100
                total_order_SGST = total_order_SGST + total

        data['total_order_IGST'] = total_order_IGST
        data['total_order_CGST'] = total_order_CGST
        data['total_order_SGST'] = total_order_SGST

        if data['Party_Address'] == 'billtoparty':
            data['Billtocode'] = proforma_serializer.data['Billtocode']
            data['Billtoaddress'] = proforma_serializer.data['Billtoaddress']
            data['Billtoaddress'] = data['Billtoaddress'].replace('\u000b', '\n')

        indent_no = proforma_serializer.data['IndentNo']
        indent_char_list = ["D", "H", "J", "K", "V", "M", "E", "B", "N", "U", "C", "P", "G", "L", "S"]
        sale_office_list = ["Delhi", "Hyderabad", "Bangladesh", "Kolkata", "Vizag", "Mumbai", "Cochin", "Baroda",
                            "Nagpur", "Bhutan", "Chennai", "Pune", "Surat", "Bangalore", "Corporate Sales"]
        global sales_office
        sales_office = ""

        if indent_no:
            if len(indent_no) == 10:
                for index, value in enumerate(indent_char_list):
                    if indent_no[1].upper() == value:
                        sales_office = sale_office_list[index]

        data['Sales_Office'] = sales_office

##        data['Discount_Percent'] = proforma_serializer.data['items'][0]['DiscountPercent']
##        data['PF_Percent'] = proforma_serializer.data['items'][0]['PFpercent']
##        data['Freight_Percent'] = proforma_serializer.data['items'][0]['FreightPercent']

        loop = proforma_serializer.data['items']

        # data['IGST_Percent'] = proforma_serializer.data['items'][0]['IGSTPercent']
        IGST_Percent = proforma_serializer.data['items'][0]['IGSTPercent']
        if IGST_Percent is not None:
            if IGST_Percent.is_integer() is True:
                data['IGST_Percent'] = int(IGST_Percent)
            elif IGST_Percent.is_integer() is not True:
                data['IGST_Percent'] = IGST_Percent
            else:
                data['IGST_Percent'] = None
        else:
            data['IGST_Percent'] = None
            for index, value in enumerate(loop):
                if value['ItemNo'] is None and value['IGSTPercent']:
                    data['IGST_Percent'] = value['IGSTPercent']
                    break

        # data['CGST_Percent'] = proforma_serializer.data['items'][0]['CGSTPercent']
        CGST_Percent = proforma_serializer.data['items'][0]['CGSTPercent']
        if CGST_Percent is not None:
            if CGST_Percent.is_integer() is True:
                data['CGST_Percent'] = int(CGST_Percent)
            elif CGST_Percent.is_integer() is not True:
                data['CGST_Percent'] = CGST_Percent
            else:
                data['CGST_Percent'] = None
        else:
            data['CGST_Percent'] = None
            for index, value in enumerate(loop):
                if value['ItemNo'] is None and value['CGSTPercent']:
                    data['CGST_Percent'] = value['CGSTPercent']
                    break

        # data['SGST_Percent'] = proforma_serializer.data['items'][0]['SGSTpercent']
        SGST_Percent = proforma_serializer.data['items'][0]['SGSTpercent']
        if SGST_Percent is not None:
            if SGST_Percent.is_integer() is True:
                data['SGST_Percent'] = int(SGST_Percent)
            elif SGST_Percent.is_integer() is not True:
                data['SGST_Percent'] = SGST_Percent
            else:
                data['SGST_Percent'] = None
        else:
            data['SGST_Percent'] = None
            for index, value in enumerate(loop):
                if value['ItemNo'] is None and value['SGSTpercent']:
                    data['SGST_Percent'] = value['SGSTpercent']
                    break

        # if data['Type'] == 'M' or data['Type'] == 'A':
        #     if data['IGST_Percent'] is not None:
        #         data['TotalAmount'] = data['TotalUnitPrice']
        #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_order_IGST)
        #
        # if data['Type'] == 'M' or data['Type'] == 'A':
        #     if data['CGST_Percent'] is not None and data['SGST_Percent'] is not None:
        #         data['TotalAmount'] = data['TotalUnitPrice']
        #         total_gst = total_order_CGST + total_order_SGST
        #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_gst)

        data['Type'] = data['order'][0]['Type']
        if data['Type'] == 'M':
            data['PaymentTerms'] = proforma_serializer.data['PaymentTerms']
            if data['MaterialReadinessDate'] is not None:
                date = datetime.datetime.strptime(data['MaterialReadinessDate'], '%Y-%m-%d')
                data['MatReadyDate'] = date.strftime('%d/%b/%Y')
            else:
                data['MatReadyDate'] = None
        else:
            data['PaymentTerms'] = data['order'][0]['PaymentTerms']
            if data['PaymentTerms'] is None:
                data['PaymentTerms'] = proforma_serializer.data['PaymentTerms']
            data['MatReadyDate'] = None

        if data['PaymentTerms'] is None:
            data['PaymentTerms'] = ""
        else:
            if "Payment Terms:" in data['PaymentTerms']:
                data['PaymentTerms'] = data['PaymentTerms'].split('Payment Terms:')
                data['PaymentTerms'] = data['PaymentTerms'][1]

        data['length'] = len(data['order'])

        if data['ProjectManagerId'] != 0:
            projectmanager_instance = projectManagerMaster.objects.get(pk=data['ProjectManagerId'])
            projectmanager_serializer = projectManagerMasterSerializer(projectmanager_instance, context={'request': request})
            data['Project_Manager'] = projectmanager_serializer.data['EmployeeName']
        else:
            data['Project_Manager'] = ""

        data['Sale_Order_No'] = data['PI_CODE']

        data['PIpdf'] = 'without'

        # data['TotalAmount'] = data['TotalUnitPrice']
        # if data['Type'] == 'M' or data['Type'] == 'A':
        #     if data['IGST_Percent'] is not None:
        #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_order_IGST)
        #     elif data['CGST_Percent'] is not None and data['SGST_Percent'] is not None:
        #         total_gst = total_order_CGST + total_order_SGST
        #         data['TotalUnitPrice'] = float(data['TotalUnitPrice']) - float(total_gst)

        if data['Party_Address'] == 'shiptoparty':
            data['Shiptoaddress'] = proforma_serializer.data['Shiptoaddress']
            x = data['Shiptoaddress'].split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['Consignee'] = x[0]
        elif data['Party_Address'] == 'soldtoparty':
            data['SoldToAddress'] = proforma_serializer.data['SoldToAddress']
            x = data['SoldToAddress'].split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['Consignee'] = x[0]
        elif data['Party_Address'] == 'enduseraddress':
            data['EndUserAddress'] = proforma_serializer.data['EndUserAddress']
            x = data['EndUserAddress'].split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['Consignee'] = x[0]
        elif data['Party_Address'] == 'billtoparty':
            x = proforma_serializer.data['Billtoaddress']
            x = x.split(",")
            if x is not None:
                x = x[0].split("\u000b")
            else:
                x = '-'
            data['Consignee'] = x[0]

        from datetime import date

        today = date.today()
        datestring = today.strftime("%d-%m-%Y")
        date = datetime.datetime.strptime(datestring, "%d-%m-%Y").date()
        
        data['TodayDate'] = date.strftime('%d-%m-%Y')

        pdf_response = PDFTemplateResponse(
            request=request,
            template='invoice_without_logo.html',
            filename=filename,
            context=data,
            cmd_options={
                'title': filename,
                'margin-top': '40',
                'print-media-type': True,
            },
            header_template='header_template.html',
            # footer_template='footer_template.html',
        )
        return pdf_response

    @action(methods=['post'], detail=False, url_path='proforma_report_list')
    def getOrderListIntoExcel(self, request):
        data = request.data
        excel = dataListToExcel(data)
        if excel.status_code == 200:
            return Response({"value": True, "message": "Proforma Report has created"})
        return Response({"value": False, "message": "Something went error"})

    @action(methods=['get'], detail=False, url_path='download_report')
    def download_excel(self, request):
        file_path = os.path.abspath('static/{}.xlsx'.format("proforma_report"))
        FilePointer = open(file_path, 'rb')
        response = HttpResponse(FilePointer.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=proforma_report.xlsx'

        return response


class orderAckViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = orderAcknowledgement.objects.all()
    serializer_class = orderAckSerializer

    def get_queryset(self):
##        query_set = self.queryset.exclude(DeleteFlag=True).order_by('OrderAckId')
        query_set = self.queryset
        return query_set

    def list(self, request, *args, **kwargs):
##        query_set = self.get_queryset()
        query_params = request.query_params.dict()

        if query_params['deletedPI'] == 'true':
            query_set = self.get_queryset().order_by('OrderAckId')
        else:
            query_set = self.get_queryset().exclude(DeleteFlag=True).order_by('OrderAckId')
            
        if query_params['pi_date'] == 'PIDateBased':
            if query_params['division_value'] != '' or query_params['category_value'] != '' or \
                    query_params['region_value'] != '' or query_params['startDate'] != '' or \
                    query_params['endDate'] != '' or query_params['pi_no'] != '' or \
                    query_params['so_no'] != '' or query_params['customer_name'] != '' or \
                    query_params['pm_value'] != '':

                division_value = query_params['division_value']
                category_value = query_params['category_value']
                region_value = query_params['region_value']
                pi_no = query_params['pi_no']
                so_no = query_params['so_no']
                customer_name = query_params['customer_name']
                start_date = query_params['startDate']
                end_date = query_params['endDate']
                project_manager = query_params['pm_value']
                jobcode = query_params['jobcode']
                wbs = query_params['wbs']

                if division_value != '0':
                    query_set = query_set.filter(DivisionId__exact=division_value)

                if region_value != '0':
                    query_set = query_set.filter(RegionId__exact=region_value)

                if category_value != '0':
                    query_set = query_set.filter(CategoryId__exact=category_value)

                if pi_no != '':
                    query_set = query_set.filter(PI_CODE__exact=pi_no)

                if so_no != '0':
                    query_set = query_set.filter(ProformaID__DocNo__exact=so_no)

                if customer_name != '':
                    query_set = query_set.filter(ProformaID__SoldToAddress__icontains=customer_name)

                if start_date != '' and end_date != '':
                    date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                    modified_date = date + timedelta(days=1)
                    end_date = datetime.datetime.strftime(modified_date, "%Y-%m-%d")
                    query_set = query_set.filter(SubmittedDate__range=[start_date, end_date])

                if project_manager != '0':
                    query_set = query_set.filter(ProjectManagerId__exact=project_manager)

                if jobcode != '':
                    query_set = query_set.filter(JobCode__exact=jobcode)

                if wbs != '':
                    query_set = query_set.filter(WBS__exact=wbs)

                if division_value == '0' and region_value == '0' and category_value == '0' and pi_no == '' and \
                        so_no == '0' and customer_name == '' and start_date == '' and end_date == '' and \
                        project_manager == '0' and jobcode == '' and wbs == '' and query_params['deletedPI'] == 'true':

                    query_set = orderAcknowledgement.objects.filter(DeleteFlag=True).order_by('OrderAckId')

        elif query_params['pi_date'] == 'PIDueDate':
            if query_params['division_value'] != '' or query_params['category_value'] != '' or \
                    query_params['region_value'] != '' or query_params['startDate'] != '' or \
                    query_params['endDate'] != '' or query_params['pi_no'] != '' or \
                    query_params['so_no'] != '' or query_params['customer_name'] != '' or \
                    query_params['pm_value'] != '':

                division_value = query_params['division_value']
                category_value = query_params['category_value']
                region_value = query_params['region_value']
                pi_no = query_params['pi_no']
                so_no = query_params['so_no']
                customer_name = query_params['customer_name']
                start_date = query_params['startDate']
                end_date = query_params['endDate']
                project_manager = query_params['pm_value']
                jobcode = query_params['jobcode']
                wbs = query_params['wbs']

                if division_value != '0':
                    query_set = query_set.filter(DivisionId__exact=division_value)

                if region_value != '0':
                    query_set = query_set.filter(RegionId__exact=region_value)

                if category_value != '0':
                    query_set = query_set.filter(CategoryId__exact=category_value)

                if pi_no != '':
                    query_set = query_set.filter(PI_CODE__exact=pi_no)

                if so_no != '0':
                    query_set = query_set.filter(ProformaID__DocNo__exact=so_no)

                if customer_name != '':
                    query_set = query_set.filter(ProformaID__SoldToAddress__icontains=customer_name)

                if start_date != '' and end_date != '':
                    date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                    modified_date = date + timedelta(days=1)
                    end_date = datetime.datetime.strftime(modified_date, "%Y-%m-%d")
                    query_set = query_set.filter(PI_DueDate__range=[start_date, end_date])

                if project_manager != '0':
                    query_set = query_set.filter(ProjectManagerId__exact=project_manager)

                if jobcode != '':
                    query_set = query_set.filter(JobCode__exact=jobcode)

                if wbs != '':
                    query_set = query_set.filter(WBS__exact=wbs)

                if division_value == '0' and region_value == '0' and category_value == '0' and pi_no == '' and \
                        so_no == '0' and customer_name == '' and start_date == '' and end_date == '' and \
                        project_manager == '0' and jobcode == '' and wbs == '' and query_params['deletedPI'] == 'true':

                    query_set = orderAcknowledgement.objects.filter(DeleteFlag=True).order_by('OrderAckId')

        elif query_params['pi_date'] == 'MaterialDate':

            if query_params['division_value'] != '' or query_params['category_value'] != '' or \
                    query_params['region_value'] != '' or query_params['startDate'] != '' or \
                    query_params['endDate'] != '' or query_params['pi_no'] != '' or \
                    query_params['so_no'] != '' or query_params['customer_name'] != '' or \
                    query_params['pm_value'] != '':

                division_value = query_params['division_value']
                category_value = query_params['category_value']
                region_value = query_params['region_value']
                pi_no = query_params['pi_no']
                so_no = query_params['so_no']
                customer_name = query_params['customer_name']
                start_date = query_params['startDate']
                end_date = query_params['endDate']
                project_manager = query_params['pm_value']
                jobcode = query_params['jobcode']
                wbs = query_params['wbs']

                if division_value != '0':
                    query_set = query_set.filter(DivisionId__exact=division_value)

                if region_value != '0':
                    query_set = query_set.filter(RegionId__exact=region_value)

                if category_value != '0':
                    query_set = query_set.filter(CategoryId__exact=category_value)

                if pi_no != '':
                    query_set = query_set.filter(PI_CODE__exact=pi_no)

                if so_no != '0':
                    query_set = query_set.filter(ProformaID__DocNo__exact=so_no)

                if customer_name != '':
                    query_set = query_set.filter(ProformaID__SoldToAddress__icontains=customer_name)

                if start_date != '' and end_date != '':
                    date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                    modified_date = date + timedelta(days=1)
                    end_date = datetime.datetime.strftime(modified_date, "%Y-%m-%d")
                    query_set = query_set.filter(MaterialReadinessDate__range=[start_date, end_date])

                if project_manager != '0':
                    query_set = query_set.filter(ProjectManagerId__exact=project_manager)

                if jobcode != '':
                    query_set = query_set.filter(JobCode__exact=jobcode)

                if wbs != '':
                    query_set = query_set.filter(WBS__exact=wbs)

                if division_value == '0' and region_value == '0' and category_value == '0' and pi_no == '' and \
                        so_no == '0' and customer_name == '' and start_date == '' and end_date == '' and \
                        project_manager == '0' and jobcode == '' and wbs == '' and query_params['deletedPI'] == 'true':

                    query_set = orderAcknowledgement.objects.filter(DeleteFlag=True).order_by('OrderAckId')


        serializer = self.serializer_class(query_set, many=True, context={'request': request})
        serializer_data = serializer.data
        
        proformaId = []
        if len(serializer_data) != 0:
            for obj in serializer_data:
                proformaId.append(obj['ProformaID'])

        queryset = proformaItemMaster.objects.filter(ProformaID__in=proformaId)
        proforma_serializer = proformaItemMasterSerializer(queryset, many=True, context={'request': request})
        proforma_serializer_data = proforma_serializer.data

        return Response({'proforma': proforma_serializer_data, 'records': serializer_data})


class orderAcknowledgementHistoryViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = orderAcknowledgementHistory.objects.all()
    serializer_class = orderAcknowledgementHistorySerializer

    def get_queryset(self):
        query_set = self.queryset.exclude(DeleteFlag=True)
        return query_set

    def list(self, request, *args, **kwargs):
        # query_params = request.query_params.dict()
        queryset = self.get_queryset()
        total_records = queryset.count()
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response({'records': serializer.data, 'totalRecords': total_records})

    def create(self, request, *args, **kwargs):
        data = request.data
        count = 0

        if isinstance(data, list):
            for index, item in enumerate(data):
                item['Revno'] = 0
                queryset = self.get_queryset()
                if queryset.filter(ProformaID=item['ProformaID']).exists():
                    count = queryset.filter(ProformaID=item['ProformaID']).values(
                        'ProformaID').annotate(count=Count('ProformaID'))
                    item['Revno'] = count[0]['count'] + index + 1
                else:
                    count += 1
                    item['Revno'] = count
                    item['OrderAckId_id'] = item['OrderAckId']
            serializer = self.serializer_class(data=data, many=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'value': True, 'data': serializer.data})
        return Response(True)

    def update(self, request, *args, **kwargs):
        data = request.data
        queries = self.get_queryset().filter(id=kwargs['pk']).first()
        serializer = self.serializer_class(queries, data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'value': True, 'data': serializer.data})
        return Response(True)

    def retrieve(self, request, *args, **kwargs):
        query = self.get_queryset().filter(OrderAck_HistoryId=kwargs['pk']).first()
        serializer = self.serializer_class(query)
        return Response(serializer.data)

    @action(methods=['post'], detail=False, url_path='update_orderAckHistory')
    def updateOrderAckHistory(self, request):
        update_list = []
        data = request.data
        for obj in data:
            if obj is not None:
                model_obj = orderAcknowledgementHistory.objects.get(OrderAck_HistoryId=obj['OrderAck_HistoryId'])
                model_obj.Description = obj['Description']
                model_obj.PercentonAmt = obj['PercentonAmt']
                model_obj.APBGDetails = obj['APBGDetails']
                model_obj.PartName = obj['PartName']
                model_obj.HSN = obj['HSN']
                model_obj.Qty = obj['Qty']
                model_obj.UOM = obj['UOM']
                model_obj.UnitPrice = obj['UnitPrice']
                model_obj.Advance = obj['Advance']
                model_obj.Retention = obj['Retention']
                if obj['MaterialReadinessDate'] is not None:
                    MaterialReadinessDate = datetime.datetime.strptime(obj['MaterialReadinessDate'], '%d-%m-%Y').date()
                    model_obj.MaterialReadinessDate = MaterialReadinessDate.strftime("%Y-%m-%d")
                else:
                    model_obj.MaterialReadinessDate = None

                model_obj.Freight = obj['Freight']
                model_obj.IGST = obj['IGST']
                model_obj.SGST = obj['SGST']
                model_obj.CGST = obj['CGST']
                model_obj.category_id = obj['category_id']
                model_obj.division_id = obj['division_id']
                model_obj.region_id = obj['region_id']
                model_obj.TotalAmount = obj['TotalAmount']
                model_obj.TotalAdvance = obj['TotalAdvance']
                model_obj.TotalRetention = obj['TotalRetention']
                model_obj.GSTBaseValue = obj['GSTBaseValue']

                model_obj.PI_Qty = obj['PI_Qty']
                model_obj.PI_Discount = obj['PI_Discount']
                model_obj.PI_Pf = obj['PI_Pf']
                model_obj.PI_Freight = obj['PI_Freight']
                model_obj.PI_SGST = obj['PI_SGST']
                model_obj.PI_CGST = obj['PI_CGST']
                model_obj.PI_IGST = obj['PI_IGST']

                update_list.append(model_obj)

        orderAcknowledgementHistory.objects.bulk_update(update_list, ['Description', 'PercentonAmt', 'APBGDetails',
                                                                      'PartName', 'HSN', 'Qty', 'UOM', 'UnitPrice',
                                                                      'Advance', 'Retention', 'MaterialReadinessDate',
                                                                      'Freight', 'IGST', 'SGST', 'CGST', 'category_id',
                                                                      'division_id', 'region_id', 'TotalAmount',
                                                                      'TotalAdvance', 'TotalRetention', 'GSTBaseValue',
                                                                      'GSTBaseValue', 'PI_Qty', 'PI_Discount',
                                                                      'PI_Pf', 'PI_Freight', 'PI_SGST', 'PI_CGST',
                                                                      'PI_IGST'])
        return Response({'status': True})
