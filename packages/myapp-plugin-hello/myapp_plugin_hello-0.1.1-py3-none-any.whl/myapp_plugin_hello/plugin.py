from myapp.plugin_base import PluginBase

class HelloPlugin(PluginBase):
    def get_name(self) -> str:
        return "hello"
    
    def execute(self, data):
        return f"Hello, {data}!"

# 插件入口点函数
def register():
    return HelloPlugin