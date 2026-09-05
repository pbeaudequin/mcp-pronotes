import asyncio
import unittest
from datetime import date
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

    def test_extract_text_resource(self) -> None:
        attachment = SimpleNamespace(
            name="lesson.txt", type=1, data="Bonjour\n\nMonde".encode()
        )

        text, error = server._extract_resource_text(attachment, 1000)

        self.assertEqual(text, "Bonjour\nMonde")
        self.assertIsNone(error)

    def test_recent_resources_marks_content_untrusted(self) -> None:
        attachment = SimpleNamespace(name="lesson.txt", type=1, data=b"Revision")
        homework = SimpleNamespace(
            subject=SimpleNamespace(name="ANGLAIS LV1"),
            description="Learn the lesson",
            date=date(2026, 9, 7),
            files=[attachment],
        )
        client = SimpleNamespace(homework=lambda _from, _to: [homework])

        content = asyncio.run(
            server._handle_recent_resources(
                client,
                {"date_from": "2026-09-01", "date_to": "2026-09-10"},
                "Clement",
            )
        )

        payload = server.json.loads(content[0].text)
        self.assertTrue(payload["external_content"]["untrusted"])
        self.assertEqual(payload["resources"][0]["text"], "Revision")


if __name__ == "__main__":
    unittest.main()
