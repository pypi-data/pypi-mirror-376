# -*- coding: utf-8 -*-

from io import StringIO
from subprocess import call
from os.path import basename, splitext
import os
import shutil
import sys
import traceback

from DisplayCAL.meta import name
from DisplayCAL.util_os import relpath, safe_glob, which

recordfile_name = "INSTALLED_FILES"

if sys.stdout and hasattr(sys.stdout, "isatty") and not sys.stdout.isatty():
    sys.stdout = StringIO()

if sys.platform == "win32":
    try:
        create_shortcut
    # this function is only available within bdist_wininst installers
    except NameError:
        try:
            from pythoncom import (
                CoCreateInstance,
                CLSCTX_INPROC_SERVER,
                IID_IPersistFile,
            )
            from win32com.shell import shell
            import win32con
        except ImportError:

            def create_shortcut(*args):
                pass

        else:

            def create_shortcut(*args):
                shortcut = CoCreateInstance(
                    shell.CLSID_ShellLink,
                    None,
                    CLSCTX_INPROC_SERVER,
                    shell.IID_IShellLink,
                )
                shortcut.SetPath(args[0])
                shortcut.SetDescription(args[1])
                if len(args) > 3:
                    shortcut.SetArguments(args[3])
                if len(args) > 4:
                    shortcut.SetWorkingDirectory(args[4])
                if len(args) > 5:
                    shortcut.SetIconLocation(args[5], args[6] if len(args) > 6 else 0)
                shortcut.SetShowCmd(win32con.SW_SHOWNORMAL)
                shortcut.QueryInterface(IID_IPersistFile).Save(args[2], 0)

    try:
        directory_created
    # this function is only available within bdist_wininst installers
    except NameError:

        def directory_created(path):
            pass

    try:
        file_created
    # this function is only available within bdist_wininst installers
    except NameError:
        try:
            import win32api
        except ImportError:

            def file_created(path):
                pass

        else:

            def file_created(path):
                if os.path.exists(recordfile_name):
                    installed_files = []
                    if os.path.exists(recordfile_name):
                        recordfile = open(recordfile_name, "r")
                        installed_files.extend(line.rstrip("\n") for line in recordfile)
                        recordfile.close()
                    try:
                        path.encode("ASCII")
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        # the contents of the record file used by distutils
                        # must be ASCII GetShortPathName allows us to avoid
                        # any issues with encoding because it returns the
                        # short path as 7-bit string (while still being a
                        # valid path)
                        path = win32api.GetShortPathName(path)
                    installed_files.append(path)
                    recordfile = open(recordfile_name, "w")
                    recordfile.write("\n".join(installed_files))
                    recordfile.close()

    try:
        get_special_folder_path
    # this function is only available within bdist_wininst installers
    except NameError:
        try:
            from win32com.shell import shell, shellcon
        except ImportError:

            def get_special_folder_path(csidl_string):
                pass

        else:

            def get_special_folder_path(csidl_string):
                return shell.SHGetSpecialFolderPath(
                    0, getattr(shellcon, csidl_string), 1
                )


def postinstall_macos(prefix=None):
    """Do postinstall actions for macOS."""
    # TODO: implement
    pass


def postinstall_windows(prefix):
    """Do postinstall actions for Windows."""
    if prefix is None:
        # assume we are running from bdist_wininst installer
        modpath = os.path.dirname(os.path.abspath(__file__))
    else:
        # assume we are running from source dir,
        # or from install dir
        modpath = prefix

    if not os.path.exists(modpath):
        print("warning - '{}' not found".format(modpath.encode("MBCS", "replace")))
        return

    if os.path.exists(recordfile_name):
        irecordfile_name = os.path.join(modpath, "INSTALLED_FILES")
        with open(irecordfile_name, "w"):  # touch create the file
            pass
        file_created(irecordfile_name)
        shutil.copy2(recordfile_name, irecordfile_name)

    mainicon = os.path.join(modpath, "theme", "icons", f"{name}.ico")
    if not os.path.exists(mainicon):
        print("warning - '{}' not found".format(icon.encode("MBCS", "replace")))
        return

    try:
        startmenu_programs_common = get_special_folder_path("CSIDL_COMMON_PROGRAMS")
        startmenu_programs = get_special_folder_path("CSIDL_PROGRAMS")
        startmenu_common = get_special_folder_path("CSIDL_COMMON_STARTMENU")
        startmenu = get_special_folder_path("CSIDL_STARTMENU")
    except OSError:
        traceback.print_exc()
        return

    filenames = [
        filename
        for filename in safe_glob(os.path.join(sys.prefix, "Scripts", f"{name}*"))
        if not filename.endswith("-script.py")
        and not filename.endswith("-script.pyw")
        and not filename.endswith(".manifest")
        and not filename.endswith(".pyc")
        and not filename.endswith(".pyo")
        and not filename.endswith("_postinstall.py")
    ] + ["LICENSE.txt", "README.html", "Uninstall"]
    installed_shortcuts = []
    for path in (startmenu_programs_common, startmenu_programs):
        if not path:
            continue
        grppath = os.path.join(path, name)
        if path == startmenu_programs:
            group = relpath(grppath, startmenu)
        else:
            group = relpath(grppath, startmenu_common)

        if not os.path.exists(grppath):
            try:
                os.makedirs(grppath)
            except Exception:
                # maybe insufficient privileges?
                pass

        if os.path.exists(grppath):
            print(
                ("Created start menu group '{}' in {}").format(
                    name,
                    (
                        str(path, "MBCS", "replace") if not isinstance(path, str) else path
                    ).encode("MBCS", "replace"),
                )
            )
        else:
            print(
                ("Failed to create start menu group '{}' in {}").format(
                    name,
                    (
                        str(path, "MBCS", "replace") if not isinstance(path, str) else path
                    ).encode("MBCS", "replace"),
                )
            )
            continue
        directory_created(grppath)
        for filename in filenames:
            lnkname = splitext(basename(filename))[0]
            lnkpath = os.path.join(grppath, f"{lnkname}.lnk")
            if os.path.exists(lnkpath):
                try:
                    os.remove(lnkpath)
                except Exception:
                    # maybe insufficient privileges?
                    print(
                        ("Failed to create start menu entry '{}' in {}").format(
                            lnkname,
                            (
                                str(grppath, "MBCS", "replace")
                                if not isinstance(grppath, str)
                                else grppath
                            ).encode("MBCS", "replace"),
                        )
                    )
                    continue
            if not os.path.exists(lnkpath):
                if lnkname != "Uninstall":
                    tgtpath = os.path.join(modpath, filename)
                try:
                    if lnkname == "Uninstall":
                        uninstaller = os.path.join(sys.prefix, f"Remove{name}.exe")
                        if os.path.exists(uninstaller):
                            create_shortcut(
                                uninstaller,
                                lnkname,
                                lnkpath,
                                '-u "{}-wininst.log"'.format(
                                    os.path.join(sys.prefix, name)
                                ),
                                sys.prefix,
                                os.path.join(
                                    modpath,
                                    "theme",
                                    "icons",
                                    f"{name}-uninstall.ico",
                                ),
                            )
                        else:
                            # When running from a
                            # bdist_wininst or bdist_msi
                            # installer, sys.executable
                            # points to the installer
                            # executable, not python.exe
                            create_shortcut(
                                os.path.join(sys.prefix, "python.exe"),
                                lnkname,
                                lnkpath,
                                '"{}" uninstall --record="{}"'.format(
                                    os.path.join(modpath, "setup.py"),
                                    os.path.join(modpath, "INSTALLED_FILES"),
                                ),
                                sys.prefix,
                                os.path.join(
                                    modpath,
                                    "theme",
                                    "icons",
                                    f"{name}-uninstall.ico",
                                ),
                            )
                    elif lnkname.startswith(name):
                        # When running from a
                        # bdist_wininst or bdist_msi
                        # installer, sys.executable
                        # points to the installer
                        # executable, not python.exe
                        icon = os.path.join(
                            modpath,
                            "theme",
                            "icons",
                            f"{lnkname}.ico",
                        )
                        icon = mainicon if not os.path.isfile(icon) else icon
                        if filename.endswith(".exe"):
                            exe = filename
                            args = ""
                        else:
                            exe = os.path.join(sys.prefix, "pythonw.exe")
                            args = f'"{tgtpath}"'
                        create_shortcut(
                            exe,
                            lnkname,
                            lnkpath,
                            args,
                            modpath,
                            icon,
                        )
                    else:
                        create_shortcut(tgtpath, lnkname, lnkpath, "", modpath)
                except Exception:
                    # maybe insufficient privileges?
                    print(
                        ("Failed to create start menu entry '{}' in {}").format(
                            lnkname,
                            (
                                str(grppath, "MBCS", "replace")
                                if not isinstance(grppath, str)
                                else grppath
                            ).encode("MBCS", "replace"),
                        )
                    )
                    continue
                print(
                    ("Installed start menu entry '{}' to {}").format(
                        lnkname,
                        (
                            str(group, "MBCS", "replace")
                            if not isinstance(group, str)
                            else group
                        ).encode("MBCS", "replace"),
                    )
                )
            file_created(lnkpath)
            installed_shortcuts.append(filename)
        if installed_shortcuts == filenames:
            break


def postinstall_linux(prefix=None):
    """Do postinstall actions for Linux."""
    # Linux/Unix
    if prefix is None:
        prefix = sys.prefix
    if which("touch"):
        call(["touch", "--no-create", f"{prefix}/share/icons/hicolor"])
    if which("xdg-icon-resource"):
        # print("installing icon resources...")
        # for size in [16, 22, 24, 32, 48, 256]:
        # call([
        #     "xdg-icon-resource",
        #     "install",
        #     "--noupdate",
        #     "--novendor",
        #     "--size",
        #     str(size),
        #     f"{prefix}/share/{name}/theme/icons/{size}x{size}/{name}.png"
        # ])
        call(["xdg-icon-resource", "forceupdate"])
    if which("xdg-desktop-menu"):
        # print("installing desktop menu entry...")
        # call([
        #     "xdg-desktop-menu",
        #     "install",
        #     "--novendor",
        #     f"{prefix}/share/{name}/{name}.desktop"
        # ])
        call(["xdg-desktop-menu", "forceupdate"])


def postinstall(prefix=None):
    if sys.platform == "darwin":
        postinstall_macos()
    elif sys.platform == "win32":
        postinstall_windows(prefix)
    else:
        postinstall_linux(prefix)


def postuninstall(prefix=None):
    if sys.platform == "darwin":
        # TODO: implement
        pass
    elif sys.platform == "win32":
        # nothing to do
        pass
    else:
        # Linux/Unix
        if prefix is None:
            prefix = sys.prefix
        if which("xdg-desktop-menu"):
            # print("uninstalling desktop menu entry...")
            # call(["xdg-desktop-menu", "uninstall", prefix +
            # (f"/share/applications/{name}.desktop")])
            call(["xdg-desktop-menu", "forceupdate"])
        if which("xdg-icon-resource"):
            # print("uninstalling icon resources...")
            # for size in [16, 22, 24, 32, 48, 256]:
            # call(["xdg-icon-resource", "uninstall", "--noupdate", "--size",
            # str(size), name])
            call(["xdg-icon-resource", "forceupdate"])


def main():
    prefix = None
    for arg in sys.argv[1:]:
        arg = arg.split("=")
        if len(arg) == 2:
            if arg[0] == "--prefix":
                prefix = arg[1]
    try:
        if "-remove" in sys.argv[1:]:
            postuninstall(prefix)
        else:
            postinstall(prefix)
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
