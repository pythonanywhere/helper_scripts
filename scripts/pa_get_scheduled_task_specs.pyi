from typing import Optional

from typing_extensions import Literal

def main(*, task_id: int, **kwargs: Optional[Literal[True]]) -> None: ...
