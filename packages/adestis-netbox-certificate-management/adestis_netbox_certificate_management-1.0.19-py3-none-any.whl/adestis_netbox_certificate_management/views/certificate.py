from netbox.views import generic
from adestis_netbox_certificate_management.forms import *
from adestis_netbox_certificate_management.models import *
from adestis_netbox_certificate_management.filtersets import *
from adestis_netbox_certificate_management.tables import *
from netbox.views import generic
from django.utils.translation import gettext as _
from adestis_netbox_certificate_management.models import *
from adestis_netbox_certificate_management.tables import *
from adestis_netbox_applications.models import InstalledApplication
from adestis_netbox_applications.tables import InstalledApplicationTable, InstalledApplicationTableTab
from utilities.views import GetRelatedModelsMixin, ViewTab, register_model_view
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError
import cert_utils 
import hashlib
from django.urls import reverse
from django.db import transaction
from django.contrib import messages
from utilities.views import GetRelatedModelsMixin, ViewTab, register_model_view
from tenancy.models import Contact, ContactGroup, Tenant
from tenancy.tables import ContactTable, ContactGroupTable, TenantTable
from dcim.models import *
from dcim.forms import *
from dcim.tables import *
from dcim.filtersets import *
from netbox.constants import DEFAULT_ACTION_PERMISSIONS
from virtualization.models import *
from virtualization.forms import VirtualMachineForm, ClusterForm, ClusterGroupForm
from virtualization.tables import VirtualMachineTable, ClusterTable, ClusterGroupTable
import re

from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from pathlib import Path

from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates




__all__ = (
    'CertificateView',
    'CertificateListView',
    'CertificateEditView',
    'CertificateDeleteView',
    'CertificateBulkDeleteView',
    'CertificateBulkEditView',
    'CertificateBulkImportView',
    'CertificateAssignApplication',
    'CertificateBulkImportCertificateView',
    'CertificateRemoveApplicationView',
    'CertificateAffectedSuccessorCertificateView',

    'DeviceAffectedCertificateView',
    'ClusterAffectedCertificateView',
    'ClusterGroupAffectedCertificateView',
    'VirtualMachineAffectedCertificateView',
    'ContactAffectedCertificateView',
    'CertificateAffectedVirtualMachineView',
    'CertificateAffectedDeviceView',
    'CertificateAffectedClusterView',
    'CertificateAffectedClusterGroupView',
    'CertificateAffectedContactView',
    'CertificateAffectedInstalledApplicationView',
    
    'CertificateAssignDevice',
    'CertificateAssignCluster',
    'CertificateAssignClusterGroup',
    'CertificateAssignVirtualMachine',
    'CertificateAssignContact',
    'CertificateRemoveDeviceView',
    'CertificateRemoveClusterView',
    'CertificateRemoveContactView',
    'CertificateRemoveClusterGroupView',
    'CertificateRemoveVirtualMachineView',
    'CertificateRemoveTenantView',
    'TenantAffectedCertificateView',
)

@contextmanager
def pfx_bytes_to_pem(pfx_bytes, pfx_password):
            '''Convert .pfx file to PEM format for use in requests or analysis.'''
            # pfx = Path(pfx_path).read_bytes()
            private_key, main_cert, add_certs = load_key_and_certificates(
                pfx_bytes, pfx_password.encode('utf-8'), None
            )

            with NamedTemporaryFile(suffix=".pem", delete=True, mode="wb") as t_pem:
                t_pem.write(private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
                t_pem.write(main_cert.public_bytes(Encoding.PEM))
                for ca in add_certs or []:
                    t_pem.write(ca.public_bytes(Encoding.PEM))
                t_pem.flush()
                yield t_pem.name

class CertificateView(generic.ObjectView):
    queryset = Certificate.objects.all()

class CertificateListView(generic.ObjectListView):
    queryset = Certificate.objects.all()
    table = CertificateTable
    filterset = CertificateFilterSet
    filterset_form = CertificateFilterForm
    template_name = 'adestis_netbox_certificate_management/cert_import.html'
    

class CertificateEditView(generic.ObjectEditView):
    queryset = Certificate.objects.all()
    form = CertificateForm


class CertificateDeleteView(generic.ObjectDeleteView):
    queryset = Certificate.objects.all() 

class CertificateBulkDeleteView(generic.BulkDeleteView):
    queryset = Certificate.objects.all()
    table = CertificateTable
    
    
class CertificateBulkEditView(generic.BulkEditView):
    queryset = Certificate.objects.all()
    filterset = CertificateFilterSet
    table = CertificateTable
    form =  CertificateBulkEditForm
    

class CertificateBulkImportView(generic.BulkImportView):
    queryset = Certificate.objects.all()
    model_form = CertificateCSVForm
    table = CertificateTable
    
class CertificateBulkImportCertificateView(generic.ObjectEditView):
    queryset = Certificate.objects.all()
    template_name = 'adestis_netbox_certificate_management/crt_import.html'
    

        
    def get(self, request):
        form = CertificateCRTForm(request.POST, request.FILES,)
        context = {
            'form': form,
            'object': Certificate(),  # wichtig für object_edit.html
            'return_url': reverse('plugins:adestis_netbox_certificate_management:certificate_list'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = CertificateCRTForm(request.POST, request.FILES, )
        if form.is_valid():
            files = request.FILES.getlist('certificate')
            created = []
            for file in files:
                filename = file.name.lower()
                file_content = file.read()

                # Prüfen, ob Datei eine PFX-Datei ist (extension .pfx oder .p12)
                if filename.endswith('.pfx') or filename.endswith('.p12'):
                    pfx_password = form.cleaned_data.get('pfx_password') or ''  # Falls Passwortfeld vorhanden
                    try:
                        with pfx_bytes_to_pem(file_content, pfx_password) as pem_path:
                            with open(pem_path, 'r') as pem_file:
                                pem_content = pem_file.read()

                            # Extrahiere Zertifikate aus PEM-Content (wie bisher)
                            certs = re.findall(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", pem_content, flags=re.DOTALL)
                            if not certs:
                                raise ValidationError("No valid certificate found inside PFX file.")

                            for single_cert in certs:
                                cleaned_cert = single_cert.replace("\r\n", "").replace("\n", "").strip()
                                existing_cert = Certificate.objects.filter(certificate=cleaned_cert)
                                if existing_cert.exists():
                                    existing_cert = existing_cert.first()
                                    return redirect(existing_cert.get_absolute_url())

                                cert_data = cert_utils.parse_cert(single_cert)
                                subject_key_identifier = cert_data.get("subject_key_identifier") or hashlib.sha1(cleaned_cert.encode()).hexdigest()

                                common_name = cert_data.get("subject", "")
                                for pair in cert_data.get("subject", "").split("\n"):
                                    if "=" in pair:
                                        name, value = pair.split("=")
                                        if name == "CN":
                                            common_name = value

                                cert = Certificate.objects.create(
                                    certificate=cleaned_cert,
                                    name=common_name,
                                    subject_key_identifier=subject_key_identifier,
                                    status=CertificateStatusChoices.STATUS_ACTIVE
                                )
                                created.append(cert)

                    except Exception as e:
                        form.add_error(None, f"Import fehlgeschlagen: {e}")
                        context = {
                            'form': form,
                            'object': Certificate(),
                            'return_url': reverse('plugins:adestis_netbox_certificate_management:certificate_list'),
                        }
                        return render(request, self.template_name, context)

                else:
                    cert_text = file_content.decode()
                        
                    match = re.findall(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", cert_text, flags=re.DOTALL) 
                    if not match:
                        raise ValidationError("No valid certificate found in file")

                    for idx, single_cert in enumerate(match):
                        cleaned_cert = single_cert.replace("\r\n", "").replace("\n", "").strip()
                           
                        # parse certificate    
                        existing_cert = Certificate.objects.filter(certificate=cleaned_cert)
                        if existing_cert.exists():
                            existing_cert = existing_cert.first()
                            return redirect(existing_cert.get_absolute_url())
                            
                        cert_data = cert_utils.parse_cert(single_cert)
                            
                        subject_key_identifier = cert_data.get("subject_key_identifier")
                        if not subject_key_identifier:
                            subject_key_identifier = hashlib.sha1(cleaned_cert.encode()).hexdigest()
                            
                        common_name = cert_data["subject"]
                        for name,value in [ (pair.split("=")) for pair in cert_data["subject"].split("\n") ]:
                            if name == "CN":
                                common_name=value
                                    
                        cert = Certificate.objects.create(
                                certificate=cleaned_cert,
                                name=common_name,
                                subject_key_identifier=subject_key_identifier,
                                status = CertificateStatusChoices.STATUS_ACTIVE
                        )
                        created.append(cert) 
            if created:
                    return redirect(reverse('plugins:adestis_netbox_certificate_management:certificate_list'))
        context = {
            'form': form,
            'return_url': reverse('plugins:adestis_netbox_certificate_management:certificate_list'),
        }
        return render(request, self.template_name, context)  
      
@register_model_view(Certificate, name='applications')
class CertificateAffectedInstalledApplicationView(generic.ObjectChildrenView):
    queryset = Certificate.objects.all()
    child_model= InstalledApplication
    table = InstalledApplicationTableTab
    template_name = "adestis_netbox_certificate_management/application.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_application': {'change'},
    }

    tab = ViewTab(
        label=_('Applications'),
        badge=lambda obj: obj.installedapplication.count(),
        weight=600
    )

    def get_children(self, request, parent):
        return InstalledApplication.objects.restrict(request.user, 'view').filter(certificate=parent)
    
@register_model_view(Certificate, 'assign_application')
class CertificateAssignApplication(generic.ObjectEditView):
    queryset = Certificate.objects.prefetch_related(
        'installedapplication', 'tags', 
    ).all()
    
    form = CertificateAssignApplicationForm
    template_name = 'adestis_netbox_certificate_management/assign_application.html'

    def get(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate,  initial=request.GET)

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': reverse('plugins:adestis_netbox_certificate_management:certificate', kwargs={'pk': pk}),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_application', kwargs={'pk': pk}),
        })

    def post(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate, request.POST)

        if form.is_valid():
            
            selected_applications = form.cleaned_data['installedapplication']
            with transaction.atomic():
                
                for installedapplication in InstalledApplication.objects.filter(pk__in=selected_applications): 
                    certificate.installedapplication.add(installedapplication)
            
            certificate.save()
            
            return redirect(certificate.get_absolute_url())

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': certificate.get_absolute_url(),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_application', kwargs={'pk': pk}),
        })
    
@register_model_view(Certificate, 'remove_application', path='application/remove')
class CertificateRemoveApplicationView(generic.ObjectEditView):
    queryset = Certificate.objects.all()
    form = CertificateRemoveApplication
    template_name = 'generic/bulk_remove.html'

    def post(self, request, pk):

        certificate = get_object_or_404(self.queryset, pk=pk)

        if '_confirm' in request.POST:
            
            form = self.form(request.POST)
            if form.is_valid():
                
                application_pks = form.cleaned_data['pk']
                with transaction.atomic():
                    certificate.installedapplication.remove(*application_pks)
                    certificate.save()

                messages.success(request, _("Removed {count} applications from certificate {certificate}").format(
                    count=len(application_pks),
                    certificate=certificate
                ))
                return redirect(certificate.get_absolute_url())
        else:
            form = self.form(initial={'pk': request.POST.getlist('pk')})

        selected_objects = InstalledApplication.objects.filter(pk__in=form.initial['pk'])
        application_table = InstalledApplicationTable(list(selected_objects), orderable=False)
        application_table.configure(request)

        return render(request, self.template_name, {
            'form': form,
            'parent_obj': certificate,
            'table': application_table,
            'obj_type_plural': 'applications',
            'return_url': certificate.get_absolute_url(),
        })  
    
@register_model_view(Certificate, name='successor_certificates')
class CertificateAffectedSuccessorCertificateView(generic.ObjectChildrenView):
    queryset = Certificate.objects.all()
    child_model= Certificate
    table = CertificateTable
    # template_name = "adestis_netbox_certificate_management/successor_certificates.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
    }

    tab = ViewTab(
        label=_('Successor Certificates'),
        badge=lambda obj: obj.authority_certificates.count(),
        hide_if_empty=False,
        weight=600
    )
    
    def get_children(self, request, parent):
        return Certificate.objects.restrict(request.user, 'view').filter(authority_key_identifier=parent)
        
@register_model_view(Certificate, name='devices')
class CertificateAffectedDeviceView(generic.ObjectChildrenView):
    queryset = Certificate.objects.all()
    child_model= Device
    table = DeviceTableCertificate
    template_name = "adestis_netbox_certificate_management/device.html"

    tab = ViewTab(
        label=_('Devices'),
        badge=lambda obj: obj.device.count(),
        weight=600
    )
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_device': {'change'},
    }
    
    def get_children(self, request, parent):
        return Device.objects.restrict(request.user, 'view').filter(certificate=parent)
    
@register_model_view(Device, name='certificate')
class DeviceAffectedCertificateView(generic.ObjectChildrenView):
    queryset = Device.objects.all()
    child_model= Certificate
    table = CertificateTable
    template_name = "adestis_netbox_certificate_management/certificate_device.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_certificate': {'change'},
    }

    tab = ViewTab(
        label=_('Certificates'),
        badge=lambda obj: obj.certificate.count(),
        hide_if_empty=False
    )

    def get_children(self, request, parent):
        return Certificate.objects.restrict(request.user, 'view').filter(device=parent)
    
@register_model_view(Certificate, 'assign_device')
class CertificateAssignDevice(generic.ObjectEditView):
    queryset = Certificate.objects.prefetch_related(
        'device', 'tags', 
    ).all()
    
    form = CertificateAssignDeviceForm
    template_name = 'adestis_netbox_certificate_management/assign_device.html'

    def get(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate,  initial=request.GET)

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': reverse('plugins:adestis_netbox_certificate_management:certificate', kwargs={'pk': pk}),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_device', kwargs={'pk': pk}),
        })

    def post(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate, request.POST)

        if form.is_valid():
            
            selected_devices = form.cleaned_data['device']
            with transaction.atomic():
                
                for device in Device.objects.filter(pk__in=selected_devices): 
                    certificate.device.add(device)
            
            certificate.save()
            
            return redirect(certificate.get_absolute_url())

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': certificate.get_absolute_url(),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_device', kwargs={'pk': pk}),
        })
        
@register_model_view(Certificate, 'remove_device', path='device/remove')
class CertificateRemoveDeviceView(generic.ObjectEditView):
    queryset = Certificate.objects.all()
    form = CertificateRemoveDevice
    template_name = 'generic/bulk_remove.html'

    def post(self, request, pk):

        certificate = get_object_or_404(self.queryset, pk=pk)

        if '_confirm' in request.POST:
            
            form = self.form(request.POST)
            if form.is_valid():
                
                device_pks = form.cleaned_data['pk']
                with transaction.atomic():
                    certificate.device.remove(*device_pks)
                    certificate.save()

                messages.success(request, _("Removed {count} devices from certificate {certificate}").format(
                    count=len(device_pks),
                    certificate=certificate
                ))
                return redirect(certificate.get_absolute_url())
        else:
            form = self.form(initial={'pk': request.POST.getlist('pk')})

        selected_objects = Device.objects.filter(pk__in=form.initial['pk'])
        device_table = DeviceTable(list(selected_objects), orderable=False)
        device_table.configure(request)

        return render(request, self.template_name, {
            'form': form,
            'parent_obj': certificate,
            'table': device_table,
            'obj_type_plural': 'devices',
            'return_url': certificate.get_absolute_url(),
        })
        
@register_model_view(Certificate, name='clusters')
class CertificateAffectedClusterView(generic.ObjectChildrenView):
    queryset = Certificate.objects.all()
    child_model= Cluster
    table = ClusterTableCertificate
    template_name = "adestis_netbox_certificate_management/cluster.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_cluster': {'change'},
    }

    tab = ViewTab(
        label=_('Clusters'),
        badge=lambda obj: obj.cluster.count(),
        weight=600
    )

    def get_children(self, request, parent):
        return Cluster.objects.restrict(request.user, 'view').filter(certificate=parent)
 
@register_model_view(Cluster, name='certificates')
class ClusterAffectedCertificateView(generic.ObjectChildrenView):
    queryset = Cluster.objects.all()
    child_model= Certificate
    table = CertificateTable
    template_name = "adestis_netbox_certificate_management/certificate_cluster.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        
    }

    tab = ViewTab(
        label=_('Certificates'),
        badge=lambda obj: obj.certificate.count(),
        hide_if_empty=False
    )

    def get_children(self, request, parent):
        return Certificate.objects.restrict(request.user, 'view').filter(cluster=parent)
    
@register_model_view(Certificate, 'assign_cluster')
class CertificateAssignCluster(generic.ObjectEditView):
    queryset = Certificate.objects.prefetch_related(
        'cluster', 'tags', 
    ).all()
    
    form = CertificateAssignClusterForm
    template_name = 'adestis_netbox_certificate_management/assign_cluster.html'

    def get(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate,  initial=request.GET)

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': reverse('plugins:adestis_netbox_certificate_management:certificate', kwargs={'pk': pk}),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_cluster', kwargs={'pk': pk}),
        })

    def post(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate, request.POST)

        if form.is_valid():
            
            selected_cluster_groups = form.cleaned_data['cluster_group']
            selected_clusters = form.cleaned_data['cluster']
            with transaction.atomic():
                
                for cluster in Cluster.objects.filter(pk__in=selected_clusters): 
                    certificate.cluster.add(cluster)
                    
                for cluster_group in ClusterGroup.objects.filter(pk__in=selected_cluster_groups): 
                    certificate.cluster_group.add(cluster_group)
            
            certificate.save()
            
            return redirect(certificate.get_absolute_url())

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': certificate.get_absolute_url(),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_cluster', kwargs={'pk': pk}),
        })
        
@register_model_view(Certificate, 'remove_cluster', path='cluster/remove')
class CertificateRemoveClusterView(generic.ObjectEditView):
    queryset = Certificate.objects.all()
    form = CertificateRemoveCluster
    template_name = 'generic/bulk_remove.html'

    def post(self, request, pk):

        certificate = get_object_or_404(self.queryset, pk=pk)

        if '_confirm' in request.POST:
            
            form = self.form(request.POST)
            if form.is_valid():
                
                cluster_pks = form.cleaned_data['pk']
                with transaction.atomic():
                    certificate.cluster.remove(*cluster_pks)
                    certificate.save()

                messages.success(request, _("Removed {count} clusters from certificate {certificate}").format(
                    count=len(cluster_pks),
                    certificate=certificate
                ))
                return redirect(certificate.get_absolute_url())
        else:
            form = self.form(initial={'pk': request.POST.getlist('pk')})

        selected_objects = Cluster.objects.filter(pk__in=form.initial['pk'])
        cluster_table = ClusterTable(list(selected_objects), orderable=False)
        cluster_table.configure(request)

        return render(request, self.template_name, {
            'form': form,
            'parent_obj': certificate,
            'table': cluster_table,
            'obj_type_plural': 'clusters',
            'return_url': certificate.get_absolute_url(),
        })
    
    
@register_model_view(Certificate, name='cluster groups')
class CertificateAffectedClusterGroupView(generic.ObjectChildrenView):
    queryset = Certificate.objects.all()
    child_model= ClusterGroup
    table = ClusterGroupTableCertificate
    template_name = "adestis_netbox_certificate_management/cluster_group.html"
    tab = ViewTab(
        label=_('Cluster Groups'),
        badge=lambda obj: obj.cluster_group.count(),
        weight=600
    )
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_cluster_group': {'change'},
    }

    def get_children(self, request, parent):
        return ClusterGroup.objects.restrict(request.user, 'view').filter(certificate=parent)

@register_model_view(ClusterGroup, name='certificate')
class ClusterGroupAffectedCertificateView(generic.ObjectChildrenView):
    queryset = ClusterGroup.objects.all()
    child_model= Certificate
    table = CertificateTable
    template_name = "adestis_netbox_certificate_management/certificate_cluster_group.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_cluster_group': {'change'},
    }

    tab = ViewTab(
        label=_('Certificates'),
        badge=lambda obj: obj.certificate.count(),
        hide_if_empty=False
    )

    def get_children(self, request, parent):
        return Certificate.objects.restrict(request.user, 'view').filter(cluster_group=parent)
    
@register_model_view(Certificate, 'assign_cluster_group')
class CertificateAssignClusterGroup(generic.ObjectEditView):
    queryset = Certificate.objects.prefetch_related(
        'cluster_group', 'tags', 
    ).all()
    
    form = CertificateAssignClusterGroupForm
    template_name = 'adestis_netbox_certificate_management/assign_cluster_group.html'

    def get(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate,  initial=request.GET)

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': reverse('plugins:adestis_netbox_certificate_management:certificate', kwargs={'pk': pk}),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_cluster_group', kwargs={'pk': pk}),
        })

    def post(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate, request.POST)

        if form.is_valid():
            
            selected_clustergroups = form.cleaned_data['cluster_group']
            with transaction.atomic():
                
                for cluster_group in ClusterGroup.objects.filter(pk__in=selected_clustergroups): 
                    certificate.cluster_group.add(cluster_group)
            
            certificate.save()
            
            return redirect(certificate.get_absolute_url())

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': certificate.get_absolute_url(),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_cluster_group', kwargs={'pk': pk}),
        })
        
@register_model_view(Certificate, 'remove_cluster_group', path='cluster_group/remove')
class CertificateRemoveClusterGroupView(generic.ObjectEditView):
    queryset = Certificate.objects.all()
    form = CertificateRemoveClusterGroup
    template_name = 'generic/bulk_remove.html'

    def post(self, request, pk):

        certificate = get_object_or_404(self.queryset, pk=pk)

        if '_confirm' in request.POST:
            
            form = self.form(request.POST)
            if form.is_valid():
                
                cluster_group_pks = form.cleaned_data['pk']
                with transaction.atomic():
                    certificate.cluster_group.remove(*cluster_group_pks)
                    certificate.save()

                messages.success(request, _("Removed {count} cluster groups from certificate {certificate}").format(
                    count=len(cluster_group_pks),
                    certificate=certificate
                ))
                return redirect(certificate.get_absolute_url())
        else:
            form = self.form(initial={'pk': request.POST.getlist('pk')})

        selected_objects = ClusterGroup.objects.filter(pk__in=form.initial['pk'])
        cluster_group_table = ClusterGroupTable(list(selected_objects), orderable=False)
        cluster_group_table.configure(request)

        return render(request, self.template_name, {
            'form': form,
            'parent_obj': certificate,
            'table': cluster_group_table,
            'obj_type_plural': 'clustergroups',
            'return_url': certificate.get_absolute_url(),
        })

@register_model_view(Certificate, name='virtual machines')
class CertificateAffectedVirtualMachineView(generic.ObjectChildrenView):
    queryset = Certificate.objects.all()
    child_model= VirtualMachine
    table = VirtualMachineTableCertificate
    template_name = "adestis_netbox_certificate_management/virtual_machine.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_virtual_machine': {'change'},
    }

    tab = ViewTab(
        label=_('Virtual Machines'),
        badge=lambda obj: obj.virtual_machine.count(),
        weight=600
    )

    def get_children(self, request, parent):
        return VirtualMachine.objects.restrict(request.user, 'view').filter(certificate=parent)
  
@register_model_view(VirtualMachine, name='certificates')
class VirtualMachineAffectedCertificateView(generic.ObjectChildrenView):
    queryset = VirtualMachine.objects.all()
    child_model= Certificate
    table = CertificateTable
    template_name = "adestis_netbox_certificate_management/certificate_virtual_machine.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_virtual_machine': {'change'},
    }

    tab = ViewTab(
        label=_('Certificates'),
        badge=lambda obj: obj.certificate.count(),
        hide_if_empty=False
    )

    def get_children(self, request, parent):
        return Certificate.objects.restrict(request.user, 'view').filter(virtual_machine=parent)
    
@register_model_view(Certificate, 'assign_virtual_machine')
class CertificateAssignVirtualMachine(generic.ObjectEditView):
    queryset = Certificate.objects.prefetch_related(
        'virtual_machine', 'tags', 
    ).all()
    
    form = CertificateAssignVirtualMachineForm
    template_name = 'adestis_netbox_certificate_management/assign_virtual_machine.html'

    def get(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate,  initial=request.GET)

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': reverse('plugins:adestis_netbox_certificate_management:certificate', kwargs={'pk': pk}),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_virtual_machine', kwargs={'pk': pk}),
        })

    def post(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate, request.POST)

        if form.is_valid():
            
            selected_virtualmachines = form.cleaned_data['virtual_machine']
            with transaction.atomic():
                
                for virtual_machine in VirtualMachine.objects.filter(pk__in=selected_virtualmachines): 
                    certificate.virtual_machine.add(virtual_machine)
            
            certificate.save()
            
            return redirect(certificate.get_absolute_url())

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': certificate.get_absolute_url(),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_virtual_machine', kwargs={'pk': pk}),
        })
        
@register_model_view(Certificate, 'remove_virtual_machine', path='virtual_machine/remove')
class CertificateRemoveVirtualMachineView(generic.ObjectEditView):
    queryset = Certificate.objects.all()
    form = CertificateRemoveVirtualMachine
    template_name = 'generic/bulk_remove.html'

    def post(self, request, pk):

        certificate = get_object_or_404(self.queryset, pk=pk)

        if '_confirm' in request.POST:
            
            form = self.form(request.POST)
            if form.is_valid():
                
                virtual_machine_pks = form.cleaned_data['pk']
                with transaction.atomic():
                    certificate.virtual_machine.remove(*virtual_machine_pks)
                    certificate.save()

                messages.success(request, _("Removed {count} virtual machine from certificate {certificate}").format(
                    count=len(virtual_machine_pks),
                    certificate=certificate
                ))
                return redirect(certificate.get_absolute_url())
        else:
            form = self.form(initial={'pk': request.POST.getlist('pk')})

        selected_objects = VirtualMachine.objects.filter(pk__in=form.initial['pk'])
        virtual_machine_table = VirtualMachineTable(list(selected_objects), orderable=False)
        virtual_machine_table.configure(request)

        return render(request, self.template_name, {
            'form': form,
            'parent_obj': certificate,
            'table': virtual_machine_table,
            'obj_type_plural': 'virtualmachines',
            'return_url': certificate.get_absolute_url(),
        })

@register_model_view(Certificate, name='contacts')
class CertificateAffectedContactView(generic.ObjectChildrenView):
    queryset = Certificate.objects.all()
    child_model= Contact
    table = ContactTableCertificate
    template_name = "adestis_netbox_certificate_management/contact.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_contact': {'change'},
    }

    tab = ViewTab(
        label=_('Contacts'),
        badge=lambda obj: obj.contact.count(),
        weight=600
    )

    def get_children(self, request, parent):
        return Contact.objects.restrict(request.user, 'view').filter(certificate=parent)
  
@register_model_view(Contact, name='certificates')
class ContactAffectedCertificateView(generic.ObjectChildrenView):
    queryset = Contact.objects.all()
    child_model= Certificate
    table = CertificateTable
    template_name = "adestis_netbox_certificate_management/certificate_contact.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_certificate': {'change'},
    }

    tab = ViewTab(
        label=_('Certificates'),
        badge=lambda obj: obj.certificate.count(),
        hide_if_empty=False
    )

    def get_children(self, request, parent):
        return Certificate.objects.restrict(request.user, 'view').filter(contact=parent)
    
@register_model_view(Certificate, 'assign_contact')
class CertificateAssignContact(generic.ObjectEditView):
    queryset = Certificate.objects.prefetch_related(
        'contact', 'tags', 
    ).all()
    
    form = CertificateAssignContactForm
    template_name = 'adestis_netbox_certificate_management/assign_contact.html'

    def get(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate, initial=request.GET)

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': reverse('plugins:adestis_netbox_certificate_management:certificate', kwargs={'pk': pk}),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_contact', kwargs={'pk': pk}),
        })

    def post(self, request, pk):
        certificate = get_object_or_404(self.queryset, pk=pk)
        form = self.form(certificate, request.POST)

        if form.is_valid():
            
            selected_contacts = form.cleaned_data['contact']
            with transaction.atomic():
                
                for contact in Contact.objects.filter(pk__in=selected_contacts): 
                    certificate.contact.add(contact)
            
            certificate.save()
            
            return redirect(certificate.get_absolute_url())

        return render(request, self.template_name, {
            'certificate': certificate,
            'form': form,
            'return_url': certificate.get_absolute_url(),
            'edit_url': reverse('plugins:adestis_netbox_certificate_management:certificate_assign_contact', kwargs={'pk': pk}),
        })
        
@register_model_view(Certificate, 'remove_contact', path='contact/remove')
class CertificateRemoveContactView(generic.ObjectEditView):
    queryset = Certificate.objects.all()
    form = CertificateRemoveContact
    template_name = 'generic/bulk_remove.html'

    def post(self, request, pk):

        certificate = get_object_or_404(self.queryset, pk=pk)

        if '_confirm' in request.POST:
            
            form = self.form(request.POST)
            if form.is_valid():
                
                contact_pks = form.cleaned_data['pk']
                with transaction.atomic():
                    certificate.contact.remove(*contact_pks)
                    certificate.save()

                messages.success(request, _("Removed {count} contact from certificate {certificate}").format(
                    count=len(contact_pks),
                    certificate=certificate
                ))
                return redirect(certificate.get_absolute_url())
        else:
            form = self.form(initial={'pk': request.POST.getlist('pk')})

        selected_objects = Contact.objects.filter(pk__in=form.initial['pk'])
        contact_table = ContactTable(list(selected_objects), orderable=False)
        contact_table.configure(request)

        return render(request, self.template_name, {
            'form': form,
            'parent_obj': certificate,
            'table': contact_table,
            'obj_type_plural': 'contacts',
            'return_url': certificate.get_absolute_url(),
        })
        
@register_model_view(Tenant, name='certificates')
class TenantAffectedCertificateView(generic.ObjectChildrenView):
    queryset = Tenant.objects.all()
    child_model= Certificate
    table = CertificateTable
    template_name = "adestis_netbox_certificate_management/certificate_tenant.html"
    actions = {
        'add': {'add'},
        'export': {'view'},
        'bulk_import': {'add'},
        'bulk_edit': {'change'},
        'bulk_remove_tenant': {'change'},
    }

    tab = ViewTab(
        label=_('Certificates'),
        badge=lambda obj: obj.certificate.count(),
        hide_if_empty=False
    )

    def get_children(self, request, parent):
        return Certificate.objects.restrict(request.user, 'view').filter(tenant=parent)
 

@register_model_view(Certificate, 'remove_tenant', path='tenant/remove')
class CertificateRemoveTenantView(generic.ObjectEditView):
    queryset = Certificate.objects.all()
    form = CertificateRemoveTenant
    template_name = 'generic/bulk_remove.html'

    def post(self, request, pk):

        certificate = get_object_or_404(self.queryset, pk=pk)

        if '_confirm' in request.POST:
            
            form = self.form(request.POST)
            if form.is_valid():
                
                tenant_pks = form.cleaned_data['pk']
                with transaction.atomic():
                    certificate.tenant.remove(*tenant_pks)
                    certificate.save()

                messages.success(request, _("Removed {count} tenant from certificate {certificate}").format(
                    count=len(tenant_pks),
                    certificate=certificate
                ))
                return redirect(certificate.get_absolute_url())
        else:
            form = self.form(initial={'pk': request.POST.getlist('pk')})

        selected_objects = Tenant.objects.filter(pk__in=form.initial['pk'])
        tenant_table = TenantTable(list(selected_objects), orderable=False)
        tenant_table.configure(request)

        return render(request, self.template_name, {
            'form': form,
            'parent_obj': certificate,
            'table': tenant_table,
            'obj_type_plural': 'tenantss',
            'return_url': certificate.get_absolute_url(),
        })
