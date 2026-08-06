import inspect

from django.db import models

from lens_monitoring.models import monitoring as lens_models

# Build registry from lens models
MODEL_REGISTRY = {
    name: obj
    for name, obj in inspect.getmembers(lens_models, inspect.isclass)
    if issubclass(obj, models.Model) and obj is not models.Model and name.lower().startswith('lens')
}

RULESET_CHOICES = [(class_name, class_name) for class_name in MODEL_REGISTRY.keys()]
