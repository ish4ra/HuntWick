"""Verify the icon referenced by each installed shell entry against the release source."""
import argparse
import configparser
import io
import plistlib
import struct
import tarfile
from pathlib import Path

from PIL import Image

ICONS = Path(__file__).resolve().parents[1] / 'src-tauri/icons'


def same_pixels(actual, expected, location):
    if actual.size != expected.size or actual.convert('RGBA').tobytes() != expected.convert('RGBA').tobytes():
        raise ValueError(f'{location}: packaged icon differs from the release source at {actual.size}')
    print(f'Verified packaged icon at {location} ({actual.width} px)')


def linux(root):
    applications = root / 'usr/share/applications'
    entries = [p for p in applications.glob('*.desktop') if 'huntwick' in p.stem.lower()]
    entry, = entries
    desktop = configparser.ConfigParser(interpolation=None, strict=False)
    desktop.read(entry, encoding='utf8')
    name = desktop['Desktop Entry']['Icon']
    expected = {}
    for source in ICONS.glob('*.png'):
        with Image.open(source) as image:
            expected[image.size] = image.convert('RGBA')
    installed = list((root / 'usr/share/icons/hicolor').glob(f'*/apps/{name}.png'))
    if not installed:
        raise ValueError(f'{entry}: no installed icon for {name!r}')
    if root != Path('/'):
        # AppImage launchers read the AppDir root desktop entry and .DirIcon.
        app_entry, = root.glob('*.desktop')
        app_desktop = configparser.ConfigParser(interpolation=None, strict=False)
        app_desktop.read(app_entry, encoding='utf8')
        installed.extend([root / (app_desktop['Desktop Entry']['Icon'] + '.png'), root / '.DirIcon'])
    for source in installed:
        with Image.open(source) as image:
            same_pixels(image, expected[image.size], source)


def mac_icon_path(plist):
    info = plistlib.loads(plist)
    name = Path(info['CFBundleIconFile'])
    if name.name != str(name):
        raise ValueError(f'Invalid app icon reference: {name}')
    return Path('Contents/Resources') / name.with_suffix('.icns')


def mac(app, archive):
    source = (ICONS / 'icon.icns').read_bytes()
    icon = app / mac_icon_path((app / 'Contents/Info.plist').read_bytes())
    if icon.read_bytes() != source:
        raise ValueError(f'{icon}: mounted DMG icon differs from the release source')
    with tarfile.open(archive) as bundle:
        plist, = [m for m in bundle if Path(m.name).parts[-3:] == (app.name, 'Contents', 'Info.plist')]
        resource = mac_icon_path(bundle.extractfile(plist).read())
        wanted = Path(plist.name).parents[1] / resource
        member, = [m for m in bundle.getmembers() if Path(m.name) == wanted]
        if bundle.extractfile(member).read() != source:
            raise ValueError(f'{archive}: updater icon differs from the release source')
    print(f'Verified {icon} and matching updater archive resource {wanted}')


def windows(exe):
    import pefile  # Locked Windows PyInstaller dependency.
    with pefile.PE(str(exe), fast_load=True) as pe:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
        resources = {node.id: node.directory.entries for node in pe.DIRECTORY_ENTRY_RESOURCE.entries}
        def data(resource):
            desc = resource.directory.entries[0].data.struct
            return pe.get_data(desc.OffsetToData, desc.Size)
        # The shell uses the first RT_GROUP_ICON for the executable. Reassemble its
        # ICO directory so Pillow can decode either PNG or Win32 DIB frames.
        group = data(resources[14][0])
        images = {node.id: node for node in resources[3]}
        count = struct.unpack_from('<H', group, 4)[0]
        ico = bytearray(group[:6])
        frames = bytearray()
        for i in range(count):
            offset = 6 + 14 * i
            resource_id = struct.unpack_from('<H', group, offset + 12)[0]
            frame = data(images[resource_id])
            ico.extend(group[offset:offset+8] + struct.pack('<II', len(frame), 6 + 16 * count + len(frames)))
            frames.extend(frame)
    with Image.open(io.BytesIO(ico + frames)) as actual, Image.open(ICONS / 'icon.ico') as expected:
        if (32, 32) not in actual.ico.sizes():
            raise ValueError(f'{exe}: no 32 px shell icon')
        for size in actual.ico.sizes():
            same_pixels(actual.ico.getimage(size), expected.ico.getimage(size), exe)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='platform', required=True)
    sub.add_parser('linux').add_argument('root', type=Path)
    osx = sub.add_parser('mac')
    osx.add_argument('app', type=Path)
    osx.add_argument('archive', type=Path)
    sub.add_parser('windows').add_argument('executables', type=Path, nargs='+')
    args = parser.parse_args()
    if args.platform == 'linux':
        linux(args.root)
    elif args.platform == 'mac':
        mac(args.app, args.archive)
    else:
        for exe in args.executables:
            windows(exe)
