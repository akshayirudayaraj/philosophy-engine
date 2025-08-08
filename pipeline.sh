#!/usr/bin/env zsh
set -e # exit on error
caffeinate -i python3 src/sep/scraping.py
caffeinate -i python3 src/sep/chunking.py
caffeinate -i python3 src/sep/embedding.py
caffeinate -i python3 src/sep/pinecone_storage.py