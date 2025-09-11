#!/bin/bash

# Load environment variables
source .env

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep -E '^version = ' pyproject.toml | cut -d'"' -f2)
echo "Current version: $CURRENT_VERSION"

# Calculate auto-increment version (patch version +1)
IFS='.' read -r major minor patch <<< "$CURRENT_VERSION"
AUTO_VERSION="$major.$minor.$((patch + 1))"

# Ask for new version
read -p "Enter new version (or press Enter for $AUTO_VERSION): " NEW_VERSION

# Use auto-increment if no input provided
if [ -z "$NEW_VERSION" ]; then
    NEW_VERSION=$AUTO_VERSION
fi

# Update version in pyproject.toml
if [ "$NEW_VERSION" != "$CURRENT_VERSION" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
    else
        # Linux
        sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
    fi
    echo "Updated version to: $NEW_VERSION"
else
    echo "Keeping version: $NEW_VERSION"
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/

# Build the package
echo "Building package with version $NEW_VERSION..."
uv build

# Publish to PyPI
echo "Publishing to PyPI..."
uv publish --token $PYPI_TOKEN

echo "Done! You can now install with: uv tool install finter-agent"