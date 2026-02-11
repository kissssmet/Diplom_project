from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import os

def student_photo_path(instance, filename):
    """Генерация пути для фотографий студентов"""
    ext = filename.split('.')[-1]
    filename = f'student_{instance.student_id}.{ext}'
    return os.path.join('students/photos', filename)

class Group(models.Model):
    """Модель учебной группы"""
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Название группы",
        help_text="Например: ИВТ-401, ПМИ-301"
    )
    faculty = models.CharField(
        max_length=100,
        verbose_name="Факультет",
        help_text="Название факультета"
    )
    course = models.IntegerField(
        verbose_name="Курс",
        help_text="Номер курса (1-6)"
    )
    @property
    def students_with_diploma_count(self):
        return self.students.filter(diploma_project__isnull=False).count()
    
    @property
    def students_without_diploma_count(self):
        return self.students.filter(diploma_project__isnull=True).count()
    
    class Meta:
        verbose_name = "Учебная группа"
        verbose_name_plural = "Учебные группы"
        ordering = ['course', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.faculty}, {self.course} курс)"

class Supervisor(models.Model):
    """Модель научного руководителя"""
    last_name = models.CharField(
        max_length=100, 
        verbose_name="Фамилия",
        help_text="Введите фамилию руководителя"
    )
    first_name = models.CharField(
        max_length=100, 
        verbose_name="Имя",
        help_text="Введите имя руководителя"
    )
    patronymic = models.CharField(
        max_length=100, 
        verbose_name="Отчество",
        help_text="Введите отчество руководителя"
    )
    academic_degree = models.CharField(
        max_length=100,
        verbose_name="Ученая степень",
        help_text="Например: к.т.н., д.ф.-м.н., PhD"
    )
    position = models.CharField(
        max_length=100,
        verbose_name="Должность",
        help_text="Например: профессор, доцент, старший преподаватель"
    )
    email = models.EmailField(
        verbose_name="Email",
        blank=True,
        null=True
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Научный руководитель"
        verbose_name_plural = "Научные руководители"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}"
    
    def get_full_name(self):
        """Полное ФИО руководителя"""
        return f"{self.last_name} {self.first_name} {self.patronymic}"

class Student(models.Model):
    """Модель студента"""
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь системы",
        help_text="Связь с учетной записью пользователя (опционально)"
    )
    last_name = models.CharField(
        max_length=100, 
        verbose_name="Фамилия",
        help_text="Введите фамилию студента"
    )
    first_name = models.CharField(
        max_length=100, 
        verbose_name="Имя",
        help_text="Введите имя студента"
    )
    patronymic = models.CharField(
        max_length=100, 
        verbose_name="Отчество",
        blank=True,
        null=True,
        help_text="Введите отчество студента (необязательно)"
    )
    photo = models.ImageField(
        upload_to=student_photo_path,
        verbose_name="Фотография",
        blank=True,
        null=True,
        help_text="Загрузите фотографию студента"
    )
    student_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Номер студенческого билета",
        help_text="Уникальный идентификатор студента"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Учебная группа",
        related_name='students'
    )
    email = models.EmailField(
        verbose_name="Email",
        blank=True,
        null=True
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        if self.patronymic:
            return f"{self.last_name} {self.first_name} {self.patronymic}"
        return f"{self.last_name} {self.first_name}"
    
    def get_full_name(self):
        """Полное ФИО студента"""
        if self.patronymic:
            return f"{self.last_name} {self.first_name} {self.patronymic}"
        return f"{self.last_name} {self.first_name}"
    
    def get_absolute_url(self):
        """URL для детальной страницы студента"""
        return reverse('student_detail', args=[str(self.id)])

class DiplomaProject(models.Model):
    """Модель дипломного проекта"""
    topic = models.CharField(
        max_length=500,
        verbose_name="Тема дипломной работы",
        help_text="Введите полное название темы дипломной работы"
    )
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        verbose_name="Студент",
        related_name='diploma_project'
    )
    supervisor = models.ForeignKey(
        Supervisor,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Научный руководитель",
        related_name='diploma_projects'
    )
    registration_date = models.DateField(
        verbose_name="Дата регистрации темы",
        help_text="Дата утверждения темы дипломной работы"
    )
    deadline = models.DateField(
        verbose_name="Плановый срок сдачи",
        help_text="Планируемая дата завершения работы"
    )
    file = models.FileField(
        "Файл диплома",
        upload_to='diplomas/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Загрузите файл дипломной работы (PDF, DOCX, DOC, TXT)"
    )

    STATUS_CHOICES = [
        ('registered', 'Зарегистрирована'),
        ('in_progress', 'В работе'),
        ('review', 'На рецензии'),
        ('completed', 'Завершена'),
        ('defended', 'Защищена'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='registered',
        verbose_name="Статус работы"
    )
    description = models.TextField(
        verbose_name="Описание работы",
        blank=True,
        null=True,
        help_text="Краткое описание дипломной работы"
    )
    
    class Meta:
        verbose_name = "Дипломный проект"
        verbose_name_plural = "Дипломные проекты"
        ordering = ['deadline']
    
    def __str__(self):
        return f"{self.topic[:50]}... ({self.student})"
    
    def get_status_display_class(self):
        """Возвращает CSS класс для статуса"""
        status_classes = {
            'registered': 'badge-info',
            'in_progress': 'badge-primary',
            'review': 'badge-warning',
            'completed': 'badge-success',
            'defended': 'badge-success',
        }
        return status_classes.get(self.status, 'badge-secondary')
    # Добавляем метод для проверки наличия файла
    def has_file(self):
        return bool(self.file)
    
    def has_file(self):
        """Проверяет, загружен ли файл"""
        return bool(self.file)
    
    def get_file_extension(self):
        """Возвращает расширение файла"""
        if self.file:
            return os.path.splitext(self.file.name)[1].lower().replace('.', '')
        return ''
    
    def get_file_size(self):
        """Возвращает размер файла"""
        if self.file and hasattr(self.file, 'size'):
            return self.file.size
        return 0

class GroupOrder(models.Model):
    """Модель приказа по группе"""
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        verbose_name="Учебная группа",
        related_name='orders'
    )
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Номер приказа"
    )
    order_date = models.DateField(
        verbose_name="Дата приказа",
        default=timezone.now
    )
    study_form = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Очная'),
            ('part_time', 'Заочная'),
        ],
        default='full_time',
        verbose_name="Форма обучения"
    )
    direction = models.CharField(
        max_length=200,
        verbose_name="Направление подготовки"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    note = models.TextField(
        verbose_name="Дополнительные примечания",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Приказ по группе"
        verbose_name_plural = "Приказы по группам"
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Приказ №{self.order_number} от {self.order_date} - {self.group.name}"
    
    def get_study_form_display(self):
        """Полное название формы обучения"""
        return dict(self._meta.get_field('study_form').choices).get(self.study_form, '')
class OrderTemplate(models.Model):
    """Шаблон приказа/договора"""
    name = models.CharField('Название шаблона', max_length=200)
    description = models.TextField('Описание шаблона', blank=True)
    
    # Тип шаблона
    TEMPLATE_TYPE_CHOICES = [
        ('student_order', 'Приказ по студенту'),
        ('group_order', 'Приказ по группе'),
        ('contract', 'Договор'),
        ('agreement', 'Соглашение'),
    ]
    template_type = models.CharField(
        'Тип шаблона',
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        default='student_order'
    )
    
    # Поля, доступные для подстановки
    available_fields = models.JSONField(
        'Доступные поля',
        default=list,
        help_text='Список доступных полей для подстановки в формате JSON'
    )
    
    # Структура документа
    content = models.TextField(
        'Содержимое шаблона',
        help_text='Используйте {{field_name}} для подстановки значений'
    )
    
    # Настройки форматирования
    default_formatting = models.JSONField(
        'Настройки форматирования',
        default=dict,
        blank=True,
        help_text='Настройки форматирования по умолчанию в формате JSON'
    )
    
    # Файл DOCX для экспорта
    docx_template = models.FileField(
        'Файл шаблона DOCX',
        upload_to='order_templates/',
        blank=True,
        null=True,
        help_text='Файл .docx с макросом для заполнения'
    )
    
    is_active = models.BooleanField('Активный', default=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def get_available_fields_list(self):
        """Получить список доступных полей"""
        return self.available_fields if isinstance(self.available_fields, list) else []
    
    class Meta:
        verbose_name = 'Шаблон приказа'
        verbose_name_plural = 'Шаблоны приказов'
        ordering = ['-updated_at']


class TemplateSection(models.Model):
    """Раздел шаблона (для гибкого редактирования)"""
    template = models.ForeignKey(
        OrderTemplate,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='Шаблон'
    )
    
    title = models.CharField('Название раздела', max_length=200)
    content = models.TextField('Содержимое раздела')
    order = models.IntegerField('Порядок', default=0)
    
    # Поля, доступные в этом разделе
    available_fields = models.JSONField(
        'Доступные поля в разделе',
        default=list,
        blank=True
    )
    
    # Условия отображения
    display_conditions = models.JSONField(
        'Условия отображения',
        default=dict,
        blank=True,
        help_text='Условия, при которых раздел отображается'
    )
    
    is_required = models.BooleanField('Обязательный раздел', default=True)
    can_be_deleted = models.BooleanField('Можно удалить', default=True)
    can_be_edited = models.BooleanField('Можно редактировать', default=True)
    
    class Meta:
        verbose_name = 'Раздел шаблона'
        verbose_name_plural = 'Разделы шаблона'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.template.name} - {self.title}"


class GeneratedDocument(models.Model):
    """Сгенерированный документ"""
    template = models.ForeignKey(
        OrderTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_documents',
        verbose_name='Шаблон'
    )
    
    # Ссылка на объект
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='generated_documents',
        verbose_name='Студент'
    )
    
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='generated_documents',
        verbose_name='Группа'
    )
    
    # Данные документа
    document_data = models.JSONField(
        'Данные документа',
        default=dict,
        help_text='Данные, использованные для генерации документа'
    )
    
    # Сгенерированный контент
    content = models.TextField('Содержимое документа')
    
    # Файлы
    html_file = models.FileField('HTML файл', upload_to='documents/html/', blank=True, null=True)
    docx_file = models.FileField('DOCX файл', upload_to='documents/docx/', blank=True, null=True)
    pdf_file = models.FileField('PDF файл', upload_to='documents/pdf/', blank=True, null=True)
    
    # Метаданные
    document_number = models.CharField('Номер документа', max_length=100, unique=True)
    document_date = models.DateField('Дата документа')
    
    # Статус
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('generated', 'Сгенерирован'),
        ('signed', 'Подписан'),
        ('archived', 'В архиве'),
    ]
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Создатель'
    )
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        verbose_name = 'Сгенерированный документ'
        verbose_name_plural = 'Сгенерированные документы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document_number} - {self.template.name if self.template else 'Без шаблона'}"


class DocumentCollaborator(models.Model):
    """Участник документа (редакторы, подписанты и т.д.)"""
    document = models.ForeignKey(
        GeneratedDocument,
        on_delete=models.CASCADE,
        related_name='collaborators',
        verbose_name='Документ'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    
    ROLE_CHOICES = [
        ('editor', 'Редактор'),
        ('reviewer', 'Рецензент'),
        ('approver', 'Согласующий'),
        ('signatory', 'Подписант'),
        ('viewer', 'Наблюдатель'),
    ]
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES)
    
    # Права
    can_edit = models.BooleanField('Может редактировать', default=False)
    can_comment = models.BooleanField('Может комментировать', default=False)
    can_approve = models.BooleanField('Может согласовывать', default=False)
    can_sign = models.BooleanField('Может подписывать', default=False)
    
    # Статус участия
    is_active = models.BooleanField('Активный участник', default=True)
    joined_at = models.DateTimeField('Присоединился', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Участник документа'
        verbose_name_plural = 'Участники документов'
        unique_together = ['document', 'user', 'role']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} ({self.document})"
# Добавляем в models.py после DocumentCollaborator

class DocumentHistory(models.Model):
    """История изменений документа"""
    document = models.ForeignKey(
        GeneratedDocument,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Документ'
    )
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Пользователь'
    )
    
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('edit', 'Редактирование'),
        ('comment', 'Комментарий'),
        ('approve', 'Согласование'),
        ('reject', 'Отклонение'),
        ('sign', 'Подписание'),
        ('export', 'Экспорт'),
    ]
    
    action = models.CharField('Действие', max_length=20, choices=ACTION_CHOICES)
    changes = models.TextField('Изменения', blank=True)
    comment = models.TextField('Комментарий', blank=True)
    
    timestamp = models.DateTimeField('Время', auto_now_add=True)
    
    class Meta:
        verbose_name = 'История документа'
        verbose_name_plural = 'Истории документов'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.document.document_number} ({self.timestamp})"

class DiplomaAIAnalysis(models.Model):
    """Анализ диплома ИИ"""
    diploma_project = models.OneToOneField(
        DiplomaProject,
        on_delete=models.CASCADE,
        related_name='ai_analysis',
        verbose_name="Дипломный проект"
    )
    
    # Проверка формата
    format_score = models.IntegerField("Оценка формата", default=0)
    format_issues = models.JSONField("Проблемы формата", default=list)
    format_metadata = models.JSONField("Метаданные", default=dict)
    
    # Рецензия
    review_text = models.TextField("Текст рецензии", blank=True)
    review_grade = models.CharField("Оценка", max_length=50, blank=True)
    review_generated_at = models.DateTimeField("Дата рецензии", null=True)
    
    # Вопросы
    questions = models.JSONField("Вопросы для защиты", default=list)
    
    # Анализ содержания
    content_analysis = models.JSONField("Анализ содержания", default=dict)
    
    # Технические данные
    ai_provider = models.CharField("Провайдер ИИ", max_length=50, default='openai')
    raw_response = models.JSONField("Сырой ответ ИИ", default=dict)
    file_metadata = models.JSONField("Метаданные файла", default=dict)
    
    # Статус
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('processing', 'В обработке'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    
    class Meta:
        verbose_name = "Анализ ИИ диплома"
        verbose_name_plural = "Анализы ИИ дипломов"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Анализ диплома #{self.diploma_project.id}"
    
    def get_format_score_color(self):
        """Цвет для отображения оценки"""
        if self.format_score >= 80:
            return 'success'
        elif self.format_score >= 60:
            return 'warning'
        else:
            return 'danger'
    
    def get_questions_count(self):
        """Количество сгенерированных вопросов"""
        return len(self.questions) if isinstance(self.questions, list) else 0


class PageAIInteraction(models.Model):
    """Взаимодействие с ИИ на странице"""
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        null=True
    )
    
    page_url = models.CharField("URL страницы", max_length=500)
    page_title = models.CharField("Название страницы", max_length=200)
    
    # Контекст страницы (сохраняем текст/контент)
    page_context = models.TextField("Контекст страницы", blank=True)
    page_summary = models.TextField("Краткое содержание", blank=True)
    
    # Взаимодействие
    questions_asked = models.JSONField("Заданные вопросы", default=list)
    ai_responses = models.JSONField("Ответы ИИ", default=list)
    
    # Сессия
    session_id = models.CharField("ID сессии", max_length=100)
    
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    last_interaction = models.DateTimeField("Последнее взаимодействие", auto_now=True)
    
    class Meta:
        verbose_name = "Взаимодействие с ИИ"
        verbose_name_plural = "Взаимодействия с ИИ"
        ordering = ['-last_interaction']
    
    def __str__(self):
        return f"Взаимодействие {self.user} на {self.page_title}"
    
    def add_interaction(self, question: str, answer: str, ai_suggestions: list = None):
        """Добавить взаимодействие"""
        interaction = {
            'question': question,
            'answer': answer,
            'suggestions': ai_suggestions or [],
            'timestamp': datetime.now().isoformat()
        }
        
        self.questions_asked.append(question)
        self.ai_responses.append(interaction)
        
        # Ограничиваем историю
        if len(self.questions_asked) > 50:
            self.questions_asked = self.questions_asked[-50:]
            self.ai_responses = self.ai_responses[-50:]
        
        self.save()


class AIQuestionBank(models.Model):
    """Банк вопросов ИИ для разных тем"""
    category = models.CharField("Категория", max_length=100)
    subcategory = models.CharField("Подкатегория", max_length=100, blank=True)
    
    question_text = models.TextField("Текст вопроса")
    question_type = models.CharField("Тип вопроса", max_length=50, choices=[
        ('theory', 'Теоретический'),
        ('methodology', 'Методологический'),
        ('practical', 'Практический'),
        ('analytical', 'Аналитический'),
        ('critical', 'Критический')
    ])
    
    difficulty = models.CharField("Сложность", max_length=20, choices=[
        ('easy', 'Легкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
        ('expert', 'Экспертный')
    ])
    
    tags = models.JSONField("Теги", default=list)
    suggested_answers = models.TextField("Примерные ответы", blank=True)
    
    usage_count = models.IntegerField("Использований", default=0)
    success_rate = models.FloatField("Успешность", default=0.0)
    
    is_active = models.BooleanField("Активный", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    
    class Meta:
        verbose_name = "Вопрос ИИ"
        verbose_name_plural = "Банк вопросов ИИ"
        ordering = ['category', 'difficulty']
    
    def __str__(self):
        return f"{self.category}: {self.question_text[:100]}..."
    
    def increment_usage(self, was_successful: bool = True):
        """Увеличить счетчик использования"""
        self.usage_count += 1
        
        if was_successful:
            current_success = self.success_rate * (self.usage_count - 1)
            self.success_rate = (current_success + 1) / self.usage_count
        
        self.save()