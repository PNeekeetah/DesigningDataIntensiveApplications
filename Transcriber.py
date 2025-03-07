import speech_recognition as sr

# Load the audio file
for i in range(21):
    audio_path = f"/mnt/c/Users/crist/Desktop/DesigningDataIntensiveApplications/part5_output_{str(i).zfill(2)}.wav"
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)

    # Transcribe the audio
    try:
        transcription = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        transcription = "Sorry, I couldn't understand the audio."
    except sr.RequestError:
        transcription = "There was an error processing the audio."

    print(transcription)