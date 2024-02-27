import datetime
from rest_framework import serializers
from .models import proformaItemMaster, proformaItem


class proformaItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = proformaItem
        fields = '__all__'


class proformaItemMasterSerializer(serializers.ModelSerializer):
##    items = proformaItemSerializer(many=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = proformaItemMaster
        fields = '__all__'

    def get_items(self, instance):
        items = instance.items.all().order_by('ProformaItemid')
        return proformaItemSerializer(items, many=True).data


class proformaMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = proformaItemMaster
        fields = '__all__'

    def to_representation(self, instance):
        primitive_repr = super().to_representation(instance)
        primitive_repr['DocDate'] = datetime.datetime.strptime(str(instance.DocDate), '%Y-%m-%d').date()
        primitive_repr['DocDate'] = primitive_repr['DocDate'].strftime("%d/%m/%Y")
        return primitive_repr


