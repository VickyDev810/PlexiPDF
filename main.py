import sys
from PySide6.QtWidgets import QApplication
from editor_gui import PDFEditor

def main():
    app = QApplication(sys.argv)
    editor = PDFEditor()
    editor.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
