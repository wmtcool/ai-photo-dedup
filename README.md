# 🤖 AI Photo Dedup — Smart Duplicate Photo Cleaner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

An intelligent tool that uses perceptual hashing and machine learning to detect and remove duplicate photos from your collection.

## ✨ Features

- 🔍 **Smart Detection**: Uses perceptual hashing (pHash, dHash, aHash) to find visually similar images
- 🧠 **ML-Powered**: Optional deep learning models for semantic similarity
- ⚡ **Fast**: Parallel processing with progress bars
- 🗂️ **Safe**: Preview mode before any deletion
- 📊 **Detailed Reports**: Export findings to JSON/CSV
- 🖼️ **Multi-format**: Supports JPG, PNG, HEIC, WEBP, BMP, TIFF

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/wmtcool/ai-photo-dedup.git
cd ai-photo-dedup

# Install dependencies
pip install -r requirements.txt

# Run the scanner
python -m photo_dedup scan /path/to/photos --report duplicates.json
```

## 📖 Usage

### Scan for duplicates

```bash
python -m photo_dedup scan /path/to/photos \
  --similarity 0.9 \
  --report duplicates.json \
  --preview
```

### Remove duplicates (with confirmation)

```bash
python -m photo_dedup clean duplicates.json --keep-newest
```

### Generate visual report

```bash
python -m photo_dedup report duplicates.json --output report.html
```

## 🔧 Configuration

Create a `config.yaml` in your working directory:

```yaml
similarity_threshold: 0.85
hash_algorithm: phash  # phash, dhash, ahash, or all
parallel_workers: 4
supported_formats:
  - .jpg
  - .jpeg
  - .png
  - .heic
  - .webp
min_file_size: 1024  # bytes
```

## 🧠 How It Works

1. **Perceptual Hashing**: Generate visual fingerprints of images
2. **Similarity Comparison**: Compare hashes using Hamming distance
3. **Grouping**: Cluster similar images together
4. **Ranking**: Score by quality, size, date to recommend which to keep
5. **Action**: Delete or move duplicates based on user preference

## 📊 Example Output

```
🔍 Scanning /Users/example/Photos...
Found 12,847 images

📊 Analysis Results:
┌─────────────────┬──────────┐
│ Total Images    │ 12,847   │
│ Unique Images   │ 9,234    │
│ Duplicates      │ 3,613    │
│ Space Wasted    │ 14.2 GB  │
│ Groups Found    │ 1,892    │
└─────────────────┴──────────┘

💾 Potential savings: 14.2 GB
```

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black photo_dedup/
isort photo_dedup/
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Credits

- [ImageHash](https://github.com/JohannesBuchner/imagehash) for perceptual hashing
- [Pillow](https://python-pillow.org/) for image processing
- [Rich](https://github.com/Textualize/rich) for beautiful CLI output

---

Made with ❤️ by [wmtcool](https://github.com/wmtcool)
