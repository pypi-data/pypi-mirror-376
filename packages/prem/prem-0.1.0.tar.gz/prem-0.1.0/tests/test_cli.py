import json

from prem.__main__ import cli


def test_cli(capsys):
    cli(['--json'])
    res = json.loads(capsys.readouterr().out)
    assert all(key in res for key in ('platform', 'sys', 'version'))
    cli([])   # pprint
