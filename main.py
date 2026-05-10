import sys
import warnings
from PyQt6.QtWidgets import QApplication
from src.gui import App

warnings.filterwarnings("ignore", category=DeprecationWarning)

app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec())
