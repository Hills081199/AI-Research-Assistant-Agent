from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI


def create_synthesis_chain(config):
    """Chain để tổng hợp tất cả thông tin thành final answer"""
    
    llm = ChatOpenAI(
        model=config.model_name,
        temperature=0.3,  # Slightly higher for creative synthesis
        max_tokens=config.max_tokens
    )
    
    synthesis_prompt = ChatPromptTemplate.from_messages([
        ("system", """Bạn là AI research synthesizer xuất sắc.

Nhiệm vụ: Tổng hợp tất cả research findings thành một response hoàn chỉnh, coherent.

Guidelines:
1. Integrate thông tin từ nhiều nguồn một cách mượt mà
2. Highlight key insights và important findings
3. Acknowledge uncertainties và conflicting information
4. Structure response rõ ràng với headings nếu cần
5. Cite sources khi reference specific facts
6. Kết thúc với actionable insights hoặc recommendations

Format:
- Executive Summary (2-3 câu)
- Main Findings (organized by themes)
- Analysis & Insights
- Limitations & Gaps
- Recommendations
- Sources
        """),
        ("user", """
ORIGINAL QUERY: {original_query}

RESEARCH FINDINGS:
{findings}

ANALYSIS RESULTS:
{analysis}

COMPARISON INSIGHTS:
{comparison}

RELEVANT PAST CONTEXT:
{past_context}

Hãy tổng hợp tất cả thành một comprehensive answer.
        """)
    ])
    
    synthesis_chain = synthesis_prompt | llm | StrOutputParser()
    
    return synthesis_chain