from __future__ import annotations

from wexample_helpers.decorator.base_class import base_class
from wexample_prompt.example.abstract_response_example import AbstractResponseExample


@base_class
class ListExample(AbstractResponseExample):
    def example_class(self):
        from wexample_prompt.responses.data.list_prompt_response import (
            ListPromptResponse,
        )

        return ListPromptResponse.create_list(
            items=self.get_test_items(),
        )

    def example_extended(self) -> None:
        self._class_with_methods.list(items=self.get_test_items())

    def example_manager(self) -> None:
        self.io.list(items=self.get_test_items())

    def get_test_items(self) -> list[str]:
        return [
            "Item A",
            "  Sub-item A1",
            "  Sub-item A2",
            "Item B",
        ]
