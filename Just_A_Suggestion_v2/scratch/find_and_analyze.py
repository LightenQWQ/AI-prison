import os
import glob
from docx import Document

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
matches = glob.glob(os.path.join(desktop, "*只是一個建議*複製*.docx"))

if matches:
    path = matches[0]
    print(f"FOUND: {path}")
    doc = Document(path)
    # 提取前 50 個有意義的段落
    content = ""
    for p in doc.paragraphs:
        if p.text.strip():
            content += p.text + "\n"
        if len(content) > 5000: break # 抓取足夠的內容來分析
    
    with open("raw_content_analysis.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Analyzed context saved to raw_content_analysis.txt")
else:
    print("ERROR: Still cannot find the file.")
