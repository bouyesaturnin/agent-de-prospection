from django.contrib import admin
from .models import Campaign, Lead, Message, AgentLog

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name',)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'company', 'status', 'campaign')
    list_filter = ('status', 'campaign')
    search_fields = ('email', 'first_name', 'last_name', 'company')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('lead', 'msg_type', 'status', 'generated_by_ai', 'sent_at')
    list_filter = ('msg_type', 'status', 'generated_by_ai')

@admin.register(AgentLog)
class AgentLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'level', 'campaign', 'lead')
    list_filter = ('level', 'action')
