from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from build_graph import KnowledgeGraphBuilder
from build_index_and_community import IndexCommunityBuilder
from build_chunk_index import ChunkIndexBuilder

class KnowledgeGraphProcessor:
    """
    知识图谱处理器，整合了图谱构建和索引处理的完整流程。
    可以选择完整流程或单独执行其中一个步骤。
    """
    
    def __init__(self):
        """初始化知识图谱处理器"""
        self.console = Console()
        
    def process_all(self):
        """执行完整的处理流程"""
        try:
            # 显示开始面板
            start_text = Text("开始知识图谱处理流程", style="bold cyan")
            self.console.print(Panel(start_text, border_style="cyan"))
            
            # 1. 构建基础图谱
            graph_builder = KnowledgeGraphBuilder()
            graph_builder.process()
            
            # 2. 构建实体索引和社区
            index_builder = IndexCommunityBuilder()
            index_builder.process()
            
            # 3. 构建Chunk索引
            chunk_index_builder = ChunkIndexBuilder()
            chunk_index_builder.process()
            
            # 显示完成面板
            success_text = Text("知识图谱处理流程完成", style="bold green")
            self.console.print(Panel(success_text, border_style="green"))
            
        except Exception as e:
            error_text = Text(f"处理过程中出现错误: {str(e)}", style="bold red")
            self.console.print(Panel(error_text, border_style="red"))
            raise

if __name__ == "__main__":
    try:
        processor = KnowledgeGraphProcessor()
        processor.process_all()
    except Exception as e:
        console = Console()
        console.print(f"[red]执行过程中出现错误: {str(e)}[/red]")