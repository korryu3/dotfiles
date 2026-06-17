#!/usr/bin/env python3
"""Braille-bar statusline with git context"""
import json, sys, subprocess
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

data = json.load(sys.stdin)

BRAILLE = ' ⣀⣄⣤⣦⣶⣷⣿'
MONTHS = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
R = '\033[0m'
DIM = '\033[2m'
CYAN = '\033[36m'

def git_info(cwd):
    try:
        branch = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=cwd, capture_output=True, text=True, timeout=2,
        ).stdout.strip()
        commit = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=cwd, capture_output=True, text=True, timeout=2,
        ).stdout.strip()
        return branch, commit
    except Exception:
        return None, None

def gradient(pct):
    if pct < 50:
        r = int(pct * 5.1)
        return f'\033[38;2;{r};200;80m'
    else:
        g = int(200 - (pct - 50) * 4)
        return f'\033[38;2;255;{max(g, 0)};60m'

def braille_bar(pct, width=8):
    pct = min(max(pct, 0), 100)
    level = pct / 100
    bar = ''
    for i in range(width):
        seg_start = i / width
        seg_end = (i + 1) / width
        if level >= seg_end:
            bar += BRAILLE[7]
        elif level <= seg_start:
            bar += BRAILLE[0]
        else:
            frac = (level - seg_start) / (seg_end - seg_start)
            bar += BRAILLE[min(int(frac * 7), 7)]
    return bar

def fmt_reset_5h(resets_at):
    dt = datetime.fromtimestamp(resets_at)
    return f' {DIM}@{dt:%H:%M}{R}'

def fmt_reset_7d(resets_at):
    dt = datetime.fromtimestamp(resets_at)
    return f' {DIM}{MONTHS[dt.month]}{dt.day}{R}'

def fmt(label, pct):
    p = round(pct)
    return f'{DIM}{label}{R} {gradient(pct)}{braille_bar(pct)}{R} {p}%'

# Line 1: model + metrics
model = data.get('model', {}).get('display_name', 'Claude')
parts = [model]

ctx = data.get('context_window', {}).get('used_percentage')
if ctx is not None:
    parts.append(fmt('ctx', ctx))

five_hour = data.get('rate_limits', {}).get('five_hour', {})
five = five_hour.get('used_percentage')
if five is not None:
    s = fmt('5h', five)
    resets_at = five_hour.get('resets_at')
    if resets_at is not None:
        s += fmt_reset_5h(resets_at)
    parts.append(s)

seven_day = data.get('rate_limits', {}).get('seven_day', {})
week = seven_day.get('used_percentage')
if week is not None:
    s = fmt('7d', week)
    resets_at = seven_day.get('resets_at')
    if resets_at is not None:
        s += fmt_reset_7d(resets_at)
    parts.append(s)

line1 = f' {DIM}│{R} '.join(parts)

# Line 2: repo + branch + commit
repo = data.get('workspace', {}).get('repo', {}).get('name', '')
cwd = data.get('cwd', '')
branch, commit = git_info(cwd) if cwd else (None, None)

line2 = ''
if repo and branch:
    line2 = f'{DIM}{repo}:{R}{CYAN}{branch}{R}'
elif branch:
    line2 = f'{CYAN}{branch}{R}'
if commit:
    line2 += f' {DIM}({commit}){R}'

if line2:
    print(f'{line1}\n{line2}', end='')
else:
    print(line1, end='')
