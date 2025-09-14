class LightpadClient:
    def __init__(self, host: str):
        self.host = host

    def connect(self):
        print(f"Connecting to Lightpads at {self.host}...")

    def set_color(self, pad_id: int, color: str):
        print(f"Pad {pad_id} -> {color}")

    def run(self):
        print("Running event loop (stub)...")
