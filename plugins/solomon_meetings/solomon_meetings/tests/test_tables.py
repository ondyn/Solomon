from decimal import Decimal

from django.test import SimpleTestCase

from solomon_meetings.models import QUORUM_TYPE_BY_SHARE, VoteWeightStyle
from solomon_meetings.tables import VoteWeightStyleTable


class VoteWeightStyleTableTests(SimpleTestCase):
    def test_weight_value_renders_as_fraction(self):
        style = VoteWeightStyle(
            voting_method=QUORUM_TYPE_BY_SHARE,
            weight_value=Decimal("0.014284"),
            weight_numerator=779,
            weight_denominator=54534,
            label="S1",
            color="#1976D2",
        )

        rendered = VoteWeightStyleTable.render_weight_value(None, style)

        self.assertEqual(rendered, "779/54534")
