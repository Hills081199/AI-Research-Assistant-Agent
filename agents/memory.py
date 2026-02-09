from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

class HybridMemory:
    """ Kết hợp short term memory và long term memory """ 
    def __init__(self, config, llm):
        self.config = config
        
        # Short term memory (recent Conversation)
        self.short_term = ConversationBufferWindowMemory(
            memory_key="short_term_memory",
            k=self.config.memory_window,
            return_messages=True
        )

        # Long term memory (semantic search over past interactions)
        self.embeddings = OpenAIEmbeddings()
        self.long_term = None  # Will initialize on first use
        self.documents: List[Document] = []

        # Summary memory for very long conversations
        self.summary = ConversationSummaryMemory(
            llm=llm,
            memory_key="conversation_summary"
        )
    
    def add_interaction(self, query: str, response: str, metadata: Optional[Dict] = None):
        # Add to short term memory
        self.short_term.save_context(
            {"input": query},
            {"output": response}
        )

        #summary
        self.summary.save_context(
            {"input": query},
            {"output": response}
        )

        # Long-term (vectorstore)
        if self.config.enable_long_term_memory:
            doc = Document(
                page_content=f"Query: {query}\n\nResponse: {response}",
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "type": "interaction",
                    **(metadata or {})
                }
            )
            self.documents.append(doc)
            
            # Rebuild vectorstore (in production, use incremental add)
            if len(self.documents) % 5 == 0:  # Rebuild every 5 interactions
                self._rebuild_long_term_memory()
        
    
    def _rebuild_long_term_memory(self):
        """Rebuild vectorstore với documents mới"""
        if self.documents:
            self.long_term = FAISS.from_documents(
                self.documents,
                self.embeddings
            )

    def get_relevant_context(self, query: str, k: int = 3) -> str:
        """Lấy context liên quan từ long-term memory"""
        if not self.long_term or not self.documents:
            return ""
        
        try:
            docs = self.long_term.similarity_search(query, k=k)
            context = "\n\n---\n\n".join([doc.page_content for doc in docs])
            return f"Relevant past context:\n{context}"
        except:
            return ""
    
    def get_short_term_history(self) -> List:
        """Lấy recent conversation history"""
        return self.short_term.load_memory_variables({}).get("chat_history", [])
    
    def get_summary(self) -> str:
        """Lấy conversation summary"""
        return self.summary.load_memory_variables({}).get("conversation_summary", "")
    
    def clear(self):
        """Clear tất cả memory"""
        self.short_term.clear()
        self.summary.clear()
        self.documents = []
        self.long_term = None
