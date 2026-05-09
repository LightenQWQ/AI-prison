#!/usr/bin/env python3
"""Patch: add manga/comic/panel to color_killers"""
path = '/workspace/Just_A_Suggestion_v2/main.py'
content = open(path, encoding='utf-8').read()

# Find the flicker line and insert after it
target = 'r"\\bflicker(?:s|ed|ing)?\\b":             "darkness",'
if target not in content:
    # try with different spacing
    import re
    m = re.search(r'r"\\bflicker\(\?:s\|ed\|ing\)\?\\b":\s+"darkness",', content)
    if m:
        target = m.group(0)
        print(f"Found with spacing: {repr(target)}")
    else:
        print("ERROR: flicker line not found")
        print(repr(content[content.find('flicker'):content.find('flicker')+100]))
        exit(1)

new_entries = '''
        # 漫畫/面板觸發詞 — 防止Imagen生成漫畫面板白邊
        r"\\bcomic(?:s)?\\b":                       "noir ink illustration",
        r"\\bmanga\\b":                              "noir ink illustration",
        r"\\bpanel(?:s)?\\b":                        "scene",
        r"\\bhalftone\\b":                           "crosshatch",'''

replacement = target + new_entries
content = content.replace(target, replacement, 1)
open(path, 'w', encoding='utf-8').write(content)
print("PATCHED: manga/comic/panel added to color_killers")
if '"noir ink illustration"' in content:
    print("VERIFIED: new entries present")
