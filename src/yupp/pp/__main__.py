import sys
from .yup import cli


def main(argv=None):
    return cli(sys.argv[1:] if argv is None else argv)


if __name__ == '__main__':
    raise SystemExit(main())
