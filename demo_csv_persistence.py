#!/usr/bin/env python3
"""
Simple demo of the CSV persistence functionality 
without requiring OpenAI API key.
"""

import os
import shutil
from datetime import datetime

# Add the app directory to the path
import sys
sys.path.insert(0, '/home/runner/work/English_leaning_for_5th_grade/English_leaning_for_5th_grade')

# Create data directory
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Import CSV functions
from app import (
    save_passage_to_csv,
    load_passages_from_csv,
    save_user_progress_to_csv,
    load_user_progress_from_csv,
    PASSAGES_CSV,
    PROGRESS_CSV
)

def demo_csv_persistence():
    """Demonstrate CSV persistence functionality"""
    print("🚀 CSV Persistence Demo")
    print("=" * 50)
    
    # Clean up any existing data
    if os.path.exists(PASSAGES_CSV):
        os.remove(PASSAGES_CSV)
    if os.path.exists(PROGRESS_CSV):
        os.remove(PROGRESS_CSV)
    
    print("1. Starting with empty CSV files...")
    passages = load_passages_from_csv()
    progress = load_user_progress_from_csv()
    print(f"   Loaded {len(passages)} passages")
    print(f"   Progress: {progress['points']} points, {progress['passages_completed']} completed")
    
    # Save some sample data
    print("\n2. Saving sample passage data...")
    sample_passage = """
    The Amazing World of Butterflies
    
    Butterflies are some of nature's most beautiful creatures. They begin their lives as tiny caterpillars, 
    eating leaves and growing bigger each day. After several weeks, they create a protective shell called 
    a chrysalis around themselves. Inside this shell, they undergo an incredible transformation called 
    metamorphosis. When they emerge, they have colorful wings and can fly from flower to flower, 
    drinking sweet nectar.
    """
    
    sample_vocab = {
        "metamorphosis": "a complete change in form or structure",
        "chrysalis": "a protective shell where butterflies develop",
        "nectar": "sweet liquid found in flowers",
        "transformation": "a complete change in appearance or form"
    }
    
    sample_questions = [
        "What do caterpillars eat to grow bigger?",
        "What is the protective shell called where butterflies develop?",
        "What do butterflies drink from flowers?"
    ]
    
    success = save_passage_to_csv(sample_passage.strip(), sample_vocab, sample_questions)
    if success:
        print("   ✓ Passage saved successfully!")
    else:
        print("   ✗ Failed to save passage")
    
    # Save progress
    print("\n3. Saving user progress...")
    success = save_user_progress_to_csv(45, 3, ["metamorphosis", "chrysalis", "nectar"])
    if success:
        print("   ✓ Progress saved successfully!")
    else:
        print("   ✗ Failed to save progress")
    
    # Load and display saved data
    print("\n4. Loading saved data...")
    passages = load_passages_from_csv()
    progress = load_user_progress_from_csv()
    
    print(f"   Loaded {len(passages)} passages")
    if passages:
        print(f"   First passage: {passages[0]['passage'][:50]}...")
        print(f"   Vocabulary words: {list(passages[0]['vocabulary'].keys())}")
        print(f"   Questions: {len(passages[0]['questions'])}")
    
    print(f"   Progress: {progress['points']} points, {progress['passages_completed']} completed")
    print(f"   Vocabulary learned: {progress['vocab_learned']}")
    
    # Add more data to demonstrate persistence
    print("\n5. Adding more sample data...")
    
    # Add second passage
    passage2 = "The solar system contains eight planets that orbit around the sun."
    vocab2 = {"solar": "relating to the sun", "orbit": "to move in a circle around something"}
    questions2 = ["How many planets are in our solar system?", "What do planets orbit around?"]
    
    save_passage_to_csv(passage2, vocab2, questions2)
    save_user_progress_to_csv(65, 4, ["metamorphosis", "chrysalis", "nectar", "solar", "orbit"])
    
    # Final load
    passages = load_passages_from_csv()
    progress = load_user_progress_from_csv()
    
    print(f"   Now have {len(passages)} passages")
    print(f"   Final progress: {progress['points']} points, {progress['passages_completed']} completed")
    print(f"   Final vocabulary: {len(progress['vocab_learned'])} words learned")
    
    # Show file structure
    print("\n6. Generated files:")
    for file in [PASSAGES_CSV, PROGRESS_CSV]:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   {file}: {size} bytes")
    
    print("\n✅ Demo completed successfully!")
    print(f"Check the '{DATA_DIR}' directory for generated CSV files.")

if __name__ == '__main__':
    demo_csv_persistence()