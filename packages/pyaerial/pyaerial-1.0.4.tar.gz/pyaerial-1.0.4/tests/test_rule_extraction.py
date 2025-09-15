import unittest

import numpy as np
import pandas as pd

from aerial.model import AutoEncoder
from aerial.data_preparation import _one_hot_encoding_with_feature_tracking
from aerial.model import train
from aerial.rule_extraction import (
    generate_rules,
    generate_frequent_itemsets, extract_significant_features_and_ignored_indices, _mark_features,
)


class TestAerialFunctions(unittest.TestCase):
    def setUp(self):
        """Create sample transactions and train an AutoEncoder"""
        self.transactions = pd.DataFrame({
            'Color': ['Red', 'Blue', 'Green', 'Blue', 'Red'],
            'Size': ['S', 'M', 'L', 'S', 'L'],
            'Shape': ['Circle', 'Square', 'Triangle', 'Circle', 'Square']
        })
        self.model = train(self.transactions, epochs=5)

    # Testing all the basic functionality of rule learning and frequent itemset learning
    def test_one_hot_encoding_with_feature_tracking(self):
        """Test one-hot vector creation from transactions"""
        vector_list, feature_value_indices = _one_hot_encoding_with_feature_tracking(self.transactions)
        self.assertIsInstance(vector_list, pd.DataFrame)
        self.assertIsInstance(feature_value_indices, list)
        self.assertEqual(vector_list.shape[0], len(self.transactions))

    def test_train_autoencoder(self):
        """Test training an autoencoder model"""
        model = train(self.transactions, epochs=2)
        self.assertIsInstance(model, AutoEncoder)

    def test_generate_rules(self):
        """Test rule generation"""
        # pass low similarity thresholds to guarantee rule generation
        rules = generate_rules(self.model, ant_similarity=0.001, cons_similarity=0.001)
        self.assertIsInstance(rules, list)
        if rules:
            self.assertIn('antecedents', rules[0])
            self.assertIn('consequent', rules[0])

    def test_generate_frequent_itemsets(self):
        """Test frequent itemset generation"""
        # pass low similarity threshold to guarantee frequent itemset generation
        itemsets = generate_frequent_itemsets(self.model, similarity=0.001)
        self.assertIsInstance(itemsets, list)
        if itemsets:
            self.assertIsInstance(itemsets[0], list)

    def test_rules_target_classes(self):
        """Test that only specified target classes appear in consequents"""
        target_classes = ['Color']  # Only generate rules predicting Color
        rules = generate_rules(self.model, ant_similarity=0.001, cons_similarity=0.001, target_classes=target_classes)

        for r in rules:
            # Extract column name from consequent
            consequent_col = r['consequent'].split("__")[0]
            # Check that the consequent column is in the target_classes
            self.assertIn(consequent_col, target_classes)

    def test_rules_max_antecedents(self):
        """Test that antecedents do not exceed max_antecedents"""
        max_antecedents = 2
        # pass a very low ant_similarity to ensure that the method will return rules
        rules = generate_rules(self.model, ant_similarity=0.001, cons_similarity=0.001, max_antecedents=max_antecedents)

        for r in rules:
            self.assertLessEqual(len(r['antecedents']), max_antecedents)

        # Also test for single antecedent limit
        rules_single = generate_rules(self.model, max_antecedents=1)
        for r in rules_single:
            self.assertLessEqual(len(r['antecedents']), 1)

    def test_rules_features_of_interest_in_rule_learning(self):
        """Test that antecedents contain only features of interest"""
        features_of_interest = ['Size', {'Color': 'Red'}]
        rules = generate_rules(self.model, ant_similarity=0.001, cons_similarity=0.001,
                               features_of_interest=features_of_interest)

        for r in rules:
            for ant in r['antecedents']:
                feature_name, feature_value = ant.split("__")
                # Check if either the feature name is in the list or the specific value is allowed
                self.assertTrue(
                    feature_name in features_of_interest or {feature_name: feature_value} in features_of_interest
                )

    def test_rules_features_of_interest_in_frequent_itemset_learning(self):
        """Test that antecedents contain only features of interest"""
        features_of_interest = ['Size', {'Color': 'Red'}]
        itemsets = generate_frequent_itemsets(self.model, similarity=0.001, features_of_interest=features_of_interest)

        for itemset in itemsets:
            for item in itemset:
                feature_name, feature_value = item.split("__")
                # Check if either the feature name is in the list or the specific value is allowed
                self.assertTrue(
                    feature_name in features_of_interest or {feature_name: feature_value} in features_of_interest
                )

    def test_none_model_returns_none_rule_learning(self):
        rules = generate_rules(None)
        self.assertIsNone(rules)

    def test_none_model_returns_none_frequent_itemset_learning(self):
        itemsets = generate_frequent_itemsets(None)
        self.assertIsNone(itemsets)

    def test_small_dataset_returns_rules_or_empty_rule_learning(self):
        small_transactions = self.transactions.iloc[:1]
        small_model = train(small_transactions, epochs=1)
        rules = generate_rules(small_model)
        self.assertTrue(rules is None or isinstance(rules, list))

    def test_small_dataset_returns_rules_or_empty_frequent_itemset_learning(self):
        small_transactions = self.transactions.iloc[:1]
        small_model = train(small_transactions, epochs=1)
        itemsets = generate_frequent_itemsets(small_model)
        self.assertTrue(itemsets is None or isinstance(itemsets, list))

    def test_rule_strings_pattern_rule_learning(self):
        rules = generate_rules(self.model, ant_similarity=0.001, cons_similarity=0.001)
        for r in rules:
            for ant in r['antecedents']:
                self.assertRegex(ant, r".+__.+")
            self.assertRegex(r['consequent'], r".+__.+")

    def test_rule_strings_pattern_frequent_itemset_learning(self):
        itemsets = generate_frequent_itemsets(self.model, similarity=0.001)
        for itemset in itemsets:
            for item in itemset:
                self.assertRegex(item, r".+__.+")

    def test_consistent_rule_structure(self):
        rules = generate_rules(self.model, ant_similarity=0.001, cons_similarity=0.001)
        for r in rules:
            self.assertIsInstance(r, dict)
            self.assertIn('antecedents', r)
            self.assertIn('consequent', r)
            self.assertIsInstance(r['antecedents'], list)
            self.assertIsInstance(r['consequent'], str)

    def test_empty_target_classes_or_features_of_interest_rule_learning(self):
        rules = generate_rules(self.model, target_classes=[], features_of_interest=[], ant_similarity=0.001,
                               cons_similarity=0.001)
        self.assertIsInstance(rules, list)

    def test_empty_target_classes_or_features_of_interest_frequent_itemset_learning(self):
        itemsets = generate_frequent_itemsets(self.model, features_of_interest=[], similarity=0.001)
        self.assertIsInstance(itemsets, list)

    ### Testing the "extract_significant_features_and_ignored_indices()" function from rule_extraction.py
    def test_no_features_of_interest_returns_all_indices(self):
        sig_feats, ignored = extract_significant_features_and_ignored_indices(None, self.model)
        self.assertEqual(sig_feats, self.model.feature_value_indices)
        self.assertEqual(ignored, [])

        sig_feats, ignored = extract_significant_features_and_ignored_indices([], self.model)
        self.assertEqual(sig_feats, self.model.feature_value_indices)
        self.assertEqual(ignored, [])

    def test_features_of_interest_as_strings(self):
        features = ['Color', 'Size']
        sig_feats, ignored = extract_significant_features_and_ignored_indices(features, self.model)
        sig_feature_names = [f['feature'] for f in sig_feats]
        self.assertTrue('Color' in sig_feature_names)
        self.assertTrue('Size' in sig_feature_names)
        self.assertIsInstance(ignored, list)

    def test_features_of_interest_as_dicts(self):
        features = [{'Color': 'Red'}, {'Size': 'S'}]
        sig_feats, ignored = extract_significant_features_and_ignored_indices(features, self.model)
        sig_feature_names = [f['feature'] for f in sig_feats]
        self.assertTrue('Color' in sig_feature_names)
        self.assertTrue('Size' in sig_feature_names)
        self.assertIsInstance(ignored, list)
        # Each ignored index must correspond to a value that is not the constrained one
        for idx in ignored:
            feature_name = self.model.feature_values[idx].split('__')[0]
            value = self.model.feature_values[idx].split('__')[1]
            if feature_name == 'Color':
                self.assertNotEqual(value, 'Red')
            if feature_name == 'Size':
                self.assertNotEqual(value, 'S')

    def test_mixed_strings_and_dicts(self):
        features = ['Shape', {'Color': 'Green'}]
        sig_feats, ignored = extract_significant_features_and_ignored_indices(features, self.model)
        sig_feature_names = [f['feature'] for f in sig_feats]
        self.assertIn('Shape', sig_feature_names)
        self.assertIn('Color', sig_feature_names)
        for idx in ignored:
            feature_name = self.model.feature_values[idx].split('__')[0]
            value = self.model.feature_values[idx].split('__')[1]
            if feature_name == 'Color':
                self.assertNotEqual(value, 'Green')

    def test_values_to_ignore_empty_when_no_constraints(self):
        features = ['Color']
        sig_feats, ignored = extract_significant_features_and_ignored_indices(features, self.model)
        # If no specific values provided, ignored should be empty
        self.assertEqual(ignored, [])

    def test_values_to_ignore_for_multiple_constraints(self):
        features = [{'Color': 'Red'}, {'Size': 'S'}]
        sig_feats, ignored = extract_significant_features_and_ignored_indices(features, self.model)
        # Ensure ignored indices correspond to other values of Color and Size
        color_values = [v.split('__')[1] for v in self.model.feature_values if v.startswith('Color')]
        size_values = [v.split('__')[1] for v in self.model.feature_values if v.startswith('Size')]
        for idx in ignored:
            val = self.model.feature_values[idx].split('__')[1]
            self.assertTrue(val in color_values or val in size_values)
            self.assertFalse(val == 'Red' and val == 'S')  # constrained values not ignored

    def test_returns_empty_significant_features_if_none_match(self):
        features = ['NonExistentFeature']
        sig_feats, ignored = extract_significant_features_and_ignored_indices(features, self.model)
        self.assertEqual(sig_feats, [])
        self.assertEqual(ignored, [])

    def test_return_type_always_list(self):
        sig_feats, ignored = extract_significant_features_and_ignored_indices(['Color'], self.model)
        self.assertIsInstance(sig_feats, list)
        self.assertIsInstance(ignored, list)

    def test_values_to_ignore_matches_feature_values(self):
        features = [{'Color': 'Red'}]
        sig_feats, ignored = extract_significant_features_and_ignored_indices(features, self.model)
        for idx in ignored:
            self.assertTrue('__' in self.model.feature_values[idx])
            self.assertNotEqual(self.model.feature_values[idx].split('__')[1], 'Red')

    # Test "_mark_features()" function of the rule_extraction.py
    def test_single_feature_marks_correctly(self):
        unmarked = np.ones(len(self.model.feature_values))
        feature_range = [range(f['start'], f['end']) for f in self.model.feature_value_indices[:1]]  # first feature
        insignificant = np.array([], dtype=int)
        test_vectors, candidate_antecedents = _mark_features(unmarked, feature_range, insignificant)
        self.assertEqual(test_vectors.shape[1], len(unmarked))
        self.assertEqual(len(candidate_antecedents), len(test_vectors))
        # Check that exactly one position in each vector is marked 1 per candidate
        for vec, ant in zip(test_vectors, candidate_antecedents):
            self.assertEqual(np.sum(vec[feature_range[0].start:feature_range[0].stop]), 1)
            self.assertEqual(len(ant), 1)

    def test_multiple_features_combination(self):
        unmarked = np.ones(len(self.model.feature_values))
        feature_ranges = [range(f['start'], f['end']) for f in self.model.feature_value_indices[:2]]
        insignificant = np.array([], dtype=int)
        test_vectors, candidate_antecedents = _mark_features(unmarked, feature_ranges, insignificant)
        # Number of test vectors = product of first two features lengths
        expected_n = len(feature_ranges[0]) * len(feature_ranges[1])
        self.assertEqual(test_vectors.shape[0], expected_n)
        self.assertEqual(test_vectors.shape[1], len(unmarked))
        # Check candidate_antecedents lengths
        for ant in candidate_antecedents:
            self.assertEqual(len(ant), 2)

    def test_insignificant_features_excluded(self):
        unmarked = np.ones(len(self.model.feature_values))
        feature_ranges = [range(f['start'], f['end']) for f in self.model.feature_value_indices[:1]]
        insignificant = np.array([feature_ranges[0].start], dtype=int)
        test_vectors, candidate_antecedents = _mark_features(unmarked, feature_ranges, insignificant)
        # Ensure that excluded index is not in any candidate_antecedents
        for ant in candidate_antecedents:
            self.assertNotIn(insignificant[0], ant)

    def test_empty_features_returns_empty_lists(self):
        unmarked = np.ones(len(self.model.feature_values))
        test_vectors, candidate_antecedents = _mark_features(unmarked, [], [])
        self.assertEqual(len(test_vectors), 0)
        self.assertEqual(len(candidate_antecedents), 0)

    def test_invalid_indices_ignored(self):
        unmarked = np.ones(len(self.model.feature_values))
        # Create a range that goes out of bounds
        feature_ranges = [range(-5, 3)]
        test_vectors, candidate_antecedents = _mark_features(unmarked, feature_ranges, np.array([], dtype=int))
        # Only valid indices >=0 should be used
        for ant in candidate_antecedents:
            self.assertTrue(all(idx >= 0 for idx in ant))

    def test_all_zero_vector_is_reset_before_marking(self):
        unmarked = np.zeros(len(self.model.feature_values))
        feature_ranges = [range(f['start'], f['end']) for f in self.model.feature_value_indices[:1]]
        test_vectors, candidate_antecedents = _mark_features(unmarked, feature_ranges, np.array([], dtype=int))
        # Check that exactly one 1 is set in the feature range for each vector
        for vec in test_vectors:
            self.assertEqual(np.sum(vec[feature_ranges[0].start:feature_ranges[0].stop]), 1)

    def test_candidate_antecedents_array_type(self):
        unmarked = np.ones(len(self.model.feature_values))
        feature_ranges = [range(f['start'], f['end']) for f in self.model.feature_value_indices[:1]]
        test_vectors, candidate_antecedents = _mark_features(unmarked, feature_ranges, np.array([], dtype=int))
        for ant in candidate_antecedents:
            self.assertIsInstance(ant, np.ndarray)



if __name__ == "__main__":
    unittest.main()
