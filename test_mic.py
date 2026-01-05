
import speech_recognition as sr
import pyaudio

print('--- AUDIO DIAGNOSTIC ---')
try:
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    print(f'Found {numdevices} devices:')
    for i in range(0, numdevices):
        dev = p.get_device_info_by_host_api_device_index(0, i)
        if dev.get('maxInputChannels') > 0:
            print(f"Input Device id {i} - {dev.get('name')}")
except Exception as e:
    print(f'PyAudio Error: {e}')

print('\nTesting Recognition...')
r = sr.Recognizer()
r.energy_threshold = 2000 # Lower threshold slightly
r.dynamic_energy_threshold = True

try:
    with sr.Microphone() as source:
        print('✅ Microphone initialized!')
        print('⏳ Adjusting for noise...')
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        print('🎤 Please say "TEST" now...')
        audio = r.listen(source, timeout=5, phrase_time_limit=3)
        print('✅ Audio captured!')
        
        print('Transcribing...')
        text = r.recognize_google(audio)
        print(f'✅ Result: {text}')
        
except sr.WaitTimeoutError:
    print('❌ Timeout: No speech detected in 3 seconds')
except sr.RequestError as e:
    print(f'❌ Network/API Error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
