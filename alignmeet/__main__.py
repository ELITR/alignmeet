import os
import sys
import struct
import math, argparse
from .autoalign import Aligner, Embedder
from .annotation import *

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

TR = 0
MIN = 1

def main():
    def embed(filename, type):
        if type == TR:
            a.open_transcript(filename)
        elif type == MIN:
            a.open_minutes(filename)
        else:
            assert False
        embeds = e.embed(a._das if type == TR else a._minutes)
        return embeds
    
    parser = argparse.ArgumentParser(prog='Alignmeet', description="Annotation Tool for Meeting Minuting", epilog="Or run without arguments for annotation GUI.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-et', dest='et', metavar='Filename', type=str, nargs='+', help='Generate embeddings for given transcripts.')
    group.add_argument('-em', dest='em', metavar='Filename', type=str, nargs='+', help='Generate embeddings for given minutes files.')
    group.add_argument('-a', '--align', dest='a', metavar=('Minutes_Embed', 'Transcript_Embed'), type=str, nargs=2, help='Generate alignment based on given file embeddings.')
    parser.add_argument('--thr', type=float, help="Threshold for alignment (0.0 to 1.0).", required=False, default=0.5)
    parser.add_argument('-nf', '--not-final', dest='final', action='store_false' , help="Store alignment as tentative (to be confirmed by hand in GUI).")
    args=parser.parse_args()
    
    if args.et:
        print("Preparing embedder...")
        e = Embedder()
        a = Annotation(False)
        a.set_path('.') #TODO: make sure this actually works lmao, will need to implement abs. paths
        for file in args.et:
            print(f"Embedding {file}...")
            Embedder.saveEmbed(embed(file, TR), file + '.embed')
    elif args.em:
        print("Preparing embedder...")
        e = Embedder()
        a = Annotation(False)
        a.set_path('.')
        for file in args.em:
            print(f"Embedding {file}...")
            Embedder.saveEmbed(embed(file, MIN), file + '.embed')
    elif args.a:
        print(f"Loading {args.a[0]}...")
        trems = Embedder.loadEmbed(args.a[0])
        print(f"Loading {args.a[1]}...")
        minems = Embedder.loadEmbed(args.a[1])
        print("Aligning...")
        alignments = Aligner.align(trems, minems, args.thr)
        tr_name = os.path.basename(args.a[0])
        if str.endswith(tr_name, '.embed'):
            tr_name = tr_name[:-6]
        min_name = os.path.basename(args.a[1])
        if str.endswith(min_name, '.embed'):
            min_name = min_name[:-6]
        al_path = os.path.join(os.path.dirname(args.a[0]), f"alignment+{tr_name}+{min_name}")
        print(f"Saving alignment in {al_path}...")
        with open(al_path, 'w') as f:
            for i, alignment in enumerate(alignments):
                if alignment > 0:
                    if args.final:
                        f.write(f"{i+1} {math.floor(alignment)} None\n")
                    else:
                        f.write(f"{i+1} {math.floor(alignment)}? None\n")
        #TODO ask if overwrite (event. add -y switch)
    else:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")    


        Settings.apply_settings()
        a = Annotations()
        a.show()

        exit(app.exec_())

if __name__ == '__main__':
    main()
