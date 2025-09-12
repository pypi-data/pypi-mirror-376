# __init__.py
# Minimal llm_formats package exposing a single public function

__all__ = ["get_llm_jsonl_formats"]

_DATA = [
  {
    'name': "OpenAI Prompt–Completion (SFT)",
    'aliases': ["openai_sft", "prompt_completion", "legacy_sft"],
    'line_regex': r'^\s*\{\s*"prompt"\s*:\s*"[\s\S]*?"\s*,\s*"completion"\s*:\s*"[\s\S]*?"\s*\}\s*$',
    'example': {
      'prompt': "Write a short greeting to a new user.",
      'completion': " Hello and welcome! Let me know how I can help."
    }
  },
  {
    'name': "OpenAI Chat Messages",
    'aliases': ["openai_chat", "chatml_jsonl", "messages_array"],
    'line_regex': r'^\s*\{\s*"messages"\s*:\s*\[\s*\{\s*"role"\s*:\s*"(system|user|assistant)"\s*,\s*"content"\s*:\s*"[\s\S]*?"\s*\}(?:\s*,\s*\{\s*"role"\s*:\s*"(system|user|assistant)"\s*,\s*"content"\s*:\s*"[\s\S]*?"\s*\})*\s*\]\s*\}\s*$',
    'example': {
      'messages': [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Give me one productivity tip.'},
        {'role': 'assistant', 'content': 'Batch similar tasks to reduce context switching.'}
      ]
    }
  },
  {
    'name': "Alpaca / Self-Instruct",
    'aliases': ['alpaca', 'self_instruct', 'instruction_input_output'],
    'line_regex': r'^\s*\{\s*"instruction"\s*:\s*"[\s\S]*?"\s*,\s*"input"\s*:\s*"[\s\S]*?"\s*,\s*"output"\s*:\s*"[\s\S]*?"\s*\}\s*$',
    'example': {
      'instruction': "Summarise the text.",
      'input': "Time management improves focus and results.",
      'output': "Effective time management boosts focus and outcomes."
    }
  },
  {
    'name': "Dolly v2",
    'aliases': ["dolly", "databricks_dolly"],
    'line_regex': r'^\s*\{\s*"instruction"\s*:\s*"[\s\S]*?"\s*,\s*"context"\s*:\s*"[\s\S]*?"\s*,\s*"response"\s*:\s*"[\s\S]*?"\s*\}\s*$',
    'example': {
      'instruction': "Explain what overfitting is.",
      'context': "Machine learning basics.",
      'response': "Overfitting happens when a model memorises training data and fails to generalise."
    }
  },
  {
    'name': "DPO (Direct Preference Optimization)",
    'aliases': ["dpo", "preference_pair", "chosen_rejected"],
    'line_regex': r'^\s*\{\s*"prompt"\s*:\s*"[\s\S]*?"\s*,\s*"chosen"\s*:\s*"[\s\S]*?"\s*,\s*"rejected"\s*:\s*"[\s\S]*?"\s*\}\s*$',
    'example': {
      'prompt': "Suggest a secure password policy.",
      'chosen': "Use at least 12 chars, mix cases, numbers, symbols; enable MFA and rotation.",
      'rejected': "Use \'password123\' and change it yearly."
    }
  },
  {
    'name': "Pairwise Ranking (A/B with Winner)",
    'aliases': ["pairwise_rm", "ab_ranking", "pairrm"],
    'line_regex': r'^\s*\{\s*"prompt"\s*:\s*"[\s\S]*?"\s*,\s*"response_a"\s*:\s*"[\s\S]*?"\s*,\s*"response_b"\s*:\s*"[\s\S]*?"\s*,\s*"winner"\s*:\s*"(A|B)"\s*\}\s*$',
    'example': {
      'prompt': "Describe HTTP/2 in one sentence.",
      'response_a': "HTTP/2 introduces multiplexing, header compression, and server push to improve web performance.",
      'response_b': "HTTP/2 is just a new port for websites.",
      'winner': "A"
    }
  },
  {
    'name': "ShareGPT-style Conversations",
    'aliases': ["sharegpt", "from_value_conversations"],
    'line_regex': r'^\s*\{\s*"conversations"\s*:\s*\[\s*\{\s*"from"\s*:\s*"(human|gpt)"\s*,\s*"value"\s*:\s*"[\s\S]*?"\s*\}(?:\s*,\s*\{\s*"from"\s*:\s*"(human|gpt)"\s*,\s*"value"\s*:\s*"[\s\S]*?"\s*\})*\s*\]\s*\}\s*$',
    'example': {
      'conversations': [
        {'from': 'human', 'value': "How do I speed up Python?"},
        {'from': 'gpt', 'value': "Profile first; then optimise hot paths and use vectorised libraries."}
      ]
    }
  },
  {
    'name': "T5/FLAN Style",
    'aliases': ['t5', 'flan', 'inputs_targets'],
    'line_regex': r'^\s*\{\s*"inputs"\s*:\s*"[\s\S]*?"\s*,\s*"targets"\s*:\s*"[\s\S]*?"\s*\}\s*$',
    'example': {
      'inputs': "Translate to French: 'good evening'",
      'targets': "bonsoir"
    }
  },
  {
    'name': "Simple QA",
    'aliases': ["qa_simple", "question_answer", "sft_qa"],
    'line_regex': r'^\s*\{\s*"question"\s*:\s*"[\s\S]*?"\s*,\s*"answer"\s*:\s*"[\s\S]*?"\s*\}\s*$',
    'example': {
      'question': "What is the capital of Japan?",
      'answer': "Tokyo"
    }
  }
]

def get_llm_jsonl_formats():
    """
    Return the data structure describing known jsonl formats used for training/fine-tuning LLMs.
    This is a self-contained dataset suitable for tests and examples.
    """
    return _DATA