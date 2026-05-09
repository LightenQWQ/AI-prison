#!/usr/bin/env python3
"""Patch: add missing light/pole words to color_killers"""
import re

path = '/workspace/Just_A_Suggestion_v2/main.py'
content = open(path, encoding='utf-8').read()

OLD = r"""    color_killers = {
        r\"\bstreetlight(?:s)?\b\":       \"darkness at end of alley\",
        r\"\blit\b\":                     \"shadowed\","""

# Find the color_killers dict and insert new entries after streetlight line
# Use a regex to find the block
pattern = r'(r"\\bstreetlight\(\?:s\)\?\\b":\s+"darkness at end of alley",\n)'

new_entries = (
    r'        r"\blight(?:s|ed|ing|post|house)?\b":    "dark void",' + '\n'
    r'        r"\bpole(?:s)?\b":                       "rusted drainpipe",' + '\n'
    r'        r"\bpost(?:s)?\b":                       "stone wall",' + '\n'
    r'        r"\bbeam(?:s)?\b":                       "darkness",' + '\n'
    r'        r"\bflicker(?:s|ed|ing)?\b":             "darkness",' + '\n'
)

# Find position of the streetlight line and insert after it
idx = content.find(r'r"\bstreetlight(?:s)?\b":       "darkness at end of alley",')
if idx == -1:
    print("ERROR: could not find streetlight line")
else:
    end_of_line = content.find('\n', idx) + 1
    patched = content[:end_of_line] + new_entries + content[end_of_line:]
    open(path, 'w', encoding='utf-8').write(patched)
    print("PATCHED: added light/pole/post/beam/flicker to color_killers")
    # verify
    if r'"dark void"' in patched:
        print("VERIFIED: new entries present")
