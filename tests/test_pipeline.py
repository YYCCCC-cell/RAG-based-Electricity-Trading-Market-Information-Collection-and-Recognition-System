import unittest
import json
import tempfile
from pathlib import Path

from market_radar.classifier import classify
from market_radar.crawler import ListingParser
from market_radar.models import Notice
from market_radar.retriever import BM25Index, answer
from market_radar.evaluation import evaluate_classification, evaluate_retrieval


def notice(notice_id: str, title: str, body: str = "") -> Notice:
    return Notice(notice_id, title, "2026-01-01", f"https://example.test/{notice_id}", body)


class PipelineTests(unittest.TestCase):
    def test_recall_only_baseline_exposes_false_alerts(self):
        positive = notice("P", "绿色电力交易结果")
        positive.gold_category = "results_settlement"
        positive.gold_market_impacting = True
        positive.label_status = "development_draft"
        negative = notice("N", "招聘公告")
        negative.gold_category = "service_other"
        negative.gold_market_impacting = False
        negative.label_status = "development_draft"
        result = evaluate_classification([positive, negative])
        self.assertEqual(result["market_impacting"]["precision"], 1.0)
        self.assertEqual(result["baselines"]["flag_everything"]["precision"], 0.5)
        self.assertEqual(result["baselines"]["flag_everything"]["false_alerts"], 1)
        self.assertEqual(result["errors"], [])

    def test_error_records_preserve_source_and_label_status(self):
        item = notice("N", "交易结果")
        item.gold_category = "service_other"
        item.gold_market_impacting = False
        item.label_status = "development_draft"
        result = evaluate_classification([item])
        self.assertEqual(result["market_impacting"]["fp"], 1)
        self.assertEqual(result["errors"][0]["notice_id"], "N")
        self.assertEqual(result["errors"][0]["url"], item.url)

    def test_retrieval_eval_rejects_nonexistent_expected_citation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "questions.jsonl"
            path.write_text(json.dumps({"question": "交易", "relevant_notice_ids": ["MISSING"]}))
            with self.assertRaisesRegex(ValueError, "present in the corpus"):
                evaluate_retrieval([notice("N", "交易结果")], path)

    def test_no_matching_evidence_returns_no_citations(self):
        result = answer(BM25Index([notice("N", "交易结果")]), "quantumneutrino")
        self.assertEqual(result["citations"], [])
        self.assertIn("没有检索", result["answer"])

    def test_result_notice_is_specific(self):
        result = classify(notice("N1", "关于发布2026年1月绿色电力交易结果的通知"))
        self.assertEqual(result.category, "results_settlement")
        self.assertTrue(result.market_impacting)

    def test_policy_outranks_generic_transaction_word(self):
        result = classify(notice("N2", "关于征求电力交易实施细则意见的函"))
        self.assertEqual(result.category, "rules_policy")

    def test_settlement_rules_are_policy_not_results(self):
        result = classify(notice("N2B", "关于印发零售结算实施细则的通知"))
        self.assertEqual(result.category, "rules_policy")

    def test_training_section_is_service_even_with_market_terms(self):
        item = notice("N2C", "电力交易结算业务培训通知")
        item.source_section = "market_training"
        result = classify(item)
        self.assertEqual(result.category, "service_other")
        self.assertIn("service_context", result.risk_flags)

    def test_transaction_plan_is_action(self):
        result = classify(notice("N2D", "关于发布2026年年度交易计划的通知"))
        self.assertEqual(result.category, "transaction_action")

    def test_unrelated_service_notice_is_not_impacting(self):
        result = classify(notice("N3", "广州电力交易中心招聘公告"))
        self.assertEqual(result.category, "service_other")
        self.assertFalse(result.market_impacting)

    def test_deadline_is_flagged(self):
        result = classify(notice("N4", "报名通知", "请于9月30日前反馈材料"))
        self.assertTrue(result.market_impacting)
        self.assertIn("deadline_detected", result.risk_flags)

    def test_answer_contains_retrieved_citation(self):
        docs = [
            notice("N1", "绿色电力交易结果", "五月绿色电力认购交易结果已经发布。"),
            notice("N2", "系统培训通知", "开展系统操作培训。"),
        ]
        result = answer(BM25Index(docs), "五月绿色电力交易结果")
        self.assertEqual(result["citations"][0]["notice_id"], "N1")
        self.assertIn("[N1]", result["answer"])

    def test_blank_optional_boolean_stays_unknown(self):
        item = Notice.from_dict(
            {
                "notice_id": "N3",
                "title": "未标注通知",
                "published_date": "2026-01-01",
                "url": "https://example.test/N3",
                "gold_market_impacting": "",
            }
        )
        self.assertIsNone(item.gold_market_impacting)
        self.assertEqual(item.source_section, "latest_notices")

    def test_listing_parser_does_not_capture_text_after_link(self):
        parser = ListingParser()
        parser.feed(
            '<a href="./202610/t20261001_123.html"><span>目标通知</span></a>'
            '<div>不应进入标题</div>'
        )
        self.assertEqual(
            parser.entries,
            [("./202610/t20261001_123.html", "目标通知")],
        )


if __name__ == "__main__":
    unittest.main()
