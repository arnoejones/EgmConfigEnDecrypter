import os
import shutil
import PySimpleGUI as sg
import subprocess
import webbrowser

def copytree(src, dst, symlinks=False, ignore=None):
    try:
        (drive, path) = os.path.splitdrive(src)
        (path, file) = os.path.split(path)

        dst = os.path.join(dst, file)

        if not os.path.exists(dst):
            os.makedirs(dst)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                copytree(s, d, symlinks, ignore)
            else:
                # unremark if you *don't want to overwrite.
                if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime <= 1:
                    shutil.copy2(s, d)

        print('Copy successful')
        return True, dst, file
    except Exception as ex:
        sg.Popup("Invalid path selected. ", ex)
        return False, None, None


def copytreeback(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    # if ignore is not None:
    #     ignored_names = ignore(src, names)
    # else:
    #     ignored_names = set()

    if not os.path.isdir(dst): # This one line does the trick
        os.makedirs(dst)
    errors = []
    for name in names:
        # if name in ignored_names:
        #     continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytreeback(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                shutil.copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)

layout = [
    [sg.Submit('Help')],
    [sg.Text('Path to ConfigurationTool: ', size=(35, 1)),
     sg.Input(r'D:\ConfigurationTool', key='_CONFIGTOOL_', do_not_clear=True), sg.FolderBrowse()],
    [sg.Text('Path to EGM configuration files directory: ', size=(35, 1)),
     sg.Input(r'H:\myConfigFileTest', key='_CONFIGFILES_', do_not_clear=True), sg.FolderBrowse()],
    [sg.Text('', key='_SDF_', font=("Helvetica", 20), text_color='green', size=(20, 1))],
    [sg.Text('', key='_SDF2_', font=("Helvetica", 14), text_color='green', size=(30, 1))],

    [sg.Submit('Decrypt Config File'), sg.Submit('Encrypt xml file')],

    [sg.Exit()]
]

window = sg.Window('EGM Config File Encrypter/Decrypter').Layout(layout)

while True:
    event, values = window.Read()

    if event is None or event == 'Exit':
        break

    tool_location = values['_CONFIGTOOL_']
    files_dir = values['_CONFIGFILES_']

    if event == 'Decrypt Config File':
        # check that tool_location even contains ConfigurationTool.exe
        if os.path.isdir(tool_location):
            if os.path.exists(os.path.join(tool_location, 'ConfigurationTool.exe')):
            # if any(File.endswith("ConfigurationTool.exe") for File in os.listdir(tool_location)):
                # 1st, copy the configuration files to the ConfigurationTools directory
                (success, destination, file) = copytree(src=files_dir, dst=tool_location)
                if success and destination is not None and file is not None:
                    # 2nd, decrypt those files into the xml file
                    for filename in os.listdir(destination):
                        if filename.endswith('encrypted'):
                            if not (filename.endswith('p.encrypted')):
                                print(filename)
                                if os.getcwd() is not tool_location:
                                    os.chdir(tool_location)
                                    subprocess.Popen(tool_location + "\\ConfigurationTool.exe --decrypt " + os.path.join(file, filename))
                                    window.FindElement('_SDF_').Update('Decryption Successful!')
                                    window.FindElement('_SDF2_').Update('')
            else:
                sg.Popup("ConfigurationTool.exe not found in ", tool_location)
        else:
            sg.Popup("Invalid location of ConfigurationTool.exe.")

    if event == 'Encrypt xml file':
        if os.path.exists(os.path.join(tool_location, 'ConfigurationTool.exe')):
            (drive, path) = os.path.splitdrive(files_dir)
            (path, file) = os.path.split(path)

            destination = os.path.join(tool_location, file)

            if os.getcwd() is not destination:
                os.chdir(destination)
                if len(os.listdir(destination)) == 0:
                    sg.Popup("Wrong directory or no files found to encrypt.\nPlease double-check\n  " + destination + "\nfor decrypted files.")
                for filename in os.listdir(destination):
                    if filename.endswith('xml'):
                        os.chdir(tool_location)
                        try:
                            subprocess.Popen(
                                tool_location + "\\ConfigurationTool.exe --encrypt " + os.path.join(file, filename))
                            #  at this point, there should be a new whatever.encrypted and whatever.security updated.
                            window.FindElement('_SDF_').Update('Encryption Successful!')
                            window.FindElement('_SDF2_').Update('You may now eject USB drive.')
                            # now copy the contents to USB drive:\
                            # todo figure out why I need to do this twice >8-(
                            copytreeback(destination, files_dir)
                            copytreeback(destination, files_dir)

                        except:
                            sg.Popup('Something is wrong; encryption failed.')
        else:
            sg.Popup("Invalid location of ConfigurationTool.exe.")

    if event == 'Help':
        print('help file goes here.')
        webbrowser.open('file://engfile6\Transfer\PublicDrop\Arno\ConfigToolUIHelp/configtooluihelp.html')
window.Close()
