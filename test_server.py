import unittest
from types import SimpleNamespace

import server


class TestHomeworkFormatting(unittest.TestCase):
    def test_resources_include_files_and_links(self) -> None:
        homework = SimpleNamespace(
            subject=SimpleNamespace(name="Maths"),
            description="Exercises",
            date=None,
            done=False,
            background_color="#fff",
            files=[
                SimpleNamespace(name="sheet.pdf", type=1, url="https://file"),
                SimpleNamespace(name="Reference", type=0, url="https://link"),
            ],
        )

        result = server._format_homework(homework)

        self.assertEqual(
            result["resources"],
            [
                {"name": "sheet.pdf", "type": "file", "url": "https://file"},
                {"name": "Reference", "type": "link", "url": "https://link"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
