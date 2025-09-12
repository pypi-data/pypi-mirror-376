from mcp.server import FastMCP

mcp = FastMCP("kitten mcp server")

@mcp.tool()
def hello_world():
    """
    测试kitten服务是否正常

    :return:
    """
    return "Hello World!"

def main():
    """启动MCP服务器"""
    mcp.run()


if __name__ == "__main__":
    main()