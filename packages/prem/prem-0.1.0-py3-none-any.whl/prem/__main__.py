"""Usage:
  prem [options]

Options:
  --json  Output JSON
"""
import json
import platform
import sys
from pprint import pprint

import shtab
from argopt import argopt

from . import __version__


def cli(args=None):
    parser = argopt(__doc__)
    shtab.add_argument_to(parser)
    args = parser.parse_args(args=args)
    info = {
        'version': __version__, 'sys': {'version': sys.version, 'platform': sys.platform},
        'platform': {'machine': platform.machine(), 'platform': platform.platform()}}

    if args.json:
        print(json.dumps(info))
    else:
        pprint(info)


if __name__ == '__main__':
    cli()
