import traceback
try:
    from chronicle_ai.memory_chat import get_memory_chat
    import logging

    # Set up logging to see errors
    logging.basicConfig(level=logging.INFO)

    print("Loading MemoryChat...")
    chat = get_memory_chat()
    query = "When did I first mention going to the gym?"
    print(f"Asking: {query}")
    response = chat.ask(query)
    print(f"QUESTION: {query}")
    print(f"ANSWER: {response.answer}")
    print(f"SOURCES: {len(response.sources)}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
