import argparse
from .core import random_string, slugify, to_snake, to_kebab, to_camel, to_pascal, to_title, only_letters, only_digits, only_alnum, only_printable, is_uuid, is_hex, safe_filename, strip_accents, normalize_space

def main():
    p = argparse.ArgumentParser(prog="stringx")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen")
    g.add_argument("--length", type=int, default=12)
    g.add_argument("--charset", default="letters+digits")
    g.add_argument("--secure", action="store_true")

    s = sub.add_parser("slugify")
    s.add_argument("text")
    s.add_argument("--sep", default="-")
    s.add_argument("--allow-unicode", action="store_true")

    c = sub.add_parser("case")
    c.add_argument("text")
    c.add_argument("--to", choices=["snake","kebab","camel","pascal","title"], required=True)

    f = sub.add_parser("filter")
    f.add_argument("text")
    f.add_argument("--only", choices=["letters","digits","alnum","printable"], required=True)

    v = sub.add_parser("validate")
    v.add_argument("text")
    v.add_argument("--uuid", action="store_true")
    v.add_argument("--hex", action="store_true")
    v.add_argument("--even-length", action="store_true")

    fn = sub.add_parser("filename")
    fn.add_argument("text")
    fn.add_argument("--maxlen", type=int, default=255)
    fn.add_argument("--allow-dot", action="store_true")

    a = sub.add_parser("strip-accents")
    a.add_argument("text")

    ns = sub.add_parser("normalize-space")
    ns.add_argument("text")

    args = p.parse_args()

    if args.cmd == "gen":
        print(random_string(args.length, args.charset, args.secure))
    elif args.cmd == "slugify":
        print(slugify(args.text, allow_unicode=args.allow_unicode, sep=args.sep))
    elif args.cmd == "case":
        if args.to == "snake":
            print(to_snake(args.text))
        elif args.to == "kebab":
            print(to_kebab(args.text))
        elif args.to == "camel":
            print(to_camel(args.text))
        elif args.to == "pascal":
            print(to_pascal(args.text))
        elif args.to == "title":
            print(to_title(args.text))
    elif args.cmd == "filter":
        if args.only == "letters":
            print(only_letters(args.text))
        elif args.only == "digits":
            print(only_digits(args.text))
        elif args.only == "alnum":
            print(only_alnum(args.text))
        elif args.only == "printable":
            print(only_printable(args.text))
    elif args.cmd == "validate":
        if args.uuid:
            print("true" if is_uuid(args.text) else "false")
        elif args.hex:
            print("true" if is_hex(args.text, even_length=args.even_length) else "false")
    elif args.cmd == "filename":
        print(safe_filename(args.text, maxlen=args.maxlen, allow_dot=args.allow_dot))
    elif args.cmd == "strip-accents":
        print(strip_accents(args.text))
    elif args.cmd == "normalize-space":
        print(normalize_space(args.text))
