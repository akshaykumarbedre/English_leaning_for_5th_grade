#!/usr/bin/env python3
"""
Demo script that shows the app working with mock OpenAI responses
to demonstrate end-to-end workflow without requiring API key.
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import streamlit as st

# Add the app directory to the path
sys.path.insert(0, '/home/runner/work/English_leaning_for_5th_grade/English_leaning_for_5th_grade')

def mock_openai_response(prompt_text):
    """Mock OpenAI response based on prompt content"""
    if "passage" in prompt_text.lower():
        return """
        The Magic of Reading
        
        Reading is like opening a door to new worlds. When you read a book, you travel to different places and meet interesting characters. Books can teach you about history, science, and many other subjects. Reading also helps you learn new words and improves your vocabulary. The more you read, the better you become at understanding different stories and ideas.
        
        **Vocabulary:**
        magic: something wonderful or extraordinary
        vocabulary: all the words you know and use
        characters: people in a story
        extraordinary: very unusual or remarkable
        """
    elif "comprehension" in prompt_text.lower():
        return """
        1. What does reading allow you to do?
        2. What can books teach you about?
        3. How does reading help improve your vocabulary?
        """
    elif "quiz" in prompt_text.lower():
        return """
        1. What does 'vocabulary' mean?
        2. What does 'characters' refer to in a story?
        3. What does 'extraordinary' mean?
        """
    else:
        return "Mock response for testing"

def test_app_end_to_end():
    """Test the complete app workflow"""
    print("🚀 End-to-End App Workflow Demo")
    print("=" * 50)
    
    # Clean up any existing data
    data_dir = "/tmp/demo_data"
    if os.path.exists(data_dir):
        import shutil
        shutil.rmtree(data_dir)
    os.makedirs(data_dir, exist_ok=True)
    
    # Mock the CSV file paths
    passages_csv = os.path.join(data_dir, "passages.csv")
    progress_csv = os.path.join(data_dir, "user_progress.csv")
    
    print("1. Setting up mock environment...")
    
    # Mock OpenAI
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = lambda prompt: MagicMock(content=mock_openai_response(str(prompt)))
    
    with patch('app.llm', mock_llm):
        with patch('app.CSV_DATA_DIR', data_dir):
            with patch('app.PASSAGES_CSV', passages_csv):
                with patch('app.PROGRESS_CSV', progress_csv):
                    
                    # Import app functions
                    from app import (
                        generate_passage, generate_questions, generate_quiz,
                        save_passage_to_csv, load_passages_from_csv,
                        save_user_progress_to_csv, load_user_progress_from_csv
                    )
                    
                    print("2. Testing passage generation...")
                    
                    # Test passage generation
                    passage, vocab_dict = generate_passage()
                    print(f"   Generated passage: {passage[:50]}...")
                    print(f"   Vocabulary words: {list(vocab_dict.keys())}")
                    
                    # Test questions generation
                    questions = generate_questions(passage)
                    print(f"   Generated {len(questions)} questions")
                    
                    # Test quiz generation
                    quiz = generate_quiz(passage)
                    print(f"   Generated {len(quiz)} quiz questions")
                    
                    print("3. Testing CSV persistence...")
                    
                    # Save passage to CSV
                    success = save_passage_to_csv(passage, vocab_dict, questions)
                    print(f"   Passage saved: {'✓' if success else '✗'}")
                    
                    # Save initial progress
                    success = save_user_progress_to_csv(15, 1, list(vocab_dict.keys())[:2])
                    print(f"   Progress saved: {'✓' if success else '✗'}")
                    
                    print("4. Testing data loading...")
                    
                    # Load passages
                    loaded_passages = load_passages_from_csv()
                    print(f"   Loaded {len(loaded_passages)} passages")
                    
                    # Load progress
                    loaded_progress = load_user_progress_from_csv()
                    print(f"   Loaded progress: {loaded_progress['points']} points")
                    
                    print("5. Testing app behavior simulation...")
                    
                    # Simulate app behavior
                    print("   Simulating first app session:")
                    print(f"   - Available passages: {len(loaded_passages)}")
                    print(f"   - User progress: {loaded_progress}")
                    
                    # Simulate user completing an activity
                    new_points = loaded_progress['points'] + 20
                    new_completed = loaded_progress['passages_completed'] + 1
                    new_vocab = loaded_progress['vocab_learned'] + ['magic']
                    
                    save_user_progress_to_csv(new_points, new_completed, new_vocab)
                    print(f"   - Updated progress: {new_points} points, {new_completed} completed")
                    
                    # Generate and save another passage
                    passage2, vocab_dict2 = generate_passage()
                    questions2 = generate_questions(passage2)
                    save_passage_to_csv(passage2, vocab_dict2, questions2)
                    
                    print("6. Testing persistence across sessions...")
                    
                    # Simulate app restart by reloading data
                    final_passages = load_passages_from_csv()
                    final_progress = load_user_progress_from_csv()
                    
                    print(f"   After restart - Passages: {len(final_passages)}")
                    print(f"   After restart - Progress: {final_progress['points']} points")
                    print(f"   After restart - Vocabulary: {len(final_progress['vocab_learned'])} words")
                    
                    # Verify CSV files exist
                    print("7. Verifying CSV files...")
                    passages_exist = os.path.exists(passages_csv)
                    progress_exist = os.path.exists(progress_csv)
                    
                    print(f"   Passages CSV exists: {'✓' if passages_exist else '✗'}")
                    print(f"   Progress CSV exists: {'✓' if progress_exist else '✗'}")
                    
                    if passages_exist:
                        size = os.path.getsize(passages_csv)
                        print(f"   Passages CSV size: {size} bytes")
                    
                    if progress_exist:
                        size = os.path.getsize(progress_csv)
                        print(f"   Progress CSV size: {size} bytes")
    
    print("\n✅ End-to-end workflow demo completed successfully!")
    print(f"Demo data saved to: {data_dir}")

if __name__ == '__main__':
    test_app_end_to_end()