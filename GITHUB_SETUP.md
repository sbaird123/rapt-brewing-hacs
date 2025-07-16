# GitHub Repository Setup Guide

Follow these steps to create a GitHub repository for HACS compatibility.

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right → "New repository"
3. Repository details:
   - **Name**: `rapt-brewing-hacs`
   - **Description**: "Home Assistant integration for RAPT Pill brewing session management"
   - **Visibility**: Public ✅ (Required for HACS)
   - **Initialize**: Don't initialize (we have existing files)
4. Click "Create repository"

## Step 2: Upload Repository Files

### Option A: Using Git Command Line

```bash
cd /opt/homebrew/var/www/rapt-brewing-hacs-github

# Configure git (if not already done)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add files and commit
git add .
git commit -m "Initial release of RAPT Brewing Session Manager v1.0.0"

# Add remote and push
git remote add origin https://github.com/YOURUSERNAME/rapt-brewing-hacs.git
git branch -M main
git push -u origin main
```

### Option B: Using GitHub Web Interface

1. In your new repository, click "uploading an existing file"
2. Drag and drop all files from `/opt/homebrew/var/www/rapt-brewing-hacs-github/`
3. Write commit message: "Initial release of RAPT Brewing Session Manager v1.0.0"
4. Click "Commit changes"

## Step 3: Create Release (Recommended)

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Release details:
   - **Tag**: `v1.0.0`
   - **Title**: `RAPT Brewing Session Manager v1.0.0`
   - **Description**: Copy from CHANGELOG.md
4. Click "Publish release"

## Step 4: Add Repository Topics

1. Go to your repository settings
2. In the "Topics" section, add:
   - `home-assistant`
   - `hacs`
   - `integration`
   - `rapt`
   - `brewing`
   - `homebrewing`
   - `iot`

## Step 5: Update README

Replace `yourusername` in the README.md with your actual GitHub username:

```bash
sed -i 's/yourusername/YOURUSERNAME/g' README.md
```

## Step 6: Test HACS Installation

1. Open Home Assistant
2. Go to HACS → Integrations
3. Click three dots → Custom repositories
4. Add: `https://github.com/YOURUSERNAME/rapt-brewing-hacs`
5. Category: Integration
6. Click "Add"
7. Search for "RAPT Brewing Session Manager"
8. Install and restart Home Assistant

## Repository Structure

Your repository should have this structure:
```
rapt-brewing-hacs/
├── custom_components/
│   └── rapt_brewing/
│       ├── __init__.py
│       ├── manifest.json
│       ├── sensor.py
│       ├── button.py
│       ├── select.py
│       ├── coordinator.py
│       ├── config_flow.py
│       ├── const.py
│       ├── data.py
│       ├── entity.py
│       ├── services.yaml
│       ├── strings.json
│       └── dashboard_config.yaml
├── hacs.json
├── info.md
├── README.md
├── LICENSE
├── CHANGELOG.md
├── VERSION
└── .gitignore
```

## Troubleshooting

**Repository not showing in HACS:**
- Ensure repository is public
- Check that all required files are present
- Verify hacs.json is valid JSON
- Wait a few minutes for HACS to validate

**Installation fails:**
- Check Home Assistant logs for errors
- Ensure RAPT BLE integration is installed first
- Verify Python syntax in all files

## Next Steps

After successful GitHub setup:
1. Share the repository URL with other brewers
2. Submit to HACS default repositories (optional)
3. Create documentation wiki
4. Set up automated testing (optional)

**Your HACS repository URL will be:**
`https://github.com/YOURUSERNAME/rapt-brewing-hacs`