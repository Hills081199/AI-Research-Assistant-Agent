import asyncio
import sys
import codecs
from config import AgentConfig
from agents.research_agent import ResearchAgent
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

console = Console(force_terminal=True, legacy_windows=False)


def run_demo_research():
    """Demo research without API calls"""
    
    # Demo result for testing
    demo_result = {
        "query": "Cơ hội và việc làm trong lĩnh vực STEM ở Việt Nam năm 2025",
        "answer": """# Cơ Hội và Việc Làm STEM ở Việt Nam 2025

## 🎯 **Tổng Quan**
Lĩnh vực STEM (Science, Technology, Engineering, Mathematics) đang phát triển mạnh mẽ tại Việt Nam, mở ra nhiều cơ hội việc làm hấp dẫn.

## 📈 **Cơ Hội Việc Làm**

### **1. Công Nghệ Thông Tin**
- **AI/Machine Learning Engineer**: $1,200-2,500/tháng
- **Data Scientist**: $1,000-2,000/tháng  
- **Software Developer**: $800-1,800/tháng
- **Cybersecurity Specialist**: $900-2,000/tháng

### **2. Kỹ Thuật & Sản Xuất**
- **Automation Engineer**: $700-1,500/tháng
- **Robotics Engineer**: $1,000-2,000/tháng
- **Quality Control Engineer**: $600-1,200/tháng

### **3. Nghiên Cứu & Phát Triển**
- **R&D Scientist**: $800-1,800/tháng
- **Lab Technician**: $500-1,000/tháng
- **Product Development Engineer**: $900-1,900/tháng

## 🏢 **Các Công Ty Tuyển Dụng Lớn**
- FPT Software
- VNG Corporation
- KMS Technology
- TMA Solutions
- Viettel
- Samsung Vietnam
- Intel Vietnam

## 🎓 **Kỹ Năng Cần Thiết**
- **Programming**: Python, Java, C++, JavaScript
- **Data Analysis**: SQL, Excel, R, Python
- **Cloud Computing**: AWS, Azure, GCP
- **AI/ML**: TensorFlow, PyTorch, Scikit-learn
- **Soft Skills**: English, Teamwork, Problem-solving

## 📚 **Học Thêm Nơi Đâu?**
- Đại học Bách Khoa Hà Nội
- Đại học Công nghệ - ĐHQGHN
- Đại học FPT
- Coursera, edX
- Google Career Certificates

## 🔮 **Xu Hướng 2025**
- AI và Machine Learning bùng nổ
- IoT và Smart Cities phát triển
- Green Technology và Sustainability
- Remote Work tăng mạnh
- Startup ecosystem lớn mạnh

## 💡 **Lời Khuyên**
1. **Học liên tục**: Công nghệ thay đổi nhanh
2. **Thực tế**: Làm dự án thực tế
3. **Networking**: Tham gia cộng đồng
4. **English**: Rất quan trọng cho công ty đa quốc gia

---

*Phân tích dựa trên dữ liệu thị trường lao động 2024-2025*""",
        "sources": [
            "Tool: web_search",
            "Tool: wikipedia", 
            "Tool: data_analyzer",
            "https://www.topcv.vn/tin-tuc/ung-tuyen-viec-lam-it-2025",
            "https://vietnamworks.com/blog/trend-it-2025",
            "https://www.fpt-software.com/news/career-2025"
        ],
        "analysis": {
            "structured": {
                "key_findings": [
                    "STEM fields growing 25% annually in Vietnam",
                    "AI/ML positions have highest salary potential",
                    "English proficiency crucial for international companies",
                    "Remote work opportunities increasing significantly"
                ],
                "data_quality": "high",
                "confidence_score": 0.85,
                "recommendations": [
                    "Focus on AI/ML skills for highest ROI",
                    "Develop English communication skills",
                    "Build portfolio with real projects",
                    "Network through tech communities"
                ],
                "sources_used": [
                    "web_search",
                    "wikipedia", 
                    "data_analyzer"
                ]
            },
            "quality": "High quality data from multiple reliable sources including job portals and company reports. Recent and relevant to 2025 market trends.",
            "status": "completed"
        },
        "intermediate_steps": 8,
        "execution_time": 2.5,
        "timestamp": "2025-02-09T10:30:00",
        "success": True
    }
    
    # Display results
    console.print("\n" + "="*60)
    console.print(Panel(
        Markdown(demo_result["answer"]),
        title="[bold green]Demo Research Results[/bold green]",
        border_style="green"
    ))
    
    # Metadata
    console.print(f"\n[dim]⏱️  Execution time: {demo_result['execution_time']:.2f}s[/dim]")
    console.print(f"[dim]🔧 Intermediate steps: {demo_result['intermediate_steps']}[/dim]")
    
    # Analysis insights
    if demo_result.get("analysis", {}).get("structured"):
        analysis = demo_result["analysis"]["structured"]
        
        console.print(f"\n[bold cyan]Analysis Insights:[/bold cyan]")
        console.print(f"  • Confidence: {analysis.get('confidence_score', 0):.2%}")
        console.print(f"  • Data Quality: {analysis.get('data_quality', 'unknown')}")
        
        if analysis.get('key_findings'):
            console.print(f"\n[bold]Key Findings:[/bold]")
            for finding in analysis['key_findings'][:3]:
                console.print(f"  • {finding}")
    
    # Sources
    console.print(f"\n[bold yellow]Sources:[/bold yellow]")
    for i, source in enumerate(demo_result['sources'][:5], 1):
        console.print(f"  {i}. {source}")
    
    # Save to file
    with open("demo_research_result.json", "w", encoding="utf-8") as f:
        json.dump(demo_result, f, indent=2, ensure_ascii=False)
    
    console.print("\n[green]✓ Demo results saved to demo_research_result.json[/green]")
    console.print("\n[yellow]💡 Note: This is demo data. To use real AI research, please:[/yellow]")
    console.print("   1. Check your OpenAI API quota at https://platform.openai.com")
    console.print("   2. Add credits to your account")
    console.print("   3. Or use a different API key")


if __name__ == "__main__":
    console.print(Panel.fit(
        "🤖 [bold blue]AI Research Assistant - Demo Mode[/bold blue]\n"
        "Demo research without API calls",
        border_style="blue"
    ))
    
    run_demo_research()
