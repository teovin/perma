def test_link_count_do_not_increment_after_saving_a_deleted_link(org_user, link_factory):
    """ Re-saving a user-deleted link must not count it as a new link """
    organization = org_user.organizations.first()
    registrar = organization.registrar
    link = link_factory(
        created_by=org_user,
        submitted_url="http://example.com",
        organization=organization,
    )
    link.safe_delete() 
    link.save() # user should have 0 links now

    # get the link counts before the link is saved again
    org_user.refresh_from_db()
    organization.refresh_from_db()
    registrar.refresh_from_db()
    user_count = org_user.link_count
    org_count = organization.link_count
    registrar_count = registrar.link_count

    link.save() # user should still have 0 links

    # get the link counts after the link is saved again
    org_user.refresh_from_db()
    organization.refresh_from_db()
    registrar.refresh_from_db()
    assert org_user.link_count == user_count
    assert organization.link_count == org_count
    assert registrar.link_count == registrar_count


def test_link_count_regular_user(link_user, link_factory):
    """ We do some link count tallying on save """
    link_count = link_user.link_count
    link = link_factory(created_by=link_user, submitted_url="http://example.com")
    link_user.refresh_from_db()
    assert link_count + 1 == link_user.link_count

    link.safe_delete()
    link.save()

    link_user.refresh_from_db()
    assert link_count == link_user.link_count

def test_link_count_for_orgs(org_user, link_factory):
    """ We do some link count tallying on save. Let's make sure
    we're adjusting the counts on the orgs """
    organization = org_user.organizations.first()
    link_count = organization.link_count
    link = link_factory(created_by=org_user, submitted_url="http://example.com", organization=organization)
    link.save()

    organization.refresh_from_db()
    assert link_count + 1 == organization.link_count

    link.safe_delete()
    link.save()

    organization.refresh_from_db()
    assert link_count == organization.link_count


def test_link_count_for_registrars(registrar_user, link_factory):
    """ We do some link count tallying on save. Let's make sure
    we're adjusting the counts on the registrars """

    org_managed_by_registrar = registrar_user.registrar.organizations.first()
    link_count = registrar_user.registrar.link_count
    link = link_factory(created_by=registrar_user, submitted_url="http://example.com", organization=org_managed_by_registrar)
    link.save()

    registrar_user.registrar.refresh_from_db()
    assert link_count + 1 == registrar_user.registrar.link_count

    link.safe_delete()
    link.save()

    registrar_user.registrar.refresh_from_db()
    assert link_count == registrar_user.registrar.link_count
