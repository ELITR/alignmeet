import os
import sys
import struct

if os.name == 'nt':
    import PySide2

    dirname = os.path.dirname(PySide2.__file__)
    plugin_path = os.path.join(dirname, 'plugins', 'platforms')
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QApplication


QCoreApplication.setOrganizationName("UFAL")
QCoreApplication.setOrganizationDomain("ufal.ms.mff.cuni.cz")
QCoreApplication.setApplicationName("Alignmeet")

if os.name == 'nt':
    arch = struct.calcsize('P') * 8
    
    if arch == 64 and os.path.exists("""C:\Program Files\VideoLAN\VLC"""):
        os.environ['PYTHON_VLC_MODULE_PATH'] = """C:\Program Files\VideoLAN\VLC"""
    elif arch == 32 and os.path.exists("""C:\Program Files (x86)\VideoLAN\VLC"""):
        os.environ['PYTHON_VLC_MODULE_PATH'] = """C:\Program Files (x86)\VideoLAN\VLC"""
    else:
        os.environ['PYTHON_VLC_MODULE_PATH'] = """program/vlc-3.0.9.2"""

from .annotations import Annotations
from .settings import Settings

def main():

    app = QApplication(sys.argv)
    app.setStyle("Fusion")    


    Settings.apply_settings()
    a = Annotations()
    a.show()

    exit(app.exec_())

if __name__ == '__main__':
    main()
