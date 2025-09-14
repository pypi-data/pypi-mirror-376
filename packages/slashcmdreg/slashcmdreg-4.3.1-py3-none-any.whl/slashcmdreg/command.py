class SlashCommand:
    def __init__(self, name, description, callback):
        self.name = name
        self.description = description
        self.callback = callback