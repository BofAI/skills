from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import digest_context  # noqa: E402


class DigestContextPublicTests(unittest.TestCase):
    def test_later_post_in_same_conversation_is_not_reply_evidence(self) -> None:
        mention = {
            "kind": "mentions_notifications",
            "id": "200",
            "conversation_id": "thread",
            "author_username": "alice",
            "raw_time": "2026-08-06T02:00:00Z",
            "referenced_tweets": [],
        }
        own = {
            "kind": "own_profile",
            "id": "201",
            "conversation_id": "thread",
            "author_username": "owner",
            "raw_time": "2026-08-06T03:00:00Z",
            "referenced_tweets": [],
        }

        result = digest_context.annotate_public_reply_states([mention, own], "owner")[0]

        self.assertNotEqual(result.get("reply_state"), "already_replied")

    def test_later_post_mentioning_same_author_is_not_reply_evidence(self) -> None:
        mention = {
            "kind": "mentions_search",
            "id": "200",
            "author_username": "alice",
            "raw_time": "2026-08-06T02:00:00Z",
            "referenced_tweets": [],
        }
        own = {
            "kind": "own_profile",
            "id": "201",
            "author_username": "owner",
            "raw_time": "2026-08-06T03:00:00Z",
            "text_excerpt": "hello @alice",
            "referenced_tweets": [],
        }

        result = digest_context.annotate_public_reply_states([mention, own], "owner")[0]

        self.assertNotEqual(result.get("reply_state"), "already_replied")

    def test_direct_later_reply_reference_is_reply_evidence(self) -> None:
        mention = {
            "kind": "mentions_notifications",
            "id": "200",
            "author_username": "alice",
            "raw_time": "2026-08-06T02:00:00Z",
            "referenced_tweets": [],
        }
        own = {
            "kind": "own_profile",
            "id": "201",
            "author_username": "owner",
            "raw_time": "2026-08-06T03:00:00Z",
            "referenced_tweets": [{"id": "200", "type": "replied_to"}],
        }

        result = digest_context.annotate_public_reply_states([mention, own], "owner")[0]

        self.assertEqual(result["reply_state"], "already_replied")

    def test_direct_reply_to_own_post_is_not_labeled_unverified(self) -> None:
        items = [
            {
                "kind": "own_profile",
                "id": "100",
                "author_username": "owner",
                "raw_time": "2026-08-06T01:00:00Z",
                "text_excerpt": "my post",
                "referenced_tweets": [],
            },
            {
                "kind": "mentions_notifications",
                "id": "200",
                "author_username": "alice",
                "raw_time": "2026-08-06T02:00:00Z",
                "text_excerpt": "reply",
                "referenced_tweets": [{"id": "100", "type": "replied_to"}],
            },
        ]

        annotated = digest_context.annotate_public_reply_states(items, "owner")
        reply = annotated[1]
        self.assertEqual(reply["interaction_type"], "replied_to_your_post")
        self.assertEqual(reply["action_state"], "incoming_reply")
        self.assertNotIn("reply_state", reply)

    def test_reply_to_older_own_post_uses_expanded_reference_author(self) -> None:
        items = [
            {
                "kind": "mentions_notifications",
                "id": "200",
                "author_username": "alice",
                "raw_time": "2026-08-06T02:00:00Z",
                "text_excerpt": "reply to an older post",
                "referenced_tweets": [
                    {"id": "50", "type": "replied_to", "author_username": "owner"}
                ],
            }
        ]

        reply = digest_context.annotate_public_reply_states(items, "owner")[0]
        self.assertEqual(reply["interaction_type"], "replied_to_your_post")
        self.assertEqual(reply["action_state"], "incoming_reply")
        self.assertNotIn("reply_state", reply)

    def test_duplicate_mentions_from_search_are_removed(self) -> None:
        items = [
            {"kind": "mentions_notifications", "id": "200"},
            {"kind": "mentions_search", "id": "200"},
            {"kind": "mentions_search", "id": "201"},
        ]

        deduplicated = digest_context.deduplicate_public_items(items)
        self.assertEqual([item["id"] for item in deduplicated], ["200", "201"])

    def test_like_item_keeps_liker_and_target_post(self) -> None:
        normalized = digest_context.normalize_public_item(
            "likes_on_own_posts",
            {
                "id": "100:1",
                "interaction_type": "liked_your_post",
                "author_username": "alice",
                "time": "2026-08-06T01:00:00Z",
                "time_basis": "own_post_created_at",
                "url": "https://x.com/owner/status/100",
                "target_post_id": "100",
                "target_post_text": "my post",
            },
        )

        self.assertEqual(normalized["author_username"], "alice")
        self.assertEqual(normalized["interaction_type"], "liked_your_post")
        self.assertEqual(normalized["target_post_text"], "my post")

        rendered = digest_context.render_public_slice_section(
            {"public": {"counts": {"likes_on_own_posts": {"total": 1}}, "items": [normalized]}},
            "timeline",
        )
        self.assertIn("interaction_type=`liked_your_post`", rendered)
        self.assertIn("target post: my post", rendered)


if __name__ == "__main__":
    unittest.main()
