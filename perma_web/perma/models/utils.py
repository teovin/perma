from django.db import models
from django.db.models import Count
from django.utils import timezone
from taggit.models import CommonGenericTaggedItemBase, TaggedItemBase


### HELPERS ###

# functions
def link_count_in_time_period(links, start_time=None, end_time=None):
    if start_time and end_time and (start_time > end_time):
        raise ValueError("specified end time is earlier than specified start time")
    elif start_time and end_time and (start_time == end_time):
        links = links.filter(creation_timestamp=start_time)
    else:
        if start_time:
            links = links.filter(creation_timestamp__gte=start_time)
        if end_time:
            links = links.filter(creation_timestamp__lte=end_time)
    return links.count()

def most_active_org_in_time_period(organizations, start_time=None, end_time=None):
    if start_time and end_time and (start_time > end_time):
        raise ValueError("specified end time is earlier than specified start time")
    # unlike 'link_count_in_time_period', no special behavior required
    # if start_time = end_time here. the end result is the same
    else:
        if start_time:
            organizations = organizations.filter(links__creation_timestamp__gte=start_time)
        if end_time:
            organizations = organizations.filter(links__creation_timestamp__lte=end_time)
        return organizations\
            .annotate(num_links=Count('links'))\
            .exclude(num_links=0)\
            .order_by('-num_links')\
            .first()


# classes

# django-taggit assumes the model being tagged has an integer primary key.
# per http://django-taggit.readthedocs.io/en/latest/custom_tagging.html,
# tag "through" this class if your model has a string as primary key.
# tags = TaggableManager(through=GenericStringTaggedItem)
# (copied straight from their docs)
class GenericStringTaggedItem(CommonGenericTaggedItemBase, TaggedItemBase):
    object_id = models.CharField(max_length=50, db_index=True)


class DeletableManager(models.Manager):
    """
        Manager that excludes results where user_deleted=True by default.
    """
    def get_queryset(self):
        # exclude deleted entries by default
        return super(DeletableManager, self).get_queryset().filter(user_deleted=False)

    def all_with_deleted(self):
        return super(DeletableManager, self).get_queryset()


class DeletableModel(models.Model):
    """
        Abstract base class that lets a model track deletion.
    """
    user_deleted = models.BooleanField(default=False, verbose_name="Deleted by user")
    user_deleted_timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def safe_delete(self):
        self.user_deleted = True
        self.user_deleted_timestamp = timezone.now()




