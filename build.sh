#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing Python Dependencies..."
pip install -r requirements.txt

echo "Initializing Database..."
python init_db.py

echo "Building React Frontend..."
cd rhymic-react
npm install
npm run build
cd ..

echo "Build Complete!"
