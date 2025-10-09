#!/bin/bash
# Test script for OpenAI API key configuration

echo "=== TESTING OPENAI API KEY SETUP ==="
echo

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file exists"
else
    echo "❌ .env file not found - run: cp .env.example .env"
    exit 1
fi

# Check if OPENAI_API_KEY is set in .env
if grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "✅ OpenAI API key appears to be set in .env"
elif grep -q "OPENAI_API_KEY=your-openai-api-key" .env; then
    echo "⚠️  OpenAI API key is still the placeholder value"
    echo "   Edit .env and replace 'your-openai-api-key' with your actual key"
else
    echo "❌ OpenAI API key not found in .env"
    echo "   Add: OPENAI_API_KEY=sk-your-actual-key-here"
fi

echo
echo "TO ADD YOUR API KEY:"
echo "1. Get key from: https://platform.openai.com/api-keys"
echo "2. Edit .env file and replace the placeholder"
echo "3. Run this script again to verify"
echo
echo "EXAMPLE .env entry:"
echo "OPENAI_API_KEY=sk-proj-abc123def456ghi789..."