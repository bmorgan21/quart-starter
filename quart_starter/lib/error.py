class ActionError(ValueError):
    def __init__(self, msg, loc=None, type=None):
        super().__init__(msg)

        self.loc = loc
        self.type = type or "value_error"
