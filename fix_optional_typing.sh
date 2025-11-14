#!/bin/bash
# Fix Optional typing in all Python files

echo "Fixing Optional typing patterns across codebase..."
echo "================================================================"

# Find all Python files with Optional[ usage
files=$(find apps/backend/api -name "*.py" -type f -exec grep -l "Optional\[" {} \; 2>/dev/null)

count=0
for file in $files; do
  echo "Processing: $file"
  
  # Replace Optional[X] patterns
  sed -i '' 's/Optional\[Any\]/Any | None/g' "$file"
  sed -i '' 's/Optional\[str\]/str | None/g' "$file"
  sed -i '' 's/Optional\[int\]/int | None/g' "$file"
  sed -i '' 's/Optional\[bool\]/bool | None/g' "$file"
  sed -i '' 's/Optional\[float\]/float | None/g' "$file"
  sed -i '' 's/Optional\[dict\]/dict | None/g' "$file"
  sed -i '' 's/Optional\[list\]/list | None/g' "$file"
  sed -i '' 's/Optional\[User\]/User | None/g' "$file"
  sed -i '' 's/Optional\[ContentVersion\]/ContentVersion | None/g' "$file"
  sed -i '' 's/Optional\[PreferenceCategory\]/PreferenceCategory | None/g' "$file"
  
  ((count++))
done

echo "================================================================"
echo "✅ Fixed Optional typing in $count files"
echo ""
echo "Verifying no Optional[ patterns remain..."
remaining=$(grep -r "Optional\[" --include="*.py" apps/backend/api 2>/dev/null | wc -l | xargs)
echo "Remaining Optional[ patterns: $remaining"

if [ "$remaining" -eq "0" ]; then
  echo "✅ All Optional patterns replaced successfully!"
else
  echo "⚠️  Some Optional patterns still remain - checking..."
  grep -r "Optional\[" --include="*.py" apps/backend/api 2>/dev/null | head -5
fi
