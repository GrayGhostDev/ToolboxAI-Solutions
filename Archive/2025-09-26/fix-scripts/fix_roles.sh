#!/bin/bash

# Fix role comparisons in TypeScript/React files
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/src/dashboard/src

# Replace role comparisons
find . -type f \( -name "*.tsx" -o -name "*.ts" \) -exec sed -i '' \
  -e 's/role === "Teacher"/role === "teacher"/g' \
  -e 's/role === "Student"/role === "student"/g' \
  -e 's/role === "Admin"/role === "admin"/g' \
  -e 's/role === "Parent"/role === "parent"/g' \
  -e 's/role: "Teacher"/role: "teacher"/g' \
  -e 's/role: "Student"/role: "student"/g' \
  -e 's/role: "Admin"/role: "admin"/g' \
  -e 's/role: "Parent"/role: "parent"/g' {} \;

echo "Role values updated to lowercase"