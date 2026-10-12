from rag.retriever import search_similar_chunks


questions = [
    "What Shopify services does KLOC provide?",
    "What does KLOCERS provide?",
    "What are KLOC's AI capabilities?",
    "Does KLOC build custom software?",
    "What features were implemented for Sleepyhead?",
    "What were the reported outcomes for Sleepyhead?",
    "What challenge did Sleepyhead have?",
    "What is KLOC's exact Shopify development pricing?",
    "What is KLOC's office location?",
    "What is KLOC's refund policy?",
]


for question in questions:

    print("\n")
    print("=" * 100)
    print("QUESTION:", question)
    print("=" * 100)

    results = search_similar_chunks(
        question,
        top_k=5,
    )

    for index, result in enumerate(results, start=1):

        print("-" * 100)

        print(f"Rank: {index}")
        print(f"Distance: {result.distance:.4f}")
        print(f"File: {result.path}")
        print(f"Section: {result.title}")
        print(f"Chunk: {result.chunk_index}")

        print("Content:")
        print(result.content)