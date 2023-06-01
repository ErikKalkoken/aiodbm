import random
import string
from typing import List


def random_strings(count: int, length: int = 64) -> List[str]:
    return [random_string(length) for _ in range(count)]


def random_string(length: int) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
