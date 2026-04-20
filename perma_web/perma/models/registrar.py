from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.db.models.query import QuerySet
from django.utils import timezone
from model_utils import FieldTracker
from simple_history.models import HistoricalRecords
from taggit.managers import TaggableManager

from perma.utils import tz_datetime

from .base import CustomerModel, link_count_in_time_period, most_active_org_in_time_period


class RegistrarQuerySet(QuerySet):
    def approved(self):
        return self.filter(status="approved")


class Registrar(CustomerModel):
    """
    This is a library, a court, a firm, or similar.
    """
    name = models.CharField(max_length=400, db_index=True)
    email = models.EmailField(max_length=254)
    website = models.URLField(max_length=500)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=20, default='pending', choices=(('pending','pending'),('approved','approved'),('denied','denied')))
    orgs_private_by_default = models.BooleanField(default=False, help_text="Whether new orgs created for this registrar default to private links.")

    address = models.CharField(max_length=500, blank=True, null=True)
    manual_sort_order = models.IntegerField(default=0, db_index=True)

    link_count = models.IntegerField(default=0) # A cache of the number of links under this registrars's purview (sum of all associated org links)

    objects = RegistrarQuerySet.as_manager()
    tracker = FieldTracker()
    history = HistoricalRecords()
    tags = TaggableManager(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from .folder import Folder
        with self.tracker:
            super(Registrar, self).save(*args, **kwargs)
            if self.tracker.has_changed('name'):
                # Rename top-level sponsored folders if registrar name changes.
                folders = Folder.objects.filter(sponsored_by=self, parent__is_sponsored_root_folder=True)
                folders.update(name=self.name)

    def link_count_in_time_period(self, start_time=None, end_time=None):
        from .link import Link
        links = Link.objects.filter(organization__registrar=self)
        return link_count_in_time_period(links, start_time, end_time)

    def link_count_this_year(self):
        return self.link_count_in_time_period(tz_datetime(timezone.now().year, 1, 1))

    def most_active_org_in_time_period(self, start_time=None, end_time=None):
        return most_active_org_in_time_period(self.organizations, start_time, end_time)

    def most_active_org_this_year(self):
        return most_active_org_in_time_period(self.organizations, tz_datetime(timezone.now().year, 1, 1))

    def active_registrar_users(self):
        return self.users.filter(is_active=True)

    def link_creation_allowed(self):
        # No logic yet for handling paid Registrar customers with limits:
        # all paid-up Registrar customers get unlimited links.
        assert self.unlimited
        if self.nonpaying:
            return True
        if self.id in settings.SPECIAL_UNLIMITED_LINKS_FOR_REGISTRAR:
            return True
        return self.subscription_status == 'active'

Registrar._meta.get_field('nonpaying').default = True
Registrar._meta.get_field('unlimited').default = True
Registrar._meta.get_field('base_rate').default = Decimal(settings.DEFAULT_BASE_RATE_REGISTRAR)


class Sponsorship(models.Model):
    registrar = models.ForeignKey(Registrar, on_delete=models.PROTECT, related_name='sponsorships')
    user = models.ForeignKey('LinkUser', on_delete=models.CASCADE, related_name='sponsorships')
    status = models.CharField(max_length=10, blank=True, null=True, choices=(('active','Active: user may create links.'), ('inactive', 'Inactive: user may view, but not create, links.')), default='active')
    status_changed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('LinkUser', related_name='created_sponsorships', on_delete=models.PROTECT)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['registrar', 'user'], name='unique_sponsorship'),
        ]
        indexes = [
            models.Index(fields=['status', 'expires_at'])
        ]

    tracker = FieldTracker()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            with self.tracker:
                super().save(*args, **kwargs)
                if not self.folders:
                    self.user.create_sponsored_folder(self.registrar)
                if self.tracker.has_changed('status'):
                    self.folders.update(read_only=self.status == 'inactive')

    @property
    def folders(self):
        from .folder import Folder
        return Folder.objects.filter(owned_by=self.user, sponsored_by=self.registrar)
