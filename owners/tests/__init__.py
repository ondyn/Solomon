"""
Solomon — Factory Boy factories for owners app.
"""

import datetime

import factory

from flats.tests import FlatFactory
from owners.models import FlatOwner, Owner


class OwnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Owner

    first_name = factory.Faker("first_name", locale="cs_CZ")
    last_name = factory.Faker("last_name", locale="cs_CZ")
    email = factory.LazyAttribute(lambda o: f"{o.first_name.lower()}.{o.last_name.lower()}@example.cz")
    phone = factory.Faker("phone_number", locale="cs_CZ")
    person_type = Owner.PersonType.NATURAL


class FlatOwnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FlatOwner

    flat = factory.SubFactory(FlatFactory)
    owner = factory.SubFactory(OwnerFactory)
    share_numerator = 1
    share_denominator = 1
    effective_from = factory.LazyFunction(lambda: datetime.date(2020, 1, 1))
