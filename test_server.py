import asyncio
import os
import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

import server


class TestHomeworkFormatting(unittest.TestCase):
    def test_resources_include_files_and_links(self) -> None:
        homework = SimpleNamespace(
            id="hw-1",
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

        self.assertEqual(result["homework_id"], "hw-1")
        self.assertEqual(result["status"], "à faire")
        self.assertEqual(result["status_emoji"], "⏳")
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

    def test_scanned_pdf_falls_back_to_ocr(self) -> None:
        attachment = SimpleNamespace(
            name="scan.pdf", type=1, data=b"%PDF scanned"
        )

        with (
            patch.object(server, "PdfReader") as reader,
            patch.object(server, "_ocr_resource", return_value=("Texte OCR", False)),
        ):
            reader.return_value.pages = [SimpleNamespace(extract_text=lambda: "")]
            text, error = server._extract_resource_text(attachment, 1000)

        self.assertEqual(text, "Texte OCR")
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

    def test_school_profile_only_exposes_homework_and_resources(self) -> None:
        previous = os.environ.get("PRONOTE_TOOL_PROFILE")
        os.environ["PRONOTE_TOOL_PROFILE"] = "school"
        try:
            tools = asyncio.run(server.list_tools())
        finally:
            if previous is None:
                os.environ.pop("PRONOTE_TOOL_PROFILE", None)
            else:
                os.environ["PRONOTE_TOOL_PROFILE"] = previous

        self.assertEqual(
            {tool.name for tool in tools},
            {
                "get_homework",
                "get_recent_resources",
                "get_recent_course_materials",
                "set_homework_status",
            },
        )

    def test_default_child_is_explicitly_reselected(self) -> None:
        client = SimpleNamespace(
            children=[SimpleNamespace(name="Clement")],
            set_child=Mock(),
        )

        selected = server._select_child(client)

        self.assertEqual(selected, "Clement")
        client.set_child.assert_called_once_with("Clement")

    def test_set_homework_status_updates_and_verifies(self) -> None:
        current = SimpleNamespace(id="hw-7", done=False, set_done=Mock())
        verified = SimpleNamespace(
            id="hw-7",
            done=True,
            subject=SimpleNamespace(name="MATHEMATIQUES"),
            description="Calculer les quotients",
        )
        client = SimpleNamespace(homework=Mock(side_effect=[[current], [verified]]))

        result = asyncio.run(
            server._handle_set_homework_status(
                client,
                {
                    "homework_id": "hw-7",
                    "due_date": "2026-09-08",
                    "done": True,
                    "child_name": "Clement",
                },
                "Clement",
            )
        )

        payload = server.json.loads(result[0].text)
        current.set_done.assert_called_once_with(True)
        self.assertTrue(payload["success"])
        self.assertTrue(payload["verified"])
        self.assertEqual(payload["new_status"], "terminé")
        self.assertEqual(payload["new_status_emoji"], "✅")

    def test_set_homework_status_is_idempotent(self) -> None:
        current = SimpleNamespace(
            id="hw-7",
            done=True,
            subject=SimpleNamespace(name="MATHEMATIQUES"),
            description="Calculer les quotients",
            set_done=Mock(),
        )
        client = SimpleNamespace(homework=Mock(side_effect=[[current], [current]]))

        result = asyncio.run(
            server._handle_set_homework_status(
                client,
                {
                    "homework_id": "hw-7",
                    "due_date": "2026-09-08",
                    "done": True,
                    "child_name": "Clement",
                },
                "Clement",
            )
        )

        payload = server.json.loads(result[0].text)
        current.set_done.assert_not_called()
        self.assertTrue(payload["success"])
        self.assertFalse(payload["changed"])

    def test_set_homework_status_rejects_stale_id(self) -> None:
        client = SimpleNamespace(homework=lambda _from, _to: [])

        with self.assertRaisesRegex(ValueError, "introuvable ou périmé"):
            asyncio.run(
                server._handle_set_homework_status(
                    client,
                    {
                        "homework_id": "stale",
                        "due_date": "2026-09-08",
                        "done": True,
                        "child_name": "Clement",
                    },
                    "Clement",
                )
            )

    def test_set_homework_status_reports_failed_verification(self) -> None:
        current = SimpleNamespace(id="hw-7", done=False, set_done=Mock())
        still_pending = SimpleNamespace(id="hw-7", done=False)
        client = SimpleNamespace(
            homework=Mock(side_effect=[[current], [still_pending]])
        )

        result = asyncio.run(
            server._handle_set_homework_status(
                client,
                {
                    "homework_id": "hw-7",
                    "due_date": "2026-09-08",
                    "done": True,
                    "child_name": "Clement",
                },
                "Clement",
            )
        )

        payload = server.json.loads(result[0].text)
        self.assertFalse(payload["success"])
        self.assertFalse(payload["verified"])
        self.assertTrue(payload["write_attempted"])
        self.assertNotIn("changed", payload)

    def test_write_tool_requires_child_name(self) -> None:
        previous = os.environ.get("PRONOTE_TOOL_PROFILE")
        os.environ["PRONOTE_TOOL_PROFILE"] = "school"
        try:
            result = asyncio.run(
                server.call_tool(
                    "set_homework_status",
                    {
                        "homework_id": "hw-7",
                        "due_date": "2026-09-08",
                        "done": True,
                    },
                )
            )
        finally:
            if previous is None:
                os.environ.pop("PRONOTE_TOOL_PROFILE", None)
            else:
                os.environ["PRONOTE_TOOL_PROFILE"] = previous

        payload = server.json.loads(result[0].text)
        self.assertIn("child_name est obligatoire", payload["error"])

    def test_recent_course_materials_reads_lesson_content(self) -> None:
        lesson = SimpleNamespace(
            id="lesson-1",
            start=server.datetime(2026, 9, 4, 10, 0),
            subject=SimpleNamespace(name="MATHEMATIQUES"),
        )
        client = SimpleNamespace(
            lessons=lambda _from, _to: [lesson],
            get_week=lambda _date: 36,
            post=lambda *_args: {
                "dataSec": {
                    "data": {
                        "ListeCahierDeTextes": {
                            "V": [
                                {
                                    "cours": {"V": {"N": "lesson-1"}},
                                    "listeContenus": {"V": [{"raw": True}]},
                                }
                            ]
                        }
                    }
                }
            },
        )
        course_content = SimpleNamespace(
            title="Calcul de quotients",
            category="Support de cours",
            description="Méthode à réviser",
            files=[SimpleNamespace(name="cours.txt", type=1, data=b"Exemple")],
        )

        with patch.object(
            server.pronotepy, "LessonContent", return_value=course_content
        ):
            result = asyncio.run(
                server._handle_recent_course_materials(
                    client,
                    {"date_from": "2026-09-01", "date_to": "2026-09-05"},
                    "Clement",
                )
            )

        payload = server.json.loads(result[0].text)
        self.assertTrue(payload["external_content"]["untrusted"])
        self.assertEqual(payload["material_count"], 1)
        self.assertEqual(payload["materials"][0]["resources"][0]["text"], "Exemple")


if __name__ == "__main__":
    unittest.main()
