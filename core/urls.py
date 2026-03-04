"""
URLs per Ericsson Analyzer
"""
from django.urls import path
from .views import (
    UploadView, 
    DashboardView, 
    AnalysisDetailView,
    ExportExcelView
)

app_name = 'core'

urlpatterns = [
    path('', UploadView.as_view(), name='upload'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('analysis/<int:pk>/', AnalysisDetailView.as_view(), name='analysis_detail'),
    path('analysis/<int:pk>/export/', ExportExcelView.as_view(), name='export_excel'),
]
