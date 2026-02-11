# diploma_orders/views_ai.py - новый файл
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
import tempfile
import uuid
from datetime import datetime

from .models import DiplomaProject, DiplomaAIAnalysis, PageAIInteraction, AIQuestionBank
from .forms import DiplomaUploadForm, AIAnalysisForm, AIQuestionForm
from .ai_services import DiplomaAnalyzer, AIChatAssistant


@login_required
def upload_diploma_for_analysis(request, diploma_id):
    """Загрузка диплома для анализа ИИ"""
    diploma = get_object_or_404(DiplomaProject, id=diploma_id)
    
    if request.method == 'POST':
        form = DiplomaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            
            # Сохраняем файл
            file_name = f"diploma_{diploma_id}_{uuid.uuid4()}{os.path.splitext(file.name)[1]}"
            file_path = default_storage.save(f'ai_analysis/{file_name}', ContentFile(file.read()))
            
            # Создаем запись анализа
            analysis = DiplomaAIAnalysis.objects.create(
                diploma_project=diploma,
                status='processing',
                ai_provider=request.POST.get('ai_provider', 'openai')
            )
            
            # Запускаем анализ в фоне (можно через Celery)
            # Здесь для простоты делаем синхронно
            try:
                analyzer = DiplomaAnalyzer(provider=analysis.ai_provider)
                
                diploma_data = {
                    'topic': diploma.topic,
                    'student_name': diploma.student.get_full_name(),
                    'supervisor_name': diploma.supervisor.get_full_name() if diploma.supervisor else 'Не указан'
                }
                
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                result = analyzer.analyze_diploma(full_path, diploma_data)
                
                # Сохраняем результаты
                analysis.format_score = result['format_check']['score']
                analysis.format_issues = result['format_check']['issues']
                analysis.format_metadata = result['format_check']['metadata']
                
                analysis.review_text = result['review']['text']
                analysis.review_grade = result['review']['grade']
                analysis.review_generated_at = datetime.fromisoformat(result['review']['generated_at'])
                
                analysis.questions = result['questions']
                analysis.content_analysis = result['content_analysis']
                analysis.file_metadata = result['metadata']
                analysis.raw_response = result
                
                analysis.status = 'completed'
                analysis.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Анализ завершен',
                    'analysis_id': analysis.id
                })
                
            except Exception as e:
                analysis.status = 'failed'
                analysis.raw_response = {'error': str(e)}
                analysis.save()
                
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def get_analysis_results(request, analysis_id):
    """Получение результатов анализа"""
    analysis = get_object_or_404(DiplomaAIAnalysis, id=analysis_id)
    
    return JsonResponse({
        'status': analysis.status,
        'format_score': analysis.format_score,
        'format_issues': analysis.format_issues,
        'review': {
            'text': analysis.review_text,
            'grade': analysis.review_grade
        },
        'questions': analysis.questions,
        'content_analysis': analysis.content_analysis
    })


@login_required
def analyze_page_content(request):
    """Анализ контента страницы и генерация вопросов"""
    if request.method == 'POST':
        data = json.loads(request.body)
        page_text = data.get('text', '')
        page_url = data.get('url', '')
        page_title = data.get('title', '')
        
        # Генерируем вопросы для страницы
        analyzer = DiplomaAnalyzer()
        questions = analyzer.generate_page_questions(page_text)
        
        # Сохраняем взаимодействие
        if request.user.is_authenticated:
            interaction, created = PageAIInteraction.objects.get_or_create(
                user=request.user,
                page_url=page_url,
                defaults={
                    'page_title': page_title,
                    'page_context': page_text[:1000],
                    'session_id': request.session.session_key
                }
            )
            
            # Обновляем краткое содержание
            if len(page_text) > 100:
                interaction.page_summary = page_text[:500] + "..."
                interaction.save()
        
        return JsonResponse({
            'questions': questions,
            'page_id': interaction.id if request.user.is_authenticated else None
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@require_POST
def ask_ai_assistant(request):
    """Задать вопрос ИИ-ассистенту"""
    data = json.loads(request.body)
    question = data.get('question', '')
    context = data.get('context', '')
    page_id = data.get('page_id')
    
    if not question:
        return JsonResponse({'error': 'Вопрос обязателен'}, status=400)
    
    # Получаем или создаем взаимодействие
    interaction = None
    if page_id and request.user.is_authenticated:
        try:
            interaction = PageAIInteraction.objects.get(id=page_id, user=request.user)
        except PageAIInteraction.DoesNotExist:
            pass
    
    # Получаем ответ от ИИ
    assistant = AIChatAssistant()
    
    if interaction:
        context_id = f"user_{request.user.id}_page_{interaction.id}"
    else:
        context_id = f"anon_{request.session.session_key}"
    
    response = assistant.get_page_assistance(
        page_text=context[:5000],
        user_question=question,
        context_id=context_id
    )
    
    # Сохраняем взаимодействие
    if interaction:
        interaction.add_interaction(
            question=question,
            answer=response['answer'],
            ai_suggestions=response['suggested_questions']
        )
    
    return JsonResponse({
        'answer': response['answer'],
        'suggested_questions': response['suggested_questions'],
        'context_id': response['context_id']
    })


@login_required
def diploma_ai_dashboard(request, diploma_id):
    """Дашборд анализа диплома"""
    diploma = get_object_or_404(DiplomaProject, id=diploma_id)
    
    # Получаем или создаем анализ
    analysis, created = DiplomaAIAnalysis.objects.get_or_create(
        diploma_project=diploma,
        defaults={'status': 'pending'}
    )
    
    # Форма для нового анализа
    analysis_form = AIAnalysisForm()
    
    # Банк вопросов для этой темы
    related_questions = AIQuestionBank.objects.filter(
        tags__contains=[tag.lower() for tag in diploma.topic.split()[:3]],
        is_active=True
    )[:10]
    
    context = {
        'diploma': diploma,
        'analysis': analysis,
        'analysis_form': analysis_form,
        'related_questions': related_questions,
        'ai_enabled': True
    }
    
    return render(request, 'diploma_orders/ai_dashboard.html', context)


@login_required
def generate_questions_for_page(request):
    """Генерация вопросов для конкретной страницы"""
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '')
        page_num = data.get('page', 1)
        
        analyzer = DiplomaAnalyzer()
        questions = analyzer.generate_page_questions(text, page_num)
        
        # Сохраняем в банк вопросов (если пользователь авторизован)
        if request.user.is_authenticated and request.user.is_staff:
            for q in questions:
                AIQuestionBank.objects.create(
                    category='diploma_defense',
                    question_text=q['text'],
                    question_type=q['type'],
                    difficulty=q['difficulty'],
                    tags=['auto_generated', 'page_questions']
                )
        
        return JsonResponse({'questions': questions})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def ai_settings(request):
    """Настройки ИИ"""
    context = {
        'providers': [
            {'id': 'openai', 'name': 'OpenAI GPT', 'enabled': True},
            {'id': 'anthropic', 'name': 'Claude', 'enabled': False},
            {'id': 'yandex', 'name': 'Yandex GPT', 'enabled': False}
        ],
        'default_provider': 'openai'
    }
    
    return render(request, 'diploma_orders/ai_settings.html', context)