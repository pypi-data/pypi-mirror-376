from django import forms
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm, NetBoxModelBulkEditForm, NetBoxModelImportForm
from utilities.forms.fields import CommentField, CSVChoiceField, TagFilterField
from adestis_netbox_certificate_management.models.certificate import Certificate, CertificateStatusChoices, FormatChoises
from adestis_netbox_applications.models import InstalledApplication
from django.utils.translation import gettext_lazy as _
from utilities.forms.widgets import DatePicker
from utilities.forms.rendering import FieldSet
from utilities.forms.fields import (
    TagFilterField,
    CSVModelChoiceField,
    CSVModelMultipleChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
)
from tenancy.models import Tenant, TenantGroup, Contact, ContactGroup
from dcim.models import *
from virtualization.models import *
from utilities.forms import ConfirmationForm
from utilities.forms import get_field_value

import logging.config
import logging


__all__ = (
    'CertificateForm',
    'CertificateFilterForm',
    'CertificateBulkEditForm',
    'CertificateCSVForm',
    'CertificateCRTForm',
    'CertificateAssignApplicationForm',
    'CertificateAssignDeviceForm',
    'CertificateAssignClusterForm',
    'CertificateAssignClusterGroupForm',
    'CertificateAssignVirtualMachineForm',
    'CertificateAssignContactForm',
    
    'CertificateRemoveApplication',
    'CertificateRemovePredecessor',

    'CertificateRemoveContact',
    'CertificateRemoveDevice',
    'CertificateRemoveCluster',
    'CertificateRemoveClusterGroup',
    'CertificateRemoveVirtualMachine',
    'CertificateRemoveTenant',
)

class CertificateCRTForm(forms.ModelForm):
      
    certificate = forms.FileField(
        label='Certificate',
        required=True,
    )
    
    status = forms.ChoiceField(
        required=False,
        label='Status',
        choices=[(CertificateStatusChoices.STATUS_ACTIVE, 'Active')]
    )
    
    format = forms.ChoiceField(
        required=False,
        label='Format',
        choices=FormatChoises,
    )
    
    pfx_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(),
        label="PFX-Password",
        help_text="Password for the .pfx file (leave blank if none was set)",
    )
    
    fieldsets = (
        FieldSet('certificate', 'status', 'format', 'pfx_password', name=_('Import Certificate')),
    )
    
    class Meta:
        model = Certificate
        fields = ['status', 'format', 'certificate', 'pfx_password']
        default_return_url = 'plugins:adestis_netbox_certificate_management:certificate_list'
             

class CertificateForm(NetBoxModelForm):

    comments = CommentField()
    
    certificate = forms.Textarea()
    
    tenant_group = DynamicModelChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        null_option='None',
    )
    
    contact_group = DynamicModelChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        null_option='None',
        help_text=_("Supplier"),
    )
    
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        query_params={
            'group_id': '$tenant_group'
        },
    )

    cluster_group = DynamicModelMultipleChoiceField(
        queryset=ClusterGroup.objects.all(),
        required=False,
        help_text=_("Cluster Group"),
    )

    cluster = DynamicModelMultipleChoiceField(
        queryset=Cluster.objects.all(),
        required=False,
        query_params={
            'group_id': '$cluster_group',
        },
        help_text=_("Cluster"),
    )
    
    device = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        query_params={
            'cluster_id': '$cluster',
        },
        help_text=_("Device"),
    )
    
    virtual_machine = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        required=False,
        null_option='None',
        query_params={
            'cluster_id': '$cluster',
            'device_id': '$device',
        },
        help_text=_("Virtual Machine"),
    )
    
    contact = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        query_params={
            'group_id': '$contact_group',
        },
        help_text=_("Contact"),
    )
    
    fieldsets = (
        FieldSet('name', 'description', 'status', 'tags', name=_('Certificate')),
        FieldSet('certificate',  'issuer_parent_certificate', 'subject', 'supplier_product', 'subject_alternative_name', 'key_technology', name=_('Certificate Chain')),
        FieldSet('tenant_group', 'tenant',  name=_('Tenant')), 
        FieldSet('cluster_group', 'cluster', 'virtual_machine', name=_('Virtualization')),   
        FieldSet('device', name=_('Device')),
        FieldSet('contact_group', 'contact', name=('Contact')),
        FieldSet('installedapplication', name=_('Appliation'))
    )

    class Meta:
        model = Certificate
        fields = ['name', 'description', 'status',  'tenant', 'tenant_group', 'cluster', 'installedapplication', 'cluster_group', 'virtual_machine', 'supplier_product', 'device', 'contact', 'comments', 'tags', 'contact_group', 'certificate', 'contact']
        help_texts = {
            'status': "Example text"
        }
        
        widgets = {
            'valid_from': DatePicker(),
            'valid_to': DatePicker(),
        }

class CertificateBulkEditForm(NetBoxModelBulkEditForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Certificate.objects.all(),
        widget=forms.MultipleHiddenInput
    )
    
    name = forms.CharField(
        required=False,
        max_length = 150,
        label=_("Name"),
    )
    
    comments = forms.CharField(
        max_length=150,
        required=False,
        label=_("Comment")
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=CertificateStatusChoices,
    )
    
    description = forms.CharField(
        max_length=500,
        required=False
    )
    
    valid_from = forms.DateField(
        required=False,
        widget=DatePicker
    )

    valid_to = forms.DateField(
        required=False,
        widget=DatePicker
    )

    contact_group = DynamicModelChoiceField(
        queryset=ContactGroup.objects.all(),
        required = False,
        label = ("Supplier")
    )
     
    certificate = forms.Textarea()
    
    virtual_machine = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        required = False,
        query_params={
            'cluster_id': '$cluster',
            'device_id': '$device',
        },
        label = ("Virtual Machines")
    )
    
    device = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required = False,
        query_params={
            'cluster_id': '$cluster',
        },
        label =_("Device")
    )
    
    tenant_group = DynamicModelChoiceField(
        queryset=TenantGroup.objects.all(),
        required = False,
        label=_("Tenant Group"),
    )
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required = False,
        label=_("Tenant"),
        query_params={
            'group_id': '$tenant_group'
        },
    )
    
    cluster_group = DynamicModelMultipleChoiceField(
        queryset=ClusterGroup.objects.all(),
        required = False,
        label=_("Cluster Group")
    )
    
    cluster = DynamicModelMultipleChoiceField(
        queryset=Cluster.objects.all(),
        required = False,
        query_params={
            'group_id': '$cluster_group',
        },
        label=_("Cluster")
    )
    
    contact = DynamicModelMultipleChoiceField(
        label=_('Contact'),
        queryset=Contact.objects.all(),
        required = False,
        query_params={
            'group_id': '$contact_group',
        },
    )
    
    installedapplication = DynamicModelChoiceField(
        label=_('Application'),
        queryset=InstalledApplication.objects.all(),
        required = False,
    )
    
    model = Certificate

    fieldsets = (
        FieldSet('name', 'description', 'status', 'tags', name=_('Certificate')),
        FieldSet('certificate', 'supplier_product', name=_('Certificate Chain')),
        FieldSet('valid_from', 'valid_to', name=_('Validity')),
        FieldSet('tenant_group', 'tenant',   name=_('Tenant')),
        FieldSet('cluster_group', 'cluster', 'virtual_machine', name=_('Virtualization')),
        FieldSet('device', name=_('Device')),
        FieldSet('contact_group', 'contact', name=_('Contact')),
        FieldSet('installedapplication', name=_('Appliation'))
    )
    
    model = Certificate

    fieldsets = (
        FieldSet('name', 'description', 'tags', 'status', 'comments', name=_('Application')),
        FieldSet('tenant_group', 'tenant', name=_('Tenant')),
        FieldSet('cluster', 'cluster_group', 'virtual_machine', name=_('Virtualization')),
        FieldSet('device', name=_('Device'))
    )

    nullable_fields = [
         'add_tags', 'remove_tags', 'description', ''
    ]
    
class CertificateFilterForm(NetBoxModelFilterSetForm):
    
    model = Certificate

    fieldsets = (
        FieldSet('q', 'index'),
        FieldSet('name', 'description', 'status', 'tags', name=_('Certificate')),
        FieldSet('certificate_id', 'issuer_parent_certificate', 'subject', 'subject_alternative_name', 'key_technology', 'supplier_product',  name=_('Certificate Chain')),
        FieldSet('valid_from', 'valid_to', name=_('Validity')),
        FieldSet('tenant_group_id', 'tenant_id',  name=_('Tenant')),
        FieldSet('cluster_group', 'cluster', 'virtual_machine', name=_('Virtualization')),
        FieldSet('device', name=_('Device')),
        FieldSet('contact_group_id', 'contact', name=_('Contact')),
        FieldSet('installedapplication', name=_('Appliation'))
    )

    index = forms.IntegerField(
        required=False
    )
    
    name = forms.CharField(
        max_length=200,
        required=False
    )

    status = forms.MultipleChoiceField(
        choices=CertificateStatusChoices,
        required=False,
        label=_('Status')
    )

    
    subject = forms.CharField(
        required=False,
        max_length=2000
    )
    
    subject_alternative_name = forms.CharField(
        max_length=2000,
        required=False
    )
    
    key_technology= forms.CharField(
        max_length=2000,
        required=False
    )
    
    valid_from = forms.DateField(
        required=False
    )
    
    valid_to = forms.DateField(
        required=False
    )
    
    issuer_parent_certificate = DynamicModelMultipleChoiceField(
        queryset=Certificate.objects.all(),
        required=False,
        label=_('Issuer')
    )
    
    virtual_machine = DynamicModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        label=_('Virtual Machines'),
        required=False,
    )
    
    cluster_group = DynamicModelMultipleChoiceField(
        queryset=ClusterGroup.objects.all(),
        label=_('Cluster Groups'),
        required=False,
    )
    
    cluster = DynamicModelMultipleChoiceField(
        queryset=Cluster.objects.all(),
        label=_('Clusters'),
        query_params={
            'group_id': '$cluster_group',
        },
        required=False,
    )
    
    device = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        label=_('Devices'),
        required=False,
    )
    
    tenant_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        null_option='None',
        query_params={
            'group_id': '$tenant_group_id'
        },
        label=_('Tenant')
    )
    
    contact_group_id = DynamicModelMultipleChoiceField(
        queryset=ContactGroup.objects.all(),
        required=False,
        null_option='None',
        label=_('Supplier')
    )
    
    tenant_group_id = DynamicModelMultipleChoiceField(
        queryset=TenantGroup.objects.all(),
        required=False,
        null_option='None',
        label=_('Tenant Group')
    )
    
    contact = DynamicModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        required=False,
        label=_('Contacts')
    )
    
    installedapplication = DynamicModelMultipleChoiceField(
        queryset = InstalledApplication.objects.all(),
        required = False,
        label=_('Applications')
    )

    tag = TagFilterField(model)

    
class CertificateCSVForm(NetBoxModelImportForm):

    status = CSVChoiceField(
        choices=CertificateStatusChoices,
        help_text=_('Status'),
        required=True,
    )
    
    tenant_group = CSVModelChoiceField(
        label=_('Tenant Group'),
        queryset=TenantGroup.objects.all(),
        required=True,
        to_field_name='name',
        help_text=('Assigned tenant group')
    )
    
    tenant = CSVModelChoiceField(
        label=_('Tenant'),
        queryset=Tenant.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Assigned tenant')
    )
    
    contact_group = CSVModelChoiceField(
        label=_('Supplier'),
        queryset=ContactGroup.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Assigned contact_group')
    )
    
    cluster_group = CSVModelMultipleChoiceField(
        label=_('Cluster Group'),
        queryset=ClusterGroup.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Assigned cluster group')
    )
    
    cluster = CSVModelMultipleChoiceField(
        label=_('Cluster'),
        queryset=Cluster.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Assigned cluster')
    )
    
    virtual_machine = CSVModelMultipleChoiceField(
        label=_('Virtual Machine'),
        queryset=VirtualMachine.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Assigned virtual machine')
    )
    
    device = CSVModelMultipleChoiceField(
        label=_('Device'),
        queryset=Device.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Assigned device')
    )
    
    contact = CSVModelMultipleChoiceField(
        label=_('Contact'),
        queryset=Contact.objects.all(),
        required = True,
        to_field_name='name',
        help_text=_('Assigned contact')
    )
    
    installedapplication = CSVModelChoiceField(
        label=_('Application'),
        queryset=InstalledApplication.objects.all(),
        required = True,
        to_field_name = 'name',
        help_text=_('Assigned application')
    )

    class Meta:
        model = Certificate
        fields = ['name' ,'status', 'valid_from', 'valid_to', 'contact_group', 'supplier_product', 'subject', 'subject_alternative_name', 'key_technology', 'device', 'virtual_machine', 'cluster', 'cluster_group', 'contact', 'issuer', 'installedapplication', 'comments', 'description', 'certificate', 'tags']
        default_return_url = 'plugins:adestis_netbox_certificate_management:Certificate_list'
        
class CertificateAssignDeviceForm(forms.Form):
    
    device = DynamicModelMultipleChoiceField(
        label=_('Devices'),
        queryset=Device.objects.all()
    )

    class Meta:
        fields = [
            'device',
        ]

    def __init__(self, certificate,*args, **kwargs):

        self.certificate = certificate

        self.device = DynamicModelMultipleChoiceField(
            label=_('Devices'),
            queryset=Device.objects.all()
        )        

        super().__init__(*args, **kwargs)

        self.fields['device'].choices = []
        
class CertificateAssignClusterForm(forms.Form):
    
    cluster_group = DynamicModelMultipleChoiceField(
            label=_('Cluster Group'),
            queryset= ClusterGroup.objects.all()
        )
    
    cluster = DynamicModelMultipleChoiceField(
        label=_('Clusters'),
        queryset=Cluster.objects.all(),
        query_params={
            'group_id': '$cluster_group',
        },)

    class Meta:
        fields = [
            'cluster_group', 'cluster',
        ]

    def __init__(self, certificate, *args, **kwargs):

        self.certificate = certificate
        
        self.cluster_group = DynamicModelMultipleChoiceField(
            label=_('Cluster Group'),
            queryset= ClusterGroup.objects.all()
        )

        self.cluster = DynamicModelMultipleChoiceField(
            label=_('Clusters'),
            queryset=Cluster.objects.all(),
            query_params={
            'group_id': '$cluster_group',
        },
        )        

        super().__init__(*args, **kwargs)

        self.fields['cluster'].choices = []
        
class CertificateAssignClusterGroupForm(forms.Form):
    
    cluster_group = DynamicModelMultipleChoiceField(
        label=_('Cluster Groups'),
        queryset=ClusterGroup.objects.all()
    )

    class Meta:
        fields = [
            'cluster_group',
        ]

    def __init__(self, certificate,*args, **kwargs):

        self.certificate = certificate

        self.cluster_group = DynamicModelMultipleChoiceField(
            label=_('Cluster Group'),
            queryset=ClusterGroup.objects.all()
        )        

        super().__init__(*args, **kwargs)

        self.fields['cluster_group'].choices = []
        
class CertificateAssignVirtualMachineForm(forms.Form):
    
    virtual_machine = DynamicModelMultipleChoiceField(
        label=_('Virtual Machines'),
        queryset=VirtualMachine.objects.all()
    )

    class Meta:
        fields = [
            'virtual_machine',
        ]

    def __init__(self, certificate, *args, **kwargs):

        self.certificate = certificate

        self.virtual_machine = DynamicModelMultipleChoiceField(
            label=_('Virtual Machines'),
            queryset=VirtualMachine.objects.all()
        )        

        super().__init__(*args, **kwargs)

        self.fields['virtual_machine'].choices = []
        
class CertificateAssignContactForm(forms.Form):
    
    contact = DynamicModelMultipleChoiceField(
        label=_('Contacts'),
        queryset=Contact.objects.all()
    )

    class Meta:
        fields = [
            'contact',
        ]

    def __init__(self, certificate, *args, **kwargs):

        self.certificate = certificate

        self.contact = DynamicModelMultipleChoiceField(
            label=_('Contacts'),
            queryset=Contact.objects.all()
        )        

        super().__init__(*args, **kwargs)

        self.fields['contact'].choices = []        
class CertificateAssignApplicationForm(forms.Form):
    
    installedapplication = DynamicModelMultipleChoiceField(
        label=_('Applications'),
        queryset=InstalledApplication.objects.all()
    )

    class Meta:
        fields = [
            'installedapplication',
        ]

    def __init__(self, certificate, *args, **kwargs):

        self.certificate = certificate

        self.installedapplication = DynamicModelMultipleChoiceField(
            label=_('Applications'),
            queryset=InstalledApplication.objects.all()
        )        

        super().__init__(*args, **kwargs)

        self.fields['installedapplication'].choices = []
        
class CertificateRemoveApplication(ConfirmationForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=InstalledApplication.objects.all(),
        widget=forms.MultipleHiddenInput()
    )
    
class CertificateRemoveContact(ConfirmationForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        widget=forms.MultipleHiddenInput()
    )

class CertificateRemovePredecessor(ConfirmationForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Certificate.objects.all(),
        widget=forms.MultipleHiddenInput()
    )
    
    
class CertificateRemoveDevice(ConfirmationForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Device.objects.all(),
        widget=forms.MultipleHiddenInput()
    ) 
        
class CertificateRemoveVirtualMachine(ConfirmationForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=VirtualMachine.objects.all(),
        widget=forms.MultipleHiddenInput()
    ) 
    
class CertificateRemoveCluster(ConfirmationForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Cluster.objects.all(),
        widget=forms.MultipleHiddenInput()
    )
    
class CertificateRemoveClusterGroup(ConfirmationForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=ClusterGroup.objects.all(),
        widget=forms.MultipleHiddenInput()
    )

class CertificateRemoveTenant(ConfirmationForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=Tenant.objects.all(),
        widget=forms.MultipleHiddenInput()
    )
