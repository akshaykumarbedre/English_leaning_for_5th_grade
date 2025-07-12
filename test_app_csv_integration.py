#!/usr/bin/env python3
"""
Test script to verify CSV persistence functionality in the app
without requiring OpenAI API calls.
"""

import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the app directory to the path
sys.path.insert(0, '/home/runner/work/English_leaning_for_5th_grade/English_leaning_for_5th_grade')

def test_app_csv_functions():
    """Test the actual CSV functions from the app"""
    print("Testing app CSV functions...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the CSV directories to use temp directory
        with patch('app.CSV_DATA_DIR', temp_dir):
            with patch('app.PASSAGES_CSV', os.path.join(temp_dir, 'passages.csv')):
                with patch('app.PROGRESS_CSV', os.path.join(temp_dir, 'user_progress.csv')):
                    
                    # Import app functions after patching
                    from app import (
                        save_passage_to_csv, 
                        load_passages_from_csv,
                        save_user_progress_to_csv,
                        load_user_progress_from_csv
                    )
                    
                    # Test passage storage
                    test_passage = "This is a test passage for learning English."
                    test_vocab = {"test": "a trial or examination", "passage": "a section of text"}
                    test_questions = ["What is this passage about?", "What does test mean?"]
                    
                    # Save passage
                    success = save_passage_to_csv(test_passage, test_vocab, test_questions)
                    assert success, "Failed to save passage to CSV"
                    
                    # Load passages
                    passages = load_passages_from_csv()
                    assert len(passages) == 1, f"Expected 1 passage, got {len(passages)}"
                    assert passages[0]['passage'] == test_passage, "Passage text doesn't match"
                    assert passages[0]['vocabulary'] == test_vocab, "Vocabulary doesn't match"
                    assert passages[0]['questions'] == test_questions, "Questions don't match"
                    
                    # Test progress storage
                    test_points = 100
                    test_passages_completed = 5
                    test_vocab_learned = ["word1", "word2", "word3"]
                    
                    # Save progress
                    success = save_user_progress_to_csv(test_points, test_passages_completed, test_vocab_learned)
                    assert success, "Failed to save progress to CSV"
                    
                    # Load progress
                    progress = load_user_progress_from_csv()
                    assert progress['points'] == test_points, "Points don't match"
                    assert progress['passages_completed'] == test_passages_completed, "Passages completed don't match"
                    assert progress['vocab_learned'] == test_vocab_learned, "Vocab learned doesn't match"
                    
                    print("✓ App CSV functions test passed!")

def test_app_initialization():
    """Test app initialization with CSV persistence"""
    print("Testing app initialization...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the CSV directories to use temp directory
        with patch('app.CSV_DATA_DIR', temp_dir):
            with patch('app.PASSAGES_CSV', os.path.join(temp_dir, 'passages.csv')):
                with patch('app.PROGRESS_CSV', os.path.join(temp_dir, 'user_progress.csv')):
                    
                    # Create some test data
                    from app import save_passage_to_csv, save_user_progress_to_csv
                    
                    # Save test data
                    save_passage_to_csv(
                        "Test passage for initialization",
                        {"initialize": "to set up or start"},
                        ["What does initialize mean?"]
                    )
                    save_user_progress_to_csv(50, 2, ["initialize"])
                    
                    # Now test loading
                    from app import load_passages_from_csv, load_user_progress_from_csv
                    
                    passages = load_passages_from_csv()
                    progress = load_user_progress_from_csv()
                    
                    assert len(passages) == 1, "Should load 1 passage"
                    assert progress['points'] == 50, "Should load 50 points"
                    assert progress['passages_completed'] == 2, "Should load 2 passages completed"
                    assert progress['vocab_learned'] == ["initialize"], "Should load vocab learned"
                    
                    print("✓ App initialization test passed!")

def test_error_handling():
    """Test error handling in CSV functions"""
    print("Testing error handling...")
    
    # Test with invalid directory (should be handled gracefully)
    with patch('app.CSV_DATA_DIR', '/invalid/nonexistent/directory'):
        with patch('app.PASSAGES_CSV', '/invalid/nonexistent/directory/passages.csv'):
            # This should not crash the app
            from app import load_passages_from_csv
            passages = load_passages_from_csv()
            assert passages == [], "Should return empty list for invalid directory"
            
            print("✓ Error handling test passed!")

def run_all_app_tests():
    """Run all app-specific tests"""
    print("Running app CSV integration tests...")
    
    test_app_csv_functions()
    test_app_initialization()
    test_error_handling()
    
    print("\n✅ All app CSV integration tests passed!")

if __name__ == '__main__':
    run_all_app_tests()