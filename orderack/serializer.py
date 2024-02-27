import datetime
from rest_framework import serializers
from .models import orderAcknowledgement, orderAcknowledgementHistory


class orderAcknowledgementHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = orderAcknowledgementHistory
        fields = '__all__'

    # def to_representation(self, data):
    #     if data.DeleteFlag is not True:
    #         return super(orderAcknowledgementHistorySerializer, self).to_representation(data)

    def create(self, validated_data):
        validated_data['SubmittedBy'] = self.context['request'].user
        return super(orderAcknowledgementHistorySerializer, self).create(validated_data=validated_data)


class orderAcknowledgementSerializer(serializers.ModelSerializer):
##    order = orderAcknowledgementHistorySerializer(many=True, allow_null=True, read_only=True)
    order = serializers.SerializerMethodField()

    class Meta:
        model = orderAcknowledgement
        fields = '__all__'

    def get_order(self, instance):
        items = instance.order.all().order_by('OrderAck_HistoryId')
        return orderAcknowledgementHistorySerializer(items, many=True).data

    def create(self, validated_data):
        validated_data['SubmittedBy'] = self.context['request'].user
        return super(orderAcknowledgementSerializer, self).create(validated_data=validated_data)

    def update(self, instance, validated_data):
        validated_data['UpdatedBy'] = self.context['request'].user
        return super(orderAcknowledgementSerializer, self).update(instance=instance, validated_data=validated_data)


class orderAckSerializer(serializers.ModelSerializer):
##    order = orderAcknowledgementHistorySerializer(many=True, allow_null=True, read_only=True)
    order = serializers.SerializerMethodField()

    class Meta:
        model = orderAcknowledgement
        fields = '__all__'

##    def to_representation(self, instance):
##        primitive_repr = super().to_representation(instance)
        # primitive_repr['SubmittedDate'] = datetime.datetime.strptime(str(instance.SubmittedDate), '%Y-%m-%d').date()
        # primitive_repr['SubmittedDate'] = primitive_repr['SubmittedDate'].strftime("%d/%m/%Y")
        # primitive_repr['PI_DueDate'] = datetime.datetime.strptime(str(instance.PI_DueDate), '%Y-%m-%d').date()
        # primitive_repr['PI_DueDate'] = primitive_repr['PI_DueDate'].strftime("%d/%m/%Y")
##        return primitive_repr

    def get_order(self, instance):
        items = instance.order.all().order_by('OrderAck_HistoryId')
        return orderAcknowledgementHistorySerializer(items, many=True).data
