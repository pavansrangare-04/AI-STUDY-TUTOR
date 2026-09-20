"""
Automated Test Suite for Virtual AI Tutor Web Application
Verifies Authentication, Database Models, RAG Search, AI Provider, Chat API, Quiz Evaluation, and RBAC.
"""
import unittest
from app import create_app
from models import db, User, Subject, Topic, StudyMaterial, MaterialChunk, Quiz, Conversation
from rag_engine import RAGEngine
from ai_provider import AIProvider
from quiz_engine import QuizEngine


class VirtualAITutorTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_01_database_and_seed_data(self):
        """Verify initial database schema and academic seed records."""
        with self.app.app_context():
            # Check users
            admin = User.query.filter_by(username="admin").first()
            student = User.query.filter_by(username="student").first()
            self.assertIsNotNone(admin, "Admin user should exist in seed data.")
            self.assertTrue(admin.is_admin, "Admin user must have admin role.")
            self.assertIsNotNone(student, "Student user should exist.")

            # Check subjects
            subjects = Subject.query.all()
            self.assertGreaterEqual(len(subjects), 4, "Should have at least 4 academic subjects.")
            os_sub = Subject.query.filter_by(code="CS301").first()
            self.assertIsNotNone(os_sub, "Operating Systems (CS301) must exist.")

            # Check indexed chunks
            chunks_count = MaterialChunk.query.count()
            self.assertGreater(chunks_count, 5, "RAG chunks must be indexed.")
            print(f"[TEST PASS] Database has {len(subjects)} subjects and {chunks_count} indexed RAG chunks.")

    def test_02_rag_search_retrieval(self):
        """Verify RAG engine retrieves relevant course notes with BM25 scoring."""
        with self.app.app_context():
            results = RAGEngine.search("What is paging and virtual memory?", min_score=0.10)
            self.assertGreater(len(results), 0, "RAG should find chunks for 'paging and virtual memory'.")
            top_result = results[0]
            self.assertIn("Operating Systems", top_result["subject_name"])
            self.assertTrue("paging" in top_result["text"].lower() or "memory" in top_result["text"].lower())
            print(f"[TEST PASS] RAG search matched: '{top_result['material_title']}' with score {top_result['score']}")

    def test_03_ai_provider_response(self):
        """Verify AI provider returns structured answer with source citations."""
        with self.app.app_context():
            res = AIProvider.generate_response(
                question="What is paging in operating systems?",
                conversation_history=[],
                user_level="intermediate",
                user_style="detailed",
            )
            self.assertIn("content", res)
            self.assertGreater(len(res["content"]), 50)
            self.assertTrue(res["is_grounded"], "Paging question should be grounded in course notes.")
            self.assertGreater(len(res["sources"]), 0, "Must include source references.")
            print(f"[TEST PASS] AI Provider returned response with {len(res['sources'])} sources.")

    def test_04_auth_flow(self):
        """Verify user login and session authentication."""
        # 1. Successful login
        resp = self.client.post("/login", data={"username": "student", "password": "student123"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Welcome back", resp.data)

        # Logout before testing invalid login
        self.client.get("/logout")

        # 2. Invalid login
        resp2 = self.client.post("/login", data={"username": "student", "password": "wrongpassword"}, follow_redirects=True)
        self.assertIn(b"Invalid username", resp2.data)
        print("[TEST PASS] Auth flow validated.")

    def test_05_chat_api(self):
        """Verify full chat creation and message sending workflow."""
        # Log in as student
        self.client.post("/login", data={"username": "student", "password": "student123"}, follow_redirects=True)

        # 1. Create new conversation
        res = self.client.post("/api/chat/new", json={"title": "Test Chat OS"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        conv_id = data["id"]
        self.assertIsNotNone(conv_id)

        # 2. Send educational question
        msg_res = self.client.post(f"/api/chat/{conv_id}/message", json={"question": "Explain CPU scheduling algorithms"})
        self.assertEqual(msg_res.status_code, 200)
        msg_data = msg_res.get_json()
        self.assertTrue(msg_data["success"])
        self.assertIn("content", msg_data)

        # 3. Rename conversation
        ren_res = self.client.post(f"/api/chat/{conv_id}/rename", json={"title": "Updated CPU Title"})
        self.assertEqual(ren_res.status_code, 200)

        # 4. Message feedback
        msg_id = msg_data["message_id"]
        fb_res = self.client.post(f"/api/chat/{conv_id}/feedback", json={"message_id": msg_id, "rating": "helpful"})
        self.assertEqual(fb_res.status_code, 200)
        print(f"[TEST PASS] Chat API verified with conversation #{conv_id}.")

    def test_06_quiz_submission_and_scoring(self):
        """Verify quiz evaluation and analytics recording."""
        self.client.post("/login", data={"username": "student", "password": "student123"}, follow_redirects=True)

        with self.app.app_context():
            quiz = Quiz.query.first()
            questions = quiz.questions.all()
            # Submit answers where 1st is correct
            sample_answers = {str(questions[0].id): questions[0].correct_option}
            for q in questions[1:]:
                sample_answers[str(q.id)] = "A"

            submit_res = self.client.post(f"/api/quiz/{quiz.id}/submit", json={"answers": sample_answers})
            self.assertEqual(submit_res.status_code, 200)
            res_data = submit_res.get_json()
            self.assertTrue(res_data["success"])
            self.assertGreaterEqual(res_data["result"]["score"], 1)
            print(f"[TEST PASS] Quiz scored: {res_data['result']['score']}/{res_data['result']['total']} ({res_data['result']['accuracy_pct']}%)")

    def test_07_admin_rbac(self):
        """Verify student is forbidden from admin routes and admin is allowed."""
        # 1. Student access blocked
        self.client.get("/logout")
        self.client.post("/login", data={"username": "student", "password": "student123"}, follow_redirects=True)
        resp = self.client.get("/admin", follow_redirects=True)
        self.assertIn(b"Access denied", resp.data)

        # 2. Admin access allowed
        self.client.get("/logout")
        self.client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        resp2 = self.client.get("/admin", follow_redirects=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertIn(b"Curriculum", resp2.data)
        print("[TEST PASS] Admin RBAC properly enforced.")


if __name__ == "__main__":
    unittest.main()
