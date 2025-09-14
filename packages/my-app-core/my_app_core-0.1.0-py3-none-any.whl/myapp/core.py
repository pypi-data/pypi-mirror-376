from myapp.plugin_manager import PluginManager

class MyApp:
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.plugin_manager.discover_plugins()
    
    def run(self):
        print("可用插件:", self.plugin_manager.list_plugins())
        
        # 使用插件
        for name, plugin in self.plugin_manager.plugins.items():
            print(f"\n运行插件: {name}")
            result = plugin.execute("测试数据")
            print(f"结果: {result}")

def main():
    app = MyApp()
    app.run()

if __name__ == "__main__":
    main()