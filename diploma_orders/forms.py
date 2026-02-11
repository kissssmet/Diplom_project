from django import forms
from datetime import date
from django.core.exceptions import ValidationError
import json

from .models import Student, Supervisor, DiplomaProject, Group, GroupOrder
from .models import OrderTemplate, TemplateSection, GeneratedDocument, DocumentCollaborator


class StudentSearchForm(forms.Form):
    """Форма поиска студентов"""
    query = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ФИО студента или номер студбилета'
        })
    )
    
    supervisor = forms.ModelChoiceField(
        queryset=Supervisor.objects.all(),
        required=False,
        label='Фильтр по руководителю',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='Фильтр по группе',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Все статусы'),
            ('registered', 'Зарегистрирована'),
            ('in_progress', 'В работе'),
            ('review', 'На рецензии'),
            ('completed', 'Завершена'),
            ('defended', 'Защищена'),
        ],
        required=False,
        label='Статус работы',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class OrderGenerationForm(forms.Form):
    """Форма выбора формата приказа"""
    FORMAT_CHOICES = [
        ('preview', 'Просмотр в браузере'),
        ('md', 'Скачать как Markdown (.md)'),
        ('docx', 'Скачать как Word (.docx)'),
    ]
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        label='Формат приказа',
        widget=forms.RadioSelect()
    )


class GroupOrderForm(forms.ModelForm):
    """Форма создания приказа по группе"""
    class Meta:
        model = GroupOrder
        fields = ['order_date', 'study_form', 'direction', 'note']
        widgets = {
            'order_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'study_form': forms.Select(attrs={'class': 'form-select'}),
            'direction': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные примечания...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order_date'].initial = date.today()


# === Новые формы для умного редактора ===

class OrderTemplateForm(forms.ModelForm):
    """Форма шаблона документа"""
    class Meta:
        model = OrderTemplate
        fields = ['name', 'description', 'template_type', 'content', 
                 'available_fields', 'default_formatting', 'docx_template', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опишите предназначение этого шаблона...'
            }),
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control template-editor',
                'rows': 15,
                'placeholder': 'Используйте {{field_name}} для подстановки значений...'
            }),
            'available_fields': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Введите JSON массив, например: ["student_name", "topic", "supervisor"]'
            }),
            'default_formatting': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Введите JSON объект, например: {"font": "Times New Roman", "size": 14}'
            }),
            'docx_template': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_available_fields(self):
        """Валидация JSON для available_fields"""
        data = self.cleaned_data['available_fields']
        if data:
            try:
                parsed = json.loads(data)
                if not isinstance(parsed, list):
                    raise ValidationError('Должен быть JSON массив (список)')
            except json.JSONDecodeError as e:
                raise ValidationError(f'Неверный формат JSON: {e}')
        return data
    
    def clean_default_formatting(self):
        """Валидация JSON для default_formatting"""
        data = self.cleaned_data['default_formatting']
        if data:
            try:
                parsed = json.loads(data)
                if not isinstance(parsed, dict):
                    raise ValidationError('Должен быть JSON объект (словарь)')
            except json.JSONDecodeError as e:
                raise ValidationError(f'Неверный формат JSON: {e}')
        return data


class TemplateSectionForm(forms.ModelForm):
    """Форма раздела шаблона"""
    class Meta:
        model = TemplateSection
        fields = ['title', 'content', 'order', 'available_fields', 
                 'display_conditions', 'is_required', 'can_be_deleted', 'can_be_edited']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control section-editor',
                'rows': 8,
                'placeholder': 'Содержимое раздела...'
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_fields': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'JSON массив полей доступных в этом разделе'
            }),
            'display_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'JSON объект условий отображения'
            }),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_be_deleted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_be_edited': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and not self.instance.can_be_deleted:
            self.fields['can_be_deleted'].widget.attrs['disabled'] = True


class DocumentGeneratorForm(forms.Form):
    """Форма для генерации документа"""
    template = forms.ModelChoiceField(
        queryset=OrderTemplate.objects.filter(is_active=True),
        label='Шаблон',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        template_id = kwargs.pop('template_id', None)
        super().__init__(*args, **kwargs)
        
        if template_id:
            try:
                template = OrderTemplate.objects.get(id=template_id)
                fields = template.get_available_fields_list()
                for field in fields:
                    self.fields[field] = forms.CharField(
                        label=field.replace('_', ' ').title(),
                        required=False,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )
            except OrderTemplate.DoesNotExist:
                pass


class DocumentCollaboratorForm(forms.ModelForm):
    """Форма добавления участника документа"""
    class Meta:
        model = DocumentCollaborator
        fields = ['user', 'role', 'can_edit', 'can_comment', 'can_approve', 'can_sign']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'can_edit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_comment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_approve': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_sign': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DocumentEditForm(forms.ModelForm):
    """Форма редактирования документа"""
    class Meta:
        model = GeneratedDocument
        fields = ['content', 'status']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control document-editor',
                'rows': 20,
                'placeholder': 'Редактируйте содержимое документа здесь...'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
# diploma_orders/forms.py - дополняем
class DiplomaUploadForm(forms.ModelForm):
    """Форма загрузки дипломной работы"""
    file = forms.FileField(
        label='Дипломная работа',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.docx,.doc,.txt,.jpg,.png'
        })
    )
    
    class Meta:
        model = DiplomaProject
        fields = ['file']  # Нужно добавить поле file в модель


class AIAnalysisForm(forms.Form):
    """Форма запроса анализа ИИ"""
    analysis_type = forms.ChoiceField(
        label='Тип анализа',
        choices=[
            ('full', 'Полный анализ (формат + рецензия + вопросы)'),
            ('format', 'Только проверка формата'),
            ('review', 'Только рецензия'),
            ('questions', 'Только вопросы для защиты')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    ai_provider = forms.ChoiceField(
        label='ИИ-провайдер',
        choices=[
            ('openai', 'OpenAI GPT'),
            ('anthropic', 'Claude (Anthropic)'),
            ('yandex', 'Yandex GPT')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class AIQuestionForm(forms.Form):
    """Форма вопроса к ИИ"""
    question = forms.CharField(
        label='Ваш вопрос',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Задайте вопрос по дипломной работе...',
            'maxlength': 500
        })
    )
    
    context = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
# diploma_orders/forms.py - добавляем новые формы
from django import forms
from .models import DiplomaProject

class DiplomaUploadForm(forms.ModelForm):
    """Форма загрузки дипломной работы"""
    class Meta:
        model = DiplomaProject
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.docx,.doc,.txt,.jpg,.jpeg,.png',
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверяем размер файла (макс 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise forms.ValidationError(f"Файл слишком большой. Максимальный размер: {max_size//1024//1024}MB")
            
            # Проверяем расширение
            allowed_extensions = ['.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(f"Неподдерживаемый формат. Разрешенные форматы: {', '.join(allowed_extensions)}")
        
        return file


class AIAnalysisRequestForm(forms.Form):
    """Форма запроса анализа ИИ"""
    analysis_type = forms.ChoiceField(
        label='Тип анализа',
        choices=[
            ('full', 'Полный анализ (формат + рецензия + вопросы)'),
            ('format', 'Только проверка формата'),
            ('review', 'Только рецензия'),
            ('questions', 'Только вопросы для защиты'),
        ],
        initial='full',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input analysis-type-radio'
        })
    )
    
    ai_provider = forms.ChoiceField(
        label='ИИ-провайдер',
        choices=[
            ('openai', 'OpenAI GPT'),
            ('anthropic', 'Claude (Anthropic)'),
        ],
        initial='openai',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'ai-provider-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамически определяем доступные провайдеры
        from django.conf import settings
        providers = []
        
        if getattr(settings, 'OPENAI_API_KEY', ''):
            providers.append(('openai', 'OpenAI GPT'))
        if getattr(settings, 'ANTHROPIC_API_KEY', ''):
            providers.append(('anthropic', 'Claude (Anthropic)'))
        
        if not providers:
            providers.append(('demo', 'Демо-режим (без API)'))
        
        self.fields['ai_provider'].choices = providers


class QuickQuestionForm(forms.Form):
    """Форма быстрого вопроса к ИИ"""
    question = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Задайте вопрос по дипломной работе...',
            'style': 'resize: none;'
        }),
        max_length=500
    )
    
    context = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )