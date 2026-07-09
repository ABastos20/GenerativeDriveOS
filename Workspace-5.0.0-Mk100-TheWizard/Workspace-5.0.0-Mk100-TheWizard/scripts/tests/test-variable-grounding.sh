#!/bin/bash
# Test script for Variable Grounding System
# Demonstrates autonomous intent analysis and confidence scoring

echo "========================================="
echo "JARVIS Variable Grounding System Test"
echo "========================================="
echo ""

echo "Test 1: Factual Query (Auto-Strict)"
echo "------------------------------------"
python -m jarvis.cli.main query "What is the Qdrant vector size?" --show-confidence
echo ""
echo ""

echo "Test 2: Creative Query (Auto-Soft)"
echo "------------------------------------"
python -m jarvis.cli.main query "Brainstorm ideas for improving the memory search" --show-confidence
echo ""
echo ""

echo "Test 3: Explanatory Query (Auto-Balanced)"
echo "------------------------------------"
python -m jarvis.cli.main query "Explain how the domain inference system works" --show-confidence
echo ""
echo ""

echo "Test 4: Manual Override (Force Strict)"
echo "------------------------------------"
python -m jarvis.cli.main query "Tell me about generative drive sines" --grounding-level strict --show-confidence
echo ""
echo ""

echo "Test 5: Disable Auto-Grounding"
echo "------------------------------------"
python -m jarvis.cli.main query "Some random question" --no-auto-grounding --grounding-level balanced
echo ""
echo ""

echo "========================================="
echo "All tests complete!"
echo "========================================="
