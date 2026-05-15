import os
import PyPDF2

pdf_path = os.path.join(os.path.expanduser("~"), "Desktop", "《只是一個建議》基於生成式人工智慧之互動解謎遊戲創作研究.pdf")

def extract_text():
    if not os.path.exists(pdf_path):
        # Try finding it if encoding is weird
        import glob
        matches = glob.glob(os.path.join(os.path.expanduser("~"), "Desktop", "*.pdf"))
        for m in matches:
            if "只是一個建議" in m or "Ch Ч" in m: # Heuristic for encoded name
                return m
        return None

actual_path = pdf_path if os.path.exists(pdf_path) else extract_text()

if actual_path:
    try:
        with open(actual_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            full_text = ""
            # Just get the first 10 pages for context
            for i in range(min(len(reader.pages), 10)):
                full_text += f"--- Page {i+1} ---\n"
                full_text += reader.pages[i].extract_text() + "\n"
            
            with open("paper_context.txt", "w", encoding="utf-8") as out:
                out.write(full_text)
            print(f"SUCCESS: Extracted {len(full_text)} characters.")
    except Exception as e:
        print(f"ERROR: {e}")
else:
    print("ERROR: File not found.")
