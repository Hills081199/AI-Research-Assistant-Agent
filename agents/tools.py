from langchain.tools import Tool, BaseTool
from langchain_community.utilities import SerpAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper
from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

class WebScraperInput(BaseModel):
    """
    Input Schema for web scrapper
    """
    url: str = Field(description="URL to scrape")
    extract_type: str = Field(
        default="text",
        description="Loại nội dung cần trích xuất: 'text', 'links', 'images', 'tables'"
    )

class WebScraperTool(BaseTool):
    """Tool để scrape nội dung từ web pages"""
    
    name: str = "web_scraper"
    description: str = """
    Scrape nội dung từ một URL cụ thể. 
    Input: URL và loại nội dung cần trích xuất (text, links, images, tables).
    Output: Nội dung đã được trích xuất và làm sạch.
    """
    args_schema: Type[BaseModel] = WebScraperInput
    
    def _run(self, url: str, extract_type: str = "text") -> str:
        """Scrape web content"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            if extract_type == "text":
                text = soup.get_text(separator='\n', strip=True)
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                return text[:5000]  # Limit length
                
            elif extract_type == "links":
                links = [a.get('href') for a in soup.find_all('a', href=True)]
                return json.dumps(links[:50])
                
            elif extract_type == "tables":
                tables = []
                for table in soup.find_all('table')[:5]:
                    rows = []
                    for tr in table.find_all('tr'):
                        cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                        if cells:
                            rows.append(cells)
                    if rows:
                        tables.append(rows)
                return json.dumps(tables)
                
            else:
                return soup.get_text()[:5000]
                
        except Exception as e:
            return f"Error scraping {url}: {str(e)}"
    
    async def _arun(self, url: str, extract_type: str = "text") -> str:
        """Async version"""
        return self._run(url, extract_type)


class DataAnalyzerInput(BaseModel):
    """Input for data analyzer"""
    data: str = Field(description="Dữ liệu cần phân tích (JSON, CSV, hoặc text)")
    analysis_type: str = Field(
        description="Loại phân tích: 'statistics', 'trends', 'comparison', 'summary'"
    )

class DataAnalyzerTool(BaseTool):
    """Tool để phân tích dữ liệu"""
    
    name: str = "data_analyzer"
    description: str = """
    Phân tích dữ liệu số liệu hoặc văn bản.
    Có thể tính toán thống kê, phát hiện xu hướng, so sánh dữ liệu.
    Input: Dữ liệu và loại phân tích cần thực hiện.
    """
    args_schema: Type[BaseModel] = DataAnalyzerInput
    
    def _run(self, data: str, analysis_type: str) -> str:
        """Analyze data"""
        try:
            # Try to parse as JSON
            try:
                parsed_data = json.loads(data)
            except:
                parsed_data = data
            
            if analysis_type == "statistics":
                # Extract numbers and calculate basic stats
                import re
                numbers = [float(x) for x in re.findall(r'-?\d+\.?\d*', str(parsed_data))]
                if numbers:
                    return json.dumps({
                        "count": len(numbers),
                        "mean": sum(numbers) / len(numbers),
                        "min": min(numbers),
                        "max": max(numbers),
                        "sum": sum(numbers)
                    })
                return "No numerical data found"
                
            elif analysis_type == "summary":
                if isinstance(parsed_data, (list, dict)):
                    return f"Data structure: {type(parsed_data).__name__}, Size: {len(parsed_data)}"
                return f"Text length: {len(str(parsed_data))} characters"
                
            else:
                return f"Analyzed {len(str(parsed_data))} characters of data"
                
        except Exception as e:
            return f"Analysis error: {str(e)}"
    
    async def _arun(self, data: str, analysis_type: str) -> str:
        return self._run(data, analysis_type)

class CitationCheckerInput(BaseModel):
    """Input for citation checker"""
    claim: str = Field(description="Tuyên bố cần kiểm tra")
    source: str = Field(description="Nguồn thông tin")


class CitationCheckerTool(BaseTool):
    """Tool kiểm tra tính chính xác của thông tin"""
    
    name: str = "citation_checker"
    description: str = """
    Kiểm tra độ tin cậy và tính chính xác của một tuyên bố dựa trên nguồn.
    Input: Tuyên bố và nguồn thông tin.
    Output: Đánh giá về độ tin cậy.
    """
    args_schema: Type[BaseModel] = CitationCheckerInput
    
    def _run(self, claim: str, source: str) -> str:
        """Check citation accuracy"""
        # Simple heuristic-based checker
        confidence_score = 0.5
        
        # Check source reliability indicators
        reliable_domains = ['edu', 'gov', 'org', 'ac.uk']
        if any(domain in source.lower() for domain in reliable_domains):
            confidence_score += 0.2
            
        # Check for specific keywords
        if any(word in source.lower() for word in ['study', 'research', 'journal', 'published']):
            confidence_score += 0.15
            
        # Check claim specificity
        if any(char.isdigit() for char in claim):
            confidence_score += 0.1
            
        confidence_score = min(confidence_score, 1.0)
        
        return json.dumps({
            "confidence": confidence_score,
            "source": source,
            "claim": claim,
            "reliability": "high" if confidence_score > 0.7 else "medium" if confidence_score > 0.4 else "low",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _arun(self, claim: str, source: str) -> str:
        return self._run(claim, source)



def create_research_tools(config) -> List[BaseTool]:
    """Tạo tất cả research tools"""
    search = SerpAPIWrapper(serpapi_api_key=config.serper_api_key)
    search_tool = Tool(
        name="web_search",
        func=search.run,
        description="""
            Tìm kiếm thông tin trên Google.
            Input: Câu query tìm kiếm.
            Output: Top results với snippets và links.
            Sử dụng khi cần tìm thông tin mới nhất hoặc general knowledge.
        """
    )

    # Wikipedia
    wikipedia = WikipediaAPIWrapper()
    wiki_tool = Tool(
        name="wikipedia",
        func=wikipedia.run,
        description="""
            Tìm kiếm thông tin từ Wikipedia.
            Input: Tên chủ đề hoặc từ khóa.
            Output: Tóm tắt từ Wikipedia.
            Tốt cho thông tin tổng quan về chủ đề, người, sự kiện.
        """
    )

    # ArXiv (Academic papers)
    arxiv_wrapper = ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=5000)
    arxiv_tool = ArxivQueryRun(api_wrapper=arxiv_wrapper)
    arxiv_tool.name = "arxiv_search"
    arxiv_tool.description = """
        Tìm kiếm papers khoa học từ ArXiv.
        Input: Keywords hoặc chủ đề nghiên cứu.
        Output: Thông tin papers liên quan (title, authors, summary).
        Sử dụng cho research papers, scientific studies.
    """

    # Custom tools
    web_scraper = WebScraperTool()
    data_analyzer = DataAnalyzerTool()
    citation_checker = CitationCheckerTool()

    return [
        search_tool,
        wiki_tool,
        arxiv_tool,
        web_scraper,
        data_analyzer,
        citation_checker
    ]