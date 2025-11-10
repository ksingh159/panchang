import speech_recognition as sr
import numpy as np
from pydub import AudioSegment
import tempfile
import os

def analyze_mantra_prunciation(audio_file, expected_mantra):
    """
    Analyze mantra pronunciation using speech recognition
    """
    # Convert audio to WAV format if needed
    if audio_file.name.endswith('.mp3'):
        audio = AudioSegment.from_mp3(audio_file)
        wav_path = tempfile.mktemp(suffix='.wav')
        audio.export(wav_path, format='wav')
    else:
        wav_path = audio_file.temporary_file_path()
    
    # Initialize recognizer
    r = sr.Recognizer()
    
    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            recognized_text = r.recognize_google(audio_data, language='sa')  # Sanskrit
        
        # Compare with expected mantra
        accuracy = calculate_pronunciation_accuracy(recognized_text, expected_mantra)
        
        return {
            "recognized_text": recognized_text,
            "accuracy": accuracy,
            "feedback": generate_pronunciation_feedback(recognized_text, expected_mantra)
        }
    
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        # Clean up temporary file
        if os.path.exists(wav_path):
            os.remove(wav_path)

def calculate_pronunciation_accuracy(recognized, expected):
    """Calculate pronunciation accuracy using Levenshtein distance"""
    # Implementation of Levenshtein distance algorithm
    if len(recognized) == 0:
        return 0
    if len(expected) == 0:
        return 0
        
    distance = levenshtein_distance(recognized.lower(), expected.lower())
    max_length = max(len(recognized), len(expected))
    accuracy = (1 - distance / max_length) * 100
    
    return round(accuracy, 2)

def levenshtein_distance(s1, s2):
    """Calculate Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def generate_pronunciation_feedback(recognized, expected):
    """Generate helpful feedback for pronunciation improvement"""
    # This would be more sophisticated in a real implementation
    feedback = []
    
    if len(recognized) < len(expected) * 0.7:
        feedback.append("Try to pronounce each syllable more clearly and completely.")
    
    # Add specific feedback based on common Sanskrit pronunciation mistakes
    common_mistakes = {
        "va": "ba",
        "sha": "sa", 
        "ṣa": "sa",
        "ṇa": "na"
    }
    
    for mistake, correction in common_mistakes.items():
        if mistake in recognized and correction in expected:
            feedback.append(f"Try to pronounce '{correction}' as '{mistake}'")
    
    return feedback if feedback else ["Your pronunciation is good! Keep practicing."]