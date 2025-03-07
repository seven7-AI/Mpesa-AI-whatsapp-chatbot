from langchain_neo4j import Neo4jGraph
from src.config.env import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from pydantic import List
from langchain_core.messages import AnyMessage


graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)

def store_conversation(user_id: str, messages: List[AnyMessage]):
    query = """
    MERGE (u:User {id: $user_id})
    CREATE (c:Conversation {timestamp: datetime()})
    CREATE (u)-[:HAS_CONVERSATION]->(c)
    WITH c
    UNWIND $messages as msg
    CREATE (c)-[:CONTAINS]->(m:Message {content: msg.content, role: msg.role})
    """
    graph.query(query, {"user_id": user_id, "messages": [{"content": m.content, "role": m.role} for m in messages]})

def add_language_data(word: str, translation: str, language: str):
    query = """
    MERGE (w:Word {text: $word, language: $language})
    SET w.translation = $translation
    """
    graph.query(query, {"word": word, "translation": translation, "language": language})