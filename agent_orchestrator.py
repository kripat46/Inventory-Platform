import os
from sqlalchemy import create_engine
from pinecone import Pinecone as PineconeClient

# 1. Modern LlamaIndex Core Imports
from llama_index.core import SQLDatabase, VectorStoreIndex, Settings
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata

# 2. Clean Specialized Extension Imports
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore

# THIS IS THE MODERN FIX: Import the active non-deprecated Agent Framework
from llama_index.core.agent import FunctionCallingAgent

def run_agent_engine(user_query: str):
    print(f"\nInitializing Intelligent Inventory Agent for Query: '{user_query}'...")
    
    # 1. Credentials Configuration Configuration
    OPENAI_API_KEY = "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"
    PINECONE_API_KEY = "pcsk_6pBXB2_7EnyeZVgWXoJFaqPLL1U3pGcGNWi8scUBo83MoQc1NaFkWPxQ1ULMdNJ6QmuNPE"
    PINECONE_INDEX_NAME = "inventory-rag-index"
    
    DB_USER = "postgres_user"
    DB_PASSWORD = "RiddhiSiddhi246!"
    DB_HOST = "inventory-db-instance.czmwusiwewpk.us-east-2.rds.amazonaws.com"
    DB_PORT = "5432"
    DB_NAME = "inventory_platform"
    
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    
    llm = LlamaOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
    embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=OPENAI_API_KEY)
    
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.api_key = OPENAI_API_KEY
    
    # ----------------------------------------------------
    # CONSTRUCT TOOL 1: SQL Structured Metric Engine
    # ----------------------------------------------------
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    sql_engine = create_engine(connection_string)
    sql_database = SQLDatabase(sql_engine, include_tables=["historical_sales", "future_forecasts", "inventory_anomalies"])
    
    sql_query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database, 
        tables=["historical_sales", "future_forecasts", "inventory_anomalies"],
        llm=llm,
        embed_model=embed_model
    )
    
    sql_tool = QueryEngineTool(
        query_engine=sql_query_engine,
        metadata=ToolMetadata(
            name="sql_metrics_tool",
            description=(
                "Use this tool to pull hard database metrics, inventory counts, dates, sales figures, "
                "historical deviations, and future demand forecast predictions for specific SKUs."
            )
        )
    )
    
    # ----------------------------------------------------
    # CONSTRUCT TOOL 2: Pinecone Unstructured RAG Engine
    # ----------------------------------------------------
    pc = PineconeClient(api_key=PINECONE_API_KEY)
    pinecone_index = pc.Index(PINECONE_INDEX_NAME)
    
    # The store will now successfully extract the default "text" field
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    
    vector_index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)
    vector_query_engine = vector_index.as_query_engine(llm=llm)
    
    vector_tool = QueryEngineTool(
        query_engine=vector_query_engine,
        metadata=ToolMetadata(
            name="logistics_rag_tool",
            description=(
                "Use this tool ONLY when you need to answer 'Why' an inventory anomaly occurred. "
                "Contains unstructured logistics data, weather incident write-ups, supplier delays, and promo calendars."
            )
        )
    )
    
    # ----------------------------------------------------
    # UNIFY TOOLS INTO PRODUCTION-READY FUNCTION AGENT
    # ----------------------------------------------------
    agent = FunctionCallingAgent.from_tools(
        tools=[sql_tool, vector_tool],
        llm=llm,
        verbose=True
    )
    
    # ----------------------------------------------------
    # EXECUTE THE WORKFLOW LOOP
    # ----------------------------------------------------
    response = agent.chat(user_query)
    
    print("\n" + "="*50)
    print("FINAL AGENT RESOLUTION STATEMENT:")
    print("="*50)
    print(response.response)

if __name__ == "__main__":
    sample_query = (
    "Query the 'inventory_anomalies' table in the database to get a list of rows. "
    "Look up those specific dates and SKUs in your logistics_rag_tool to find "
    "the matching logistics or weather incidents that explain what caused those disruptions."
)

    run_agent_engine(sample_query)