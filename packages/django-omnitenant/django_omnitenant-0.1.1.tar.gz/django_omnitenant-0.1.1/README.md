# django-omnitenant

django-omnitenant is a Django app that enables multi-tenancy with DB-level isolation and schema-level isolation.

Detailed documentation is in the "docs" directory.

## Quick start

1. Add "django_omnitenant" to your `INSTALLED_APPS` setting like this:

```python
INSTALLED_APPS = [
    ...,
    "django_omnitenant",
]

**Note:** Add your apps in CUSTOM_APPS
**Note:** Place django_omnitenant before django.contrib.auth if you want to use overridden commands like createsuperuser

