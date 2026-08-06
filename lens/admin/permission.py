# admin.py
from django import forms
from django.apps import apps
from django.contrib import admin, messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelForm
from django.shortcuts import redirect


class PermissionForm(ModelForm):
    """Custom form to make permission creation more user-friendly"""
    
    class Meta:
        model = Permission
        fields = ['name', 'codename', 'content_type']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Can view MyModel'}),
            'codename': forms.TextInput(attrs={'placeholder': 'e.g., view_mymodel'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for codename field
        self.fields['codename'].help_text = (
            "Use format: action_modelname (e.g., view_mymodel, add_mymodel, "
            "change_mymodel, delete_mymodel, or custom_mymodel)"
        )
    
    def clean_codename(self):
        """Validate codename follows Django conventions"""
        codename = self.cleaned_data['codename']
        
        # Check basic format requirements
        if not codename:
            raise forms.ValidationError("Codename is required.")
        
        # Check for valid characters (lowercase letters, numbers, underscores)
        if not codename.replace('_', '').replace('-', '').isalnum():
            raise forms.ValidationError(
                "Codename can only contain lowercase letters, numbers, underscores, and hyphens."
            )
        
        # Check if it's lowercase
        if codename != codename.lower():
            raise forms.ValidationError("Codename must be lowercase.")
        
        # Check length (Django's auth_permission.codename field is max 100 chars)
        if len(codename) > 100:
            raise forms.ValidationError("Codename cannot exceed 100 characters.")
        
        # Check for Django's standard permission format (action_modelname)
        if '_' in codename:
            parts = codename.split('_')
            if len(parts) < 2:
                raise forms.ValidationError(
                    "Codename should follow Django convention: action_modelname "
                    "(e.g., view_mymodel, add_mymodel, change_mymodel, delete_mymodel)"
                )
            
            action = parts[0]
            model_name = '_'.join(parts[1:])
            
            # Validate action part
            standard_actions = ['add', 'change', 'delete', 'view']
            if action not in standard_actions and not action.isalpha():
                raise forms.ValidationError(
                    f"Action '{action}' should be descriptive. "
                    f"Standard actions are: {', '.join(standard_actions)}"
                )
            
            # Validate model name part
            if not model_name.replace('_', '').isalnum():
                raise forms.ValidationError(
                    f"Model name '{model_name}' should only contain letters, numbers, and underscores."
                )
        
        # Check for duplicate permissions
        content_type = self.cleaned_data.get('content_type')
        if content_type:
            existing_permission = Permission.objects.filter(
                codename=codename,
                content_type=content_type
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_permission.exists():
                raise forms.ValidationError(
                    f"Permission with codename '{codename}' already exists for {content_type}."
                )
        
        return codename


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    form = PermissionForm
    list_display = ['name', 'codename', 'content_type']
    list_filter = ['content_type']
    search_fields = ['name', 'codename']
    ordering = ['content_type', 'codename']
    actions = ['create_missing_contenttypes']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'codename', 'content_type'),
            'description': 'Create custom permissions for models. Use standard Django naming conventions.'
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('content_type')
    
    
    @admin.action(description='Create missing ContentType objects for all models')
    def create_missing_contenttypes(self, request, queryset):
        """Admin action to create ContentType objects for all models"""
 
        created_count = 0
        updated_count = 0
        apps_processed = []
        
        try:
            for app_config in apps.get_app_configs():
                app_models = []
                
                for model in app_config.get_models():
                    # Skip abstract models
                    if model._meta.abstract:
                        continue
                    
                    # This will create the ContentType if it doesn't exist
                    ct_before_count = ContentType.objects.filter(
                        app_label=model._meta.app_label,
                        model=model._meta.model_name
                    ).count()
                    
                    # Use get_for_model to create ContentType if missing
                    ct = ContentType.objects.get_for_model(model)
                    
                    ct_after_count = ContentType.objects.filter(
                        app_label=model._meta.app_label,
                        model=model._meta.model_name
                    ).count()
                    
                    if ct_after_count > ct_before_count:
                        created_count += 1
                        app_models.append(model.__name__)
                    else:
                        # Update name if it changed
                        if ct.name != model._meta.verbose_name:
                            ct.name = model._meta.verbose_name
                            ct.save()
                            updated_count += 1
                            app_models.append(f"{model.__name__} (updated)")
                
                if app_models:
                    apps_processed.append(f"{app_config.label}: {', '.join(app_models)}")
            
            # Create success message
            if created_count > 0 or updated_count > 0:
                message_parts = []
                if created_count > 0:
                    message_parts.append(f"Created {created_count} ContentType(s)")
                if updated_count > 0:
                    message_parts.append(f"Updated {updated_count} ContentType(s)")
                
                main_message = " and ".join(message_parts)
                
                if apps_processed:
                    detail_message = "Apps processed: " + "; ".join(apps_processed)
                    full_message = f"{main_message}. {detail_message}"
                else:
                    full_message = main_message
                
                messages.success(request, full_message)
            else:
                messages.info(request, "All ContentType objects already exist and are up to date.")
                
        except Exception as e:
            messages.error(request, f"Error creating ContentTypes: {str(e)}")


    def changelist_view(self, request, extra_context=None):
        """Handle action form submission and bypass selection check"""
        # Check if this is an action request for our specific action
        if request.method == 'POST' and request.POST.get('action') == 'create_missing_contenttypes':
            # Call our action directly
            self.create_missing_contenttypes(request, None)
            # Redirect back to the changelist
            return redirect(request.get_full_path().split('?')[0])
        
        return super().changelist_view(request, extra_context=extra_context)


    def has_add_permission(self, request):
        return request.user.is_superuser
