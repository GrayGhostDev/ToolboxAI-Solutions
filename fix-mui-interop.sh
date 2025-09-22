#!/bin/bash

# Comprehensive MUI _interopRequireDefault Fix Script
# This script patches all MUI files that use the problematic require statement
# and replaces it with an inline function definition for ESM/Vite compatibility

set -e

BASE_DIR="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
MUI_DIR="$BASE_DIR/node_modules/@mui"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 MUI _interopRequireDefault Patcher${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to patch a single file
patch_file() {
    local file="$1"
    local relative_path="${file#$MUI_DIR/}"

    # Check if file exists and contains the problematic require
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}❌ File not found: $relative_path${NC}"
        return 1
    fi

    if ! grep -q 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");' "$file"; then
        echo -e "${YELLOW}⏭️  Already patched or no issue: $relative_path${NC}"
        return 0
    fi

    # Create backup
    cp "$file" "$file.backup-$(date +%Y%m%d-%H%M%S)"

    # Apply patch using sed
    sed -i '' 's/var _interopRequireDefault = require("@babel\/runtime\/helpers\/interopRequireDefault");/\/\/ Patched: Define _interopRequireDefault inline to fix ESM\/CommonJS issues\nvar _interopRequireDefault = function(obj) {\n  return obj \&\& obj.__esModule ? obj : { default: obj };\n};/' "$file"

    echo -e "${GREEN}✅ Patched: $relative_path${NC}"
    return 0
}

# Function to patch multiple files in parallel
patch_files_batch() {
    local -a files=("$@")
    local batch_size=10
    local pids=()

    for ((i=0; i<${#files[@]}; i+=batch_size)); do
        # Process batch in parallel
        for ((j=i; j<i+batch_size && j<${#files[@]}; j++)); do
            patch_file "${files[j]}" &
            pids+=($!)
        done

        # Wait for current batch to complete
        for pid in "${pids[@]}"; do
            wait "$pid"
        done
        pids=()

        echo -e "${BLUE}📊 Processed $((i+batch_size < ${#files[@]} ? i+batch_size : ${#files[@]})) / ${#files[@]} files${NC}"
    done
}

echo -e "${YELLOW}🔍 Finding files that need patching...${NC}"

# Find all files that need patching, excluding already patched ones
readarray -t FILES_TO_PATCH < <(find "$MUI_DIR" -name "*.js" -type f -exec grep -l 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");' {} \;)

total_files=${#FILES_TO_PATCH[@]}

if [[ $total_files -eq 0 ]]; then
    echo -e "${GREEN}🎉 All files already patched! No work needed.${NC}"
    exit 0
fi

echo -e "${YELLOW}📋 Found $total_files files that need patching${NC}"
echo ""

# Show breakdown by package
echo -e "${BLUE}📦 Breakdown by package:${NC}"
printf '%s\n' "${FILES_TO_PATCH[@]}" | sed "s|$MUI_DIR/||" | cut -d'/' -f1 | sort | uniq -c | while read count package; do
    echo -e "   ${package}: ${count} files"
done
echo ""

# Confirm before proceeding
read -p "🚀 Proceed with patching? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ Aborted by user${NC}"
    exit 1
fi

echo -e "${BLUE}🔨 Starting patch process...${NC}"
echo ""

# Start timing
start_time=$(date +%s)

# Patch files in batches for better performance
patch_files_batch "${FILES_TO_PATCH[@]}"

# End timing
end_time=$(date +%s)
duration=$((end_time - start_time))

echo ""
echo -e "${GREEN}🎉 Patching completed successfully!${NC}"
echo -e "${BLUE}📊 Statistics:${NC}"
echo -e "   Files processed: ${total_files}"
echo -e "   Time taken: ${duration} seconds"
echo ""

# Verify patches
echo -e "${YELLOW}🔍 Verifying patches...${NC}"
failed_files=()

for file in "${FILES_TO_PATCH[@]}"; do
    if grep -q 'var _interopRequireDefault = require("@babel/runtime/helpers/interopRequireDefault");' "$file"; then
        failed_files+=("$file")
    fi
done

if [[ ${#failed_files[@]} -eq 0 ]]; then
    echo -e "${GREEN}✅ All patches verified successfully!${NC}"
else
    echo -e "${RED}❌ ${#failed_files[@]} files failed to patch:${NC}"
    printf '%s\n' "${failed_files[@]}" | sed "s|$MUI_DIR/||" | while read file; do
        echo -e "   ${file}"
    done
fi

echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo -e "   1. Test your dashboard to ensure it loads correctly"
echo -e "   2. If issues persist, check the browser console for errors"
echo -e "   3. Backup files are saved with timestamp suffix for rollback if needed"
echo ""

# Check if dashboard directory exists and suggest testing
if [[ -d "$BASE_DIR/apps/dashboard" ]]; then
    echo -e "${YELLOW}🧪 To test the fix:${NC}"
    echo -e "   cd '$BASE_DIR/apps/dashboard' && npm run dev"
    echo ""
fi

echo -e "${GREEN}🎯 Patch script completed!${NC}"