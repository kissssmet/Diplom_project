# diploma_orders/views_upload.py - новый файл
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import uuid
import json
from datetime import datetime

from .models import DiplomaProject, DiplomaAIAnalysis
from .forms import DiplomaUploadForm, AIAnalysisRequestForm
from .ai_services import DiplomaAnalyzer


@login_required
def upload_diploma_file(request, diploma_id):
    """Загрузка файла дипломной работы"""
    diploma = get_object_or_404(DiplomaProject, id=diploma_id)
    
    # Проверяем права (только студент или администратор)
    if not (request.user.is_staff or request.user == diploma.student.user):
        messages.error(request, "У вас нет прав для загрузки файла")
        return redirect('diploma_orders:student_detail', pk=diploma.student.id)
    
    if request.method == 'POST':
        form = DiplomaUploadForm(request.POST, request.FILES, instance=diploma)
        if form.is_valid():
            form.save()
            messages.success(request, "Файл диплома успешно загружен!")
            
            # Если это AJAX запрос
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Файл загружен',
                    'file_url': diploma.file.url if diploma.file else '',
                    'file_name': os.path.basename(diploma.file.name) if diploma.file else ''
                })
            
            return redirect('diploma_orders:diploma_analysis', diploma_id=diploma.id)
    
    else:
        form = DiplomaUploadForm(instance=diploma)
    
    context = {
        'diploma': diploma,
        'form': form,
        'title': f'Загрузка диплома - {diploma.topic[:50]}...'
    }
    
    return render(request, 'diploma_orders/upload_diploma.html', context)


@login_required
def diploma_analysis_dashboard(request, diploma_id):
    """Дашборд анализа диплома"""
    diploma = get_object_or_404(DiplomaProject, id=diploma_id)
    
    # Проверяем права
    if not (request.user.is_staff or request.user == diploma.student.user):
        messages.error(request, "У вас нет прав для просмотра этой страницы")
        return redirect('diploma_orders:home')
    
    # Получаем или создаем анализ
    analysis = None
    if hasattr(diploma, 'ai_analysis'):
        analysis = diploma.ai_analysis
    
    # Формы
    upload_form = DiplomaUploadForm(instance=diploma)
    analysis_form = AIAnalysisRequestForm()
    
    context = {
        'diploma': diploma,
        'analysis': analysis,
        'upload_form': upload_form,
        'analysis_form': analysis_form,
        'has_file': diploma.has_file(),
        'file_extension': diploma.get_file_extension(),
    }
    
    return render(request, 'diploma_orders/diploma_analysis.html', context)


@login_required
def run_ai_analysis(request, diploma_id):
    """Запуск ИИ-анализа диплома"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    diploma = get_object_or_404(DiplomaProject, id=diploma_id)
    
    # Проверяем права
    if not (request.user.is_staff or request.user == diploma.student.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Проверяем наличие файла
    if not diploma.file:
        return JsonResponse({
            'error': 'Сначала загрузите файл диплома',
            'requires_upload': True
        }, status=400)
    
    # Получаем параметры анализа
    analysis_type = request.POST.get('analysis_type', 'full')
    ai_provider = request.POST.get('ai_provider', 'openai')
    
    # Создаем или обновляем запись анализа
    analysis, created = DiplomaAIAnalysis.objects.update_or_create(
        diploma_project=diploma,
        defaults={
            'status': 'processing',
            'ai_provider': ai_provider,
            'diploma_file': diploma.file  # Сохраняем ссылку на файл
        }
    )
    
    try:
        # Запускаем анализ
        analyzer = DiplomaAnalyzer(provider=ai_provider)
        
        diploma_data = {
            'topic': diploma.topic,
            'student_name': diploma.student.get_full_name(),
            'supervisor_name': diploma.supervisor.get_full_name() if diploma.supervisor else 'Не указан'
        }
        
        # Получаем путь к файлу
        if hasattr(diploma.file, 'path'):
            file_path = diploma.file.path
        else:
            file_path = os.path.join(settings.MEDIA_ROOT, diploma.file.name)
        
        # Выполняем анализ в зависимости от типа
        if analysis_type == 'format':
            text, metadata = analyzer.extract_text_from_file(file_path)
            format_check = analyzer.check_format_compliance(text, metadata)
            
            analysis.format_score = format_check['score']
            analysis.format_issues = format_check['issues']
            analysis.format_metadata = format_check['metadata']
            analysis.file_metadata = metadata
            analysis.status = 'completed'
            
        elif analysis_type == 'review':
            text, metadata = analyzer.extract_text_from_file(file_path)
            review = analyzer.generate_review(text, diploma_data)
            
            analysis.review_text = review['text']
            analysis.review_grade = review['grade']
            analysis.review_generated_at = datetime.now()
            analysis.file_metadata = metadata
            analysis.status = 'completed'
            
        elif analysis_type == 'questions':
            text, metadata = analyzer.extract_text_from_file(file_path)
            questions = analyzer.generate_page_questions(text)
            
            analysis.questions = questions
            analysis.file_metadata = metadata
            analysis.status = 'completed'
            
        else:  # full analysis
            result = analyzer.analyze_diploma(file_path, diploma_data)
            
            analysis.format_score = result.get('format_check', {}).get('score', 0)
            analysis.format_issues = result.get('format_check', {}).get('issues', [])
            analysis.format_metadata = result.get('format_check', {}).get('metadata', {})
            
            review = result.get('review', {})
            analysis.review_text = review.get('text', '')
            analysis.review_grade = review.get('grade', '')
            analysis.review_generated_at = datetime.now()
            
            analysis.questions = result.get('questions', [])
            analysis.content_analysis = result.get('content_analysis', {})
            analysis.file_metadata = result.get('metadata', {})
            analysis.raw_response = result
            analysis.status = 'completed'
        
        analysis.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Анализ успешно завершен',
            'analysis_id': analysis.id,
            'redirect_url': f'/diploma/{diploma_id}/analysis/'
        })
        
    except Exception as e:
        analysis.status = 'failed'
        analysis.raw_response = {'error': str(e)}
        analysis.save()
        
        return JsonResponse({
            'success': False,
            'error': f'Ошибка анализа: {str(e)}'
        }, status=500)


@login_required
def delete_diploma_file(request, diploma_id):
    """Удаление файла диплома"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    diploma = get_object_or_404(DiplomaProject, id=diploma_id)
    
    # Проверяем права
    if not (request.user.is_staff or request.user == diploma.student.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Удаляем файл
    if diploma.file:
        file_path = diploma.file.path
        diploma.file.delete(save=False)
        diploma.file = None
        diploma.save()
        
        # Также удаляем связанный анализ
        DiplomaAIAnalysis.objects.filter(diploma_project=diploma).delete()
        
        messages.success(request, "Файл диплома удален")
        
        return JsonResponse({
            'success': True,
            'message': 'Файл удален'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Файл не найден'
    }, status=404)


@login_required
def download_diploma_file(request, diploma_id):
    """Скачивание файла диплома"""
    diploma = get_object_or_404(DiplomaProject, id=diploma_id)
    
    if not diploma.file:
        messages.error(request, "Файл не найден")
        return redirect('diploma_orders:diploma_analysis', diploma_id=diploma.id)
    
    # Проверяем права
    if not (request.user.is_staff or request.user == diploma.student.user or 
            (diploma.supervisor and request.user == diploma.supervisor.user)):
        messages.error(request, "У вас нет прав для скачивания файла")
        return redirect('diploma_orders:home')
    
    response = HttpResponse(diploma.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(diploma.file.name)}"'
    return response


def public_diploma_view(request, diploma_id, token):
    """Публичный доступ к диплому по токену"""
    # Реализация публичных ссылок
    pass