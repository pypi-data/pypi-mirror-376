from abc import ABC, abstractmethod

class PluginBase(ABC):
    """所有插件必须继承的基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """返回插件名称"""
        pass
    
    @abstractmethod
    def execute(self, data):
        """执行插件功能"""
        pass