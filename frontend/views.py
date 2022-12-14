from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from django.apps import apps
from datetime import datetime
from inspect import isabstract
from django.contrib import admin
from django.db import transaction
from django.shortcuts import render
from django.template import RequestContext
from django.urls import reverse_lazy
from typing import Iterable, Sequence, Type
from crispy_forms.helper import FormHelper
from django.db.models import QuerySet, Model
from crispy_forms.utils import TEMPLATE_PACK
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.contrib.admin import ModelAdmin, BooleanFieldListFilter, TabularInline
from django.forms import ModelForm, Form, ChoiceField, inlineformset_factory, MediaDefiningClass
from django.views.generic import DeleteView, CreateView, ListView, UpdateView
from crispy_forms.layout import Layout, Div, Fieldset, LayoutObject, HTML, ButtonHolder, Submit


class Formset(LayoutObject):
    template = 'frontend/formset.html'

    def __init__(self, formset_name_in_context, template=None):
        self.formset_name_in_context = formset_name_in_context
        self.fields = []
        if template:
            self.template = template

    def render(self, form, form_style, context: RequestContext, template_pack=TEMPLATE_PACK):
        formset = context[self.formset_name_in_context]
        return render_to_string(self.template, {'formset': formset})


# Create your views here.
class GenericAppModelList(ListView):  # Creates a list view consisting of models, that are registered in the admin panel, for a specified app
    template_name = 'frontend/genericappmodellist.html'
    current_app: str = None  # Remember to change this to your preferred app's app_label/name
    exclude = []  # Models which you wish to exclude.

    def get_context_data(self, **kwargs):
        modellist = sorted([i.__name__.lower() for i in apps.get_app_config(self.current_app).get_models() if i in admin.site._registry])
        verboselist = (apps.get_model(app_label=self.current_app, model_name=i)._meta.verbose_name_plural for i in modellist)

        return super().get_context_data(**kwargs) | {
            'appname': self.current_app,
            'zipped_list': zip(modellist, verboselist),
            'excluded': self.exclude,  # List of excluded models. Will be checked against both modellist and verboselist.
        }

    def get_queryset(self):
        pass


class GenericForm(ModelForm):
    model: Model = None

    def __init__(self, *args, **kwargs):
        super(GenericForm, self).__init__(*args, **kwargs)
        model_admin = admin.site._registry[self.model]
        for i in (model_admin.readonly_fields or ()):
            if i in self.model._meta._property_names:
                continue
            self.fields[i].widget.attrs['readonly'] = True
        for i in (model_admin.exclude or ()):
            try:
                del self.fields[i]
            except KeyError:
                pass
        self.helper = FormHelper()
        self.helper.form_tag = True
        # self.helper.form_class = 'form-horizontal'
        # self.helper.label_class = 'col-md-3 create-label'
        # self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            Div(
                Fieldset(model_admin.model._meta.verbose_name or model_admin.model._meta.object_name,
                         *self.fields),

                Fieldset('Inlines',
                         Formset('inline')),
                HTML("<br>"),
                ButtonHolder(Submit('submit', 'save')),
            )
        )


class _UseAdminValueMeta(type):
    """ Make default attributes appear as None, so they are ignored or overriden by Django """

    def __bool__(self):
        return False


class _UseAdminValue(metaclass=_UseAdminValueMeta):
    """ Sentinel class used by generic views when an attributes should be derived from their respective ModelAdmin """


class AdminDependantMixIn:
    """ Useful for views that would like access to the/a ModelAdmin for their model (whether real or fake). """

    adminmodel: ModelAdmin | None = None
    uses_real_admin: bool = None  # Is the current model registered  # TODO Kevin: probably not a good solution.

    model: Model = None  # Should be implemented by subclass

    # Fake ModelAdmins are put here for reuse, so we don't create too many classes.
    _fake_modeladmin_cache: dict[Type[Model], Type[ModelAdmin]] = {}

    @classmethod
    def _get_admin_model(cls) -> ModelAdmin:
        assert cls.model is not None, '_get_admin_model() should not be called before a model has been defined.'
        try:
            cls.adminmodel = admin.site._registry[cls.model]
            cls.uses_real_admin = True
        except KeyError:
            if cls.model not in AdminDependantMixIn._fake_modeladmin_cache:
                AdminDependantMixIn._fake_modeladmin_cache[cls.model] = type(f"{cls.model._meta.object_name}Admin", (ModelAdmin,), {'model': cls.model})
            # Make an instance of the ModelAdmin for every class.
            cls.adminmodel = AdminDependantMixIn._fake_modeladmin_cache[cls.model](cls.model, admin.site)
            cls.uses_real_admin = False

        return cls.adminmodel

    def __init_subclass__(cls) -> None:
        # We need to be a bit careful about when we see/create the subclasses, as admin.py must come first
        super().__init_subclass__()

        # Not strictly necessary, maybe the user wants to use a fake admin.
        # TODO Kevin: Uncomment when isabstract() starts returning True,
        #   for ABC subclasses that dont define any @abstractmethod.
        #   We will currently get an obscure error if no subclass defines the model.
        #assert isabstract(cls) or cls.model is not None, f"{cls.__qualname__} should implement a 'model' attribute"

        if cls.model is not None:  # Wait for a subclass that defines a model
            cls._get_admin_model()


class GenericListView(AdminDependantMixIn, ABC, ListView):  # Using this generic ListView; we only need to indicate which model we would like a list view for, and the rest will be handled automatically
    template_name = "frontend/generic_listview.html"
    context_object_name = "objects"
    paginate_by = 50  # Amount of objects displayed per page

    list_per_page: int = _UseAdminValue  # Alternative to paginate_by, will be used when overriden in subclass
    list_display: list[str] = _UseAdminValue  # Will be extended with values from ModelAdmin.list_display if use_list_display is True
    list_filter: list[str] = _UseAdminValue  # Determines which fields a filter should be generated for.
    list_display_links: list[str] = _UseAdminValue  # Determines which fields should link to the current model (NOTE: Same as admin; this will not link to the model matching the field name)  # TODO Kevin View: Perhaps make this a possibility?
    exclude: list[str] = _UseAdminValue  # Determines if certain fields should be excluded from the ListView. Useful if they have been grabbed from the ModelAdmin.
    ordering: list[str] | str = _UseAdminValue  # Set to name of field to order by, uses the ModelAdmin value by default.

    # Set to False, to disable all attributes from deriving values from the ModelAdmin.
    # May require certain variables to be set manually if False
    # TODO Kevin: Currently requires all variables be set manually, so what's the point?
    #   We should probably handle default values when possible.
    use_admin_values = True

    # use_admin_list_display = True  # Determines whether to exclude fields not included in the ModelAdmin list_display
    # TODO Kevin View: Perhaps add an alias feature for list_display, or find a better way to change something like 'Indented Title' for asset to 'Title'

    def get_ordering(self) -> Sequence[str] | None:
        if self.ordering is _UseAdminValue and self.use_admin_values:
            return self.adminmodel.get_ordering(self.request)
        elif self.ordering or self.model._meta.ordering:
            return self.ordering or self.model._meta.ordering
        elif 'MPTTModel' in [cls.__name__ for cls in self.model.__bases__]:
            return None
        else:  # Default ordering when nothing has been overridden.
            return ['-pk']

    def get_queryset(self) -> QuerySet:
        adminmodel = self.adminmodel

        if len(self.request.GET.get('o', '').split('|')) > 1:
            order = self.request.GET.get('o').split('|')
        else:
            order = (self.request.GET.get('o'),) or self.get_ordering()

        try:
            filter_terms = dict([(i, (None if dict(self.request.GET)[i][0] == 'None' else dict(self.request.GET)[i][0])) for i in dict(self.request.GET) if i not in ['o', self.page_kwarg, 'q']])

            if order and order[0] not in ['None', None]:
                return adminmodel.get_search_results(self.request, adminmodel.get_queryset(self.request).filter(**filter_terms).order_by(*order), self.request.GET.get('q', ''))[0]
            else:
                return adminmodel.get_search_results(self.request, adminmodel.get_queryset(self.request).filter(**filter_terms), self.request.GET.get('q', ''))[0]
        except TypeError:
            return adminmodel.get_search_results(self.request, adminmodel.get_queryset(self.request).all().order_by(*order), self.request.GET.get('q', ''))[0]

    def get_list_display(self) -> Iterable[str]:
        """ Should return an iterable of field names to be displayed on the changelist """
        # TODO Kevin: Determining whether to use the ModelAdmin could be done in a metaclass

        if self.list_display is _UseAdminValue and self.use_admin_values:
            return self.adminmodel.get_list_display(self.request)  # TODO Kevin: Dunno if this works
        # Consider raising exceptions if self.list_display entries are invalid fields
        return self.list_display or ()  # Don't return _UseAdminValue

    def get_list_filter(self) -> Iterable[str]:
        if self.list_filter is _UseAdminValue and self.use_admin_values:
            return self.adminmodel.get_list_filter(self.request)
        return self.list_filter or ()  # Don't return _UseAdminValue

    def get_exclude(self) -> Iterable[str]:
        if self.exclude is _UseAdminValue and self.use_admin_values:
            return self.adminmodel.get_exclude(self.request) or ()
        return self.exclude or ()  # Don't return _UseAdminValue

    def get_list_display_links(self) -> Iterable[str]:
        if self.list_display_links is _UseAdminValue and self.use_admin_values:
            return self.adminmodel.get_list_display_links(self.request, self.get_list_display()) or ()
        return self.list_display_links or ()

    def beatify_fieldname(self, fieldname: str) -> str:
        if fieldname == self.model.__str__.__name__:  # fieldname == '__str__'
            return self.model._meta.object_name
        return fieldname.lower().strip('_').replace('_', ' ')

    def get_context_data(self, *, object_list=None, **kwargs):
        # TODO Kevin: The following check should probably not occur on runtime, if at all.
        adminmodel = self.adminmodel
        if self.uses_real_admin:  # Check if the current model is registered as a ModelAdmin, if not; don't use values from there.
            if self.list_per_page:
                self.paginate_by = self.list_per_page
            elif self.list_per_page is _UseAdminValue and self.use_admin_values:
                self.paginate_by = adminmodel.list_per_page

            def getactionname(action):
                try:
                    return action.short_description
                except AttributeError:
                    return action.__name__.replace('_', ' ')

            class GenericActionForm(Form):
                Actions = ChoiceField(choices=[(None, '------'), (0, f"Delete selected {self.model._meta.verbose_name_plural}")] + [(i+1, getactionname(action)) for i, action in enumerate(adminmodel.actions)])

        else:
            self.use_admin_values = False
            # self.use_admin_list_display = False

        context = super().get_context_data(**kwargs)  # Overwrite values from parent class above this line, create new ones below it.

        if self.use_admin_values:
            context['form'] = GenericActionForm

        if self.page_kwarg in self.request.GET:  # 'page' needs to be removed from the GET request while we create the filters, as Django believes 'page' to be a field to create a filter for.
            from django.http import QueryDict
            self.request.GET = QueryDict.copy(self.request.GET)  # self.request.GET is initially immutable, but by making it a copy of itself, we can make it mutable.
            del self.request.GET['page']

        context['currentparams'] = self.request.META['QUERY_STRING'].replace([[o for o in self.request.META['QUERY_STRING'].split('&') if o.startswith('page=')] + ['NOT_FOUND']][0][0], '').replace('&&&', '&').replace('&&', '&').strip('&')

        # TODO Kevin: Ew ew ew! Don't use the ModelAdmin changelist instance, make your own dammit!
        original_admin_list_filter = copy(adminmodel.list_filter)  # We have to store a copy of the original list filter, such that we can restore it, once we have our changelist.
        adminmodel.list_filter += tuple(self.list_filter or ())  # Adding filters from self.list_filter, such that Django will get values for them as well.
        for customfilter in [filterobject for filterobject in adminmodel.list_filter if isinstance(filterobject, type)]:  # TODO Kevin Views: Custom filters are currently not supported, so we should exclude them, as to not confuse users.
            adminmodel.list_filter.remove(customfilter)
        context['changelist_filter'] = adminmodel.get_changelist_instance(self.request)
        for filterobject in context['changelist_filter'].filter_specs:
            if isinstance(filterobject, BooleanFieldListFilter):
                filterobject.lookup_choices = [('1', 'Yes'), ('0', 'No')]
            if hasattr(filterobject, 'lookup_choices'):  # TODO Kevin Views: Certain Django filters lack lookup choices, and therefore filter by other means (such as DateFieldListFilter), these filters are currently excluded (Perhaps alter them, like BooleanFieldListFilter).
                for i, choice in enumerate(filterobject.lookup_choices):
                    if f"{filterobject.lookup_kwarg}={choice[0]}" in context['currentparams']:
                        filterobject.lookup_choices[i] = (choice[0], choice[1], True)
        adminmodel.list_filter = original_admin_list_filter

        context |= {
            'modeltitles': (self.model._meta.verbose_name, self.model._meta.verbose_name_plural, f"{self.model._meta.model_name}-create", f"{self.model._meta.model_name}-update", f"{self.model._meta.model_name}-delete"),  # Model names and URL's to use in context
            'list_display': {self.beatify_fieldname(i): i for i in self.get_list_display() if i not in self.get_exclude()},
            'list_filter': self.get_list_filter(),
            'list_display_links': tuple(self.beatify_fieldname(i) for i in self.get_list_display_links()),
            'previous_search_term': self.request.GET.get('q', ''),
            'empty_value_display': adminmodel.get_empty_value_display(),
            'field_names': tuple(field.name for field in self.model._meta.fields),
            'active_orderings': tuple(order.lstrip('-') for order in self.request.GET.get('o', '').split('|'))
        }

        before_for = datetime.now()
        context['object_pk_and_value_list'] = [(mdl.pk, {display: (mdl.__dict__.get(value) or getattr(mdl, value, getattr(adminmodel.__class__, value)(adminmodel, mdl) if value in dir(adminmodel.__class__) else None) if value != '__str__' else getattr(mdl, value)()) for display, value in context['list_display'].items()}) for mdl in context['objects']]
        print(f"List generation for {self.model._meta.verbose_name_plural} took: {datetime.now() - before_for}")
        del before_for

        return context

    def post(self, request, *args, **kwargs):
        def fixurl(str, strong=True):
            return str.replace('&&&', '&').replace('&&', '&').replace('?&', '?').replace('%7C', '|').replace('=|', '=').replace('||', '|').strip('%7C').strip('|') \
                if strong else str.replace('&&&', '&').replace('&&', '&').replace('?&', '?')

        if 'Actions' in request.POST:
            if int(request.POST.getlist('Actions')[0]) == 0:
                """from django.contrib.admin.actions import delete_selected  # Attempt to use Django's admin delete action. Does not seem to work, as it fails validation (or something) outside of admin (Stored here as it may come in useful in the future).
                delete_selected(admin.site._registry[self.model], self.request, self.model.objects.filter(pk__in=request.POST.getlist('checker')))"""
                self.model.objects.filter(pk__in=request.POST.getlist('checker')).delete()
            else:
                self.adminmodel.actions[int(request.POST.getlist('Actions')[0])-1](admin.site._registry[self.model], request, self.model.objects.filter(pk__in=request.POST.getlist('checker')))
        elif 'filter_request' in request.POST:
            if request.POST['filter_request'] not in request.META['QUERY_STRING']:
                name_and_value = request.POST['filter_request'].split('=')
                previous_filter = [[o for o in request.META['QUERY_STRING'].split('&') if o.startswith(f"{name_and_value[0]}=")] + ['NOT_FOUND']][0][0]
                if 'all' in name_and_value:
                    return HttpResponseRedirect(fixurl(f"{request.path}?{request.META['QUERY_STRING'].replace(previous_filter, '')}", strong=False))
                elif name_and_value[0] in request.META['QUERY_STRING']:
                    return HttpResponseRedirect(f"{request.path}?{request.META['QUERY_STRING'].replace(previous_filter, request.POST['filter_request'])}")
                else:
                    return HttpResponseRedirect(f"{request.path}?{request.META['QUERY_STRING']}&{request.POST['filter_request']}")
        elif 'order_request' in request.POST and request.POST['order_request'] in [field.name for field in self.model._meta.fields]:  # TODO Kevin View: Change this if ordering on properties is to be added.
            previous_order = [[o for o in request.META['QUERY_STRING'].split('&') if o.startswith('o') and 'o=' in o] + ['&o=']][0][0]
            if previous_order in request.META['QUERY_STRING']:
                if request.POST['order_request'] in previous_order:
                    if f"-{request.POST['order_request']}" in request.META['QUERY_STRING']:  # For some odd reason '|' changes to '%7C' once the string has undergone enough transformations, this is why '%7C' appears in the later replace methods. NOTE: This appears to be due to URL encoding, but otherwise the '|' character seems issue-free.
                        return HttpResponseRedirect(fixurl(f"{request.path}?{request.META['QUERY_STRING'].replace(previous_order, 'o={}|{}'.format(request.POST['order_request'], previous_order.replace('o=', '').replace('-{}'.format(request.POST['order_request']), '')))}"))
                    else:
                        return HttpResponseRedirect(fixurl(f"{request.path}?{request.META['QUERY_STRING'].replace(previous_order, 'o=-{}|{}'.format(request.POST['order_request'], previous_order.replace('o=', '').replace(request.POST['order_request'], '')))}"))
                else:
                    return HttpResponseRedirect(fixurl(f"{request.path}?{request.META['QUERY_STRING'].replace(previous_order, 'o={}|{}'.format(request.POST['order_request'], previous_order.replace('o=', '')))}", strong=False))
            else:
                return HttpResponseRedirect(f"{request.path}?{request.META['QUERY_STRING']}&o={request.POST['order_request']}".replace('&&&', '&').replace('&&', '&').replace('?&', '?'))
        elif 'remove_order' in request.POST:
            blank = '&o=' if len(request.GET.get('o', '').split('|')) > 1 else ''
            return HttpResponseRedirect(fixurl(f"{request.path}?{request.META['QUERY_STRING'].replace('%7C', '|').replace('o={}'.format(request.GET.get('o', '')), '')}{blank}{request.GET.get('o', '').replace('-{}'.format(request.POST.get('remove_order', '')) , '').replace(request.POST.get('remove_order', ''), '')}"))
        elif 'search_term' in request.POST:
            blank = '&q=' if request.POST.get('search_term', '') else ''
            return HttpResponseRedirect(fixurl(f"{request.path}?{request.META['QUERY_STRING'].replace('q={}'.format(request.GET.get('q', '')), '')}{blank}{request.POST['search_term']}", strong=False))
        return HttpResponseRedirect(f"{request.path}?{request.META['QUERY_STRING']}")  # Fallback option for errors or filters already in use


class GenericCreateView(AdminDependantMixIn, ABC, CreateView):
    form_class = None
    inlineform_fields = []
    template_name = 'frontend/generic_createview.html'

    def get_context_data(self, **kwargs):
        data = super(GenericCreateView, self).get_context_data(**kwargs)
        adminmodel = self.adminmodel
        inlinelist: list[InlineFormSet] = []
        inlines: Iterable[TabularInline] = (adminmodel.inlines or ())
        for inline in inlines:

            fieldlist: Iterable[str]
            if self.inlineform_fields:
                fieldlist = self.inlineform_fields
            elif inline.fields:
                fieldlist = inline.fields
            else:
                fieldlist = *(i.name for i in inline.model._meta.fields if i.editable and i.name not in (inline.exclude or ())),

            if inline.model._meta._property_names:
                lst = [property for property in inline.model._meta._property_names if property in fieldlist]
                lst2 = [prop for prop in inline.model._meta._property_names if prop in inline.readonly_fields]

                if lst or len(lst2) == len(inline.model._meta._property_names):
                    continue

            class gform(inline.form):
                inlinemodel = inline

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.helper = FormHelper()
                    self.helper.form_show_labels = False
                    try:
                        if inline.readonly_fields:
                            for i in inline.readonly_fields:
                                if i in inline.model._meta._property_names:
                                    continue
                                self.fields[i].widget.attrs['readonly'] = True
                    except Exception:
                        pass

                    if hasattr(self.inlinemodel, 'formfield_overrides'):
                        for field, value in self.fields.items():
                            widget_override = next((widget['widget'] for cls, widget in self.inlinemodel.formfield_overrides.items() if cls == getattr(self.inlinemodel.model, field).field.__class__), None)
                            if widget_override:
                                value.widget = widget_override

                class Meta:
                    model = inline.model
                    fields = fieldlist

            InlineFormSet = inlineformset_factory(self.model, inline.model, form=gform, extra=inline.extra,
                                                  can_delete=True)

            inlinelist.append(InlineFormSet)
        if self.request.POST:

            temp = self.request.POST.copy()
            for key in temp.keys():
                if all(x in key.lower() for x in ['_set-', 'received_date']):
                    del temp[key]
                    break

            if adminmodel.inlines:
                data['inline'] = [inline(temp, prefix=f"formset-{index}") for index, inline in enumerate(inlinelist)]
            else:
                data['inline'] = None
        else:
            data['inline'] = [inline(instance=self.object, prefix=f"formset-{index}") for index, inline in enumerate(inlinelist)]
        data['current_model'] = adminmodel.model._meta.verbose_name
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        inline = context['inline']
        with transaction.atomic():
            self.object = form.save()
            for i in (inline or ()):  # TODO Kevin: Inline is None
                if i.is_valid():
                    i.instance = self.object
                    i.save()
        return super(GenericCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.model._meta.model_name)


class GenericUpdateView(AdminDependantMixIn, ABC, UpdateView):
    form_class = None
    inlineform_fields = []
    template_name = 'frontend/generic_createview.html'

    def get_context_data(self, **kwargs):
        data = super(GenericUpdateView, self).get_context_data(**kwargs)
        adminmodel = self.adminmodel
        inlinelist = []
        if adminmodel.inlines:
            for inline in adminmodel.inlines:
                fieldlist = []
                if self.inlineform_fields:
                    fieldlist = self.inlineform_fields
                elif inline.form.base_fields:
                    for field in inline.form.base_fields:
                        fieldlist.append(field)
                elif inline.fields:
                    fieldlist = inline.fields
                else:
                    for i in inline.model._meta.fields:
                        if i.editable is False:
                            continue
                        else:
                            fieldlist.append(i.name)

                if inline.exclude:
                    for item in inline.exclude:
                        if item in fieldlist:
                            fieldlist.remove(item)
                if inline.model._meta._property_names:
                    lst = [property for property in inline.model._meta._property_names if property in fieldlist]
                    lst2 = [prop for prop in inline.model._meta._property_names if prop in inline.readonly_fields]

                    if lst or len(lst2) == len(inline.model._meta._property_names):
                        continue

                class gform(inline.form):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self.helper = FormHelper()
                        self.helper.form_show_labels = False
                        try:
                            if inline.readonly_fields:
                                for i in inline.readonly_fields:
                                    if i in inline.model._meta._property_names:
                                        continue
                                    self.fields[i].widget.attrs['readonly'] = True
                        except Exception:
                            pass

                    class Meta:
                        model = inline.model
                        fields = fieldlist

                InlineFormSet = inlineformset_factory(self.model, inline.model, form=gform, extra=3,
                                                      can_delete=True)

                inlinelist.append(InlineFormSet)

        if self.request.POST:

            temp = self.request.POST.copy()
            for key in temp.keys():
                if all(x in key.lower() for x in ['_set-', 'received_date']):
                    del temp[key]
                    break

            if adminmodel.inlines:
                data['inline'] = [inline(temp, instance=self.object, prefix=f"formset-{index}") for index, inline in enumerate(inlinelist)]
            else:
                data['inline'] = None
        else:
            data['inline'] = [inline(instance=self.object, prefix=f"formset-{index}") for index, inline in enumerate(inlinelist)]
        data['object'] = self.object
        data['delete_url'] = f'{self.model._meta.model_name}-delete'
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        inline = context['inline']
        with transaction.atomic():
            self.object = form.save()
            for i in (inline or ()):  # TODO Kevin: Inline is None
                if i.is_valid():
                    i.instance = self.object
                    i.save()
        return super(GenericUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.model._meta.model_name)


class GenericDeleteView(DeleteView):
    model: Model = None
    template_name = 'frontend/generic_deleteview.html'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            'model_name': self.model._meta.model_name,
            'object_name': self.model._meta.object_name,
            'instance_name': str(self.object),
        }

    def get_success_url(self):
        return reverse_lazy(self.model._meta.model_name)
