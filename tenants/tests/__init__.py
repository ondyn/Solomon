"""
Solomon — Factory Boy factories for tenants app.
"""

import datetime

import factory

from flats.tests import FlatFactory
from tenants.models import Tenant


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    flat = factory.SubFactory(FlatFactory)
    first_name = factory.Faker("first_name", locale="cs_CZ")
    last_name = factory.Faker("last_name", locale="cs_CZ")
    email = factory.LazyAttribute(lambda o: f"{o.first_name.lower()}.{o.last_name.lower()}@example.cz")
    phone = factory.Faker("phone_number", locale="cs_CZ")
    effective_from = factory.LazyFunction(lambda: datetime.date(2023, 1, 1))
