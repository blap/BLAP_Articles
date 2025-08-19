# Changelog

## [1.0.0] - 2025-08-19

### Added
- **Initial Application Structure**: Complete project architecture with Core, GUI, Plugins, and Tests.
- **Core API**: Robust backend API for managing library items, collections, tags, creators, and attachments.
- **Data Portability**: Application data (database, attachments) is now stored in a `data/` folder relative to the executable, making the app fully portable.
- **Functional GUI**: Kivy-based graphical user interface with a three-panel layout:
    - Collection tree for navigation.
    - Performant `RecycleView` list for library items.
    - Detail panel to show information for selected items.
- **Plugin System**: Extensible plugin architecture with hooks for item events (`add`, `update`, `delete`).
- **Example Plugins**:
    - `check_for_updates`: A basic plugin demonstrating web requests to the CrossRef API.
    - `arxiv_version_checker`: An advanced plugin to find and flag updated versions of arXiv papers, with full GUI integration.
- **Web Connector**: Chrome extension and native messaging host to save items directly from the browser.
- **PDF Import**: Functionality to create a new library item by importing a PDF file, including metadata extraction via DOI and CrossRef.
- **User Experience**:
    - Onboarding popup for first-time users.
    - Error handling popups for backend failures.
    - Visual indicators for updatable items.
- **Build Automation**: A `build.sh` script to test, package with PyInstaller, and create a final distributable archive.

### Fixed
- Numerous bugs throughout the development process, including:
    - Kivy GUI crashes related to widget properties, layout rules, and startup logic.
    - Database constraint and pathing issues.
    - Test suite errors and inconsistencies.
- Corrected application behavior to be more robust and predictable.
