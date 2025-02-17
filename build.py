# build.py
import subprocess
import os
import shutil

def clean_dist():
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')

def build():
    clean_dist()
    subprocess.run(['pyinstaller', 'build.spec'], check=True)
    shutil.copy('config.ini', 'dist/config.ini')

if __name__ == '__main__':
    build()