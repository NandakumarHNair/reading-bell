#!/usr/bin/env python3
"""Publish this project using your own GitHub CLI login; no tokens in the project.
Requires Python 3.8+ and GitHub CLI (gh). Run: python3 publish.py
Creates a PUBLIC repository, uploads only the listed project files and enables Pages.
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Optional
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
FILES = ('index.html', '.nojekyll', 'README.md', 'publish.py',
         'tests/session.py', 'tests/README.md', '.gitignore', 'HANDOFF.md')


class APIError(RuntimeError):
    def __init__(self, status: Optional[int], message: str):
        super().__init__(message)
        self.status = status


def api(path: str, method: str = 'GET', payload: Optional[dict] = None) -> Any:
    args = ['gh', 'api', '--hostname', 'github.com', '--method', method,
            '-H', 'Accept: application/vnd.github+json', path]
    if payload is not None:
        args += ['--input', '-']
    result = subprocess.run(args, input=json.dumps(payload) if payload is not None else None,
                            capture_output=True, text=True, timeout=90)
    try:
        data = json.loads(result.stdout) if result.stdout.strip() else None
    except json.JSONDecodeError:
        data = None
    if result.returncode:
        match = re.search(r'HTTP\s+(\d{3})', result.stderr)
        raw_status = data.get('status') if isinstance(data, dict) else None
        status = int(raw_status) if str(raw_status).isdigit() else int(match[1]) if match else None
        message = result.stderr.strip() or (data.get('message') if isinstance(data, dict) else None) or 'GitHub request failed.'
        raise APIError(status, message)
    return data


def optional(path: str) -> Any:
    try:
        return api(path)
    except APIError as error:
        if error.status == 404:
            return None
        raise


def file_bytes(record: Any) -> bytes:
    if not isinstance(record, dict) or record.get('type') != 'file' or record.get('encoding') != 'base64':
        raise RuntimeError('GitHub did not return a readable file; stopping rather than overwriting it.')
    return base64.b64decode(record.get('content', ''))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='reading-bell', help='Repository name in the signed-in account')
    parser.add_argument('--yes', action='store_true', help='Confirm public publication without prompting')
    options = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', options.repo):
        raise RuntimeError('Use a repository name containing only letters, numbers, dots, underscores and hyphens.')
    for name in FILES:
        if not (ROOT / name).is_file():
            raise RuntimeError(f'Missing {name}. Extract the whole project ZIP before running this script.')
    if not shutil.which('gh'):
        raise RuntimeError('GitHub CLI is missing. Install it first (on a Mac with Homebrew: brew install gh), then rerun this script.')
    auth = subprocess.run(['gh', 'auth', 'status', '--hostname', 'github.com'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    if auth.returncode:
        subprocess.run(['gh', 'auth', 'login', '--hostname', 'github.com',
                        '--git-protocol', 'https', '--web'], check=True)
    owner = api('user')['login']
    full_name = owner + '/' + options.repo
    base = 'repos/' + full_name
    repo = optional(base)
    if repo:
        if repo.get('private'):
            raise RuntimeError('That repository is private. Its visibility was not changed. Choose another name using --repo NAME.')
        existing = optional(base + '/contents/index.html')
        if not existing or b'reading-bell.settings.v1' not in file_bytes(existing):
            raise RuntimeError('That repository is not recognized as Reading Bell. Nothing was changed. Choose another name using --repo NAME.')
        if not repo.get('permissions', {}).get('push', False):
            raise RuntimeError('Your GitHub login does not have write access to this repository.')
    print('Account:', owner)
    print(('Update' if repo else 'Create') + ' PUBLIC repository:', full_name)
    print('Publish its root directory to GitHub Pages. Project code and docs will be public.')
    print('Local settings, reading progress, fonts, screenshots and credentials are not uploaded.')
    if not options.yes:
        if input('Continue? [y/N] ').strip().lower() not in ('y', 'yes'):
            print('Cancelled. No repository or Pages settings were changed.')
            return
    if not repo:
        repo = api('user/repos', 'POST', {
            'name': options.repo, 'private': False,
            'description': 'A lightweight reading session timer with start/end buzzers only. No build step or runtime dependencies.',
            'auto_init': False,
        })
    for name in FILES:
        path = base + '/contents/' + quote(name, safe='/')
        current = optional(path)
        content = (ROOT / name).read_bytes()
        if current and file_bytes(current) == content:
            print('Unchanged:', name)
            continue
        payload = {'message': 'Update Reading Bell 2.0.0 quiet sessions: ' + name,
                   'content': base64.b64encode(content).decode('ascii')}
        if current:
            payload['sha'] = current['sha']
        api(path, 'PUT', payload)
        print('Uploaded:', name)
    # Use GitHub's actual default branch rather than assuming it is named main.
    repo = api(base)
    source = {'branch': repo['default_branch'], 'path': '/'}
    pages = optional(base + '/pages')
    if pages is None:
        pages = api(base + '/pages', 'POST', {'source': source, 'build_type': 'legacy'})
    elif pages.get('source') != source or pages.get('build_type') == 'workflow':
        api(base + '/pages', 'PUT', {'source': source, 'build_type': 'legacy'})
        pages = api(base + '/pages')
    # Request a branch build. A busy build is not a failed upload.
    try:
        api(base + '/pages/builds', 'POST')
        build_message = 'GitHub Pages build requested.'
    except APIError as error:
        if error.status in (409, 422):
            build_message = 'Pages is configured; GitHub did not accept an additional build request. Check the repository Actions tab.'
        else:
            raise
    pages = api(base + '/pages')
    print('\nProject uploaded:', repo['html_url'])
    print(build_message)
    print('Site address (may still be building):', pages['html_url'])
    print('Deployment status:', pages.get('status') or 'Check the repository Actions tab')
    print('No claim of a live deployment is made until GitHub finishes the build.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nStopped. Previously uploaded files may remain on GitHub.', file=sys.stderr)
        sys.exit(130)
    except (APIError, RuntimeError, OSError, ValueError, KeyError, EOFError, subprocess.SubprocessError) as error:
        print('\nPublishing stopped: ' + str(error), file=sys.stderr)
        print('An earlier successful upload may remain. This script never deletes files or force-pushes.', file=sys.stderr)
        sys.exit(1)
