from typing import Optional

from typing_extensions import Literal

def main(
    command: str, hour: Optional[str], minute: str, disabled: Optional[Literal[True]]
) -> None: ...
