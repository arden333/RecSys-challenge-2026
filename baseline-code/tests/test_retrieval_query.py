import unittest

from mcrs.custom_crs_baseline import CRS_BASELINE


class FakeRetriever:
    def __init__(self):
        self.queries = []

    def text_to_item_retrieval(self, query, topk):
        self.queries.append(query)
        return [f"track-{index}" for index in range(topk)]

    def batch_text_to_item_retrieval(self, queries, topk):
        self.queries.extend(queries)
        return [[f"track-{index}" for index in range(topk)] for _ in queries]


class FakeItemDB:
    def id_to_metadata(self, track_id):
        return {"track_id": track_id}


class RetrievalQueryTests(unittest.TestCase):
    def setUp(self):
        self.crs = CRS_BASELINE.__new__(CRS_BASELINE)
        self.crs.retrieval = FakeRetriever()
        self.crs.item_db = FakeItemDB()
        self.crs.generate_response = False
        self.crs.session_memory = []

    def test_first_turn_matches_existing_query(self):
        result = self.crs.batch_chat([
            {"user_query": "energetic electronic music", "user_id": "user-1", "session_memory": []}
        ])

        self.assertEqual(self.crs.retrieval.queries, ["user: energetic electronic music"])
        self.assertEqual(len(result[0]["retrieval_items"]), 20)

    def test_later_turn_preserves_full_history(self):
        history = [
            {"role": "user", "content": "I like electronic music"},
            {"role": "assistant", "content": "Try this synthpop track"},
            {"role": "assistant", "content": {"track_name": "Old Song", "tag_list": ["synthpop"]}},
            {"role": "user", "content": "Something more upbeat"},
        ]
        result = self.crs.batch_chat([
            {"user_query": "Make it good for dancing", "user_id": "user-1", "session_memory": history}
        ], retrieval_topk=100)

        self.assertEqual(
            self.crs.retrieval.queries,
            [
                "user: I like electronic music\n"
                "assistant: Try this synthpop track\n"
                "assistant: {'track_name': 'Old Song', 'tag_list': ['synthpop']}\n"
                "user: Something more upbeat\n"
                "user: Make it good for dancing"
            ],
        )
        self.assertEqual(len(result[0]["retrieval_items"]), 100)
        self.assertEqual(len(history), 4)

    def test_single_turn_uses_the_same_full_history(self):
        self.crs.session_memory = [
            {"role": "assistant", "content": "Ignore this response"},
            {"role": "user", "content": "I like jazz"},
        ]

        self.crs.chat("Now something calm")

        self.assertEqual(
            self.crs.retrieval.queries,
            ["assistant: Ignore this response\nuser: I like jazz\nuser: Now something calm"],
        )


if __name__ == "__main__":
    unittest.main()
