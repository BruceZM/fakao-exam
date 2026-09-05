import json
import os
import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from server.main import app, QUESTIONS
from server.practice import adapt, attach_rubrics
from server.grading import validate_feedback


class PracticeTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'ACCESS_CODE': 'local-test-one', 'ACCESS_USERS': json.dumps({'second': {'code': 'local-test-two', 'name': '乙'}})})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = TestClient(app)
        self.headers = {'X-Access-Code': 'local-test-one'}

    def test_users_and_auth(self):
        self.assertEqual(self.client.get('/api/subjects').status_code, 403)
        self.assertEqual(self.client.post('/api/verify', json={'code': 'wrong'}).status_code, 403)
        one = self.client.post('/api/verify', json={'code': 'local-test-one'}).json()['user']
        two = self.client.post('/api/verify', json={'code': 'local-test-two'}).json()['user']
        self.assertNotEqual(one['id'], two['id'])
        self.assertEqual(one, self.client.post('/api/verify', json={'code': 'local-test-one'}).json()['user'])
        self.assertNotIn('code', two)

    def test_answers_hidden_and_reference_explicit(self):
        q = QUESTIONS[0]
        response = self.client.get('/api/questions/' + q['question_id'], headers=self.headers).json()
        self.assertNotIn('answer', response)
        self.assertNotIn('explanation', response)
        ref = self.client.get('/api/questions/' + q['question_id'] + '/reference', headers=self.headers).json()
        self.assertIn('answer', ref)

    def test_objective_sets_and_invalid_choices(self):
        for typ in ['single_choice', 'multiple_choice', 'true_false']:
            q = next(q for q in QUESTIONS if q['question_type'] == typ and q['practice_ready'])
            payload = {'question_id': q['question_id'], 'selected': q['answer_keys'][::-1]}
            self.assertTrue(self.client.post('/api/submit', headers=self.headers, json=payload).json()['correct'])
            payload['selected'] = ['Z']
            self.assertEqual(self.client.post('/api/submit', headers=self.headers, json=payload).status_code, 422)
        q = next(q for q in QUESTIONS if q['question_type'] == 'multiple_choice' and len(q['answer_keys']) > 1 and q['practice_ready'])
        self.assertFalse(self.client.post('/api/submit', headers=self.headers, json={'question_id': q['question_id'], 'selected': q['answer_keys'][:1]}).json()['correct'])

    def test_incomplete_questions_browse_only(self):
        practice = self.client.get('/api/questions?stage=objective&limit=1500', headers=self.headers).json()['items']
        self.assertTrue(all(q['practice_ready'] for q in practice))
        browse = self.client.get('/api/questions?stage=objective&mode=browse&limit=1500', headers=self.headers).json()['items']
        bad = next(q for q in browse if not q['practice_ready'])
        self.assertEqual(self.client.post('/api/submit', headers=self.headers, json={'question_id': bad['question_id'], 'selected': ['A']}).status_code, 422)
        self.assertEqual(self.client.get('/api/next?stage=objective&subject=不存在', headers=self.headers).json(), {'question': None})

    def test_mapping_and_completeness(self):
        q = adapt({'question_id': 'canonical', 'question_type': 'short_answer', 'stem': '理由？（2分）', 'answer_raw': '条件已成就（2分）'})
        rule = {'question_id': 'alias', 'rubric_id': 'r1', 'point_text': '条件已成就', 'score': 2, 'extraction_status': 'explicit_from_answer'}
        self.assertFalse(attach_rubrics([q], {'items': [rule]}, {})[0]['rubrics'])
        mapping = {'items': [{'question_id': 'alias', 'canonical_question_id': 'canonical'}]}
        self.assertEqual(attach_rubrics([q], {'items': [rule]}, mapping)[0]['max_score'], 2)
        rule['score'] = 1
        self.assertFalse(attach_rubrics([q], {'items': [rule]}, mapping)[0]['rubrics'])

    def test_evidence_and_no_invented_scores(self):
        q = next(q for q in QUESTIONS if q['rubrics'])
        answer = '这是学生原文'
        data = {'summary': '反馈', 'score': 999, 'points': [{'rubric_id': r['rubric_id'], 'status': 'hit', 'evidence': answer} for r in q['rubrics']]}
        self.assertEqual(validate_feedback(q, answer, data)['score'], q['max_score'])
        data['points'][0]['evidence'] = '伪造的原文'
        with self.assertRaises(ValueError): validate_feedback(q, answer, data)
        q = next(q for q in QUESTIONS if q['practice_stage'] == 'subjective' and not q['rubrics'])
        self.assertIsNone(validate_feedback(q, answer, data)['score'])

    def test_stream_completion_and_failure(self):
        q = next(q for q in QUESTIONS if q['practice_stage'] == 'subjective')
        payload = {'question_id': q['question_id'], 'answer': '我的作答'}
        with patch('server.main.grade', new=AsyncMock(return_value={'points': [], 'score': None, 'summary': '建议'})):
            r = self.client.post('/api/grade_stream', headers=self.headers, json=payload)
            self.assertIn('event: complete', r.text)
        with patch('server.main.grade', new=AsyncMock(side_effect=TimeoutError)):
            r = self.client.post('/api/grade_stream', headers=self.headers, json=payload)
            self.assertIn('event: error', r.text)
            self.assertNotIn('event: complete', r.text)


if __name__ == '__main__': unittest.main()
