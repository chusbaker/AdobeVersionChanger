#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created in 2019
@author: chusbaker
@site: https://github.com/chusbaker
@email: chusbaker@gmail.com
@file:
@description:
Drag and drop a Premiere Pro Project file into the main window and it will downgrade the version of the project
so it can be oppened with previous versions of Adobe Premiere Pro. It also takes Motion Graphics files
(.mogrt extension files) and downgrades also downgrades the version of the Motion Graphics file so it can be imported
to previous versions of Adobe Premiere Pro


THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

import os
import gzip
import zipfile
import shutil
import sys
import xml.etree.ElementTree as et
from PySide2.QtWidgets import (QApplication, QLabel, QToolTip, QDesktopWidget,\
                               QWidget, QGridLayout, QProgressBar)
from PySide2.QtGui import QFont, QIcon
from PySide2.QtCore import QPropertyAnimation
import json

__Author__ = 'chusbaker'
__Copyright__ = 'Copyright (c) 2019 chusbaker'
__Version__ = 1.0


class Window(QWidget):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.resize(400, 200)
        self._value = 0

        self.setWindowTitle('Adobe Version Changer')
        self.setWindowIcon(QIcon('version_changer.jpg'))
        self.progressbar = QProgressBar(self)
        self.progressbar.setRange(0, 99)

        self.widget = QWidget(self)
        self.layout = QGridLayout(self.widget)
        self.label = QLabel('|  Drop your file here  |')

        self.layout.addWidget(self.label, 1, 23, 30, 10)
        self.layout.addWidget(self.progressbar, 2, 0, 1, 58)

        QToolTip.setFont(QFont('Helvetica', 20))
        self.setToolTip(
            '''Drag and Drop into this window a <b>Premiere Project File or Motion Graphics File</b> 
            to be converted. You will find a file named as the Project or Motion Graphic file with 
            the extension <b>"_changed"</b> in that same location.'''
                        )
        self.setAcceptDrops(True)

        
    def progressStart(self):
        animation = QPropertyAnimation(self.progressbar, b'value', self)
        x = int(os.stat(self.userInput).st_size) / 40
        # print(x)
        animation.setDuration(x)
        animation.setLoopCount(1)
        animation.setKeyValueAt(0, self.progressbar.minimum())
        animation.setKeyValueAt(0.1, 10)
        animation.setKeyValueAt(0.2, 30)
        animation.setKeyValueAt(0.5, 60)
        animation.setKeyValueAt(0.7, 80)
        animation.setKeyValueAt(1, self.progressbar.maximum())
        animation.start(animation.DeleteWhenStopped)


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

            
    def dropEvent(self, e):
        for url in e.mimeData().urls():
            self.userInput = url.toLocalFile()

            func(self.userInput)
            self.progressStart()

            self.label.setText("| Another file? |") # repeat
        return self.userInput


    def startprogressBar(self):
        self.progressBar.setVisible(True)
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(100, self)


def gunzip_shutil(source_filepath, dest_filepath, block_size=65536):
    with gzip.open(source_filepath, 'rb') as s_file, \
            open(dest_filepath, 'wb') as d_file:
        shutil.copyfileobj(s_file, d_file, block_size)
        

def convertPP(userInput):
    # file and path separation
    # print("value of userInput is: ", userInput)
    # convert the string to a path
    f = userInput
    file2convert = f.split("/")[-1]                # takes the file name with extension
    # print("file2 convert: ", file2convert)
    file2comvert_name = file2convert.split(".")[0]  # remove extension
    # file2convert_ext = file2convert.split(".")[1]   # store the extension only
    path2file = os.path.dirname(os.path.abspath(f)) # takes the path to the file

    # _____ convertion begins____
    # step 1: create a new folder and copy the file to the folder renamed with sufix "_changed"
    # build the path
    path_1 = (path2file, file2comvert_name)         # the new directory is path + file name
    path_2 = "\\".join(path_1)                      # done
    path_3 = (path_2, "changed")                    # add the underscore "change" sufix to path
    new_dir = "_".join(path_3)                      # done

    xml2change_list = (new_dir, file2comvert_name)  # xml to convert
    xml2change = "\\".join(xml2change_list)         # name of xml file compressed

    # create folder
    os.makedirs(new_dir)
    # build the new file name
    new_name = (file2comvert_name, "changed")       # create name of new file with no extension just add sufix "_changed"
    new_file_name = "_".join(new_name)              # done - apply to the new xml name and new project name
    full_path = (new_dir, new_file_name)            # take the full path to the new files
    full_file_path = "\\".join(full_path)           # done - apply to the new xml name and new project name
    full_xml_path = full_file_path + ".xml"         # add ext .xml to the path. This is the xml file to be changed

    # copy file
    shutil.copy(f, xml2change)

    # step 2: unzip gz file to a xml file
    gunzip_shutil(xml2change, full_xml_path)            # extract the xml file to the directory to be changed

    # # step 3: change the version number
    with open(full_xml_path, encoding='UTF-8') as f:
        tree = et.parse(f)
        xml_file = tree.getroot()

    version = xml_file.find("./Project[@Version]")
    version.attrib["Version"] = '36'
    # save the changes
    tree.write(full_xml_path)

    # # step 4: compress the file to a gz and rename to a premiere project
    fin = full_xml_path
    fout = full_file_path + ".prproj"
    with open(fin, 'rb') as f_in, gzip.open(fout, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    label6 = QLabel("Succesfully, PREMIERE PROJECT VERSION 36 CREATED.")
    label6.move(120, 110)
    # cleaning files
    os.remove(xml2change)
    os.remove(full_xml_path)

def convertMG(userInput):
    # file and path separation
    # print("value of userInput is: ", userInput)
    # convert the string to a path
    f = userInput
    file2convert = f.split("/")[-1]                # takes the file name with extension
    # print("file2 convert: ", file2convert)
    file2comvert_name = file2convert.split(".")[0]  # remove extension
    # file2convert_ext = file2convert.split(".")[1]   # store the extension only
    path2file = os.path.dirname(os.path.abspath(f)) # takes the path to the file


    # _____ convertion begins____
    # step 1: create a new folder and copy the file to the folder renamed with sufix "_changed"
    # build the path
    path_1 = (path2file, file2comvert_name)         # the new directory is path + file name
    path_2 = "\\".join(path_1)                      # done
    path_3 = (path_2, "changed")                    # add the underscore "change" sufix to path
    new_dir = "_".join(path_3)                      # done

    with zipfile.ZipFile(userInput,"r") as zip_ref:
        zip_ref.extractall(new_dir)
    file2change = new_dir + "\\definition.json"

    with open(file2change, "r", encoding="utf8") as f:
        content = f.read()
        c = json.loads(content.replace('\r\n', ''))
        c['apiVersion'] = "1.4"
    os.remove(file2change)

    with open(file2change, 'w') as f:
            f.write(json.dumps(c))

    # # step 4: compress the file to a gz and rename to a motion project file
    new_extension = '.mogrt'
    shutil.make_archive(new_dir, 'zip', new_dir)  # (name of file to zip, ext, base dir, dir where the files to zip are)

    # change extension
    new_dir_zip = new_dir + '.zip'
    pre, ext = os.path.splitext(new_dir_zip)
    os.rename(new_dir_zip, pre + new_extension)
    shutil.rmtree(new_dir, ignore_errors=True) # delete folder

def func(userInput):
    # check if userInput has the extension .prproj
    check = userInput
    # print(userInput)
    if check.endswith('.prproj'):
        # "Successfully received the file, now creating the changed version of the file"
        convertPP(check)
    elif check.endswith('.mogrt'):
        # "Successfully received the file, now creating the changed version of the file"
        convertMG(check)
    else:
        print("Try Again!")
        # "That file was not an Adobe Premiere Project or Motion Graphics, try again"
    return check


if __name__ == '__main__':

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec_())
