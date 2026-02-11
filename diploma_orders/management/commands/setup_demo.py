from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from diploma_orders.models import Group, Supervisor, Student, DiplomaProject
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Настройка демо данных для системы дипломных приказов'

    def handle(self, *args, **kwargs):
        self.stdout.write('🚀 Настройка демо данных...')
        
        # Создаем группы
        groups_data = [
            {'name': 'ИВТ-401', 'faculty': 'Информатика и вычислительная техника', 'course': 4},
            {'name': 'ПМИ-301', 'faculty': 'Прикладная математика и информатика', 'course': 3},
            {'name': 'ИБ-501', 'faculty': 'Информационная безопасность', 'course': 5},
            {'name': 'ФИИТ-201', 'faculty': 'Фундаментальная информатика и ИТ', 'course': 2},
        ]
        
        groups = []
        for data in groups_data:
            group = Group.objects.create(**data)
            groups.append(group)
        
        self.stdout.write('✅ Созданы группы')
        
        # Создаем руководителей
        supervisors_data = [
            {
                'last_name': 'Иванов',
                'first_name': 'Иван',
                'patronymic': 'Иванович',
                'academic_degree': 'д.т.н.',
                'position': 'профессор',
                'email': 'i.ivanov@university.edu',
                'phone': '+7 (999) 123-45-67'
            },
            {
                'last_name': 'Петрова',
                'first_name': 'Мария',
                'patronymic': 'Сергеевна',
                'academic_degree': 'к.т.н.',
                'position': 'доцент',
                'email': 'm.petrova@university.edu',
                'phone': '+7 (999) 234-56-78'
            },
            {
                'last_name': 'Сидоров',
                'first_name': 'Алексей',
                'patronymic': 'Петрович',
                'academic_degree': 'к.ф.-м.н.',
                'position': 'старший преподаватель',
                'email': 'a.sidorov@university.edu',
                'phone': '+7 (999) 345-67-89'
            },
        ]
        
        supervisors = []
        for data in supervisors_data:
            supervisor = Supervisor.objects.create(**data)
            supervisors.append(supervisor)
        
        self.stdout.write('✅ Созданы руководители')
        
        # Создаем демо студентов
        first_names = ['Александр', 'Мария', 'Дмитрий', 'Анна', 'Сергей', 'Екатерина', 'Алексей', 'Ольга', 'Иван', 'Наталья']
        last_names = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Фёдоров', 'Морозов', 'Волков']
        
        demo_students = []
        for i in range(1, 21):
            group = groups[i % len(groups)]
            student = Student.objects.create(
                last_name=last_names[i % len(last_names)],
                first_name=first_names[i % len(first_names)],
                patronymic='Александрович' if i % 2 == 0 else 'Алексеевна',
                student_id=f'STD-2023-{i:03d}',
                group=group,
                email=f'student{i}@university.edu',
                phone=f'+7 (999) {500+i:03d}-{i:02d}-{(i+10):02d}'
            )
            demo_students.append(student)
        
        self.stdout.write('✅ Созданы демо студенты')
        
        # Создаем демо дипломные проекты
        topics = [
            'Разработка системы управления учебным процессом',
            'Исследование методов машинного обучения для анализа текста',
            'Создание мобильного приложения для университета',
            'Разработка веб-сервиса для онлайн-обучения',
            'Анализ и проектирование баз данных',
            'Исследование алгоритмов компьютерного зрения',
            'Разработка системы защиты информации',
            'Создание платформы для дистанционного образования',
            'Анализ больших данных в образовании',
            'Разработка интеллектуальной системы тестирования',
        ]
        
        statuses = ['registered', 'in_progress', 'review', 'completed', 'defended']
        
        for i, student in enumerate(demo_students):
            if i < len(topics):
                status = statuses[i % len(statuses)]
                
                DiplomaProject.objects.create(
                    topic=topics[i],
                    student=student,
                    supervisor=supervisors[i % len(supervisors)],
                    registration_date=date(2023, 9, 1) + timedelta(days=i*10),
                    deadline=date(2024, 6, 15) + timedelta(days=i*5),
                    status=status,
                    description=f'Демо описание дипломной работы студента {student.get_full_name()}'
                )
        
        self.stdout.write('✅ Созданы демо дипломные проекты')
        self.stdout.write('\n🎉 Демо данные успешно настроены!')
        self.stdout.write('👉 Перейдите на http://localhost:8000/ для просмотра')