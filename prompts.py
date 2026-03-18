"""Task pack: 15 prompts across 5 categories for the tournament."""

TASK_PACK: list[dict] = [
    # ── Rewriting (3) ───────────────────────────────────────────
    {
        "id": "rewrite-clarity",
        "category": "rewriting",
        "prompt_text": (
            "Rewrite the following paragraph so it is clear, concise, and "
            "easy to understand for a general audience. Preserve the core "
            "meaning.\n\n"
            "\"The implementation of the aforementioned regulatory framework "
            "necessitates the establishment of a multi-stakeholder governance "
            "body that shall be vested with the authority to promulgate "
            "binding directives pertaining to the utilization of artificial "
            "intelligence systems within the jurisdictional boundaries of "
            "the signatory states, notwithstanding any pre-existing bilateral "
            "agreements that may be in contravention thereof.\""
        ),
        "max_tokens": 300,
    },
    {
        "id": "rewrite-tone",
        "category": "rewriting",
        "prompt_text": (
            "Rewrite the following customer support reply so it sounds warm, "
            "empathetic, and helpful instead of robotic.\n\n"
            "\"Your request has been received and logged under ticket #4821. "
            "Processing time is 3-5 business days. No further action is "
            "required from you at this time. If the issue persists after "
            "resolution, submit a new ticket.\""
        ),
        "max_tokens": 300,
    },
    {
        "id": "rewrite-simplify",
        "category": "rewriting",
        "prompt_text": (
            "Simplify the following technical explanation so a 12-year-old "
            "could understand it. Use analogies if helpful.\n\n"
            "\"A transformer neural network uses self-attention mechanisms to "
            "compute weighted representations of input tokens, enabling "
            "parallel processing of sequential data. The multi-head attention "
            "layers allow the model to jointly attend to information from "
            "different representation subspaces at different positions.\""
        ),
        "max_tokens": 300,
    },

    # ── Extraction (3) ──────────────────────────────────────────
    {
        "id": "extract-contact",
        "category": "extraction",
        "prompt_text": (
            "Extract structured contact information from this messy email "
            "signature. Return it as JSON with keys: name, title, company, "
            "email, phone, address.\n\n"
            "\"Best regards,\n"
            "  Dr. Maria Chen-Watanabe | Sr. Director of AI Research\n"
            "  NovaMind Technologies, Inc.\n"
            "  mchen@novamind.io  ·  +1 (415) 555-0192\n"
            "  350 Mission St, Suite 800, San Francisco CA 94105\n"
            "  She/Her\""
        ),
        "max_tokens": 250,
    },
    {
        "id": "extract-events",
        "category": "extraction",
        "prompt_text": (
            "Extract all events mentioned in this paragraph as a JSON array. "
            "Each event should have: name, date, location, description.\n\n"
            "\"This spring is packed! The Global AI Summit runs March 15-17 in "
            "Geneva. Then there's PyCon US in Pittsburgh from May 14 through "
            "May 22. Oh, and don't forget the smaller DevOps Days conference "
            "happening April 8th in Austin, TX-it's single-day but always great "
            "for networking.\""
        ),
        "max_tokens": 400,
    },
    {
        "id": "extract-sentiment",
        "category": "extraction",
        "prompt_text": (
            "Analyze the sentiment of each sentence below. Return a JSON array "
            "where each item has: sentence, sentiment (positive/negative/neutral), "
            "confidence (0-1), key_phrase.\n\n"
            "1. \"The new update is absolutely fantastic, everything loads instantly!\"\n"
            "2. \"I've been waiting three weeks and still no response from support.\"\n"
            "3. \"The product works as described in the documentation.\"\n"
            "4. \"Honestly this is the worst purchase I've ever made.\"\n"
            "5. \"Shipping was surprisingly fast, arrived two days early.\""
        ),
        "max_tokens": 500,
    },

    # ── Creative (3) ────────────────────────────────────────────
    {
        "id": "creative-story",
        "category": "creative",
        "prompt_text": (
            "Write the opening paragraph (100-150 words) of a short story "
            "that begins with a librarian discovering that one specific book "
            "on the shelf changes its contents every time it's opened. "
            "Set the tone as literary fiction, not fantasy."
        ),
        "max_tokens": 300,
    },
    {
        "id": "creative-ads",
        "category": "creative",
        "prompt_text": (
            "Generate exactly 5 short ad copy variants (each under 15 words) "
            "for a noise-cancelling headphone brand called 'HushWave'. "
            "Target audience: remote workers. Tone: calm, premium, clever."
        ),
        "max_tokens": 250,
    },
    {
        "id": "creative-metaphor",
        "category": "creative",
        "prompt_text": (
            "Explain the concept of 'technical debt' using three different "
            "extended metaphors. Each metaphor should be 2-3 sentences and "
            "come from a different domain (e.g., cooking, construction, health)."
        ),
        "max_tokens": 400,
    },

    # ── Reasoning (3) ───────────────────────────────────────────
    {
        "id": "reason-logic",
        "category": "reasoning",
        "prompt_text": (
            "Solve this logic puzzle step by step:\n\n"
            "Five friends-Alice, Bob, Carol, Dave, and Eve-sit in a row at a "
            "movie theater.\n"
            "- Alice is not at either end.\n"
            "- Bob sits immediately to the left of Carol.\n"
            "- Dave is at one of the ends.\n"
            "- Eve is not next to Alice.\n\n"
            "Find all valid seating arrangements."
        ),
        "max_tokens": 600,
    },
    {
        "id": "reason-estimate",
        "category": "reasoning",
        "prompt_text": (
            "Estimate how many piano tuners there are in Chicago. Walk through "
            "your reasoning step by step with rough numbers for each assumption, "
            "then give a final estimate."
        ),
        "max_tokens": 500,
    },
    {
        "id": "reason-compare",
        "category": "reasoning",
        "prompt_text": (
            "Compare and contrast microservices vs. monolithic architecture. "
            "Give exactly 3 advantages and 3 disadvantages of each. "
            "Then recommend which is better for a 5-person startup building "
            "an MVP, with a one-sentence justification."
        ),
        "max_tokens": 600,
    },

    # ── Code (3) ────────────────────────────────────────────────
    {
        "id": "code-write",
        "category": "code",
        "prompt_text": (
            "Write a Python function `merge_sorted_streams(*iterators)` that "
            "takes multiple iterators, each yielding values in sorted order, "
            "and yields all values in globally sorted order. Use a heap. "
            "Include a docstring and type hints."
        ),
        "max_tokens": 400,
    },
    {
        "id": "code-debug",
        "category": "code",
        "prompt_text": (
            "Explain the bug in this Python code and fix it:\n\n"
            "```python\n"
            "def flatten(lst):\n"
            "    result = []\n"
            "    for item in lst:\n"
            "        if isinstance(item, list):\n"
            "            result.extend(flatten(item))\n"
            "        else:\n"
            "            result.append(item)\n"
            "    return result\n"
            "\n"
            "data = [1, [2, [3, 4]], [5, (6, 7)], 'hello']\n"
            "print(flatten(data))\n"
            "```\n\n"
            "Is there actually a bug, or does it work correctly? "
            "Discuss edge cases involving tuples, strings, and other iterables."
        ),
        "max_tokens": 500,
    },
    {
        "id": "code-refactor",
        "category": "code",
        "prompt_text": (
            "Refactor this JavaScript to be more readable, use modern syntax, "
            "and handle errors properly:\n\n"
            "```javascript\n"
            "function getData(url, cb) {\n"
            "  var xhr = new XMLHttpRequest();\n"
            "  xhr.open('GET', url);\n"
            "  xhr.onload = function() {\n"
            "    if (xhr.status == 200) {\n"
            "      var data = JSON.parse(xhr.responseText);\n"
            "      cb(null, data);\n"
            "    } else {\n"
            "      cb('Error: ' + xhr.status);\n"
            "    }\n"
            "  }\n"
            "  xhr.onerror = function() { cb('Network error'); }\n"
            "  xhr.send();\n"
            "}\n"
            "```"
        ),
        "max_tokens": 400,
    },
]
