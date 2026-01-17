#!/usr/bin/env python3
"""Test URL parser with various formats."""
# -*- coding: utf-8 -*-

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.youtube_player.url_parser import YouTubeURLParser

# Test cases
test_cases = [
    # The problematic URL from the donation
    "https://music.youtube.com/watch?v=pvgfto0hNsg&si=jTXigAvJ1bOcqj-G hello",
    # Standard formats
    "https://www.youtube.com/watch?v=pvgfto0hNsg",
    "https://youtu.be/pvgfto0hNsg",
    "https://music.youtube.com/watch?v=pvgfto0hNsg",
    # With parameters
    "https://www.youtube.com/watch?v=pvgfto0hNsg&t=10",
    "https://music.youtube.com/watch?v=pvgfto0hNsg&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
    # In text
    "Hey, check this out: https://music.youtube.com/watch?v=JlNbeydRCQs&si=12345",
    "test https://www.youtube.com/watch?v=abc123 test",
]

print("=" * 70)
print("URL PARSER TEST")
print("=" * 70)

parser = YouTubeURLParser()

for i, test_text in enumerate(test_cases, 1):
    print(f"\nTest {i}:")
    print(f"Input:  {test_text[:70]}")
    url = parser.extract_url(test_text)
    print(f"Output: {url}")
    print()

print("=" * 70)
