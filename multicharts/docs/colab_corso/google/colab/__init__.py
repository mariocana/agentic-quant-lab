"""Finto google.colab: files.upload() restituisce i file passati a run_colab.py."""
import os


class files:
    @staticmethod
    def upload():
        return {f: open(f, 'rb').read() for f in os.environ['MC_FILES'].split(',')}
