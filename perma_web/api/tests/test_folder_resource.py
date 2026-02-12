from .utils import ApiResourceTestCase
from django.conf import settings
from perma.models import LinkUser, Folder
from rest_framework.settings import api_settings


class FolderResourceTestCase(ApiResourceTestCase):

    resource_url = '/folders'

    @classmethod
    def setUpTestData(cls):
        cls.org_user = LinkUser.objects.get(pk=3)
        cls.empty_child_folder = Folder.objects.get(pk=29)
        cls.nonempty_child_folder = Folder.objects.get(pk=30)

    def nested_url(self, obj):
        return self.detail_url(obj) + "/folders"

    def test_should_strip_whitespace_from_name(self):
        name = 'This is a folder name'
        obj = self.successful_post(self.nested_url(self.org_user.root_folder),
                                   data={'name': ' '+name+'  '},
                                   user=self.org_user)

        self.assertEqual(obj['name'], name)

    def test_limit_is_capped_to_page_size(self):
        data = self.successful_get(
            self.list_url,
            user=self.org_user,
            data={'limit': 9999},
        )
        self.assertKeys(data, ['meta', 'objects'])
        self.assertEqual(data['meta']['limit'], settings.API_LONG_PAGE_SIZE)

    def test_default_limit_matches_page_size(self):
        data = self.successful_get(self.list_url, user=self.org_user)
        self.assertKeys(data, ['meta', 'objects'])
        self.assertEqual(data['meta']['limit'], api_settings.PAGE_SIZE)

    def test_moving(self):
        user = self.empty_child_folder.created_by
        parent_folder = self.nonempty_child_folder
        child_folder = self.empty_child_folder

        self.successful_put(
            "{0}/folders/{1}".format(self.detail_url(parent_folder), child_folder.pk),
            user=user
        )

        # Make sure it's listed in the folder
        obj = self.successful_get(self.detail_url(child_folder), user=user)
        data = self.successful_get(self.detail_url(parent_folder)+"/folders", user=user)

        self.assertIn(obj, data['objects'])

    def test_should_reject_duplicate_folder_name(self):
        self.rejected_post(self.nested_url(self.empty_child_folder.parent),
                            data={'name': self.empty_child_folder.name},
                            user=self.empty_child_folder.created_by,
                            expected_status_code=400,
                            expected_data={"name":["A folder with that name already exists at that location."]})
