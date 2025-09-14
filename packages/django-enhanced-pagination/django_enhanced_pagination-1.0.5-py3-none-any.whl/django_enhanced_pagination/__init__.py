# Django Enhanced Pagination
# An enhanced version of django-pure-pagination with additional features

__version__ = '1.0.5'
__author__ = 'Your Name'
__email__ = 'your.email@example.com'

# Import main classes for easy access
from .pagination.paginator import Paginator, EmptyPage, InvalidPage, PageNotAnInteger
from .pagination.mixins import PaginationMixin

__all__ = ['Paginator', 'EmptyPage', 'InvalidPage', 'PageNotAnInteger', 'PaginationMixin']

default_app_config = 'django_enhanced_pagination.apps.DjangoEnhancedPaginationConfig'