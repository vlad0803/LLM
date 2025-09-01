<<<<<<< HEAD
import os


def get_summary_by_title(title: str, file_path: str = None) -> str:
    """Find the exact title in the local file and return its full summary."""
    if file_path is None:
        # Caută fișierul în root față de backend
        backend_path = os.path.join(os.path.dirname(__file__), "book_summaries.txt")
        if os.path.exists(backend_path):
            file_path = backend_path
        else:
            raise FileNotFoundError(f"book_summaries.txt not found in root: {root_path}")
    # Citire explicită cu encoding UTF-8 pentru a evita caracterele speciale
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    collecting = False
    summary_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Title:"):
            found_title = stripped.replace("## Title:", "").strip()
            if found_title == title:
                collecting = True
                summary_lines = []
            else:
                collecting = False
        elif collecting:
            if stripped.startswith("## Title:"):
                break
            if stripped:
                summary_lines.append(stripped)

    if summary_lines:
        return "\n".join(summary_lines)
    else:
        return f"❌ Summary not found for title: {title}"
=======
import os


def get_summary_by_title(title: str, file_path: str = None) -> str:
    """Find the exact title in the local file and return its full summary."""
    if file_path is None:
        # Caută fișierul în root față de backend
        backend_path = os.path.join(os.path.dirname(__file__), "book_summaries.txt")
        if os.path.exists(backend_path):
            file_path = backend_path
        else:
            raise FileNotFoundError(f"book_summaries.txt not found in root: {root_path}")
    # Citire explicită cu encoding UTF-8 pentru a evita caracterele speciale
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    collecting = False
    summary_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Title:"):
            found_title = stripped.replace("## Title:", "").strip()
            if found_title == title:
                collecting = True
                summary_lines = []
            else:
                collecting = False
        elif collecting:
            if stripped.startswith("## Title:"):
                break
            if stripped:
                summary_lines.append(stripped)

    if summary_lines:
        return "\n".join(summary_lines)
    else:
        return f"❌ Summary not found for title: {title}"
>>>>>>> 0e35a9f7b2f106794b9685bdb81ce13b8126b6bb
