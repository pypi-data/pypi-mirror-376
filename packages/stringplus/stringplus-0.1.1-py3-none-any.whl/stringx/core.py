import re
import random
import secrets
import string
import unicodedata
import textwrap
import uuid
from collections import Counter
from string import ascii_letters, digits, hexdigits, ascii_lowercase, ascii_uppercase, punctuation, printable, whitespace
from typing import Iterable, List, Dict

def _words(s: str) -> List[str]:
    return re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[0-9]+", s)

def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def normalize_space(s: str) -> str:
    return " ".join(s.split())

def slugify(text: str, allow_unicode: bool = False, sep: str = "-") -> str:
    s = text if allow_unicode else strip_accents(text)
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", sep, s).strip(sep)
    return s

def to_snake(s: str) -> str:
    return "_".join(w.lower() for w in _words(s))

def to_kebab(s: str) -> str:
    return "-".join(w.lower() for w in _words(s))

def to_pascal(s: str) -> str:
    return "".join(w[:1].upper() + w[1:].lower() for w in _words(s))

def to_camel(s: str) -> str:
    ws = _words(s)
    return (ws[0].lower() if ws else "") + "".join(w[:1].upper() + w[1:].lower() for w in ws[1:])

def to_title(s: str) -> str:
    return " ".join(w[:1].upper() + w[1:].lower() for w in _words(s))

def _charset_from_spec(spec) -> str:
    if isinstance(spec, str):
        tokens = [t.strip() for t in spec.split("+")]
        bank = ""
        for t in tokens:
            if t in {"letters", "alpha"}:
                bank += ascii_letters
            elif t in {"lower", "lowercase"}:
                bank += ascii_lowercase
            elif t in {"upper", "uppercase"}:
                bank += ascii_uppercase
            elif t in {"digits", "nums", "numbers"}:
                bank += digits
            elif t in {"hex"}:
                bank += hexdigits
            elif t in {"punct", "punctuation"}:
                bank += punctuation
            elif t in {"printable"}:
                bank += printable
            elif t in {"whitespace", "space"}:
                bank += whitespace
        return "".join(sorted(set(bank)))
    try:
        return "".join(spec)
    except TypeError:
        raise TypeError("Unsupported charset spec")

def random_string(length: int = 12, charset="letters+digits", secure: bool = False) -> str:
    chars = _charset_from_spec(charset)
    if not chars:
        raise ValueError("Empty charset")
    if secure:
        return "".join(secrets.choice(chars) for _ in range(length))
    return "".join(random.choice(chars) for _ in range(length))

def secure_token(nbytes: int = 16, urlsafe: bool = True) -> str:
    return secrets.token_urlsafe(nbytes) if urlsafe else secrets.token_hex(nbytes)

def only_letters(s: str) -> str:
    return "".join(ch for ch in s if ch.isalpha())

def only_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

def only_alnum(s: str) -> str:
    return "".join(ch for ch in s if ch.isalnum())

def only_printable(s: str) -> str:
    return "".join(ch for ch in s if ch in printable)

def filter_chars(s: str, keep: Iterable[str] = None, remove: Iterable[str] = None) -> str:
    if keep is not None:
        ks = set(keep)
        return "".join(ch for ch in s if ch in ks)
    if remove is not None:
        rs = set(remove)
        return "".join(ch for ch in s if ch not in rs)
    return s

def is_hex(s: str, even_length: bool = False) -> bool:
    if not s:
        return False
    if even_length and len(s) % 2 != 0:
        return False
    return all(ch in hexdigits for ch in s)

def is_uuid(s: str) -> bool:
    try:
        val = uuid.UUID(str(s))
        return str(val) == str(s).lower()
    except Exception:
        return False

def ngrams(s: str, n: int = 2, step: int = 1) -> List[str]:
    if n <= 0 or step <= 0:
        return []
    return [s[i:i+n] for i in range(0, max(len(s) - n + 1, 0), step)]

def chunks(s: str, size: int) -> List[str]:
    if size <= 0:
        return []
    return [s[i:i+size] for i in range(0, len(s), size)]

def char_freq(s: str) -> Dict[str, int]:
    return dict(Counter(s))

def truncate(s: str, maxlen: int, ellipsis: str = "...") -> str:
    if maxlen < len(ellipsis):
        return ellipsis[:maxlen]
    return s if len(s) <= maxlen else s[: maxlen - len(ellipsis)] + ellipsis

def pad_left(s: str, width: int, char: str = " ") -> str:
    return s.rjust(width, char)

def pad_right(s: str, width: int, char: str = " ") -> str:
    return s.ljust(width, char)

def ensure_prefix(s: str, prefix: str) -> str:
    return s if s.startswith(prefix) else prefix + s

def ensure_suffix(s: str, suffix: str) -> str:
    return s if s.endswith(suffix) else s + suffix

def safe_filename(s: str, maxlen: int = 255, allow_dot: bool = False) -> str:
    base = strip_accents(s)
    base = re.sub(r"[^\w\s.-]" if allow_dot else r"[^\w\s-]", "", base)
    base = re.sub(r"\s+", "_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    return base[:maxlen] if maxlen > 0 else base

def repeat(s: str, times: int, sep: str = "") -> str:
    if times <= 0:
        return ""
    return sep.join(s for _ in range(times))

def fill_template(text: str, mapping: dict, safe: bool = True) -> str:
    t = string.Template(text)
    return t.safe_substitute(mapping) if safe else t.substitute(mapping)
