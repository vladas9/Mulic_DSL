# flask_server.py - Backend server for Music DSL Web IDE

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
import os
import json
from music_dsl import Lexer, Parser, Interpreter  # Import your existing classes
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Store generated files temporarily
generated_files = {}

@app.route('/')
def index():
    return '''
    <h1>Music DSL Backend Server</h1>
    <p>Server is running! Use the web IDE to generate music.</p>
    <p>Endpoints:</p>
    <ul>
        <li>POST /generate - Generate music from DSL code</li>
        <li>GET /download/&lt;file_id&gt;/&lt;type&gt; - Download generated files</li>
    </ul>
    '''

@app.route('/generate', methods=['POST'])
def generate_music():
    try:
        # Get the DSL code from request
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': 'No code provided'}), 400
        
        dsl_code = data['code']
        print(f"Received DSL code: {len(dsl_code)} characters")
        
        # Generate unique ID for this session
        session_id = str(uuid.uuid4())[:8]
        
        # Create temporary directory for this session
        temp_dir = tempfile.mkdtemp(prefix=f'music_dsl_{session_id}_')
        
        try:
            # Save the DSL code to a temporary file
            dsl_file = os.path.join(temp_dir, 'music.dsl')
            with open(dsl_file, 'w') as f:
                f.write(dsl_code)
            
            # Process the DSL code
            print("Tokenizing source code...")
            lexer = Lexer(dsl_code)
            tokens = lexer.scan_tokens()
            
            print("Parsing tokens into AST...")
            parser = Parser(tokens)
            tracks = parser.parse()
            
            if not tracks:
                return jsonify({'error': 'No valid tracks found in the code'}), 400
            
            print(f"Successfully parsed {len(tracks)} tracks")
            
            # Create interpreter and interpret AST
            print("Interpreting the music...")
            interpreter = Interpreter()
            interpreter.interpret(tracks)
            
            # Generate files
            base_filename = os.path.join(temp_dir, 'generated_music')
            
            # Generate MIDI file
            print("Generating MIDI file...")
            midi_file = base_filename + '.mid'
            interpreter.generate_midi(midi_file)
            
            # Generate MP3 file
            print("Generating MP3 file...")
            mp3_file = base_filename + '.mp3'
            interpreter.convert_midi_to_mp3(midi_file, mp3_file)
            
            # Generate sheet music data
            print("Generating sheet music...")
            sheet_html = base_filename + '_sheet.html'
            interpreter.generate_vexflow_data(sheet_html)
            
            # Read the generated JSON data for sheet music
            sheet_json = base_filename + '_sheet.json'
            sheet_data = None
            if os.path.exists(sheet_json):
                with open(sheet_json, 'r') as f:
                    sheet_data = json.load(f)
            
            # Store file paths
            generated_files[session_id] = {
                'midi': midi_file if os.path.exists(midi_file) else None,
                'mp3': mp3_file if os.path.exists(mp3_file) else None,
                'sheet_html': sheet_html if os.path.exists(sheet_html) else None,
                'sheet_json': sheet_json if os.path.exists(sheet_json) else None,
                'created_at': datetime.now().isoformat(),
                'temp_dir': temp_dir
            }
            
            # Prepare response
            response_data = {
                'success': True,
                'session_id': session_id,
                'tracks_count': len(tracks),
                'events_count': len(interpreter.events),
                'duration': max((event.start_time + event.duration for event in interpreter.events 
                               if hasattr(event, 'start_time')), default=0),
                'files': {
                    'midi': f'/download/{session_id}/midi',
                    'mp3': f'/download/{session_id}/mp3',
                    'sheet_html': f'/download/{session_id}/sheet_html'
                },
                'sheet_data': sheet_data
            }
            
            print(f"Generation completed successfully! Session ID: {session_id}")
            return jsonify(response_data)
            
        except Exception as e:
            print(f"Error during music generation: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': f'Error generating music: {str(e)}',
                'session_id': session_id
            }), 500
            
    except Exception as e:
        print(f"Error in generate_music endpoint: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/download/<session_id>/<file_type>')
def download_file(session_id, file_type):
    try:
        if session_id not in generated_files:
            return jsonify({'error': 'Session not found'}), 404
        
        files = generated_files[session_id]
        
        if file_type == 'midi' and files['midi']:
            return send_file(
                files['midi'],
                as_attachment=True,
                download_name='generated_music.mid',
                mimetype='audio/midi'
            )
        elif file_type == 'mp3' and files['mp3']:
            return send_file(
                files['mp3'],
                as_attachment=True,
                download_name='generated_music.mp3',
                mimetype='audio/mpeg'
            )
        elif file_type == 'sheet_html' and files['sheet_html']:
            return send_file(
                files['sheet_html'],
                as_attachment=True,
                download_name='sheet_music.html',
                mimetype='text/html'
            )
        else:
            return jsonify({'error': 'File not found or not generated'}), 404
            
    except Exception as e:
        print(f"Error downloading file: {e}")
        return jsonify({'error': f'Download error: {str(e)}'}), 500

@app.route('/audio/<session_id>')
def serve_audio(session_id):
    """Serve audio file for the web player"""
    try:
        if session_id not in generated_files:
            return jsonify({'error': 'Session not found'}), 404
        
        files = generated_files[session_id]
        if files['mp3'] and os.path.exists(files['mp3']):
            return send_file(
                files['mp3'],
                mimetype='audio/mpeg',
                as_attachment=False  # Stream instead of download
            )
        else:
            return jsonify({'error': 'Audio file not found'}), 404
            
    except Exception as e:
        print(f"Error serving audio: {e}")
        return jsonify({'error': f'Audio serve error: {str(e)}'}), 500

@app.route('/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """Clean up temporary files for a session"""
    try:
        if session_id in generated_files:
            temp_dir = generated_files[session_id]['temp_dir']
            
            # Remove temporary files
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # Remove from memory
            del generated_files[session_id]
            
            return jsonify({'success': True, 'message': 'Session cleaned up'})
        else:
            return jsonify({'error': 'Session not found'}), 404
            
    except Exception as e:
        print(f"Error cleaning up session: {e}")
        return jsonify({'error': f'Cleanup error: {str(e)}'}), 500

@app.route('/status')
def status():
    """Get server status and active sessions"""
    return jsonify({
        'status': 'running',
        'active_sessions': len(generated_files),
        'sessions': {
            session_id: {
                'created_at': data['created_at'],
                'files_available': {
                    'midi': data['midi'] is not None,
                    'mp3': data['mp3'] is not None,
                    'sheet': data['sheet_html'] is not None
                }
            }
            for session_id, data in generated_files.items()
        }
    })

# Cleanup old sessions periodically (in a real app, use a background task)
import threading
import time

def cleanup_old_sessions():
    """Remove sessions older than 1 hour"""
    while True:
        try:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, data in generated_files.items():
                created_time = datetime.fromisoformat(data['created_at'])
                age = (current_time - created_time).total_seconds()
                
                # Remove sessions older than 1 hour (3600 seconds)
                if age > 3600:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                print(f"Cleaning up old session: {session_id}")
                try:
                    temp_dir = generated_files[session_id]['temp_dir']
                    if os.path.exists(temp_dir):
                        import shutil
                        shutil.rmtree(temp_dir)
                    del generated_files[session_id]
                except Exception as e:
                    print(f"Error cleaning up session {session_id}: {e}")
                    
        except Exception as e:
            print(f"Error in cleanup thread: {e}")
        
        # Sleep for 10 minutes before next cleanup
        time.sleep(600)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    print("Starting Music DSL Backend Server...")
    print("Make sure you have the following dependencies installed:")
    print("  pip install flask flask-cors")
    print("\nServer will run on http://localhost:5000")
    print("Access the API at http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)