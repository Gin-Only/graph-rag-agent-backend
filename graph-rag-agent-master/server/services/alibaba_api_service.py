from typing import Dict, Any, Optional, List, Union
import os
import json
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("alibaba_api_service")

# 加载环境变量
load_dotenv()

# 备用模型配置
FALLBACK_MODELS = {
    "qwen-turbo": ["qwen-plus", "qwen-max", "gpt-3.5-turbo"],
    "qwen-plus": ["qwen-max", "qwen-turbo", "gpt-3.5-turbo"],
    "qwen-max": ["qwen-plus", "qwen-turbo", "gpt-3.5-turbo"],
    "text-embedding-v1": ["text-embedding-v2", "text-embedding-3-small"]
}

class AlibabaAPIService:
    """阿里巴巴API服务管理类，处理API调用错误和模型回退"""
    
    def __init__(self):
        """初始化服务"""
        self.api_key = os.getenv('ALIBABA_API_KEY')
        self.base_url = os.getenv('ALIBABA_BASE_URL')
        self.current_models = {
            "llm": os.getenv('ALIBABA_LLM_MODEL', 'qwen-turbo'),
            "embeddings": os.getenv('ALIBABA_EMBEDDINGS_MODEL', 'text-embedding-v1')
        }
        self.fallback_attempts = {}
        
    def get_current_llm_model(self) -> str:
        """获取当前使用的LLM模型名称"""
        return self.current_models["llm"]
    
    def get_current_embeddings_model(self) -> str:
        """获取当前使用的嵌入模型名称"""
        return self.current_models["embeddings"]
    
    def handle_api_error(self, error: Exception, model_type: str = "llm") -> Dict[str, Any]:
        """处理API错误并尝试使用备用模型
        
        Args:
            error: 发生的异常
            model_type: 模型类型 ("llm" 或 "embeddings")
            
        Returns:
            Dict: 包含错误信息和处理结果的字典
        """
        error_str = str(error)
        current_model = self.current_models[model_type]
        logger.error(f"API调用错误 ({current_model}): {error_str}")
        
        # 解析错误信息
        error_info = self._parse_error_message(error_str)
        
        # 检查是否是模型不可用错误
        if self._is_model_unavailable_error(error_info, current_model):
            # 尝试切换到备用模型
            next_model = self._get_next_fallback_model(current_model)
            if next_model:
                logger.info(f"切换到备用模型: {next_model}")
                self.current_models[model_type] = next_model
                # 更新环境变量
                if model_type == "llm":
                    os.environ['ALIBABA_LLM_MODEL'] = next_model
                else:
                    os.environ['ALIBABA_EMBEDDINGS_MODEL'] = next_model
                    
                return {
                    "status": "fallback",
                    "message": f"模型 {current_model} 不可用，已切换到 {next_model}",
                    "new_model": next_model
                }
            else:
                return {
                    "status": "error",
                    "message": f"模型 {current_model} 不可用，且没有可用的备用模型",
                    "error": error_str
                }
        
        # 其他类型的错误
        return {
            "status": "error",
            "message": self._get_user_friendly_error_message(error_info),
            "error": error_str
        }
    
    def _parse_error_message(self, error_str: str) -> Dict[str, Any]:
        """解析错误消息，尝试提取JSON结构"""
        # 尝试提取JSON部分
        try:
            # 查找可能的JSON部分
            if "{" in error_str and "}" in error_str:
                json_start = error_str.find("{")
                json_end = error_str.rfind("}") + 1
                json_str = error_str[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # 如果无法解析JSON，返回原始错误字符串
        return {"message": error_str}
    
    def _is_model_unavailable_error(self, error_info: Dict[str, Any], model_name: str) -> bool:
        """检查是否是模型不可用错误"""
        # 检查错误消息中是否包含特定模型不可用的信息
        error_message = error_info.get("message", "") 
        if isinstance(error_message, str):
            return model_name in error_message and ("无可用渠道" in error_message or "unavailable" in error_message)
        
        # 检查嵌套的错误结构
        if "error" in error_info and isinstance(error_info["error"], dict):
            nested_message = error_info["error"].get("message", "")
            if isinstance(nested_message, str):
                return model_name in nested_message and ("无可用渠道" in nested_message or "unavailable" in nested_message)
        
        return False
    
    def _get_next_fallback_model(self, current_model: str) -> Optional[str]:
        """获取下一个备用模型"""
        # 初始化当前模型的尝试计数
        if current_model not in self.fallback_attempts:
            self.fallback_attempts[current_model] = 0
        
        # 获取备用模型列表
        fallback_list = FALLBACK_MODELS.get(current_model, [])
        
        # 检查是否有可用的备用模型
        if self.fallback_attempts[current_model] < len(fallback_list):
            next_model = fallback_list[self.fallback_attempts[current_model]]
            self.fallback_attempts[current_model] += 1
            return next_model
        
        return None
    
    def _get_user_friendly_error_message(self, error_info: Dict[str, Any]) -> str:
        """获取用户友好的错误消息"""
        # 提取错误消息
        message = ""
        
        # 检查嵌套的错误结构
        if "error" in error_info and isinstance(error_info["error"], dict):
            message = error_info["error"].get("message", "")
        else:
            message = error_info.get("message", "未知错误")
        
        # 根据错误类型提供友好消息
        if "rate limit" in str(message).lower():
            return "API请求频率超限，请稍后再试"
        elif "invalid api key" in str(message).lower():
            return "API密钥无效，请检查配置"
        elif "context length" in str(message).lower():
            return "输入内容过长，请减少文本长度"
        elif "无可用渠道" in str(message):
            return "当前模型暂时不可用，系统将尝试使用备用模型"
        
        # 默认消息
        return f"API调用失败: {message}"

# 创建全局实例
alibaba_api_service = AlibabaAPIService()