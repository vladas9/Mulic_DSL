import fluidsynth
import time
import math
from pydub import AudioSegment

NOTE_FREQUENCIES = {
    'do': 261.63, 're': 293.66, 'mi': 329.63, 'fa': 349.23, 'sol': 392.00, 
    'la': 440.00, 'si': 493.88
}

class MusicInterpreter:
    def __init__(self, parsed_data, soundfont_path):
        self.parsed_data = parsed_data
        self.tempo = 120  
        self.volume = 80  
        self.fs = fluidsynth.Synth()
        self.output_wav = "temp_output.wav"
        # Configure fluidsynth to write to a WAV file
        self.fs.setting("audio.file.name", self.output_wav)
        self.fs.setting("audio.file.type", "wav")
        self.fs.start(driver="file")
        self.fs.sfload(soundfont_path)  # Load the SoundFont

    def fraction_to_duration(self, fraction, tempo):
        beat_duration_in_ms = (60 / tempo) * 1000
        return beat_duration_in_ms * eval(fraction)

    def play_piano_note(self, frequency, duration_ms):
        midi_note = self.freq_to_midi(frequency)
        self.fs.noteon(0, midi_note, self.volume)  # Channel 0, MIDI note, velocity
        time.sleep(duration_ms / 1000.0)
        self.fs.noteoff(0, midi_note)  # Turn off the note

    def play_guitar_note(self, frequency, duration_ms):
        midi_note = self.freq_to_midi(frequency)
        self.fs.noteon(1, midi_note, self.volume)  # Use channel 1 for guitar
        time.sleep(duration_ms / 1000.0)
        self.fs.noteoff(1, midi_note)

    def freq_to_midi(self, frequency):
        # Convert frequency to MIDI note
        return int(69 + 12 * (math.log(frequency / 440.0) / math.log(2)))

    def generate_music(self):
        for chunk in self.parsed_data:
            for statement in chunk['statements']:
                if statement['type'] == 'TIME_SIGNATURE':
                    pass  # Handle time signature
                elif statement['type'] == 'TEMPO':
                    self.tempo = int(statement['value'].split('=')[1])
                elif statement['type'] == 'VOLUME':
                    self.volume = int(statement['value'].split('=')[1])
                elif statement['type'] == 'PIANO':
                    self.handle_piano(statement)
                elif statement['type'] == 'GUITAR':
                    self.handle_guitar(statement)
                elif statement['type'] == 'SYNC':
                    self.handle_sync(statement['statements'])
                elif statement['type'] == 'LOOP':
                    self.handle_loop(statement)
        # Close the synth to finalize the WAV file
        self.fs.delete()

    def handle_piano(self, statement):
        note_name = statement['identifier2']
        fraction = statement['fraction']
        frequency = NOTE_FREQUENCIES.get(note_name)
        if frequency:
            duration_ms = self.fraction_to_duration(fraction, self.tempo)
            self.play_piano_note(frequency, duration_ms)

    def handle_guitar(self, statement):
        note_name = statement['identifier2']
        fraction = statement['fraction']
        frequency = NOTE_FREQUENCIES.get(note_name)
        if frequency:
            duration_ms = self.fraction_to_duration(fraction, self.tempo)
            self.play_guitar_note(frequency, duration_ms)

    def handle_sync(self, sync_statements):
        for statement in sync_statements:
            if statement['type'] == 'PIANO':
                self.handle_piano(statement)
            elif statement['type'] == 'GUITAR':
                self.handle_guitar(statement)

    def handle_loop(self, loop_data):
        loop_start_value = loop_data['start_value']
        loop_condition = loop_data['condition_value']
        loop_increment = int(loop_data['increment_value'])
        loop_body = loop_data['body']
        
        loop_start_frequency = NOTE_FREQUENCIES.get(loop_start_value)
        loop_condition_frequency = NOTE_FREQUENCIES.get(loop_condition)
        
        if loop_start_frequency is None or loop_condition_frequency is None:
            raise ValueError(f"Invalid note in loop: {loop_start_value} or {loop_condition}")

        current_frequency = loop_start_frequency

        while current_frequency <= loop_condition_frequency:
            for action in loop_body:
                if action['type'] == 'PIANO':
                    self.handle_piano(action)
                elif action['type'] == 'GUITAR':
                    self.handle_guitar(action)
            current_frequency += loop_increment * (loop_condition_frequency - loop_start_frequency) / 7
