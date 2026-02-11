from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views, views_upload, views_ai

app_name = 'diploma_orders'

urlpatterns = [
    # Основные маршруты
    path('', views.HomeView.as_view(), name='home'),
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('students/<int:student_id>/generate-order/', views.generate_order, name='generate_order'),
    
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('group-orders/', views.GroupOrderListView.as_view(), name='group_order_list'),
    path('groups/<int:group_id>/create-order/', views.create_group_order, name='create_group_order'),
    path('group-orders/<int:order_id>/', views.group_order_detail, name='group_order_detail'),
    path('group-orders/<int:order_id>/preview/', views.generate_group_order_preview, name='group_order_preview'),
    path('group-orders/<int:order_id>/download/', views.generate_group_order_docx, name='group_order_download'),
    
    # Умный редактор документов (Новые маршруты)
    # Шаблоны
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.TemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/', views.TemplateDetailView.as_view(), name='template_detail'),
    path('templates/<int:template_id>/editor/', views.template_editor, name='template_editor'),
    
    # Генерация документов
    path('documents/generate/<str:object_type>/<int:object_id>/', 
         views.generate_document, name='generate_document'),
    
    # Документы
    path('documents/', views.DocumentListView.as_view(), name='document_list'),
    path('documents/<int:document_id>/', views.document_view, name='document_view'),
    path('documents/<int:document_id>/edit/', views.document_edit, name='document_edit'),
    path('documents/<int:document_id>/history/', views.document_history, name='document_history'),
    path('documents/<int:document_id>/export/<str:format_type>/', 
         views.export_document, name='export_document'),
    path('documents/<int:document_id>/add-collaborator/', 
         views.add_collaborator, name='add_collaborator'),
    path('documents/<int:document_id>/remove-collaborator/<int:collaborator_id>/', 
         views.remove_collaborator, name='remove_collaborator'),
    
    # API
    path('api/sections/<int:section_id>/', views.api_section_detail, name='api_section_detail'),
    path('api/sections/<int:section_id>/edit-form/', 
         views.api_section_edit_form, name='api_section_edit_form'),
    path('api/templates/<int:template_id>/save-content/', 
         views.save_template_content, name='save_template_content'),
      # API для умного редактора
    path('api/templates/<int:template_id>/fields/', views.api_template_fields, name='api_template_fields'),
    path('api/templates/<int:template_id>/preview/', views.api_template_preview, name='api_template_preview'),

     path('diploma/<int:diploma_id>/upload/', views_upload.upload_diploma_file, name='upload_diploma'),
    path('diploma/<int:diploma_id>/analysis/', views_upload.diploma_analysis_dashboard, name='diploma_analysis'),
    path('diploma/<int:diploma_id>/analyze/run/', views_upload.run_ai_analysis, name='run_ai_analysis'),
    path('diploma/<int:diploma_id>/file/delete/', views_upload.delete_diploma_file, name='delete_diploma_file'),
    path('diploma/<int:diploma_id>/file/download/', views_upload.download_diploma_file, name='download_diploma'),
    
    # ИИ-функционал (если еще не добавлены)
    path('api/ai/ask/', views_ai.ask_ai_assistant, name='ai_ask_assistant'),
    path('api/ai/generate-questions/', views_ai.generate_questions_for_page, name='ai_generate_questions'),
    path('ai-settings/', views_ai.ai_settings, name='ai_settings'),
]

# Для обслуживания медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)