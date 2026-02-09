from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class AnalysisResult(BaseModel):
    """Schema cho analysis output"""
    key_findings: List[str] = Field(description="Các phát hiện chính")
    data_quality: str = Field(description="Đánh giá chất lượng dữ liệu: high/medium/low")
    confidence_score: float = Field(description="Độ tin cậy từ 0-1")
    recommendations: List[str] = Field(description="Đề xuất bước tiếp theo")
    sources_used: List[str] = Field(description="Các nguồn đã sử dụng")

def create_analysis_chain(config):
    """Tạo chain để phân tích dữ liệu research"""
    llm = ChatOpenAI(
        model_name=config.model_name,
        temperature=config.temperature,
        openai_api_key=config.openai_api_key,
        max_tokens=config.max_tokens,
    )

    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", """Bạn là một AI research analyst chuyên nghiệp.
        
            Nhiệm vụ của bạn:
            1. Phân tích dữ liệu được cung cấp một cách khách quan
            2. Xác định các patterns, trends, và insights quan trọng
            3. Đánh giá chất lượng và độ tin cậy của dữ liệu
            4. Đưa ra recommendations cho bước tiếp theo

            Luôn:
            - Dựa trên evidence cụ thể
            - Phân biệt facts vs opinions
            - Chỉ ra gaps trong dữ liệu
            - Đề xuất cách verify thông tin
                    """),
                    ("user", """Hãy phân tích dữ liệu sau:

            TOPIC: {topic}

            DATA COLLECTED:
            {data}

            SOURCES:
            {sources}

            Trả về phân tích theo format JSON với các trường:
            - key_findings: list các phát hiện chính
            - data_quality: "high", "medium", hoặc "low"
            - confidence_score: số từ 0 đến 1
            - recommendations: list các đề xuất
            - sources_used: list các nguồn đã dùng"""
        )
    ])

    # Parser
    json_parser = PydanticOutputParser(pydantic_object=AnalysisResult)

        # build chain
    analysis_chain = (
            analysis_prompt 
            | llm
            | json_parser
        ).with_retry(
            stop_after_attempt=config.max_retries,
            wait_exponential_jitter=True
        )

    return analysis_chain

def create_comparision_chain(config):
    "Chain để so sánh nhiều nguồn thông tin"
    llm = ChatOpenAI(
        model_name = config.model_name,
        temperature = config.temperature,
        openai_api_key = config.openai_api_key,
        max_tokens = config.max_tokens,
    )
    
    comparision_prompt = ChatPromptTemplate.from_template("""
        Hãy so sánh các nguồn thông tin sau về topic: {topic}

        SOURCE 1: {source1_name}
        {source1_content}

        SOURCE 2: {source2_name}
        {source2_content}

        SOURCE 3 (nếu có): {source3_name}
        {source3_content}

        Phân tích:
        1. Điểm tương đồng giữa các nguồn
        2. Điểm khác biệt hoặc mâu thuẫn
        3. Nguồn nào đáng tin cậy hơn và tại sao
        4. Kết luận tổng hợp

        Trả về dưới dạng structured analysis.
    """)

    comparision_chain = comparision_prompt | llm | StrOutputParser()
    return comparision_chain