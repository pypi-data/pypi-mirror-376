# Django Headless

[![PyPI version](https://badge.fury.io/py/django-headless.svg)](https://badge.fury.io/py/django-headless)
[![Python versions](https://img.shields.io/pypi/pyversions/django-headless.svg)](https://pypi.org/project/django-headless/)
[![Django versions](https://img.shields.io/badge/django-5.0%2B-blue.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

With Django Headless you quickly create a REST API for your models, making it easy to turn Django into a powerful headless CMS.

## ✨ Features

- **🎯 Easy configuration**: Add `@register` decorator to any model and get instant REST endpoints
- **🤝 Plays nice**: Seamlessly integrates with existing Django applications
- **💈 Supports singletons**: Special handling for singleton models (settings, configurations, etc.)
- **🔍 Flexible filtering**: Optional filtering backend based on Django ORM lookups
- **🛡️ Secure**: Inherits Django's security features and permissions system

## 🚀 Quick Start

### Installation

☝️ Django Headless depends on Django and Django Rest Framework.

```bash
pip install django-headless
```

### Add to Django Settings

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'headless',  # Add this
    # ... your apps
]

REST_FRAMEWORK = {
    # Optional: add the lookup filter backend
    "DEFAULT_FILTER_BACKENDS": [
        "headless.rest.filters.LookupFilter",
    #...
    # Optional: add the secret key authentication class
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "headless.rest.authentication.SecretKeyAuthentication",
    #... other DRF config
}
```

### Create Your First Headless Model

```python
# models.py
from django.db import models
from headless import register

@register()
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
```

### Add URLs

```python
# urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('headless.urls')),
]
```

That's it! 🎉 Your model is now available via REST API at `/api/blog-post/`

## 📖 Usage Examples

### Basic Model Registration

```python
from headless import register

@register()
class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
```

**Generated endpoints:**
- `GET /api/article/` - List all articles
- `POST /api/article/` - Create new article
- `GET /api/article/{id}/` - Retrieve specific article
- `PUT /api/article/{id}/` - Update article
- `PATCH /api/article/{id}/` - Partially update article
- `DELETE /api/article/{id}/` - Delete article

### Singleton Models

Perfect for site settings, configurations, or any model that should have only one instance:

```python
@register(singleton=True)
class SiteConfiguration(models.Model):
    site_name = models.CharField(max_length=100)
    maintenance_mode = models.BooleanField(default=False)
    contact_email = models.EmailField()
    
    class Meta:
        verbose_name = "Site Configuration"
```

**Generated endpoints:**
- `GET /api/site-configuration/` - Get configuration
- `PUT /api/site-configuration/` - Update configuration
- `PATCH /api/site-configuration/` - Partial update

### Advanced Filtering

Django Headless supports Django ORM lookups for powerful filtering.
Add the LookupFilter backend to your default filter backends:

```python
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "headless.rest.filters.LookupFilter",
    #... other DRF config
}
```

**Filter examples:**
```bash
# Basic filtering
GET /api/blogpost/?published=true

# Field lookups
GET /api/blogpost/?title__icontains=django
GET /api/blogpost/?created_at__gte=2023-01-01
GET /api/blogpost/?author__username=john

# Multiple filters
GET /api/blogpost/?published=true&created_at__year=2023
```

Values are automatically cast based on the field type. Booleans can be represented
as `true`, `1` or `on` (and `false`, `0` or `off`). Multi-value lookups can be comma-separated (e.g. `id__in=1,2,3`).


## 🎛️ Configuration Options

The `@register` decorator accepts the following configuration options:

| Option | Type | Default | Description                                                        |
|--------|------|---------|--------------------------------------------------------------------|
| `singleton` | `bool` | `False` | Creates singleton endpoints (no create, list and delete endpoints) |



### Global Settings

```python
# settings.py
HEADLESS =  {
    "AUTH_SECRET_KEY": None,
    "AUTH_SECRET_KEY_HEADER": "X-Secret-Key",
    "FILTER_EXCLUSION_SYMBOL": "~",
    "NON_FILTER_FIELDS": [
        "search",
        "limit",
        "page",
        "fields",
        "exclude",
        "expand",
    ],

}
```

## 🛠️ Requirements

- Python 3.10+
- Django 5.0+
- Django REST Framework 3.16+

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite (`python manage.py test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/StructuralRealist/django-headless.git
cd django-headless

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python manage.py test

# Run example project
cd example_project
python manage.py migrate
python manage.py runserver
```

## 📚 Documentation

For detailed documentation, visit [djangoheadless.org](https://djangoheadless.org)

## 🐛 Issues & Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/StructuralRealist/django-headless/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/StructuralRealist/django-headless/discussions)
- 📧 **Email**: leon@devtastic.io

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the shoulders of [Django](https://www.djangoproject.com/) and [Django REST Framework](https://www.django-rest-framework.org/)
- Inspired by the headless CMS and Jamstack movement
- Thanks to all contributors and the Django community

## 🔗 Links

- [PyPI Package](https://pypi.org/project/django-headless/)
- [Documentation](https:/djangoheadless.org)
- [GitHub Repository](https://github.com/StructuralRealist/django-headless)
- [Changelog](CHANGELOG.md)

---

Made in Europe 🇪🇺 with 💚 for Django