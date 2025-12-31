# Custom migration for UsageType model and ForeignKey relationships

from django.db import migrations, models
import django.db.models.deletion


def create_default_usage_types(apps, schema_editor):
    """Create default usage types"""
    UsageType = apps.get_model('it_tools', 'UsageType')
    
    default_types = [
        {'name': 'AD Log Analizi', 'code': 'AD_LOG', 'description': 'Active Directory log dosyalarının analizi için'},
        {'name': 'Email Şablonları', 'code': 'EMAIL_TEMPLATE', 'description': 'Email gönderimi için kullanılan şablonlar'},
        {'name': 'Yedekleme', 'code': 'BACKUP', 'description': 'Yedekleme işlemleri için'},
        {'name': 'Veri Dışa Aktarma', 'code': 'EXPORT', 'description': 'Veri dışa aktarma işlemleri için'},
        {'name': 'Sistem Bildirimi', 'code': 'SYSTEM_NOTIFICATION', 'description': 'Sistem bildirimleri için'},
        {'name': 'Rapor Gönderimi', 'code': 'REPORT', 'description': 'Rapor gönderimi için'},
        {'name': 'Uyarı', 'code': 'ALERT', 'description': 'Uyarı mesajları için'},
        {'name': 'Diğer', 'code': 'OTHER', 'description': 'Diğer işlemler için'},
    ]
    
    for type_data in default_types:
        UsageType.objects.get_or_create(
            code=type_data['code'],
            defaults={
                'name': type_data['name'],
                'description': type_data['description'],
                'is_active': True,
            }
        )


def migrate_path_definition_usage_types(apps, schema_editor):
    """Migrate PathDefinition usage_type CharField values to FK"""
    PathDefinition = apps.get_model('it_tools', 'PathDefinition')
    UsageType = apps.get_model('it_tools', 'UsageType')
    
    for path_def in PathDefinition.objects.all():
        old_value = path_def.usage_type_old  # Temporarily renamed CharField
        usage_type = UsageType.objects.filter(code=old_value).first()
        if usage_type:
            path_def.usage_type = usage_type
            path_def.save(update_fields=['usage_type'])


def migrate_email_template_usage_types(apps, schema_editor):
    """Migrate ADLogEmailTemplate usage_type CharField values to FK"""
    ADLogEmailTemplate = apps.get_model('it_tools', 'ADLogEmailTemplate')
    UsageType = apps.get_model('it_tools', 'UsageType')
    
    for template in ADLogEmailTemplate.objects.all():
        old_value = template.usage_type_old  # Temporarily renamed CharField
        usage_type = UsageType.objects.filter(code=old_value).first()
        if usage_type:
            template.usage_type = usage_type
            template.save(update_fields=['usage_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('it_tools', '0004_alter_adlogemailtemplate_options_and_more'),
    ]

    operations = [
        # Step 1: Create UsageType model
        migrations.CreateModel(
            name='UsageType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Örn: AD Log Analizi, Email Şablonları, Yedekleme', max_length=100, unique=True, verbose_name='İş Kolu Adı')),
                ('code', models.CharField(help_text='Programatik erişim için kod (örn: AD_LOG)', max_length=50, unique=True, verbose_name='Kod')),
                ('description', models.TextField(blank=True, help_text='Bu iş kolunun detaylı açıklaması', verbose_name='Açıklama')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Oluşturma Tarihi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')),
            ],
            options={
                'verbose_name': 'İş Kolu',
                'verbose_name_plural': 'İş Kolları',
                'ordering': ['name'],
            },
        ),
        
        # Step 2: Create default UsageType records
        migrations.RunPython(
            code=create_default_usage_types,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Step 3: Remove unique_together constraint from PathDefinition
        migrations.AlterUniqueTogether(
            name='pathdefinition',
            unique_together=set(),
        ),
        
        # Step 4: Rename old CharField in PathDefinition
        migrations.RenameField(
            model_name='pathdefinition',
            old_name='usage_type',
            new_name='usage_type_old',
        ),
        
        # Step 4: Add new FK field to PathDefinition (nullable temporarily)
        migrations.AddField(
            model_name='pathdefinition',
            name='usage_type',
            field=models.ForeignKey(
                help_text='Bu path hangi işlem için kullanılacak',
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='path_definitions',
                to='it_tools.usagetype',
                verbose_name='Kullanım Türü (İş Kolu)'
            ),
        ),
        
        # Step 5: Migrate existing PathDefinition data
        migrations.RunPython(
            code=migrate_path_definition_usage_types,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Step 6: Remove old CharField from PathDefinition
        migrations.RemoveField(
            model_name='pathdefinition',
            name='usage_type_old',
        ),
        
        # Step 7: Make FK non-nullable and add back unique_together
        migrations.AlterField(
            model_name='pathdefinition',
            name='usage_type',
            field=models.ForeignKey(
                help_text='Bu path hangi işlem için kullanılacak',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='path_definitions',
                to='it_tools.usagetype',
                verbose_name='Kullanım Türü (İş Kolu)'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='pathdefinition',
            unique_together={('usage_type', 'name')},
        ),
        
        # Step 8: Remove unique_together constraint from ADLogEmailTemplate
        migrations.AlterUniqueTogether(
            name='adlogemailtemplate',
            unique_together=set(),
        ),
        
        # Step 9: Rename old CharField in ADLogEmailTemplate
        migrations.RenameField(
            model_name='adlogemailtemplate',
            old_name='usage_type',
            new_name='usage_type_old',
        ),
        
        # Step 9: Add new FK field to ADLogEmailTemplate (nullable temporarily)
        migrations.AddField(
            model_name='adlogemailtemplate',
            name='usage_type',
            field=models.ForeignKey(
                help_text='Bu şablon hangi işlem için kullanılacak',
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='email_templates',
                to='it_tools.usagetype',
                verbose_name='Kullanım Türü (İş Kolu)'
            ),
        ),
        
        # Step 10: Migrate existing ADLogEmailTemplate data
        migrations.RunPython(
            code=migrate_email_template_usage_types,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Step 11: Remove old CharField from ADLogEmailTemplate
        migrations.RemoveField(
            model_name='adlogemailtemplate',
            name='usage_type_old',
        ),
        
        # Step 12: Make FK non-nullable and add back unique_together
        migrations.AlterField(
            model_name='adlogemailtemplate',
            name='usage_type',
            field=models.ForeignKey(
                help_text='Bu şablon hangi işlem için kullanılacak',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='email_templates',
                to='it_tools.usagetype',
                verbose_name='Kullanım Türü (İş Kolu)'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='adlogemailtemplate',
            unique_together={('usage_type', 'name')},
        ),
    ]
