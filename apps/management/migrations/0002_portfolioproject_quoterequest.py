from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortfolioProject',
            fields=[
                ('id',             models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_en',       models.CharField(max_length=200, verbose_name='Title (English)')),
                ('title_ar',       models.CharField(max_length=200, verbose_name='Title (Arabic)')),
                ('description_en', models.CharField(blank=True, max_length=300, verbose_name='Description (English)')),
                ('description_ar', models.CharField(blank=True, max_length=300, verbose_name='Description (Arabic)')),
                ('event_type',     models.CharField(
                    choices=[('conference', 'Conference / مؤتمر'), ('exhibition', 'Exhibition / معرض'), ('corporate', 'Corporate / شركات')],
                    default='conference', max_length=20, verbose_name='Event Type'
                )),
                ('image',       models.ImageField(upload_to='portfolio/', verbose_name='Event Photo')),
                ('is_featured', models.BooleanField(default=True, verbose_name='Show on website')),
                ('order',       models.PositiveIntegerField(default=0, verbose_name='Display order')),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name':        'Portfolio Project',
                'verbose_name_plural': 'Portfolio Projects',
                'ordering':            ['order', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='QuoteRequest',
            fields=[
                ('id',           models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',         models.CharField(max_length=200, verbose_name='Name')),
                ('company',      models.CharField(max_length=200, verbose_name='Company')),
                ('email',        models.EmailField(verbose_name='Email')),
                ('phone',        models.CharField(max_length=30, verbose_name='Phone')),
                ('event_type',   models.CharField(max_length=50, verbose_name='Event Type')),
                ('attendees',    models.CharField(blank=True, max_length=50, verbose_name='Expected Attendees')),
                ('event_date',   models.DateField(blank=True, null=True, verbose_name='Event Date')),
                ('services',     models.CharField(blank=True, max_length=500, verbose_name='Services Required')),
                ('notes',        models.TextField(blank=True, verbose_name='Additional Notes')),
                ('is_contacted', models.BooleanField(default=False, verbose_name='Contacted?')),
                ('created_at',   models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name':        'Quote Request',
                'verbose_name_plural': 'Quote Requests',
                'ordering':            ['-created_at'],
            },
        ),
    ]
