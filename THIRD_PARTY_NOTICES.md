# Third-party notices

Original HuntWick code is distributed under the MIT License. The Sherlock Project supplies the username discovery engine and site definitions. Sherlock is MIT licensed. Its copyright and license are preserved in [engine/notices](engine/notices). The database is a bundled upstream snapshot whose revision is tracked by the adapter.

Desktop also bundles Maigret 0.6.7 and a compiled subset of its site definitions. The upstream MIT notice and catalog provenance accompany the executable. [Maigret MIT license](engine/notices/Maigret-MIT.txt) · [Catalog provenance](engine/notices/Provenance.md)


HuntWick uses Tauri and the Rust ecosystem for desktop IPC and platform integration, React and React DOM for the interface, and Lucide for interface icons. PyInstaller packages the Python interpreter and engine libraries. These components retain their own licenses.

Installer preparation collects the license files and declared licenses shipped by production npm packages and the resolved Rust dependencies in the bundled engine's `notices/desktop` directory. Some packages offer a choice of licenses. Consult the individual license text for terms. OS-provided components including WebView2, WebKit and GTK follow their respective distribution terms.

## Platform marks

The catalog uses locally bundled service and software-family logos. The asset ledger records the authoring collection, original artwork, applicable guidelines and file checksum. Collection notices and individual artwork licenses ship with the application. Trademarks belong to their respective owners. [Asset credits](public/platforms/credits.csv) · [Licenses and modifications](public/platforms/NOTICE.txt) · [Coverage and maintenance](docs/platform-logos/README.md)
