#!/usr/bin/env python3
"""Quick test of JARVIS 0.1 LLM integration."""
from jarvis.llm.client import call_llm

print('Testing JARVIS 0.1 LLM Integration...')
print('-' * 50)

try:
    response = call_llm(
        'Hello JARVIS 0.1! Say hi back in one short sentence.',
        provider='auto',
        max_tokens=50
    )

    print(f'✅ SUCCESS!')
    print(f'Provider: {response.provider}')
    print(f'Model: {response.model}')
    print(f'Response: {response.content}')
    print(f'Cost: ${response.cost_usd:.6f}')
    print(f'Tokens: {response.input_tokens} in, {response.output_tokens} out')
    print('-' * 50)
    print('🎉 JARVIS 0.1 is LIVE with full LLM integration!')

except Exception as e:
    print(f'❌ ERROR: {e}')
    import traceback
    traceback.print_exc()
