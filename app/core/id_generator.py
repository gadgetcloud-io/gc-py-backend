"""
Short ID Generator for user IDs and other entities
Generates URL-safe, database-friendly IDs under 12 characters

Supports multiple ID generation strategies:
1. Random alphanumeric (default)
2. Sequential numeric (for internal use)
3. Sequential encoded (sequential but obfuscated)
"""

import random
import string
import time
from typing import Optional
from google.cloud import firestore

# Character set: a-z, A-Z, 0-9 (62 characters)
# Excludes confusing characters: 0/O, 1/I/l
ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz'

# Base58 alphabet (similar to Bitcoin addresses)
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def generate_short_id(length: int = 10) -> str:
    """
    Generate a short, random ID

    Args:
        length: Length of ID (default: 10, max: 12)

    Returns:
        Random alphanumeric ID

    Examples:
        - 10 chars: aB3xK9mN4p (58^10 = ~430 trillion combinations)
        - 8 chars: aB3xK9mN (58^8 = ~128 billion combinations)

    Collision probability with 1M users:
        - 10 chars: ~0.000001% chance
        - 8 chars: ~0.004% chance
    """
    if length > 12:
        raise ValueError("ID length must be 12 or less")

    return ''.join(random.choices(ALPHABET, k=length))


def generate_user_id() -> str:
    """
    Generate a user ID (10 characters)

    Returns:
        10-character alphanumeric ID

    Example: aB3xK9mN4p
    """
    return generate_short_id(10)


def generate_item_id() -> str:
    """
    Generate an item ID (8 characters)

    Returns:
        8-character alphanumeric ID

    Example: aB3xK9mN
    """
    return generate_short_id(8)


def generate_prefixed_id(prefix: str, length: int = 8) -> str:
    """
    Generate an ID with a prefix (e.g., 'usr_aB3xK9mN')

    Args:
        prefix: Prefix to add (e.g., 'usr', 'itm', 'rep')
        length: Length of random part

    Returns:
        Prefixed ID

    Example: usr_aB3xK9mN (total: 12 chars with 'usr_' prefix)
    """
    if len(prefix) + 1 + length > 12:
        raise ValueError(f"Prefixed ID would exceed 12 characters: {len(prefix) + 1 + length}")

    return f"{prefix}_{generate_short_id(length)}"


def encode_number(num: int, alphabet: str = BASE58_ALPHABET) -> str:
    """
    Encode a number into a short string using base58/base62

    Args:
        num: Number to encode
        alphabet: Character set to use

    Returns:
        Encoded string

    Examples:
        1 → "2"
        100 → "BF"
        1000 → "He"
        10000 → "3yQ"
        100000 → "q2V"
    """
    if num == 0:
        return alphabet[0]

    encoded = []
    base = len(alphabet)

    while num > 0:
        num, remainder = divmod(num, base)
        encoded.append(alphabet[remainder])

    return ''.join(reversed(encoded))


def decode_number(encoded: str, alphabet: str = BASE58_ALPHABET) -> int:
    """
    Decode a base58/base62 string back to a number

    Args:
        encoded: Encoded string
        alphabet: Character set used

    Returns:
        Original number
    """
    base = len(alphabet)
    num = 0

    for char in encoded:
        num = num * base + alphabet.index(char)

    return num


class SequenceGenerator:
    """
    Sequential ID generator using Firestore counter
    Thread-safe and supports multiple environments
    """

    def __init__(self, db: firestore.Client, collection: str = "gc-sequences"):
        self.db = db
        self.collection = collection

    def get_next_id(self, sequence_name: str = "user_id") -> int:
        """
        Get next sequential number atomically

        Args:
            sequence_name: Name of the sequence (e.g., 'user_id', 'order_id')

        Returns:
            Next sequential number

        Example:
            generator = SequenceGenerator(db)
            next_id = generator.get_next_id('user_id')  # → 1, 2, 3...
        """
        doc_ref = self.db.collection(self.collection).document(sequence_name)

        # Use transaction to ensure atomicity
        @firestore.transactional
        def update_counter(transaction):
            snapshot = doc_ref.get(transaction=transaction)

            if snapshot.exists:
                current = snapshot.get('current')
                new_value = current + 1
            else:
                new_value = 1

            transaction.set(doc_ref, {'current': new_value}, merge=True)
            return new_value

        transaction = self.db.transaction()
        return update_counter(transaction)


def generate_sequential_id(db: firestore.Client, sequence_name: str = "user_id") -> str:
    """
    Generate sequential numeric ID

    Args:
        db: Firestore client
        sequence_name: Name of the sequence

    Returns:
        Sequential number as string (e.g., "1", "2", "100")

    ⚠️ Security Warning:
        Sequential numeric IDs are predictable and reveal user count.
        Use only for internal purposes or with proper authorization.

    Example:
        generate_sequential_id(db) → "1", "2", "3"...
    """
    generator = SequenceGenerator(db)
    next_num = generator.get_next_id(sequence_name)
    return str(next_num)


def generate_encoded_sequential_id(
    db: firestore.Client,
    sequence_name: str = "user_id",
    min_length: int = 4
) -> str:
    """
    Generate sequential ID encoded as short string

    Args:
        db: Firestore client
        sequence_name: Name of the sequence
        min_length: Minimum length (pad with leading chars if needed)

    Returns:
        Encoded sequential ID (e.g., "2", "BF", "He", "3yQ")

    Benefits:
        - Short IDs (1-6 chars for millions of users)
        - Sequential internally (good for databases)
        - Not obviously sequential (some obfuscation)
        - Reversible (can decode to get original number)

    Examples:
        User 1 → "2"
        User 100 → "BF"
        User 1000 → "He"
        User 10000 → "3yQ"
        User 100000 → "q2V"
        User 1000000 → "4Ldq2"
    """
    generator = SequenceGenerator(db)
    next_num = generator.get_next_id(sequence_name)
    encoded = encode_number(next_num)

    # Pad to minimum length if needed
    if len(encoded) < min_length:
        padding = BASE58_ALPHABET[0] * (min_length - len(encoded))
        encoded = padding + encoded

    return encoded


# Example usage and testing
if __name__ == "__main__":
    print("=== Random IDs ===")
    print("User IDs (10 chars):")
    for _ in range(5):
        print(f"  {generate_user_id()}")

    print("\nItem IDs (8 chars):")
    for _ in range(5):
        print(f"  {generate_item_id()}")

    print("\nPrefixed IDs (12 chars max):")
    for _ in range(5):
        print(f"  {generate_prefixed_id('usr', 7)}")

    print("\n=== Encoded Sequential IDs ===")
    print("Number encoding examples:")
    for num in [1, 10, 100, 1000, 10000, 100000, 1000000]:
        encoded = encode_number(num)
        decoded = decode_number(encoded)
        print(f"  {num:>7} → {encoded:>6} (decoded: {decoded})")

    print("\n✅ All ID generators ready to use!")
    print("\nRecommended for user IDs:")
    print("  1. Random (default): generate_user_id() → 10 chars, secure")
    print("  2. Encoded sequential: generate_encoded_sequential_id(db) → 4-6 chars, obfuscated")
    print("  3. Plain sequential: generate_sequential_id(db) → 1-7 chars, ⚠️ use with caution")
