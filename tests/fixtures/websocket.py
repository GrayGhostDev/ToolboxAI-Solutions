class MockWebSocket:
    async def send(self, msg):
        pass

    async def receive(self):
        return {"type": "test"}

    async def close(self):
        pass


def create_websocket():
    return MockWebSocket()
