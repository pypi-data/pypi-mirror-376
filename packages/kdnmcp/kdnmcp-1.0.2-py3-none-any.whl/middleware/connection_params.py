"""连接参数中间件 - 用于获取SSE连接的URL参数"""

import urllib.parse
from typing import Any, Dict, Optional
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from utils.logger import app_logger as logger



class ConnectionParamsMiddleware(Middleware):
    """获取SSE连接参数的中间件"""
    
    def __init__(self):
        super().__init__()
        self.connection_params: Dict[str, Dict[str, Any]] = {}
    
    async def __call__(self, context: MiddlewareContext, call_next):
        """通用中间件入口点，处理所有类型的调用"""
        
        # 记录中间件被调用
        logger.info(f"ConnectionParamsMiddleware called with context type: {type(context)}")
        
        # 尝试从上下文中获取连接参数
        connection_info = self._extract_connection_params(context)
        
        if connection_info:
            session_id = getattr(context, 'session_id', None) or 'default'
            self.connection_params[session_id] = connection_info
            logger.info(f"Connection params for session {session_id}: {connection_info}")
        else:
            logger.info("No connection info extracted from context")
        
        # 继续处理
        return await call_next(context)
    

    
    def _extract_connection_params(self, context: MiddlewareContext) -> Optional[Dict[str, Any]]:
        """从上下文中提取连接参数"""
        connection_info = {}
        
        try:
            # 尝试使用依赖注入获取HTTP请求
            try:
                request: Request = get_http_request()
                if request:
                    connection_info['url'] = str(request.url)
                    connection_info['method'] = request.method
                    connection_info['headers'] = dict(request.headers)
                    connection_info['query_params'] = dict(request.query_params)
                    
                    # 获取客户端信息
                    if hasattr(request, 'client') and request.client:
                        connection_info['client_host'] = request.client.host
                        connection_info['client_port'] = request.client.port
                    
                    logger.info(f"Extracted HTTP request info via dependency injection: {connection_info}")
            except Exception as e:
                logger.debug(f"Could not get HTTP request via dependency injection: {e}")
            # 尝试获取其他上下文属性
            # for attr in ['method', 'request_id', 'client_id']:
            #     if hasattr(context, attr):
            #         connection_info[attr] = getattr(context, attr)
            #     elif hasattr(context, 'ctx') and hasattr(context.ctx, attr):
            #         try:
            #             if attr == 'request_id':
            #                 connection_info[attr] = context.ctx.request_id()
            #             else:
            #                 connection_info[attr] = getattr(context.ctx, attr)
            #         except:
            #             pass
            # logger.debug(f"HTTP request1: {connection_info}")

            return connection_info if connection_info else None
            
        except Exception as e:
            logger.error(f"Error extracting connection params: {e}")
            return None
    
    def get_connection_params(self, session_id: str = 'default') -> Optional[Dict[str, Any]]:
        """获取指定会话的连接参数"""
        return self.connection_params.get(session_id)
    
    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """获取所有连接的参数"""
        return self.connection_params.copy()
    
    def clear_connection(self, session_id: str):
        """清除指定会话的连接参数"""
        if session_id in self.connection_params:
            del self.connection_params[session_id]
            logger.info(f"Cleared connection params for session {session_id}")