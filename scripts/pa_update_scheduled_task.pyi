from typing import Optional

from typing_extensions import Literal

def main(
    *,
    task_id: str,
    command: Optional[str],
    hour: Optional[str],
    minute: Optional[str],
    **kwargs: Optional[Literal[True]]
) -> None:
    def parse_opts(*opts: str) -> str: ...
    ...
