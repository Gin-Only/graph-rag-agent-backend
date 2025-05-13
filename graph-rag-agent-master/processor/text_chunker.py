import hanlp
from typing import List, Tuple

class ChineseTextChunker:
    """中文文本分块器，将长文本分割成带有重叠的文本块"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        """
        初始化分块器
        
        Args:
            chunk_size: 每个文本块的目标大小（tokens数量）
            overlap: 相邻文本块的重叠大小（tokens数量）
        """
        if chunk_size <= overlap:
            raise ValueError("chunk_size必须大于overlap")
            
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
        
    def process_files(self, file_contents: List[Tuple[str, str]]) -> List[Tuple[str, str, List[List[str]]]]:
        """
        处理多个文件的内容
        
        Args:
            file_contents: List of (filename, content) tuples
            
        Returns:
            List of (filename, content, chunks) tuples
        """
        results = []
        for filename, content in file_contents:
            chunks = self.chunk_text(content)
            results.append((filename, content, chunks))
        return results
        
    def chunk_text(self, text: str) -> List[List[str]]:
        """
        将单个文本分割成块
        
        Args:
            text: 要分割的文本
            
        Returns:
            分割后的文本块列表，每个块是token列表
        """
        # 处理空文本或太短的文本
        if not text or len(text) < self.chunk_size / 10:  # 如果文本长度不到chunk_size的1/10
            # 尝试简单分词并返回单个块
            try:
                tokens = self.tokenizer(text)
                return [tokens] if tokens else []
            except Exception as e:
                print(f"分词失败：{str(e)}")
                # 如果连分词都失败，则手动分字符
                return [[char for char in text]] if text else []
                
        paragraphs = text.split('\n')
        chunks = []
        buffer = []
        
        i = 0
        while i < len(paragraphs):
            # 填充buffer
            while len(buffer) < self.chunk_size and i < len(paragraphs):
                try:
                    tokens = self.tokenizer(paragraphs[i])
                    buffer.extend(tokens)
                except Exception as e:
                    print(f"分词失败 ({i}): {str(e)}")
                    # 如果分词失败，直接按字符添加
                    buffer.extend([char for char in paragraphs[i]])
                i += 1
                
            # 空buffer检查
            if not buffer:
                continue
                    
            # 处理当前buffer
            while len(buffer) >= self.chunk_size:
                try:
                    end = self._find_next_sentence_end(buffer, self.chunk_size)
                    chunk = buffer[:end]
                    chunks.append(chunk)
                    
                    start_next = self._find_previous_sentence_end(buffer, end - self.overlap)
                    if start_next == 0:
                        start_next = self._find_previous_sentence_end(buffer, end - 1)
                    if start_next == 0:
                        start_next = max(0, end - self.overlap)
                        
                    buffer = buffer[start_next:]
                except IndexError:
                    # 处理可能的索引错误
                    print("处理buffer时出现索引错误，使用安全分块")
                    mid = len(buffer) // 2
                    chunks.append(buffer[:mid])
                    buffer = buffer[max(0, mid - self.overlap):]
        
        # 处理剩余内容
        if buffer:
            if not chunks:  # 如果之前没有生成任何块
                chunks.append(buffer)
            else:
                last_chunk = chunks[-1]
                # 安全检查：确保索引有效
                if len(last_chunk) >= len(buffer):
                    rest = ''.join(buffer)
                    temp = ''.join(last_chunk[len(last_chunk)-len(buffer):])
                    if temp != rest:
                        chunks.append(buffer)
                else:
                    # 索引无效，直接添加剩余内容
                    chunks.append(buffer)
                    
        return chunks
    
    def _is_sentence_end(self, token: str) -> bool:
        """判断token是否为句子结束符"""
        return token in ['。', '！', '？']
    
    def _find_next_sentence_end(self, tokens: List[str], start_pos: int) -> int:
        """从指定位置向后查找句子结束位置"""
        for i in range(start_pos, len(tokens)):
            if self._is_sentence_end(tokens[i]):
                return i + 1
        return len(tokens)
    
    def _find_previous_sentence_end(self, tokens: List[str], start_pos: int) -> int:
        """从指定位置向前查找句子结束位置"""
        for i in range(start_pos - 1, -1, -1):
            if self._is_sentence_end(tokens[i]):
                return i + 1
        return 0