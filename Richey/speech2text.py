import speech_recognition as sr
from sys import byteorder
from array import array
from struct import pack
import pyaudio, wave, os, glob
from playsound import playsound
from gtts import gTTS

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def trim(snd_data):
    "Trim the blank spots at the start and end"
    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i)>THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def add_silence(snd_data, seconds):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    silence = [0] * int(seconds * RATE)
    r = array('h', silence)
    r.extend(snd_data)
    r.extend(silence)
    return r

def record():
    """
    Record a word or words from the microphone and
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the
    start and end, and pads with 0.5 seconds of
    blank sound to make sure VLC et al can play
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    while 1:
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

        if snd_started and num_silent > 30:
            break

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    r = trim(r)
    r = add_silence(r, 0.5)
    return sample_width, r

def record_to_file(path):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record()
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

def recognize_speech(file_path):
    recognizer = sr.Recognizer()

    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)  # Records the entire audio file
        recognizer.adjust_for_ambient_noise(source)
    try:
        text = recognizer.recognize_google(audio_data)  # Uses Google Web Speech API
        return text
    except sr.UnknownValueError:   # No words error
        return "Speech recognition could not understand audio"
    except sr.RequestError as e:   # No internet error
        return f"Could not request results from Google Web Speech API service; {e}"


if __name__ == '__main__':
    print("Wave files:", glob.glob("*.wav"))
    print("  Enter a wave file name")
    IN = input("  or speak words into the microphone: ")

    delete_file = False

    if os.path.isfile(IN):
        # If input is an existing WAV file
        text = recognize_speech(IN)
        print("Transcribed text:")
        print(text)
    else:
        WAVE = '0000_example.wav'
        record_to_file(WAVE)
        print("Sound: saved to <%s>" % (WAVE))

        text = recognize_speech(WAVE)
        print("Transcribed text:")
        print(text)

        delete_file = True

    if delete_file and os.path.exists(WAVE):
        # Delete the file only if it was created from the mic
        os.remove(WAVE)

    audio = gTTS(text=text, lang="en", tld="co.in", slow=False)
    respeech = 'respeech.wav'
    audio.save(respeech);  playsound(respeech);  os.remove(respeech)