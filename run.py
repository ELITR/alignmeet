import os
import sys
import struct
from sys import argv

if os.name == 'nt':
    import PySide2

    dirname = os.path.dirname(PySide2.__file__)
    plugin_path = os.path.join(dirname, 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PySide2.QtCore import Qt, QCoreApplication
from settings import Settings

QCoreApplication.setOrganizationName("UFAL")
QCoreApplication.setOrganizationDomain("ufal.ms.mff.cuni.cz")
QCoreApplication.setApplicationName("Annotations")

if os.name == 'nt':
    arch = struct.calcsize('P') * 8
    
    if arch == 64 and os.path.exists("""C:\Program Files\VideoLAN\VLC"""):
        os.environ['PYTHON_VLC_MODULE_PATH'] = """C:\Program Files\VideoLAN\VLC"""
    elif arch == 32 and os.path.exists("""C:\Program Files (x86)\VideoLAN\VLC"""):
        os.environ['PYTHON_VLC_MODULE_PATH'] = """C:\Program Files (x86)\VideoLAN\VLC"""
    else:
        os.environ['PYTHON_VLC_MODULE_PATH'] = """program/vlc-3.0.9.2"""

from PySide2.QtWidgets import QApplication
from annotations import Annotations

def main():

    app = QApplication(sys.argv)
    app.setStyle("Fusion")    


    Settings.apply_settings()
    a = Annotations()
    a.show()

    exit(app.exec_())

if __name__ == '__main__':
    main()
