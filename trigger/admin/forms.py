from django import forms
from trigger.models.trigger import BacktestTrigger, TaskTrigger, TaskTrigger2
import decimal

def convert_decimal(input_p):
    try:
        return decimal.Decimal(input_p)
    except:
        return str(input_p)
    
def convert_int(input_p):
    try:
        return int(input_p)
    except:
        return str(input_p)

def transform_parameters(parameters):
    lines = parameters.split('\n')
    if len(lines) != 2: # Input error.
        parameter_dict = {}
    else :
        # Handle multi-line input.
        parameter_names = [name.strip() for name in lines[0].split(',')]
        parameter_values = [value.strip() for value in lines[1].split(',')]
        parameter_dict = dict(zip(parameter_names, parameter_values))
    return parameter_dict

# Base Form overide function
def create_dynamic_form(form_data, obj_parameters):
    # Parameter Dict eg. {'p1':'5', 'p2':'10'}
    parameter_dict = transform_parameters(obj_parameters)
    # Widgets (Dictionary of {key:object} pair)
    fields = {} # {'p1':forms.IntegerField(**field_kwargs), .....}
    # Fields
    keys = ('ruleset_name','start_date','end_date','is_trigger',)
    # Update fields using Ruleset's form data     {'ruleset_name':'LENs_Wash_Trade_APAC','celery_name':'LENs_Wash_Trade_APAC','task_name':'libs.lens.output_tasks.lens_wash_trade_apac.start',
    # 'fields':[{'param_name':'p1', 'label':'Trade frequency threshold lv1 (p1):', 'type':'IntegerField', 'help_text':'time(s)', 'default':p1_lv1_ratio}]}
    fields['ruleset_name']=forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), required=False, help_text=form_data['ruleset_name'])
    
    for field in form_data['fields']:
        field_type = field['type']
        field_kwargs = {
            'label':field['label'],
            'help_text':field['help_text'],
            'required':True,
            'error_messages':{'required': 'Please enter a valid value.'}
        }

        # Default value type
        if field_type == 'IntegerField':
            saved_parameter = convert_int(parameter_dict.get(field['param_name'],field['default']))
            field_kwargs['initial'] = saved_parameter
        else:
            saved_parameter = convert_decimal(parameter_dict.get(field['param_name'],field['default']))
            field_kwargs['initial'] = saved_parameter
        
        # Field case
        if field_type == 'IntegerField':
            fields[field['param_name']]=forms.IntegerField(**field_kwargs)
        elif field_type == 'DecimalField':
            fields[field['param_name']]=forms.DecimalField(**field_kwargs)
        elif field_type == 'CharField':
            fields[field['param_name']]=forms.CharField(**field_kwargs)
        keys += (field['param_name'],)
    keys += ('parameters','tag','comments',)
    fields['parameters']=forms.CharField(widget=forms.HiddenInput(), required=False)

    # Meta class
    meta_class=type('Meta',(),{
            'model':BacktestTrigger,
            'fields':keys,
            'widgets':{'start_date':DateInput(),'end_date':DateInput(),},
            'readonly_fields':('event_log', 'ruleset_name',),
            'exclude':( 'created_at',),
        })
    
    dynamic_form_structure={'Meta':meta_class}
    dynamic_form_structure.update(fields)

    DynamicForm=type('BacktestDynamicForm', (BacktestBaseForm, ), dynamic_form_structure)
    return DynamicForm

# Date widgets
class DateInput(forms.DateInput):
    input_type='date'
    
# Base form use to generate the dynamic form 
class BacktestBaseForm(forms.ModelForm):
    class Meta:
        model=BacktestTrigger
        fields=(
            'ruleset_name',
            'start_date',
            'end_date',
            'is_trigger',
            'parameters',
            'tag',
            'comments',
        )

    def clean(self):
        cleaned_data=super().clean()
        parameters_dict={}
        for field_name, field_value in cleaned_data.items():
            if len(field_name)==2 and field_name.startswith('p') and field_value!=None:
                parameters_dict[field_name]=field_value

        if parameters_dict:
            parameter_names=','.join(parameters_dict.keys())
            parameter_values=','.join(str(val) for val in parameters_dict.values())
            cleaned_data['parameters']=f"{parameter_names}\n{parameter_values}"
        return cleaned_data   

# Blank form = User first create the trigger.
class BacktestBlankForm(forms.ModelForm):
    class Meta:
        model=BacktestTrigger
        fields=[
            'ruleset_name',
        ]

    def clean(self):
        cleaned_data=super().clean()
        return cleaned_data

