# Django FSM Dynamic

Dynamic workflow extensions for [django-fsm-2](https://github.com/django-commons/django-fsm-2) that allow optional Django apps to modify FSM state machines without creating database migrations.

[![PyPI version](https://badge.fury.io/py/django-fsm-dynamic.svg)](https://badge.fury.io/py/django-fsm-dynamic)
[![Python Support](https://img.shields.io/pypi/pyversions/django-fsm-dynamic.svg)](https://pypi.org/project/django-fsm-dynamic/)
[![Django Support](https://img.shields.io/badge/django-4.2%2B-blue)](https://docs.djangoproject.com/en/stable/releases/)

## Features

- **Dynamic State Enums**: Extend state enums at runtime without migrations
- **Callable Choices**: Prevent Django from generating migrations when choices change
- **Transition Builder**: Programmatically create FSM transitions
- **Workflow Extensions**: Structured app-based workflow modifications
- **Migration-Free**: All extensions work without requiring database migrations

## Installation

```bash
pip install django-fsm-dynamic
```

**Requirements:**
- Python 3.8+
- Django 4.2+
- django-fsm-2 4.0+

## Quick Start

### 1. Create a Dynamic State Enum

```python
from django_fsm_dynamic import DynamicStateEnum
from django_fsm import FSMIntegerField
from django.db import models

class BlogPostStateEnum(DynamicStateEnum):
    NEW = 10
    PUBLISHED = 20
    HIDDEN = 30

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    state = FSMIntegerField(
        default=BlogPostStateEnum.NEW,
        choices=BlogPostStateEnum.get_choices  # Prevents migrations!
    )
```

### 2. Extend from Another App

```python
# In your review app's apps.py
from django.apps import AppConfig
from django_fsm_dynamic import WorkflowExtension, TransitionBuilder

class ReviewWorkflowExtension(WorkflowExtension):
    target_model = 'blog.BlogPost'
    target_enum = 'blog.models.BlogPostStateEnum'
    
    def extend_states(self, enum_class):
        enum_class.add_state('IN_REVIEW', 15)
        enum_class.add_state('APPROVED', 17)
    
    def extend_transitions(self, model_class, enum_class):
        builder = TransitionBuilder(model_class)
        builder.add_transition('send_to_review', enum_class.NEW, enum_class.IN_REVIEW)
        builder.add_transition('approve', enum_class.IN_REVIEW, enum_class.APPROVED)
        builder.build_and_attach()

class ReviewConfig(AppConfig):
    name = 'review'
    
    def ready(self):
        ReviewWorkflowExtension(self).apply()
```

### 3. Use the Extended Workflow

```python
# Create a blog post
post = BlogPost.objects.create(title="My Post", state=BlogPostStateEnum.NEW)

# Use dynamically added transitions
post.send_to_review()  # NEW -> IN_REVIEW
post.approve()         # IN_REVIEW -> APPROVED
```

## Core Components

### DynamicStateEnum

Base class for extensible state enums:

```python
from django_fsm_dynamic import DynamicStateEnum

class MyStateEnum(DynamicStateEnum):
    NEW = 10
    PUBLISHED = 20

# Other apps can extend:
MyStateEnum.add_state('IN_REVIEW', 15)

# Get all choices including dynamic ones:
choices = MyStateEnum.get_choices()  # [(10, 'New'), (15, 'In Review'), (20, 'Published')]
```

### Dynamic Choices

Use the `get_choices` method directly to prevent Django migrations:

```python
class MyModel(models.Model):
    state = FSMIntegerField(
        default=MyStateEnum.NEW,
        choices=MyStateEnum.get_choices  # No migrations when enum changes!
    )
```

### TransitionBuilder

Programmatically create FSM transitions:

```python
from django_fsm_dynamic import TransitionBuilder

builder = TransitionBuilder(MyModel)
builder.add_transition(
    'approve', 
    source=MyStateEnum.IN_REVIEW,
    target=MyStateEnum.APPROVED,
    conditions=[lambda instance: instance.is_valid()],
    permission='myapp.can_approve'
).build_and_attach()
```

### WorkflowExtension

Structured approach to extending workflows:

```python
from django_fsm_dynamic import WorkflowExtension

class MyExtension(WorkflowExtension):
    target_model = 'app.Model'
    target_enum = 'app.models.StateEnum'
    
    def extend_states(self, enum_class):
        enum_class.add_state('NEW_STATE', 99)
    
    def extend_transitions(self, model_class, enum_class):
        # Add new transitions
        pass
    
    def modify_existing_transitions(self, model_class, enum_class):
        # Modify existing transitions
        pass
```

## Migration from django-fsm-2

If you were using the dynamic utilities from django-fsm-2, simply update your imports:

```python
# Old (django-fsm-2 < 4.1.0)
from django_fsm.dynamic import DynamicStateEnum, TransitionBuilder

# New (with django-fsm-dynamic)
from django_fsm_dynamic import DynamicStateEnum, TransitionBuilder
```

**Note**: If you were using `make_callable_choices` from django-fsm-2, simply use `MyStateEnum.get_choices` directly instead - Django 5.0+ accepts callables for the choices parameter.

All functionality remains the same, just in a separate package.

## Documentation

- [Complete Documentation](docs/dynamic_workflows.md)
- [API Reference](docs/api.md)
- [Examples](examples/)

## Why Separate Package?

Dynamic workflows are a powerful but specialized feature. By extracting them into a separate package:

1. **Focused Development**: Each package has a clear, focused scope
2. **Optional Dependency**: Only install if you need dynamic workflows  
3. **Independent Versioning**: Features can evolve independently
4. **Cleaner Core**: django-fsm-2 stays focused on core FSM functionality

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.