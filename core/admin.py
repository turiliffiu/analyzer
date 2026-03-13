"""
Django Admin - Ericsson Log Analyzer
"""
from django.contrib import admin
from .models import (LogFile, Analysis, RadioUnit, Alarm, FRU, PuschData,
                     RETDevice, TMADevice, FiberLink, SFPModule, BranchPair)


@admin.register(LogFile)
class LogFileAdmin(admin.ModelAdmin):
    list_display = ['apparato_nome', 'filename', 'uploaded_by', 'uploaded_at', 'file_size']
    list_filter = ['uploaded_at']
    search_fields = ['apparato_nome', 'filename']
    readonly_fields = ['uploaded_at']


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'created_at', 'radio_units_count',
                    'alarms_critical_count', 'alarms_major_count', 'vswr_critical_count']
    list_filter = ['created_at']
    readonly_fields = ['created_at']


@admin.register(RadioUnit)
class RadioUnitAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'fru', 'rf_port', 'vswr', 'is_vswr_critical']
    list_filter = ['is_vswr_critical', 'is_vswr_warning']
    search_fields = ['fru', 'board']


@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'severity', 'alarm_number', 'cause']
    list_filter = ['severity']
    search_fields = ['alarm_number', 'cause']


@admin.register(FRU)
class FRUAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'name', 'board', 'temp', 'is_temp_high']
    list_filter = ['is_temp_high']


@admin.register(PuschData)
class PuschDataAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'cell', 'pusch', 'pucch', 'is_rssi_high']
    list_filter = ['is_rssi_high']


@admin.register(FiberLink)
class FiberLinkAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'link', 'fru', 'dl_loss', 'ul_loss', 'is_dl_critical']
    list_filter = ['is_dl_critical', 'is_ul_critical']


@admin.register(SFPModule)
class SFPModuleAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'port', 'fru', 'rx_dbm', 'is_tn_backhaul', 'is_rx_critical']
    list_filter = ['is_tn_backhaul', 'is_rx_critical']


admin.site.register(RETDevice)
admin.site.register(TMADevice)
admin.site.register(BranchPair)

admin.site.site_header = "Ericsson Log Analyzer"
admin.site.site_title = "Ericsson Analyzer"
admin.site.index_title = "Pannello Amministrazione"


# UserProfile Admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Utente', {
            'fields': ('user',)
        }),
        ('Ruolo e Permessi', {
            'fields': ('role',)
        }),
        ('Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# TNBackhaul Admin
from .models import TNBackhaul

@admin.register(TNBackhaul)
class TNBackhaulAdmin(admin.ModelAdmin):
    list_display = ['port', 'board', 'vendor', 'vendor_product', 'tx_dbm', 'rx_dbm', 'temperature', 'has_optical_data', 'is_rx_critical']
    list_filter = ['vendor', 'has_optical_data', 'is_rx_critical']
    search_fields = ['port', 'serial', 'vendor_product']
