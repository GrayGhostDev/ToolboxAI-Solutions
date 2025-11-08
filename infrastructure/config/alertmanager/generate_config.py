#!/usr/bin/env python3
"""Generate Alertmanager config.yml from config.yml.tpl and .env file(s).

Usage: python3 generate_config.py [template_path] [output_path]

This script looks for two env files relative to its directory:
- ../../docker/compose/.env
- ../../docker/compose/.env.secret (optional)

It merges variables (secret file overrides) and substitutes ${VAR} in the template.
"""
import os
import sys
from pathlib import Path
import re


def load_env_file(env_path):
    env = {}
    if not env_path.exists():
        return env
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, v = line.split('=', 1)
            v = v.strip()
            # remove surrounding quotes if present
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            env[k.strip()] = v
    return env


def render_template(tpl_text, env):
    # replace ${VAR} occurrences
    def repl(m):
        name = m.group(1)
        return env.get(name, '')
    return re.sub(r"\$\{([A-Za-z0-9_]+)\}", repl, tpl_text)


def main():
    base = Path(__file__).parent
    # default template and output
    default_tpl = base / 'config.yml.tpl'
    default_out = base / 'config.yml'

    tpl_file = Path(sys.argv[1]) if len(sys.argv) > 1 else default_tpl
    out_file = Path(sys.argv[2]) if len(sys.argv) > 2 else default_out

    env_file = (base / '../../docker/compose/.env').resolve()
    secret_file = (base / '../../docker/compose/.env.secret').resolve()

    # load base env then overlay secret env (secrets override)
    env = {}
    env.update(load_env_file(env_file))
    env.update(load_env_file(secret_file))

    if not tpl_file.exists():
        print('Template file not found:', tpl_file)
        sys.exit(1)

    tpl_text = tpl_file.read_text()
    out_text = render_template(tpl_text, env)
    out_file.write_text(out_text)
    print('Wrote', out_file)

if __name__ == '__main__':
    main()
