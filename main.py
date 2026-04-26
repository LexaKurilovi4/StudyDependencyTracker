import sys
from PyQt6.QtWidgets import QApplication
from gui import App


def main() -> None:
    """Точка входа в приложение PyQt6."""
    app: QApplication = QApplication(sys.argv)
    app.setStyle("Fusion")

    window: App = App()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()