"""Safe structured errors for offline tooling; never include raw imported payloads."""


class ToolError(RuntimeError):
    def __init__(self, code: str, message: str, exit_code: int = 4, **context) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.context = context

    def as_dict(self) -> dict:
        return {
            "committed": False,
            "graph_counts": None,
            "error": {"code": self.code, "message": str(self)},
            **self.context,
        }
