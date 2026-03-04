"""
Solomon — Factory Boy factories for flats app.
"""

import factory

from buildings.tests import BuildingFactory
from flats.models import Flat


class FlatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Flat

    building = factory.SubFactory(BuildingFactory)
    flat_number = factory.Sequence(lambda n: str(n + 1))
    floor = factory.LazyAttribute(lambda o: (int(o.flat_number) - 1) // 4 + 1)
    area_m2 = factory.LazyFunction(lambda: 65.50)
    disposition = "3+1"
    number_of_rooms = 3
