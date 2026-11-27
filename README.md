<div align="center">
<img src="frontend/src-tauri/icons/icon.png" alt="Atelier" width="256" height="256">

# Atelier

**Your art collection, understood.**<br>
A gallery that classifies, tags and organizes your artwork automatically.

[Quick start](#quick-start) · [NAS](INSTALLATION_GUIDE.md) · [Docs](docs/ARCHITECTURE.md)

<br>
<img src="docs/screenshots/grid-overview.png" alt="Atelier gallery view" width="860">
</div>
<br>

## Why Atelier

Digital art collections grow messy fast: thousands of files, no consistent names, no way to find "that blue-ish watercolor landscape". Atelier looks at every piece and does the filing for you, so you can spend your time on the work, not on folders.

## What it does

|                              |                                                                         |
| ---------------------------- | ----------------------------------------------------------------------- |
| **Classifies automatically** | Detects type (painting, illustration, photo…), subject and technique.   |
| **Understands color**        | Extracts each palette so you can filter your whole collection by color. |
| **Organizes in bulk**        | Batch tagging and editing across hundreds of pieces at once.            |
| **Runs everywhere**          | Web, plus native desktop apps for Windows, macOS and Linux.             |
| **Looks the part**           | Clean interface with light and dark themes.                             |

<br>
<table>
  <tr>
    <td width="33%"><img src="docs/screenshots/artwork-detail-2.png" alt="Artwork review in dark mode"></td>
    <td width="33%"><img src="docs/screenshots/photo-person.png" alt="Classify Photographs"></td>
    <td width="33%"><img src="docs/screenshots/detail-tag-1.png" alt="Creating a tag"></td>
  </tr>
  <tr>
    <td align="center"><sub>Review and classify</sub></td>
    <td align="center"><sub>Classify Photographs</sub></td>
    <td align="center"><sub>Create tags on the fly</sub></td>
  </tr>
  <tr>
    <td width="33%"><img src="docs/screenshots/bulk-select-actions.png" alt="Bulk selection and actions"></td>
    <td width="33%"><img src="docs/screenshots/card-flip-over.png" alt="Card flipped to show metadata"></td>
    <td width="33%"><img src="docs/screenshots/artwork-detail.png" alt="Artwork review in light mode"></td>
  </tr>
  <tr>
    <td align="center"><sub>Bulk actions and filter by color</sub></td>
    <td align="center"><sub>Flip a card for details</sub></td>
    <td align="center"><sub>Light mode</sub></td>
  </tr>
</table>
<br>

## Quick start

**Desktop app (standalone, no server or internet needed)**

1. Build: `./build-desktop.sh` (needs Python 3.11, Node and Rust; ~10 min the first time).
2. Install: open `frontend/src-tauri/target/release/bundle/dmg/Atelier_*.dmg` and drag Atelier to Applications. Apple Silicon only.
3. Run: open Atelier. The first launch takes a minute or two; later ones a few seconds.
4. Import: **Import folder…** copies a folder of images into the library, skipping duplicates and non-image files.
5. Data lives in `~/Library/Application Support/Atelier` (`atelier.db` + `images/`); change it in Settings.
6. Back up: Settings → **Back up now** to any folder (external disk, a NAS share), or just copy the data folder.
7. NAS: run `docker-compose.nas.yml` on the NAS, then Settings → **On a server**. The Mac classifies, the NAS stores.

**Web (Docker)**

```bash
docker-compose up -d   # http://localhost:3000
```

## Built with

FastAPI · SQLite · React 19 · TypeScript · Tailwind CSS · Tauri · Docker

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit together.

## Contributing

Contributions are welcome. Fork the repo, create a feature branch and open a pull request with a short description of the change.

## License

[MIT](LICENSE)

<br>
<div align="center">
<sub>Made with ❤️ for artists and curators.</sub>

</div>
