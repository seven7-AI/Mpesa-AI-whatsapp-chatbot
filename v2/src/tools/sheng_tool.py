from langgraph_bigtool import BigTool
from src.memory.neo4j_store import graph

sheng_tool = BigTool(
    name="sheng_check",
    func=lambda w: graph.query("MATCH (w:Word {text: $word, language: 'Sheng'}) RETURN w.translation", {"word": w})
)

