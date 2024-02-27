from rest_framework import serializers
from .models import divisionMaster, categoryMaster, regionMaster, projectManagerMaster


class divisionMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = divisionMaster
        fields = '__all__'

    def create(self, validated_data):
        validated_data['submittedBy_id'] = self.context['request'].user.id
        return super(divisionMasterSerializer, self).create(validated_data=validated_data)


class categoryMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = categoryMaster
        fields = '__all__'

    def create(self, validated_data):
        validated_data['submittedBy_id'] = self.context['request'].user.id
        return super(categoryMasterSerializer, self).create(validated_data=validated_data)


class regionMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = regionMaster
        fields = '__all__'

    def create(self, validated_data):
        validated_data['submittedBy_id'] = self.context['request'].user.id
        return super(regionMasterSerializer, self).create(validated_data=validated_data)


class projectManagerMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = projectManagerMaster
        fields = '__all__'

    def create(self, validated_data):
        validated_data['submittedBy_id'] = self.context['request'].user.id
        return super(projectManagerMasterSerializer, self).create(validated_data=validated_data)
