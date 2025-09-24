class MockGraph:
    def add_node(self, n): pass
    def add_edge(self, f, t): pass
    async def run(self, i): return {'status': 'success'}
def create_graph(): return MockGraph()