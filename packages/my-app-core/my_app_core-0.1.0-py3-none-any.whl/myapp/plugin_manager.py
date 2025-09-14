import importlib.metadata
from typing import Dict, List
from myapp.plugin_base import PluginBase

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
    
    def discover_plugins(self):
        """使用entry points发现插件"""
        entry_points = importlib.metadata.entry_points()
        
        # 查找myapp.plugins组的插件
        plugins = entry_points.select(group='myapp.plugins')
        
        for ep in plugins:
            try:
                plugin_class = ep.load()
                if (isinstance(plugin_class, type) and 
                    issubclass(plugin_class, PluginBase) and 
                    plugin_class != PluginBase):
                    
                    plugin_instance = plugin_class()
                    self.plugins[ep.name] = plugin_instance
                    print(f"✅ 加载插件: {ep.name}")
                    
            except Exception as e:
                print(f"❌ 加载插件 {ep.name} 失败: {e}")
    
    def get_plugin(self, name: str) -> PluginBase:
        """获取指定插件"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """列出所有可用插件"""
        return list(self.plugins.keys())