#!/bin/bash
# Comprehensive version update for Scientific Calculator MCP Server
set -e

# Function to show usage
show_usage() {
    echo "Usage: $0 [VERSION_TYPE|SPECIFIC_VERSION]"
    echo ""
    echo "VERSION_TYPE options:"
    echo "  patch   - Increment patch version (2.0.0 → 2.0.1) [default]"
    echo "  minor   - Increment minor version (2.0.0 → 2.1.0)"
    echo "  major   - Increment major version (2.0.0 → 3.0.0)"
    echo ""
    echo "SPECIFIC_VERSION examples:"
    echo "  2.0.1   - Set specific version"
    echo "  2.1.0   - Set specific version"
    echo ""
    echo "Examples:"
    echo "  $0 patch      # 2.0.0 → 2.0.1"
    echo "  $0 2.0.1      # Set to 2.0.1"
}

# Check if help requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

VERSION_INPUT=${1:-"patch"}
CURRENT_VERSION=$(python3 -c "import calculator; print(calculator.__version__)" 2>/dev/null || echo "2.0.0")

echo "🔍 Current version: $CURRENT_VERSION"

# Determine new version
if [[ "$VERSION_INPUT" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    # Specific version provided
    NEW_VERSION="$VERSION_INPUT"
    echo "📝 Setting specific version: $NEW_VERSION"
else
    # Parse current version for increment
    IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
    MAJOR=${VERSION_PARTS[0]}
    MINOR=${VERSION_PARTS[1]}
    PATCH=${VERSION_PARTS[2]}

    # Calculate new version based on type
    case $VERSION_INPUT in
        "major")
            NEW_MAJOR=$((MAJOR + 1))
            NEW_MINOR=0
            NEW_PATCH=0
            ;;
        "minor")
            NEW_MAJOR=$MAJOR
            NEW_MINOR=$((MINOR + 1))
            NEW_PATCH=0
            ;;
        "patch")
            NEW_MAJOR=$MAJOR
            NEW_MINOR=$MINOR
            NEW_PATCH=$((PATCH + 1))
            ;;
        *)
            echo "❌ ERROR: Invalid input '$VERSION_INPUT'"
            echo ""
            show_usage
            exit 1
            ;;
    esac

    NEW_VERSION="$NEW_MAJOR.$NEW_MINOR.$NEW_PATCH"
    echo "📈 Incrementing $VERSION_INPUT version: $NEW_VERSION"
fi

echo ""
echo "🎯 Version Update Summary:"
echo "   From: $CURRENT_VERSION"
echo "   To:   $NEW_VERSION"
echo ""

# Confirm with user
read -p "❓ Update version from $CURRENT_VERSION to $NEW_VERSION? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "❌ Version update cancelled"
    exit 0
fi

echo ""
echo "🔄 Updating version in all files..."

# Files to update with version references
declare -a FILES_TO_UPDATE=(
    "calculator/__init__.py"
    "calculator/server/middleware.py"
    "calculator/server/compatibility.py"
    "README.md"
    "docs/installation.md"
    "docs/security.md"
    "docs/developer_guide.md"
    "docs/ci_cd.md"
    "docs/configuration.md"
    "docs/deployment.md"
    "docs/readme.md"
    "docs/scripts_and_tools.md"
    "docs/troubleshooting.md"
    "docs/api_reference.md"
    "docs/architecture.md"
    "docs/examples.md"
    "scripts/deployment/deploy-pipeline.sh"
)

# Update each file
for file in "${FILES_TO_UPDATE[@]}"; do
    if [[ -f "$file" ]]; then
        echo "   📄 Updating $file"
        # Create backup
        cp "$file" "$file.bak"
        
        # Update version references
        sed -i.tmp "s/v$CURRENT_VERSION/v$NEW_VERSION/g" "$file"
        sed -i.tmp "s/Version $CURRENT_VERSION/Version $NEW_VERSION/g" "$file"
        sed -i.tmp "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/g" "$file"
        sed -i.tmp "s/calculator_version\"] = \"$CURRENT_VERSION\"/calculator_version\"] = \"$NEW_VERSION\"/g" "$file"
        sed -i.tmp "s/version: str = \"$CURRENT_VERSION\"/version: str = \"$NEW_VERSION\"/g" "$file"
        sed -i.tmp "s/version.*$CURRENT_VERSION/version $NEW_VERSION/g" "$file"
        sed -i.tmp "s/Server v$CURRENT_VERSION/Server v$NEW_VERSION/g" "$file"
        sed -i.tmp "s/Guide v$CURRENT_VERSION/Guide v$NEW_VERSION/g" "$file"
        sed -i.tmp "s/Documentation v$CURRENT_VERSION/Documentation v$NEW_VERSION/g" "$file"
        
        # Clean up temp files
        rm "$file.tmp"
        
        # Check if file actually changed
        if ! diff -q "$file" "$file.bak" > /dev/null 2>&1; then
            echo "   ✅ Updated $file"
            rm "$file.bak"
        else
            echo "   ⚪ No changes needed in $file"
            mv "$file.bak" "$file"
        fi
    else
        echo "   ⚠️  File not found: $file"
    fi
done

# Update CHANGELOG.md
if [[ -f "CHANGELOG.md" ]]; then
    echo "   📄 Updating CHANGELOG.md"
    # Add new version entry at the top
    sed -i.bak "s/## \[Unreleased\]/## [Unreleased]\n\n## [$NEW_VERSION] - $(date +%Y-%m-%d)\n\n### Changed\n- Version bump to $NEW_VERSION\n/" CHANGELOG.md
    rm CHANGELOG.md.bak
    echo "   ✅ Updated CHANGELOG.md"
fi

echo ""
echo "✅ Version updated to $NEW_VERSION in all files!"

# Verify the update worked
UPDATED_VERSION=$(python3 -c "import calculator; print(calculator.__version__)" 2>/dev/null || echo "unknown")
if [[ "$UPDATED_VERSION" == "$NEW_VERSION" ]]; then
    echo "✅ Version verification successful: $UPDATED_VERSION"
else
    echo "❌ Version verification failed. Expected: $NEW_VERSION, Got: $UPDATED_VERSION"
    exit 1
fi

echo ""
echo "🏷️  Git Operations:"

# Offer to create git tag
read -p "❓ Create git commit and tag v$NEW_VERSION? (y/N): " create_tag
if [[ $create_tag == [yY] ]]; then
    # Add all changed files
    git add -A
    
    # Create commit
    git commit -m "🔖 Bump version to $NEW_VERSION

- Updated version references across all documentation
- Updated version in calculator/__init__.py
- Updated middleware and compatibility modules
- Updated CHANGELOG.md with new version entry"
    
    # Create tag
    git tag "v$NEW_VERSION"
    
    echo "✅ Git commit and tag v$NEW_VERSION created"
    echo ""
    echo "🚀 Next steps:"
    echo "   git push origin main --tags"
    echo ""
else
    echo "⚪ Skipped git operations"
    echo ""
    echo "📝 Manual git commands:"
    echo "   git add -A"
    echo "   git commit -m 'Bump version to $NEW_VERSION'"
    echo "   git tag 'v$NEW_VERSION'"
    echo "   git push origin main --tags"
    echo ""
fi

echo "🎉 Version update complete!"
echo ""
echo "📋 Summary:"
echo "   ✅ Version: $CURRENT_VERSION → $NEW_VERSION"
echo "   ✅ Files: Updated $(echo "${FILES_TO_UPDATE[@]}" | wc -w) files"
echo "   ✅ Verification: Passed"
echo ""