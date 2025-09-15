# stringx

Extended string utilities plus a CLI. Re-exports all `string` constants and adds helpers for case conversion, slugify, filters, validators, tokens, and more.

## Install
pip install stringx

## Python
```python
from stringx import ascii_letters, random_string, slugify, to_snake, to_camel, only_digits, is_uuid, safe_filename
print(ascii_letters[:10])
print(random_string(16, "letters+digits", secure=True))
print(slugify("Hello, World!"))
print(to_snake("MyHTTPServer"))
print(to_camel("my_http_server"))
print(only_digits("a1b2c3"))
print(is_uuid("123e4567-e89b-12d3-a456-426614174000"))
print(safe_filename("Quarterly Report: Q1/2025.pdf", allow_dot=True))
