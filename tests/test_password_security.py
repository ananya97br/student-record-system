# Security requirement: password hashes must be validated using a strong keyed algorithm.
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.test import SimpleTestCase


class PasswordHashingTests(SimpleTestCase):
    def test_argon2_is_primary_hasher(self):
        self.assertTrue(settings.PASSWORD_HASHERS[0].endswith("Argon2PasswordHasher"))

    def test_password_is_not_stored_as_plaintext(self):
        hashed = make_password("Example-Pass-123")
        self.assertNotEqual(hashed, "Example-Pass-123")
        self.assertTrue(hashed.startswith("argon2$argon2id$"))
        self.assertTrue(check_password("Example-Pass-123", hashed))
        self.assertFalse(check_password("wrong-password", hashed))