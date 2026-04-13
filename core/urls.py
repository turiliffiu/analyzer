"""
URLs per Ericsson Analyzer
"""
from django.urls import path
from .views import (
    LgaTrendView,
    UploadView, 
    DashboardView, 
    AnalysisDetailView,
    ExportExcelView,
    DeleteAnalysisView,
    DeleteAllAnalysesView,
    CustomLoginView,
    CustomLogoutView
)

app_name = 'core'

urlpatterns = [
    # Auth
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    
    # App
    path('', UploadView.as_view(), name='upload'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('analysis/<int:pk>/', AnalysisDetailView.as_view(), name='analysis_detail'),
    path('analysis/<int:pk>/export/', ExportExcelView.as_view(), name='export_excel'),
    path('analysis/<int:pk>/lga-trend/', LgaTrendView.as_view(), name='lga_trend'),
    path('analysis/<int:pk>/delete/', DeleteAnalysisView.as_view(), name='delete_analysis'),
    path('analysis/delete-all/', DeleteAllAnalysesView.as_view(), name='delete_all_analyses'),
]
