# Plexi PDF Editor 🧾⚡

A lightweight, blazing-fast desktop PDF editor built with Python and Qt.  
No subscriptions. No watermarks. Just edit your damn PDF.

---

## ✨ Features

- 📄 Open and view any PDF
- 🖊️ Edit **form fields** (AcroForms)
- 🧷 Add **permanent text** anywhere on the page
- 💾 Save modified PDFs with your changes

---

## 🛠 Requirements

- Python 3.10 or higher
- `PyMuPDF` (for PDF handling)
- `PySide6` (for GUI)

Install dependencies:

```bash
pip install -r requirements.txt
````

---

## 🚀 Usage

Clone the repo and run the editor:

```bash
git clone git@github.com:VickyDev810/PlexiPDF.git
cd PlexiPDF
python main.py
```

---

## 📋 Keyboard & UI Flow

| Action            | How                               |
| ----------------- | --------------------------------- |
| Open PDF          | File → Open                       |
| Navigate pages    | Prev / Next / Page Spinner        |
| Edit form fields  | Toolbar → "Edit Form Fields"      |
| Add text anywhere | Toolbar → "Add Text" (then click) |
| Save PDF          | File → Save As                    |

---

## 📂 Project Structure

```
PlexiPDF/
├── main.py           # Entry point
├── pdf_engine.py     # PDF handling logic (PyMuPDF)
└── editor_gui.py     # Qt GUI with all functionality
```

---

## 🧠 Roadmap / Ideas

* [ ] Add undo support
* [ ] Customize font, size, and color for inserted text
* [ ] Export flattened PDFs
* [ ] Form field creation

---

## 👨‍💻 Author

Built by [Veer Vikram Singh](#) – because we don’t pay monthly to edit a damn PDF.

---

## ⚖️ License

MIT License – do what you want, just don’t make it worse.


