EVALUATION_DATASET = [
    # ---------------------------------------------------------
    # COMPANY
    # ---------------------------------------------------------

    {
        "question": "What does KLOC do?",
        "expected_paths": [
            "company/company-overview.md",
            "faq/general-faq.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "What are KLOC's main divisions?",
        "expected_paths": [
            "company/company-overview.md",
            "faq/general-faq.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "Where is KLOC located?",
        "expected_paths": [
            "company/contact.md",
            "company/company-overview.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "How can I contact KLOC?",
        "expected_paths": [
            "company/contact.md",
        ],
        "type": "retrieval",
    },

    # ---------------------------------------------------------
    # KLOCOM
    # ---------------------------------------------------------

    {
        "question": "What does KLOCOM do?",
        "expected_paths": [
            "klocom/overview.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "Does KLOCOM support Shopify migrations?",
        "expected_paths": [
            "faq/general-faq.md",
            "klocom/overview.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "What integrations does KLOCOM provide?",
        "expected_paths": [
            "klocom/integrations.md",
            "klocom/overview.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "What Shopify services does KLOCOM offer?",
        "expected_paths": [
            "klocom/overview.md",
        ],
        "type": "retrieval",
    },

    # ---------------------------------------------------------
    # KLOCAPPS
    # ---------------------------------------------------------

    {
        "question": "What does KLOCAPPS do?",
        "expected_paths": [
            "klocapps/overview.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "Does KLOCAPPS build mobile applications?",
        "expected_paths": [
            "klocapps/overview.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "What AI products does KLOCAPPS provide?",
        "expected_paths": [
            "klocapps/overview.md",
        ],
        "type": "retrieval",
    },

    # ---------------------------------------------------------
    # KLOCERS
    # ---------------------------------------------------------

    {
        "question": "What does KLOCERS do?",
        "expected_paths": [
            "klocers/overview.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "Does KLOCERS provide dedicated teams?",
        "expected_paths": [
            "klocers/overview.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "What are KLOCERS delivery pods?",
        "expected_paths": [
            "klocers/overview.md",
        ],
        "type": "retrieval",
    },

    # ---------------------------------------------------------
    # AI
    # ---------------------------------------------------------

    {
        "question": "What AI capabilities does KLOC provide?",
        "expected_paths": [
            "ai/agentic-commerce.md",
            "klocapps/overview.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "What is KLOC's agentic commerce offering?",
        "expected_paths": [
            "ai/agentic-commerce.md",
        ],
        "type": "retrieval",
    },

    # ---------------------------------------------------------
    # CASE STUDIES
    # ---------------------------------------------------------

    {
        "question": "What features were implemented for Sleepyhead?",
        "expected_paths": [
            "case-studies/sleepyhead.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "What were the reported outcomes for Sleepyhead?",
        "expected_paths": [
            "case-studies/sleepyhead.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "How did KLOC's work affect Pothys's load times, conversion rates, and online sales?",
        "expected_paths": [
            "case-studies/pothys.md",
        ],
        "type": "retrieval",
    },

    {
        "question": "What was implemented for Roam?",
        "expected_paths": [
            "case-studies/roam.md",
        ],
        "type": "retrieval",
    },

    # ---------------------------------------------------------
    # UNKNOWN / UNANSWERABLE
    # ---------------------------------------------------------

    {
        "question": "What is KLOC's exact Shopify pricing?",
        "expected_paths": [],
        "type": "answerability",
    },

    {
        "question": "What is KLOC's refund policy?",
        "expected_paths": [],
        "type": "answerability",
    },
]