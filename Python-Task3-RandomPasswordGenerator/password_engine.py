"""Secure password-generation utilities; no GUI dependencies."""
from __future__ import annotations

from dataclasses import dataclass
import math
import secrets
import string

AMBIGUOUS = frozenset("0Ol1I")


@dataclass(frozen=True)
class PasswordOptions:
    length: int = 16
    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.length, bool) or not isinstance(self.length, int):
            raise TypeError("length must be an integer")
        if not 8 <= self.length <= 128:
            raise ValueError("length must be between 8 and 128 characters")
        if sum((self.uppercase, self.lowercase, self.digits, self.symbols)) < 2:
            raise ValueError("select at least two character groups")


def character_groups(options: PasswordOptions) -> list[str]:
    groups: list[str] = []
    if options.uppercase:
        groups.append(string.ascii_uppercase)
    if options.lowercase:
        groups.append(string.ascii_lowercase)
    if options.digits:
        groups.append(string.digits)
    if options.symbols:
        groups.append(string.punctuation)
    if options.exclude_ambiguous:
        groups = ["".join(ch for ch in group if ch not in AMBIGUOUS) for group in groups]
    groups = [group for group in groups if group]
    if len(groups) < 2:
        raise ValueError("selected character groups must contain at least two non-empty groups")
    return groups


def generate_password(options: PasswordOptions) -> str:
    """Generate with the `secrets` module and guarantee each selected group appears."""
    groups = character_groups(options)
    if options.length < len(groups):
        raise ValueError("length must be at least the number of selected groups")
    pool = "".join(groups)
    chars = [secrets.choice(group) for group in groups]
    chars.extend(secrets.choice(pool) for _ in range(options.length - len(chars)))
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def estimate_entropy_bits(options: PasswordOptions) -> float:
    """Approximate log2(pool_size**length); not a password-cracking guarantee."""
    pool_size = len(set("".join(character_groups(options))))
    return options.length * math.log2(pool_size)


def strength_label(entropy_bits: float) -> str:
    """A transparent heuristic, not a formal security certification."""
    if entropy_bits < 40:
        return "Low"
    if entropy_bits < 60:
        return "Moderate"
    if entropy_bits < 80:
        return "Good"
    return "High"
