# English Learning for 5th Grade - CSV Persistence Implementation

## Overview

This Streamlit application helps 5th graders learn English through interactive reading passages, vocabulary exercises, and comprehension questions. The app now includes robust CSV data persistence to store generated content and user progress.

## Features

### Core Features
- **Interactive Reading Passages**: AI-generated reading passages suitable for 5th graders
- **Vocabulary Learning**: New words with definitions and audio pronunciation
- **Comprehension Questions**: Questions to test understanding
- **Progress Tracking**: Points and progress tracking with rewards
- **Text-to-Speech**: Audio playback for passages and vocabulary words

### New CSV Persistence Features
- **Persistent Data Storage**: All generated content is saved to CSV files
- **Smart Content Loading**: App loads existing passages instead of generating new ones
- **User Progress Persistence**: Points, completion status, and vocabulary learned are saved
- **Data Management**: Clear and save progress functionality

## Setup Instructions

### Prerequisites
- Python 3.7+
- OpenAI API key (for generating new content)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/akshaykumarbedre/English_leaning_for_5th_grade.git
   cd English_leaning_for_5th_grade
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # Create a .env file in the root directory
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

### Running the Application
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Usage Guide

### First Time Usage
1. **Start the app**: Run `streamlit run app.py`
2. **Generate first passage**: Click "Get Your First Reading Passage" to create and save your first passage
3. **Complete activities**: Read the passage, learn vocabulary, answer questions, and take the quiz
4. **Track progress**: Check your progress in the sidebar

### Subsequent Usage
1. **Load existing content**: The app will show available passages from previous sessions
2. **Choose your option**:
   - **"Use Existing Passage"**: Load a previously generated passage
   - **"Generate New Passage"**: Create and save a new passage
3. **Continue learning**: Complete activities and track your progress

## CSV Data Structure

### Passages CSV (`data/passages.csv`)
| Column | Description |
|--------|-------------|
| `passage` | The reading passage text |
| `vocabulary` | Vocabulary words and definitions (format: "word1:def1,word2:def2") |
| `questions` | Comprehension questions (format: "q1;q2;q3") |
| `created_at` | Timestamp when the passage was created |

### User Progress CSV (`data/user_progress.csv`)
| Column | Description |
|--------|-------------|
| `points` | Total points earned |
| `passages_completed` | Number of passages completed |
| `vocab_learned` | Vocabulary words learned (format: "word1,word2,word3") |
| `last_updated` | Timestamp of last update |

## Data Management

### Saving Progress
- Progress is automatically saved when you:
  - Complete a passage
  - Learn new vocabulary
  - Submit answers or complete quizzes
- Manual save option available in the sidebar

### Clearing Data
- Use the "Clear All Data" button in the sidebar to reset all progress
- This will delete CSV files and reset session state

## Testing

### Run Tests
```bash
# Run basic CSV functionality tests
python test_csv_persistence.py

# Run app integration tests
python test_app_csv_integration.py

# Run demonstration
python demo_csv_persistence.py
```

## File Structure
```
English_leaning_for_5th_grade/
├── app.py                      # Main Streamlit application
├── main.py                     # Alternative version with JSON storage
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
├── data/                       # CSV data directory (auto-created)
│   ├── passages.csv           # Stored passages
│   └── user_progress.csv      # User progress
├── test_csv_persistence.py    # CSV functionality tests
├── test_app_csv_integration.py # App integration tests
├── demo_csv_persistence.py    # Demonstration script
└── README.md                  # This file
```

## Key Implementation Details

### CSV Persistence Logic
1. **On app start**: Load existing passages and user progress from CSV files
2. **Content generation**: New passages are immediately saved to CSV
3. **Progress updates**: User progress is saved after each activity
4. **Data rotation**: Existing passages are rotated through before generating new ones

### Error Handling
- Graceful handling of missing or corrupted CSV files
- Default values returned when data cannot be loaded
- Error messages displayed to users when save operations fail

### Data Integrity
- UTF-8 encoding for special characters
- Proper escaping of commas and quotes in CSV format
- Structured data format for reliable parsing

## Troubleshooting

### Common Issues
1. **Missing OpenAI API key**: Set the `OPENAI_API_KEY` environment variable
2. **Permission errors**: Ensure the app has write permissions to the data directory
3. **CSV parsing errors**: Check that CSV files are not corrupted or manually edited improperly

### Data Recovery
- If CSV files are corrupted, delete them and the app will recreate them
- Progress will be lost but the app will continue to function
- Always backup your data directory before making changes

## Future Enhancements
- Export/import functionality for sharing progress
- Multiple user profiles
- Enhanced analytics and reporting
- Integration with learning management systems

## License
This project is open source and available under the MIT License.