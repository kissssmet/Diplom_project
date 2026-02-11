from django.contrib import admin
from django.db.models import Count, Q
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from datetime import datetime, date
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
import json

# Импортируем ВСЕ модели
from .models import (
    Student, Supervisor, DiplomaProject, Group, GroupOrder,
    OrderTemplate, TemplateSection, GeneratedDocument, 
    DocumentCollaborator, DocumentHistory,  DiplomaAIAnalysis, PageAIInteraction, AIQuestionBank 
)

# === Ресурсы для импорта/экспорта ===

class GroupResource(resources.ModelResource):
    class Meta:
        model = Group
        fields = ('id', 'name', 'faculty', 'course')
        export_order = fields

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        fields = ('id', 'last_name', 'first_name', 'patronymic', 'student_id', 'group', 'email', 'phone')
        export_order = fields

class SupervisorResource(resources.ModelResource):
    class Meta:
        model = Supervisor
        fields = ('id', 'last_name', 'first_name', 'patronymic', 'academic_degree', 'position', 'email', 'phone')
        export_order = fields

class DiplomaProjectResource(resources.ModelResource):
    class Meta:
        model = DiplomaProject
        fields = ('id', 'topic', 'student', 'supervisor', 'registration_date', 'deadline', 'status')
        export_order = fields

# === Inline классы ===

class DiplomaProjectInline(admin.StackedInline):
    model = DiplomaProject
    extra = 0
    fields = ('topic', 'supervisor', 'registration_date', 'deadline', 'status', 'description')
    verbose_name_plural = "Дипломный проект"

class TemplateSectionInline(admin.TabularInline):
    model = TemplateSection
    extra = 1
    fields = ('title', 'content', 'order', 'is_required', 'can_be_deleted', 'can_be_edited')

class DocumentCollaboratorInline(admin.TabularInline):
    model = DocumentCollaborator
    extra = 1
    autocomplete_fields = ['user']

# === Admin классы ===

@admin.register(Group)
class GroupAdmin(ImportExportModelAdmin):
    resource_class = GroupResource
    list_display = ('name', 'faculty', 'course', 'student_count', 'diploma_count')
    search_fields = ('name', 'faculty')
    list_filter = ('course', 'faculty')
    ordering = ['course', 'name']

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "Студентов"

    def diploma_count(self, obj):
        return obj.students.filter(diploma_project__isnull=False).count()
    diploma_count.short_description = "Дипломов"

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ('get_photo', 'get_full_name', 'student_id', 'group', 'get_diploma_status', 'get_supervisor')
    list_display_links = ('get_full_name',)
    search_fields = ('last_name', 'first_name', 'patronymic', 'student_id', 'email')
    list_filter = ('group', 'group__course', 'diploma_project__status')
    inlines = [DiplomaProjectInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('last_name', 'first_name', 'patronymic', 'student_id', 'photo')
        }),
        ('Контактная информация', {
            'fields': ('email', 'phone'),
            'classes': ('collapse',)
        }),
        ('Учебная информация', {
            'fields': ('group', 'user')
        }),
    )

    def get_photo(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%;" />', obj.photo.url)
        return "—"
    get_photo.short_description = "Фото"

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = "ФИО"

    def get_supervisor(self, obj):
        try:
            return obj.diploma_project.supervisor
        except:
            return "—"
    get_supervisor.short_description = "Руководитель"

    def get_diploma_status(self, obj):
        try:
            status = obj.diploma_project.get_status_display()
            return format_html('<span class="badge">{}</span>', status)
        except:
            return format_html('<span class="badge bg-secondary">Нет темы</span>')
    get_diploma_status.short_description = "Статус диплома"

@admin.register(Supervisor)
class SupervisorAdmin(ImportExportModelAdmin):
    resource_class = SupervisorResource
    list_display = ('get_full_name', 'academic_degree', 'position', 'student_count', 'email', 'phone')
    search_fields = ('last_name', 'first_name', 'patronymic', 'email')
    list_filter = ('academic_degree', 'position')

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = "ФИО"

    def student_count(self, obj):
        return obj.diploma_projects.count()
    student_count.short_description = "Кол-во студентов"

@admin.register(DiplomaProject)
class DiplomaProjectAdmin(ImportExportModelAdmin):
    resource_class = DiplomaProjectResource
    list_display = ('topic_short', 'student', 'supervisor', 'status_display', 'registration_date', 'deadline')
    list_filter = ('supervisor', 'status', 'registration_date', 'deadline')
    search_fields = ('topic', 'student__last_name', 'student__first_name')
    autocomplete_fields = ['student', 'supervisor']

    def topic_short(self, obj):
        return obj.topic[:100] + "..." if len(obj.topic) > 100 else obj.topic
    topic_short.short_description = "Тема"

    def status_display(self, obj):
        from django.utils.html import format_html
        return format_html('<span class="badge">{}</span>', obj.get_status_display())
    status_display.short_description = "Статус"

@admin.register(GroupOrder)
class GroupOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'group', 'order_date', 'study_form', 'direction')
    list_filter = ('order_date', 'study_form', 'group')
    search_fields = ('order_number', 'group__name', 'direction')
    ordering = ('-order_date',)

@admin.register(OrderTemplate)
class OrderTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_active', 'created_at')
    list_filter = ('template_type', 'is_active')
    search_fields = ('name', 'description')
    inlines = [TemplateSectionInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'template_type', 'is_active')
        }),
        ('Содержимое', {
            'fields': ('content', 'available_fields', 'default_formatting')
        }),
        ('Файлы', {
            'fields': ('docx_template',),
            'classes': ('collapse',)
        }),
    )

@admin.register(TemplateSection)
class TemplateSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'template', 'order', 'is_required')
    list_filter = ('template', 'is_required')
    search_fields = ('title', 'content')

@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'template', 'student', 'group', 'status', 'created_at')
    list_filter = ('status', 'template', 'created_at')
    search_fields = ('document_number', 'content')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DocumentCollaboratorInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('document_number', 'document_date', 'status', 'template')
        }),
        ('Объекты', {
            'fields': ('student', 'group')
        }),
        ('Содержимое', {
            'fields': ('content', 'document_data'),
            'classes': ('collapse',)
        }),
        ('Файлы', {
            'fields': ('html_file', 'docx_file', 'pdf_file'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DocumentCollaborator)
class DocumentCollaboratorAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'role', 'can_edit', 'is_active')
    list_filter = ('role', 'is_active', 'can_edit')
    search_fields = ('user__username', 'user__email', 'document__document_number')

@admin.register(DocumentHistory)
class DocumentHistoryAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('document__document_number', 'user__username')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
# diploma_orders/admin.py - дополняем
   
@admin.register(DiplomaAIAnalysis)
class DiplomaAIAnalysisAdmin(admin.ModelAdmin):
    list_display = ('diploma_project', 'format_score', 'review_grade', 'status', 'created_at')
    list_filter = ('status', 'review_grade', 'ai_provider', 'created_at')
    search_fields = ('diploma_project__topic', 'review_text')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('diploma_project', 'status', 'ai_provider')
        }),
        ('Результаты анализа', {
            'fields': ('format_score', 'format_issues', 'review_text', 'review_grade', 'questions')
        }),
        ('Технические данные', {
            'fields': ('content_analysis', 'file_metadata', 'raw_response'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PageAIInteraction)
class PageAIInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'page_title', 'session_id', 'last_interaction')
    list_filter = ('last_interaction',)
    search_fields = ('page_title', 'page_url', 'user__username')
    readonly_fields = ('created_at', 'last_interaction')

@admin.register(AIQuestionBank)
class AIQuestionBankAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'category', 'question_type', 'difficulty', 'usage_count', 'is_active')
    list_filter = ('category', 'question_type', 'difficulty', 'is_active')
    search_fields = ('question_text', 'tags')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('category', 'subcategory', 'question_text', 'is_active')
        }),
        ('Классификация', {
            'fields': ('question_type', 'difficulty', 'tags')
        }),
        ('Статистика', {
            'fields': ('usage_count', 'success_rate'),
            'classes': ('collapse',)
        }),
    )