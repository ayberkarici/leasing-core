"""
Management command to seed initial admin user and departments.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import CustomUser, Department


class Command(BaseCommand):
    help = 'Seed initial admin user and departments'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Admin username (default: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@leasing.local',
            help='Admin email (default: admin@leasing.local)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Admin password (default: admin123)'
        )
    
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding initial data...')
        
        # Create departments
        departments_data = [
            {'name': 'Satış', 'department_type': Department.DepartmentType.SALES},
            {'name': 'Finans', 'department_type': Department.DepartmentType.FINANCE},
            {'name': 'Hukuk', 'department_type': Department.DepartmentType.LEGAL},
            {'name': 'Operasyon', 'department_type': Department.DepartmentType.OPERATIONS},
            {'name': 'Bilgi Teknolojileri', 'department_type': Department.DepartmentType.IT},
            {'name': 'İnsan Kaynakları', 'department_type': Department.DepartmentType.HR},
        ]
        
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'department_type': dept_data['department_type']}
            )
            if created:
                self.stdout.write(f'  Created department: {dept.name}')
            else:
                self.stdout.write(f'  Department exists: {dept.name}')
        
        # Create admin user
        username = options['username']
        email = options['email']
        password = options['password']
        
        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Sistem',
                'last_name': 'Yöneticisi',
                'user_type': CustomUser.UserType.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f'\nAdmin user created:'
                f'\n  Username: {username}'
                f'\n  Email: {email}'
                f'\n  Password: {password}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Admin user already exists: {username}'
            ))
        
        # Create a sample salesperson
        sales_user, created = CustomUser.objects.get_or_create(
            username='satis1',
            defaults={
                'email': 'satis1@leasing.local',
                'first_name': 'Ahmet',
                'last_name': 'Yılmaz',
                'user_type': CustomUser.UserType.SALESPERSON,
                'department': Department.objects.get(name='Satış'),
                'is_verified': True,
            }
        )
        
        if created:
            sales_user.set_password('satis123')
            sales_user.save()
            self.stdout.write(self.style.SUCCESS(
                f'\nSalesperson created:'
                f'\n  Username: satis1'
                f'\n  Password: satis123'
            ))
        
        # Create a sample customer
        customer_user, created = CustomUser.objects.get_or_create(
            username='musteri1',
            defaults={
                'email': 'musteri1@example.com',
                'first_name': 'Mehmet',
                'last_name': 'Demir',
                'user_type': CustomUser.UserType.CUSTOMER,
                'is_verified': True,
            }
        )
        
        if created:
            customer_user.set_password('musteri123')
            customer_user.save()
            self.stdout.write(self.style.SUCCESS(
                f'\nCustomer created:'
                f'\n  Username: musteri1'
                f'\n  Password: musteri123'
            ))
        
        self.stdout.write(self.style.SUCCESS('\nSeeding completed!'))

