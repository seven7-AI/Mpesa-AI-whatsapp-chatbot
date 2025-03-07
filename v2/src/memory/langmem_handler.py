from langmem import InMemoryStore, MemorySaver

short_term_memory = MemorySaver()
long_term_memory = InMemoryStore()  # Replace with Neo4j integration for production

def get_user_memory(user_id: str):
    return short_term_memory.get(user_id) or {"messages": []}