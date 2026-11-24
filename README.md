<div align="center">
<img src="frontend/public/favicon.svg" alt="Atelier" width="88" height="88">
# Atelier

**Your art collection, understood.**<br>
A gallery that classifies, tags and organizes your artwork automatically.

[Quick start](#quick-start) · [NAS](INSTALLATION_GUIDE.md) · [Docs](docs/ARCHITECTURE.md)

<br>
<img src="docs/main_gallery.png" alt="Atelier gallery view" width="860">
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
    <td width="33%"><img src="docs/artwork_detail.png" alt="Artwork detail"></td>
    <td width="33%"><img src="docs/color_filter.png" alt="Color filter"></td>
    <td width="33%"><img src="docs/dark_light_mode.png" alt="Dark and light mode"></td>
  </tr>
  <tr>
    <td align="center"><sub>Automatic classification</sub></td>
    <td align="center"><sub>Filter by color</sub></td>
    <td align="center"><sub>Light &amp; dark</sub></td>
  </tr>
</table>
<br>
## Quick start

```bash
git clone <repository-url>
cd atelier
docker-compose up -d
```

Then open **http://localhost:3000** (API docs at http://localhost:8000/docs).

Running on a NAS? See the [installation guide](INSTALLATION_GUIDE.md).

## Built with

FastAPI · PostgreSQL · React 19 · TypeScript · Tailwind CSS · Tauri · Docker

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit together.

## Contributing

Contributions are welcome. Fork the repo, create a feature branch and open a pull request with a short description of the change.

## License

[MIT](LICENSE)

<br>
<div align="center">
  <sub>Made with ❤️ for artists and curators.</sub>
</div>

