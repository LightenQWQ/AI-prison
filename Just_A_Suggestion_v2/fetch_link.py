import urllib.request
url = "https://kenkenbgm.blogspot.com/2023/11/bgmbgmroyalty-free-music315.html"
html = urllib.request.urlopen(url).read().decode('utf-8')
idx = html.find('Google+Drive.png')
if idx != -1:
    start_a = html.rfind('<a', 0, idx)
    end_a = html.find('>', start_a)
    tag = html[start_a:end_a+1]
    import re
    m = re.search(r'href=[\'"]?([^\'" >]+)', tag)
    if m:
        print("Found Link:", m.group(1))
    else:
        print("href not found in tag:", tag)
else:
    print("Not found.")
