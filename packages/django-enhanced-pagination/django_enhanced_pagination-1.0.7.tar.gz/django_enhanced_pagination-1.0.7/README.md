# Django Enhanced Pagination

An enhanced version of django-pure-pagination with additional features and improvements.

## Features

- **Enhanced Pagination**: All the features of django-pure-pagination with additional enhancements
- **Bootstrap Support**: Built-in Bootstrap pagination templates
- **Customizable**: Easy to customize pagination display
- **Django Compatible**: Works with Django 2.2+ and Python 3.6+

## Installation

```bash
pip install django-enhanced-pagination
```

## Quick Start

1. Add `django_enhanced_pagination` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'django_enhanced_pagination',
]
```

2. In your views:

```python
from django_enhanced_pagination import Paginator, EmptyPage, PageNotAnInteger

def my_view(request):
    objects = MyModel.objects.all()
    paginator = Paginator(objects, 25)  # Show 25 objects per page
    
    page = request.GET.get('page')
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
    
    return render(request, 'my_template.html', {'objects': objects})
```

3. In your templates:

```html
{% load i18n %}
<div class="pagination-wrapper">
    {% include "pure_pagination/pagination.html" %}
</div>
```

## Configuration

You can customize pagination settings in your Django settings:

```python
PAGINATION_SETTINGS = {
    'PAGE_RANGE_DISPLAYED': 10,
    'MARGIN_PAGES_DISPLAYED': 2,
    'SHOW_FIRST_PAGE_WHEN_INVALID': True,
}
```

## License

This project is licensed under the BSD License - see the LICENSE file for details.

## Acknowledgments

- Based on django-pure-pagination by James Pacileo
- Enhanced with additional features and improvements