"""
URLs per Ericsson Analyzer
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    LgaTrendView,
    ExportPreSwapView,
    SintesiView,
    alarm_pattern_add,
    alarm_pattern_delete,
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
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='core/password_change.html',
        success_url='/password-change/done/'
    ), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='core/password_change_done.html'
    ), name='password_change_done'),
    
    # App
    path('', UploadView.as_view(), name='upload'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('analysis/<int:pk>/', AnalysisDetailView.as_view(), name='analysis_detail'),
    path('analysis/<int:pk>/export/', ExportExcelView.as_view(), name='export_excel'),
    path('analysis/<int:pk>/export-preswap/', ExportPreSwapView.as_view(), name='export_preswap'),
    path('analysis/<int:pk>/lga-trend/', LgaTrendView.as_view(), name='lga_trend'),
    path('sintesi/', SintesiView.as_view(), name='sintesi'),
    path('api/alarm-patterns/add/', alarm_pattern_add, name='alarm_pattern_add'),
    path('api/alarm-patterns/<int:pk>/delete/', alarm_pattern_delete, name='alarm_pattern_delete'),
    path('analysis/<int:pk>/delete/', DeleteAnalysisView.as_view(), name='delete_analysis'),
    path('analysis/delete-all/', DeleteAllAnalysesView.as_view(), name='delete_all_analyses'),
]
