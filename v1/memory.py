# from langchain.memory import VectorStoreRetrieverMemory
# from langchain_openai import OpenAIEmbeddings
# from langchain.docstore import InMemoryDocstore
# from langchain_community.vectorstores import faiss

# import faiss

# import os
# from dotenv import load_dotenv

# load_dotenv()

# os.environ["OPENAI_API_KEY"] 

# embedding_size = 1536
# index = faiss.IndexFlatL2(embedding_size)
# embedding_fn = OpenAIEmbeddings().embed_query
# vectorstore = faiss(embedding_fn, index, InMemoryDocstore({}), {})

# retriever = vectorstore.as_retriever(search_kwargs=dict(k=1))
# memory = VectorStoreRetrieverMemory(retriever=retriever)

# def save_user_input(user_input):
#     # Save the user input to memory
#     memory.save_context({"input": user_input})

#     # You can print or log the saved input for verification
#     print(f"Saved user input: {user_input}")

# # # Example usage
# # save_user_input("Hello, how are you?")


