#!/usr/bin/env python3
"""Self-diagnostic script for AI Memory OS environments.

Purpose:
    Run this script to check the health of your AI development environment.
    The AI agent can call this at any time to verify system state and
    automatically decide what needs repair.

Usage:
    python scripts/system/health_check.py
    python scripts/system/health_check.py --json

Output: Human-readable status report (default) or JSON (with --json flag).
"""
import sys
import json
import subprocess
from pathlib import Path


def check_docker() -> dict:
    """Check if Docker containers are running."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {'status': 'error', 'message': 'Docker not accessible'}
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('\t')
                containers.append({'name': parts[0], 'status': parts[1] if len(parts) > 1 else 'unknown'})
        return {'status': 'ok' if containers else 'warning', 'containers': containers}
    except FileNotFoundError:
        return {'status': 'error', 'message': 'Docker not installed'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def check_venv() -> dict:
    """Check if Python virtual environment exists."""
    venv_path = Path('.venv')
    if venv_path.exists() and (venv_path / 'bin' / 'python').exists():
        return {'status': 'ok', 'path': str(venv_path)}
    return {'status': 'missing', 'message': 'Run: uv venv'}


def check_lancedb() -> dict:
    """Check if LanceDB is initialized."""
    db_path = Path('.lancedb')
    if not db_path.exists():
        return {'status': 'missing', 'message': 'Run: python scripts/ingest.py'}
    tables = list(db_path.glob('*.lance'))
    return {'status': 'ok', 'tables': len(tables)}


def check_git() -> dict:
    """Check git repository status."""
    if not Path('.git').exists():
        return {'status': 'missing', 'message': 'Not a git repository'}
    try:
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=5)
        remotes = result.stdout.strip()
        branch = subprocess.run(
            ['git', 'branch', '--show-current'], capture_output=True, text=True, timeout=5
        ).stdout.strip()
        return {'status': 'ok', 'branch': branch, 'has_remote': bool(remotes)}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def check_scripts() -> dict:
    """Check which AI Memory OS scripts are present."""
    scripts = {
        'ingest.py': Path('scripts/ingest.py'),
        'query.py': Path('scripts/query.py'),
        'bundle_context.py': Path('scripts/bundle_context.py'),
        'cache.py': Path('scripts/cache.py'),
        'conversation_digest.py': Path('scripts/system/conversation_digest.py'),
    }
    found = {name: path.exists() for name, path in scripts.items()}
    return {'status': 'ok', 'scripts': found}


def check_agents_md() -> dict:
    """Check if AGENTS.md exists and has content."""
    p = Path('AGENTS.md')
    if not p.exists():
        return {'status': 'missing', 'message': 'AGENTS.md not found'}
    size = p.stat().st_size
    return {'status': 'ok', 'size_bytes': size}


def main():
    use_json = '--json' in sys.argv

    checks = {
        'docker': check_docker(),
        'venv': check_venv(),
        'lancedb': check_lancedb(),
        'git': check_git(),
        'scripts': check_scripts(),
        'agents_md': check_agents_md(),
    }

    if use_json:
        print(json.dumps(checks, indent=2))
    else:
        icons = {'ok': '\u2705', 'warning': '\u26a0\ufe0f ', 'missing': '\u274c', 'error': '\u274c'}
        print('\n[SYSTEM] AI Memory OS Health Check\n' + '=' * 40)
        for name, result in checks.items():
            icon = icons.get(result['status'], '\u2753')
            print(f"{icon} {name}: {result['status']}")
            if result.get('message'):
                print(f"   \u2514\u2500 {result['message']}")
            if result.get('containers'):
                for c in result['containers']:
                    print(f"   \u2514\u2500 {c['name']}: {c['status']}")
            if result.get('scripts'):
                for script, exists in result['scripts'].items():
                    s = '\u2705' if exists else '\u274c'
                    print(f"   \u2514\u2500 {s} {script}")
        print('=' * 40)
        ok_count = sum(1 for r in checks.values() if r['status'] == 'ok')
        print(f"\nOverall: {ok_count}/{len(checks)} checks passed")


if __name__ == '__main__':
    main()
