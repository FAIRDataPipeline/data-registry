"""
The registry's vocabulary page defines every term of its own that the provenance
report and the RO Crate use, and no other.

The terms in use are read from the two modules' source, in the two forms they write
them: a QualifiedName in the fair namespace in prov.py, and _fair_term in rocrate.py.
A term written any other way is not seen.
"""

import html
from pathlib import Path
import re

from django.test import TestCase
from django.urls import reverse

from data_management import vocab

SOURCE = Path(__file__).resolve().parent.parent


def _terms_used():
    """Every registry term the report and the crate write."""
    prov = (SOURCE / "prov.py").read_text()
    crate = (SOURCE / "rocrate.py").read_text()
    return {
        *re.findall(r'vocab_namespaces\[FAIR_VOCAB_PREFIX\], "([A-Za-z_]+)"', prov),
        *re.findall(r'hash_term="([A-Za-z_]+)"', prov),
        *re.findall(r'_fair_term\(crate, "([A-Za-z_]+)"\)', crate),
    }


class VocabTests(TestCase):

    def test_every_term_used_is_defined_and_no_other(self):
        self.assertEqual({term.name for term in vocab.TERMS}, _terms_used())

    def test_page_is_read_only(self):
        self.assertEqual(self.client.post(reverse("vocab")).status_code, 405)

    def test_page_defines_every_term(self):
        response = self.client.get(reverse("vocab"))
        self.assertEqual(response.status_code, 200)
        page = html.unescape(response.content.decode())
        for term in vocab.TERMS:
            self.assertIn(f'id="{term.name}"', page)
            self.assertIn(term.definition[:40], page)
