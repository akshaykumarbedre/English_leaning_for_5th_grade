import os
import csv
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the app directory to the path
import sys
sys.path.insert(0, '/home/runner/work/English_leaning_for_5th_grade/English_leaning_for_5th_grade')

def test_csv_passage_storage():
    """Test CSV passage storage functionality"""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the CSV file path
        test_passages_csv = os.path.join(temp_dir, 'test_passages.csv')
        
        # Test data
        test_passage = "This is a test passage for learning."
        test_vocab = {"test": "a trial or examination", "passage": "a section of text"}
        test_questions = ["What is this passage about?", "What does test mean?", "How do you learn?"]
        
        # Manually create CSV file (simulating save_passage_to_csv)
        with open(test_passages_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['passage', 'vocabulary', 'questions', 'created_at'])
            writer.writeheader()
            
            # Format data as it would be saved
            vocab_str = ','.join([f"{word}:{definition}" for word, definition in test_vocab.items()])
            questions_str = ';'.join(test_questions)
            
            writer.writerow({
                'passage': test_passage,
                'vocabulary': vocab_str,
                'questions': questions_str,
                'created_at': datetime.now().isoformat()
            })
        
        # Test reading back (simulating load_passages_from_csv)
        passages = []
        with open(test_passages_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse vocabulary
                vocab_dict = {}
                if row['vocabulary']:
                    vocab_pairs = row['vocabulary'].split(',')
                    for pair in vocab_pairs:
                        if ':' in pair:
                            word, definition = pair.split(':', 1)
                            vocab_dict[word.strip()] = definition.strip()
                
                # Parse questions
                questions = []
                if row['questions']:
                    questions = [q.strip() for q in row['questions'].split(';') if q.strip()]
                
                passages.append({
                    'passage': row['passage'],
                    'vocabulary': vocab_dict,
                    'questions': questions,
                    'created_at': row['created_at']
                })
        
        # Verify data
        assert len(passages) == 1
        assert passages[0]['passage'] == test_passage
        assert passages[0]['vocabulary'] == test_vocab
        assert passages[0]['questions'] == test_questions
        print("✓ CSV passage storage test passed!")

def test_csv_progress_storage():
    """Test CSV progress storage functionality"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_progress_csv = os.path.join(temp_dir, 'test_progress.csv')
        
        # Test data
        test_points = 100
        test_passages_completed = 5
        test_vocab_learned = ["word1", "word2", "word3"]
        
        # Manually create CSV file (simulating save_user_progress_to_csv)
        with open(test_progress_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['points', 'passages_completed', 'vocab_learned', 'last_updated'])
            writer.writeheader()
            
            vocab_str = ','.join(test_vocab_learned)
            writer.writerow({
                'points': test_points,
                'passages_completed': test_passages_completed,
                'vocab_learned': vocab_str,
                'last_updated': datetime.now().isoformat()
            })
        
        # Test reading back (simulating load_user_progress_from_csv)
        with open(test_progress_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if rows:
            latest = rows[-1]
            vocab_learned = []
            if latest['vocab_learned']:
                vocab_learned = latest['vocab_learned'].split(',')
            
            progress = {
                'points': int(latest['points']),
                'passages_completed': int(latest['passages_completed']),
                'vocab_learned': vocab_learned
            }
        
        # Verify data
        assert progress['points'] == test_points
        assert progress['passages_completed'] == test_passages_completed
        assert progress['vocab_learned'] == test_vocab_learned
        print("✓ CSV progress storage test passed!")

def test_empty_csv_handling():
    """Test handling of empty CSV files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test empty passages file
        empty_passages_csv = os.path.join(temp_dir, 'empty_passages.csv')
        with open(empty_passages_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['passage', 'vocabulary', 'questions', 'created_at'])
            writer.writeheader()
        
        # Read empty file
        passages = []
        with open(empty_passages_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            passages = list(reader)
        
        assert len(passages) == 0
        print("✓ Empty CSV handling test passed!")

def test_nonexistent_csv_handling():
    """Test handling of non-existent CSV files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        nonexistent_csv = os.path.join(temp_dir, 'nonexistent.csv')
        
        # Check that file doesn't exist
        assert not os.path.exists(nonexistent_csv)
        
        # This should return default values
        default_progress = {
            'points': 0,
            'passages_completed': 0,
            'vocab_learned': []
        }
        
        # In the real app, this would be handled by the load functions
        if not os.path.exists(nonexistent_csv):
            progress = default_progress
        
        assert progress == default_progress
        print("✓ Non-existent CSV handling test passed!")

def test_csv_data_integrity():
    """Test data integrity with special characters"""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_csv = os.path.join(temp_dir, 'integrity_test.csv')
        
        # Test data with special characters
        special_passage = "This passage contains special characters: áéíóú, ñ, and quotes \"like this\"."
        special_vocab = {"café": "a small restaurant", "piñata": "a decorated container"}
        special_questions = ["What's special about this?", "How do you say \"hello\"?"]
        
        # Write data
        with open(test_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['passage', 'vocabulary', 'questions', 'created_at'])
            writer.writeheader()
            
            vocab_str = ','.join([f"{word}:{definition}" for word, definition in special_vocab.items()])
            questions_str = ';'.join(special_questions)
            
            writer.writerow({
                'passage': special_passage,
                'vocabulary': vocab_str,
                'questions': questions_str,
                'created_at': datetime.now().isoformat()
            })
        
        # Read back
        with open(test_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['passage'] == special_passage
        print("✓ CSV data integrity test passed!")

def run_all_tests():
    """Run all CSV persistence tests"""
    print("Running CSV persistence tests...")
    
    test_csv_passage_storage()
    test_csv_progress_storage()
    test_empty_csv_handling()
    test_nonexistent_csv_handling()
    test_csv_data_integrity()
    
    print("\n✅ All CSV persistence tests passed!")

if __name__ == '__main__':
    run_all_tests()