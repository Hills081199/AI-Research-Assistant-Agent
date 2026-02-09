from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableBranch
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import json

from .tools import create_research_tools
from .memory import HybridMemory
from chains.analysis_chain import create_analysis_chain, create_comparision_chain
from chains.synthesis_chain import create_synthesis_chain


class ResearchAgent:
    """Production-level Research Agent với full LCEL implementation"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            streaming=True
        )
        
        # Initialize tools
        self.tools = create_research_tools(config)
        
        # Initialize memory
        self.memory = HybridMemory(config, self.llm)
        
        # Initialize chains
        self.analysis_chain = create_analysis_chain(config)
        self.comparision_chain = create_comparision_chain(config)
        self.synthesis_chain = create_synthesis_chain(config)
        
        # Create agent
        self.agent = self._create_agent()
        self.agent_executor = self._create_executor()
        
    def _create_agent(self):
        """Tạo OpenAI tools agent với custom prompt"""
        
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", """Bạn là AI Research Assistant chuyên nghiệp với khả năng:

1. **Information Gathering**: Tìm kiếm từ nhiều nguồn (web, wikipedia, academic papers)
2. **Critical Analysis**: Phân tích và đánh giá độ tin cậy
3. **Synthesis**: Tổng hợp thông tin thành insights có giá trị
4. **Verification**: Cross-check facts từ nhiều nguồn

WORKFLOW CỦA BẠN:
1. Hiểu rõ câu hỏi và xác định scope
2. Plan: Quyết định tools nào cần dùng và thứ tự
3. Execute: Thu thập thông tin từ nhiều nguồn
4. Analyze: Đánh giá và so sánh thông tin
5. Synthesize: Tổng hợp thành answer hoàn chỉnh

RULES:
- Luôn cite sources cho claims cụ thể
- Acknowledge khi thông tin không chắc chắn
- So sánh multiple sources khi có thể
- Phân biệt facts vs opinions
- Đề xuất further research nếu cần

AVAILABLE TOOLS:
{tools}

TOOL USAGE TIPS:
- web_search: Cho current events, general info
- wikipedia: Cho background/overview
- arxiv_search: Cho scientific research
- web_scraper: Cho detailed content từ specific URLs
- data_analyzer: Cho numerical analysis
- citation_checker: Cho verification

Hãy suy nghĩ từng bước và sử dụng tools hiệu quả!
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=agent_prompt
        )
        
        return agent
    
    def _create_executor(self):
        """Tạo agent executor với configurations"""
        
        executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=self.config.max_iterations,
            max_execution_time=self.config.max_execution_time,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
        )
        
        return executor
    
    async def research(
        self,
        query: str,
        enable_deep_analysis: bool = True,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Main research method với full pipeline
        
        Args:
            query: Research question
            enable_deep_analysis: Có chạy deep analysis không
            stream: Stream response hay không
            
        Returns:
            Dict chứa research results và metadata
        """
        
        start_time = datetime.now()
        
        # Step 1: Retrieve relevant context from memory
        past_context = self.memory.get_relevant_context(query)
        chat_history = self.memory.get_short_term_history()
        
        # Step 2: Execute agent để gather information
        print(f"\n{'='*60}")
        print(f"🔍 Starting research: {query}")
        print(f"{'='*60}\n")
        
        try:
            agent_result = await self.agent_executor.ainvoke({
                "input": query,
                "chat_history": chat_history,
                "tools": self.tools
            })
            
            raw_output = agent_result.get("output", "")
            intermediate_steps = agent_result.get("intermediate_steps", [])
            
        except Exception as e:
            print(f"❌ Agent execution error: {e}")
            return {
                "query": query,
                "answer": f"Error during research: {str(e)}",
                "success": False,
                "error": str(e)
            }
        
        # Step 3: Extract data và sources từ intermediate steps
        collected_data = self._extract_data_from_steps(intermediate_steps)
        sources = self._extract_sources(intermediate_steps)
        
        # Step 4: Deep analysis (parallel execution)
        if enable_deep_analysis and collected_data:
            print("\n🔬 Running deep analysis...")
            
            analysis_result = await self._run_deep_analysis(
                query=query,
                data=collected_data,
                sources=sources
            )
        else:
            analysis_result = {"status": "skipped"}
        
        # Step 5: Synthesize final answer
        print("\n✨ Synthesizing final answer...")
        
        final_answer = await self._synthesize_answer(
            query=query,
            raw_output=raw_output,
            collected_data=collected_data,
            analysis=analysis_result,
            past_context=past_context,
            sources=sources
        )
        
        # Step 6: Save to memory
        self.memory.add_interaction(
            query=query,
            response=final_answer,
            metadata={
                "sources": sources,
                "analysis": analysis_result,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
        )
        
        # Prepare result
        result = {
            "query": query,
            "answer": final_answer,
            "sources": sources,
            "analysis": analysis_result,
            "intermediate_steps": len(intermediate_steps),
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
        print(f"\n{'='*60}")
        print(f"✅ Research completed in {result['execution_time']:.2f}s")
        print(f"{'='*60}\n")
        
        return result
    
    def _extract_data_from_steps(self, steps: List) -> str:
        """Extract collected data từ intermediate steps"""
        data_pieces = []
        
        for action, observation in steps:
            if observation and len(str(observation)) > 50:
                tool_name = action.tool
                data_pieces.append(f"[{tool_name}]\n{observation}\n")
        
        return "\n---\n".join(data_pieces) if data_pieces else "No data collected"
    
    def _extract_sources(self, steps: List) -> List[str]:
        """Extract sources từ intermediate steps"""
        sources = set()
        
        for action, observation in steps:
            # Extract URLs from observations
            import re
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', 
                            str(observation))
            sources.update(urls)
            
            # Add tool name as source type
            sources.add(f"Tool: {action.tool}")
        
        return list(sources)[:10]  # Limit to 10 sources
    
    async def _run_deep_analysis(
        self,
        query: str,
        data: str,
        sources: List[str]
    ) -> Dict[str, Any]:
        """
        Run parallel deep analysis
        Uses RunnableParallel to analyze data from multiple angles
        """
        
        try:
            # Parallel analysis
            parallel_analysis = RunnableParallel({
                "structured_analysis": self.analysis_chain,
                "quality_check": self._create_quality_check_chain()
            })
            
            analysis_input = {
                "topic": query,
                "data": data[:3000],  # Limit data length
                "sources": "\n".join(sources)
            }
            
            results = await parallel_analysis.ainvoke(analysis_input)
            
            return {
                "structured": results.get("structured_analysis", {}),
                "quality": results.get("quality_check", ""),
                "status": "completed"
            }
            
        except Exception as e:
            print(f"Analysis error: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _create_quality_check_chain(self):
        """Chain to check data quality"""
        
        quality_prompt = ChatPromptTemplate.from_template("""
Đánh giá chất lượng dữ liệu sau:

DATA: {data}
SOURCES: {sources}

Kiểm tra:
1. Completeness (đủ info không?)
2. Reliability (sources đáng tin không?)
3. Consistency (có mâu thuẫn không?)
4. Recency (thông tin mới không?)

Trả về: High/Medium/Low và giải thích ngắn gọn.
        """)
        
        return quality_prompt | self.llm | StrOutputParser()
    
    async def _synthesize_answer(
        self,
        query: str,
        raw_output: str,
        collected_data: str,
        analysis: Dict,
        past_context: str,
        sources: List[str]
    ) -> str:
        """Synthesize final comprehensive answer"""
        
        try:
            # Convert analysis to JSON-serializable format
            structured_analysis = analysis.get("structured", {})
            if hasattr(structured_analysis, 'dict'):
                structured_analysis = structured_analysis.dict()
            elif hasattr(structured_analysis, 'model_dump'):
                structured_analysis = structured_analysis.model_dump()
            
            synthesis_input = {
                "original_query": query,
                "findings": collected_data[:2000],
                "analysis": json.dumps(structured_analysis, indent=2),
                "comparison": analysis.get("quality", ""),
                "past_context": past_context[:500] if past_context else "None"
            }
            
            final_answer = await self.synthesis_chain.ainvoke(synthesis_input)
            
            # Append sources
            if sources:
                final_answer += f"\n\n**Sources:**\n"
                for i, source in enumerate(sources[:5], 1):
                    final_answer += f"{i}. {source}\n"
            
            return final_answer
            
        except Exception as e:
            print(f"Synthesis error: {e}")
            # Fallback to raw output
            return raw_output
    
    def stream_research(self, query: str):
        """Stream research results"""
        # Implement streaming logic
        pass
    
    def get_memory_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "short_term_messages": len(self.memory.get_short_term_history()),
            "long_term_documents": len(self.memory.documents),
            "summary": self.memory.get_summary()[:200]
        }