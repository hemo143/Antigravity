# 🎉 Apex Events

نظام متكامل لإدارة الأحداث مبني بـ Django + Bootstrap 5

---

## 🚀 تشغيل المشروع (خطوة بخطوة)

### المتطلبات
- Python 3.10+
- pip

---

### الخطوة 1: إنشاء البيئة الافتراضية
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### الخطوة 2: تثبيت المكتبات
```bash
pip install -r requirements.txt
```

### الخطوة 3: إعداد قاعدة البيانات
```bash
python manage.py migrate
```

### الخطوة 4: ملء البيانات التجريبية
```bash
python manage.py seed_data
```

### الخطوة 5: تشغيل السيرفر
```bash
python manage.py runserver
```

افتح المتصفح على: **http://127.0.0.1:8000**

---

## 🔑 بيانات الدخول (بعد seed_data)

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@eventpro.com | admin123 |
| Organizer | organizer@eventpro.com | org123 |
| Attendee | user@eventpro.com | user123 |

---

## 🌐 الروابط المهمة

| الصفحة | الرابط |
|--------|--------|
| Dashboard | http://127.0.0.1:8000/dashboard/ |
| Events | http://127.0.0.1:8000/events/ |
| Login | http://127.0.0.1:8000/accounts/login/ |
| Register | http://127.0.0.1:8000/accounts/register/ |
| Admin Panel | http://127.0.0.1:8000/admin/ |
| REST API | http://127.0.0.1:8000/api/v1/ |

---

## 🔌 REST API Endpoints

```
GET    /api/v1/events/           → قائمة الأحداث
POST   /api/v1/events/           → إنشاء حدث
GET    /api/v1/events/<slug>/    → تفاصيل حدث
PUT    /api/v1/events/<slug>/    → تعديل حدث
DELETE /api/v1/events/<slug>/    → حذف حدث

GET    /api/v1/categories/       → قائمة الفئات
POST   /api/v1/categories/       → إنشاء فئة

GET    /api/v1/bookings/         → حجوزاتي
POST   /api/v1/bookings/         → حجز جديد

GET    /api/v1/stats/            → إحصائيات
```

### فلترة وبحث في الـ API
```
/api/v1/events/?search=python
/api/v1/events/?category=1
/api/v1/events/?is_free=true
/api/v1/events/?city=cairo
/api/v1/events/?upcoming=true
/api/v1/events/?ordering=-start_date
```

---

## 🗄️ التحويل إلى PostgreSQL

### الخطوة 1: تثبيت psycopg2
```bash
pip install psycopg2-binary
```

### الخطوة 2: تعديل .env
```env
DATABASE_URL=postgres://username:password@localhost:5432/event_db
```

### الخطوة 3: تعديل settings.py
في `config/settings.py`، uncomment هذه الأسطر:
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}
```

### الخطوة 4: Migrate
```bash
python manage.py migrate
```

---

## ☁️ النشر على Render.com (مجاني)

### الخطوة 1: إنشاء ملف `render.yaml`
```yaml
services:
  - type: web
    name: event-management-system
    env: python
    buildCommand: "pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate"
    startCommand: "gunicorn config.wsgi:application"
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: false
      - key: ALLOWED_HOSTS
        value: your-app.onrender.com
```

### الخطوة 2: ربط GitHub وRender
1. ارفع الكود على GitHub
2. اذهب إلى render.com وأنشئ Web Service جديد
3. اربطه بـ Repository على GitHub
4. أضف متغيرات البيئة

---

## 🏗️ هيكل المشروع

```
event-management-system/
├── config/                 # إعدادات Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/          # المستخدمين والمصادقة
│   │   ├── models.py      # Custom User Model
│   │   ├── views.py       # Login/Register/Profile
│   │   ├── forms.py
│   │   └── urls.py
│   ├── events/            # الأحداث والحجوزات
│   │   ├── models.py      # Event/Category/Booking
│   │   ├── views.py       # CRUD + Booking
│   │   ├── forms.py
│   │   ├── serializers.py # REST API
│   │   ├── api_views.py   # API Views
│   │   ├── api_urls.py
│   │   ├── signals.py     # Email Notifications
│   │   └── urls.py
│   └── dashboard/         # لوحة التحكم
│       ├── views.py       # Stats & Charts
│       └── urls.py
├── templates/             # HTML Templates
├── static/                # CSS & JS
├── media/                 # Uploaded Files
├── requirements.txt
├── manage.py
└── .env
```

---

## ✅ Features المنفذة

- [x] Custom User Model (email login)
- [x] Register / Login / Logout
- [x] Dashboard مع إحصائيات حية
- [x] رسم بياني للنشاط (Chart.js)
- [x] CRUD كامل للأحداث
- [x] CRUD كامل للفئات
- [x] نظام حجز المقاعد
- [x] إلغاء الحجز
- [x] Email Notifications (Signals)
- [x] بحث وفلترة الأحداث
- [x] Pagination
- [x] REST API (DRF)
- [x] API Authentication (Token)
- [x] Admin Panel مخصص
- [x] Responsive Design
- [x] Static & Media Files
- [x] Seed Data Command
- [x] Deployment Ready (Render/VPS)
