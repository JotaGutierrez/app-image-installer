#!/usr/bin/python3

import argparse
import os
import stat
import sys
import json

GNOME_LAUNCH_TEMPLATE = """[Desktop Entry]
Encoding=UTF-8
Name={app_name}
Exec={app}
Icon={app}
Type=Application
Terminal=false
"""


def running_as_root() -> bool:
    return os.getuid() == 0


USER = os.environ.get("SUDO_USER" if running_as_root() else "USER")
USER_UID = os.environ.get("SUDO_UID") if running_as_root() else os.getuid()
USER_GID = os.environ.get("SUDO_GID") if running_as_root() else os.getgid()
HOME = os.path.expanduser(f'~{USER}')
APP_CACHE = os.path.join(HOME, ".appImageInstaller", "apps")


def list_installed_apps(args):
    """
    List installed app images in cache. Also verifies that all app are properly installed and gives feedback about them
    """
    files = [f for f in os.listdir(APP_CACHE)]

    sys.stdout.write(f'Installed apps: {(len(files))}\n')

    for f in files:
        sys.stdout.write(f'\n{f}\n')
        app = json.load(open(os.path.join(APP_CACHE, f)))
        sys.stdout.write(f'\tApp name:\t \t{app["app_name"]}\n')
        sys.stdout.write(f'\tInstallation path: \t{app["dest_path"]}\n')
        sys.stdout.write(f'\tExecutable symlink: \t{app["symlink"]}\n')
        sys.stdout.write(f'\tOriginal file name: \t{app["app_file_path"]}\n')


def read_app_cache_info(app_name):
    return json.load(open(os.path.join(APP_CACHE, app_name)))


def create_app_launcher(args):
    launcher_dir_path = os.path.join(HOME, '.local', 'share', 'applications')
    if not os.path.exists(launcher_dir_path):
        sys.stdout.write(f'Gnome local application directory {launcher_dir_path} does not exists.\n Exiting...\n')

    launcher_file_path = os.path.join(launcher_dir_path, f'{args.app_name}.desktop')
    app = read_app_cache_info(args.app_name)

    with open(launcher_file_path, 'w') as fp:
        fp.write(GNOME_LAUNCH_TEMPLATE.format(
            app_name=app['app_name'],
            app=app['symlink'],
            icon=app['symlink'],
        ))


def save_installed_appImage(app):
    """
    Save an app image to the app cache, which is a file under ~/.appImageInstaller/apps
    """
    file_path = os.path.join(HOME, ".appImageInstaller", "apps", app['app_name'])

    with open(file_path, 'w') as fp:
        json.dump(app, fp)

    os.chown(file_path, int(USER_UID), int(USER_GID))


def uninstall_app(args):
    """
    Delete an installed app image from cache, deletes symlink and /opt installation
    """
    if not running_as_root() and not args.force:
        sys.stdout.write('We need root privileges.\n Sudoing command...\n')
        elevate_privileges()

    file_path = os.path.join(HOME, ".appImageInstaller", "apps", args.app_name)

    if not os.path.isfile(file_path):
        sys.stdout.write('App does not seems to be installed by AppImageInstaller\n')
        return

    with open(file_path, 'r') as fp:
        app = json.load(fp)

    sys.stdout.write('Restoring app to home directory...\n')
    os.rename(os.path.join(app['dest_path'], app['app_file_path']), os.path.join(HOME, app['app_file_path']))

    sys.stdout.write('Removing symlink...\n')
    os.remove(app['symlink'])
    sys.stdout.write('Removing app directory...\n')
    os.removedirs(app['dest_path'])
    sys.stdout.write('Removing cache file...\n')
    os.remove(file_path)

    sys.stdout.write('App uninstalled\n')


def install_app(args):
    """
    Install an app by
        creating /opt/app_name
        moving executable to /opt/app_name
        creating a symlink to /opt/app_name/app_image
    """
    if not running_as_root() and not args.force:
        sys.stdout.write('We need root privileges.\n Sudoing command...\n')
        elevate_privileges()

    dest_path = '/opt/{appName}'.format(appName=args.app_name)
    filename = os.path.basename(args.app_image)
    dest_file = os.path.join(dest_path, filename)

    os.mkdir(dest_path)
    os.rename(args.app_image, dest_file)

    st = os.stat(dest_file)
    os.chmod(dest_file, st.st_mode | stat.S_IEXEC)

    symlink = '/usr/local/bin/{appName}'.format(appName=args.app_name)

    os.symlink(dest_file, symlink)

    save_installed_appImage({
        'app_name': args.app_name,
        'dest_path': dest_path,
        'app_file_path': filename,
        'symlink': symlink
    })


def verify_installer():
    if not os.path.exists(os.path.join(HOME, ".appImageInstaller")):
        os.mkdir(os.path.join(HOME, ".appImageInstaller"))
        os.chown(os.path.join(HOME, ".appImageInstaller"), int(USER_UID), int(USER_GID))

    if not os.path.exists(os.path.join(HOME, ".appImageInstaller", "apps")):
        os.mkdir(os.path.join(HOME, ".appImageInstaller", "apps"))
        os.chown(os.path.join(HOME, ".appImageInstaller"), int(USER_UID), int(USER_GID))


def elevate_privileges():
    if os.getuid() != 0:
        cmd = ("sudo", sys.executable, *sys.argv)
        os.execvp("sudo", cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    install_parser = subparsers.add_parser('install', help='Install new app')
    install_parser.add_argument('app_image')
    install_parser.add_argument('app_name')
    install_parser.add_argument('-f', '--force', action='store_true', help='Disable root privileges check')
    install_parser.set_defaults(func=install_app)

    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall existing app')
    uninstall_parser.add_argument('-f', '--force', action='store_true', help='Disable root privileges check')
    uninstall_parser.add_argument('app_name')
    uninstall_parser.set_defaults(func=uninstall_app)

    list_parser = subparsers.add_parser('list', help='List installed apps')
    list_parser.set_defaults(func=list_installed_apps)

    launcher_parser = subparsers.add_parser('launcher', help='Create Gnome desktop launcher')
    launcher_parser.add_argument('app_name')
    launcher_parser.set_defaults(func=create_app_launcher)

    verify_installer()

    args = parser.parse_args()
    args.func(args)
