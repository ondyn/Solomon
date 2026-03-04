"""
Solomon — Factory Boy factories for buildings app.
"""

import factory

from buildings.models import Building


class BuildingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Building

    name = factory.Sequence(lambda n: f"Building {n}")
    street = factory.Faker("street_name", locale="cs_CZ")
    house_number = factory.Sequence(lambda n: str(100 + n))
    city = "Brno"
    postal_code = "612 00"
    number_of_floors = 5
    elevator = True
    year_built = 1985
    total_units = 20
