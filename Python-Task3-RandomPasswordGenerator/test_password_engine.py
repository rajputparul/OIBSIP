import unittest
from password_engine import (
    PasswordOptions, character_groups, estimate_entropy_bits,
    generate_password, strength_label,
)


class PasswordEngineTests(unittest.TestCase):
    def test_password_has_requested_length(self):
        self.assertEqual(len(generate_password(PasswordOptions(length=24))), 24)

    def test_each_selected_group_is_present(self):
        opts = PasswordOptions(length=32, uppercase=True, lowercase=True, digits=True, symbols=True)
        password = generate_password(opts)
        self.assertTrue(any(c.isupper() for c in password))
        self.assertTrue(any(c.islower() for c in password))
        self.assertTrue(any(c.isdigit() for c in password))
        self.assertTrue(any(not c.isalnum() for c in password))

    def test_length_bounds(self):
        for value in (7, 129):
            with self.assertRaises(ValueError):
                PasswordOptions(length=value)

    def test_requires_two_groups(self):
        with self.assertRaises(ValueError):
            PasswordOptions(uppercase=True, lowercase=False, digits=False, symbols=False)

    def test_excludes_ambiguous_characters(self):
        opts = PasswordOptions(length=40, exclude_ambiguous=True)
        self.assertFalse(set("0Ol1I") & set(generate_password(opts)))

    def test_entropy_and_labels(self):
        opts = PasswordOptions(length=20)
        self.assertGreater(estimate_entropy_bits(opts), 80)
        self.assertEqual(strength_label(90), "High")


if __name__ == "__main__":
    unittest.main()
