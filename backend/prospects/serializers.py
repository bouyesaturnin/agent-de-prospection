from rest_framework import serializers
from .models import Campaign, Lead, Message, AgentLog, DiscoveredProspect


class MessageSerializer(serializers.ModelSerializer):
    msg_type_display = serializers.CharField(source='get_msg_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Message
        fields = '__all__'


class AgentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentLog
        fields = '__all__'


class LeadSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Lead
        fields = '__all__'


class CampaignSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    leads_count = serializers.IntegerField(source='leads.count', read_only=True)

    class Meta:
        model = Campaign
        fields = '__all__'


class DiscoveredProspectSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DiscoveredProspect
        fields = '__all__'
        read_only_fields = ['google_place_id', 'name', 'address', 'phone', 'category', 'search_location', 'converted_lead']