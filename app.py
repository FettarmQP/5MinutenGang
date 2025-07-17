from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import asyncio
import threading
import time
import requests
import os
import socket
import ssl
from datetime import datetime, timedelta
from collections import deque
import random
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Twitch Configuration
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID', 'your_client_id_here')
TWITCH_ACCESS_TOKEN = os.getenv('TWITCH_ACCESS_TOKEN', 'your_access_token_here')
TWITCH_CHANNEL = os.getenv('TWITCH_CHANNEL', 'your_channel_name')

# Global variables - organized by channel
channels_data = {}  # Dictionary für alle Channel-Daten

def get_channel_data(channel_name):
    """Hole oder erstelle Channel-spezifische Daten"""
    if channel_name not in channels_data:
        channels_data[channel_name] = {
            'chatters_queue': deque(),
            'displayed_users': set(),
            'collected_users': set(),
            'stream_start_time': None,
            'is_collecting': False,
            'twitch_irc': None
        }
    return channels_data[channel_name]

class TwitchIRCClient:
    def __init__(self, channel, oauth_token):
        self.channel = channel.lower()
        self.oauth_token = oauth_token
        self.socket = None
        self.connected = False
        self.chatters = set()
        self.running = False
        self.chat_messages = []  # Sammelt echte Chat-Nachrichten
        self.active_chatters = set()  # User die tatsächlich geschrieben haben
        self.first_messages = {}  # Speichert die erste Nachricht jedes Users
        
    def connect(self):
        """Verbindung zu Twitch IRC"""
        try:
            # IRC Socket erstellen
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            
            # SSL Wrapper
            context = ssl.create_default_context()
            self.socket = context.wrap_socket(self.socket, server_hostname='irc.chat.twitch.tv')
            
            # Verbindung zu Twitch IRC
            self.socket.connect(('irc.chat.twitch.tv', 6697))
            
            # Authentifizierung
            self.socket.send(f'PASS oauth:{self.oauth_token}\r\n'.encode())
            self.socket.send(f'NICK 5minutengang_bot\r\n'.encode())
            self.socket.send(f'JOIN #{self.channel}\r\n'.encode())
            
            # Capabilities für bessere Chat-Info
            self.socket.send('CAP REQ :twitch.tv/membership\r\n'.encode())
            self.socket.send('CAP REQ :twitch.tv/tags\r\n'.encode())
            self.socket.send('CAP REQ :twitch.tv/commands\r\n'.encode())
            
            self.connected = True
            print(f"✅ Verbunden mit Twitch Chat: #{self.channel}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Verbinden mit Twitch IRC: {e}")
            self.connected = False
            return False
    
    def listen(self):
        """Höre auf Chat-Nachrichten"""
        self.running = True
        buffer = ""
        
        while self.running and self.connected:
            try:
                # Daten empfangen
                data = self.socket.recv(1024).decode('utf-8', errors='ignore')
                buffer += data
                
                # Zeilen verarbeiten
                while '\r\n' in buffer:
                    line, buffer = buffer.split('\r\n', 1)
                    self.process_message(line)
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Fehler beim Lesen von IRC: {e}")
                break
    
    def process_message(self, message):
        """Verarbeite IRC-Nachrichten"""
        try:
            # PING antworten
            if message.startswith('PING'):
                pong = message.replace('PING', 'PONG')
                self.socket.send(f'{pong}\r\n'.encode())
                return
            
            # Chat-Nachricht parsen - nur echte Nachrichten von Usern
            if 'PRIVMSG' in message:
                # Neues Format mit Tags: @tags :username!username@username.tmi.twitch.tv PRIVMSG #channel :message
                # Altes Format: :username!username@username.tmi.twitch.tv PRIVMSG #channel :message
                
                # Regex für beide Formate
                match = re.match(r'(?:@[^:]*\s+)?:(\w+)!.*PRIVMSG #\w+ :(.*)', message)
                if match:
                    username = match.group(1)
                    chat_message = match.group(2).strip()
                    print(f"✅ Chat-Nachricht erkannt - {username}: {chat_message}")
                    
                    # Ignoriere Bot-Commands und sehr kurze Nachrichten
                    if not chat_message.startswith('!') and len(chat_message) > 0:
                        # Timestamp für die Nachricht
                        timestamp = datetime.now()
                        
                        # Nur die erste Nachricht des Users speichern
                        if username not in self.first_messages:
                            # Erste Nachricht dieses Users speichern
                            chat_entry = {
                                'username': username,
                                'message': chat_message,
                                'timestamp': timestamp
                            }
                            self.first_messages[username] = chat_entry
                            self.chat_messages.append(chat_entry)
                            
                            # User zu aktiven Chattern hinzufügen
                            if username not in self.active_chatters:
                                self.active_chatters.add(username)
                                print(f"🆕 Neuer User in der Gang: {username} - '{chat_message[:50]}{'...' if len(chat_message) > 50 else ''}'")
                        
                        # Auch zur allgemeinen Chatter-Liste hinzufügen
                        self.chatters.add(username)
                        
        except Exception as e:
            print(f"Fehler beim Verarbeiten der Nachricht: {e}")
    
    def get_active_chatters(self):
        """Hole User die tatsächlich Chat-Nachrichten geschrieben haben"""
        return list(self.active_chatters)
    
    def get_recent_messages(self, limit=20):
        """Hole die letzten Chat-Nachrichten"""
        return self.chat_messages[-limit:] if self.chat_messages else []
    
    def get_new_chatters(self):
        """Hole neue aktive Chatter seit dem letzten Aufruf (nur die die geschrieben haben)"""
        return self.get_active_chatters()
    
    def get_recent_messages(self, limit=20):
        """Hole die letzten Chat-Nachrichten"""
        return self.chat_messages[-limit:] if self.chat_messages else []
    
    def disconnect(self):
        """Verbindung trennen"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        print("🔌 Twitch IRC Verbindung getrennt")


class TwitchChatMonitor:
    def __init__(self):
        self.headers = {
            'Client-ID': TWITCH_CLIENT_ID,
            'Authorization': f'Bearer {TWITCH_ACCESS_TOKEN}'
        }
    
    def get_user_info(self, username):
        """Get user info including profile picture from Twitch API"""
        try:
            url = f'https://api.twitch.tv/helix/users?login={username}'
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data['data']:
                    user = data['data'][0]
                    return {
                        'username': user['display_name'],
                        'profile_image': user['profile_image_url'],
                        'id': user['id']
                    }
        except Exception as e:
            print(f"Error getting user info for {username}: {e}")
        
        return {
            'username': username,
            'profile_image': 'https://static-cdn.jtvnw.net/jtv_user_pictures/default_profile_picture-70x70.png',
            'id': None
        }
    
    def get_chatters(self, channel_name):
        """Get current active chatters from Twitch IRC (nur die die geschrieben haben)"""
        channel_data = get_channel_data(channel_name)
        twitch_irc = channel_data['twitch_irc']
        
        try:
            if twitch_irc and twitch_irc.connected:
                # Echte aktive Chatter vom IRC (nur die die geschrieben haben)
                return twitch_irc.get_active_chatters()
            else:
                # Kein IRC verbunden - keine Chatter
                return []
                
        except Exception as e:
            print(f"Error getting chatters for {channel_name}: {e}")
            return []
    
    
monitor = TwitchChatMonitor()

def collect_chatters(channel_name):
    """Collect chatters for the first 5 minutes of stream"""
    channel_data = get_channel_data(channel_name)
    
    print(f"🚀 Starting chatter collection for #{channel_name}...")
    channel_data['stream_start_time'] = datetime.now()
    channel_data['is_collecting'] = True
    
    # IRC-Verbindung starten wenn möglich
    token = TWITCH_ACCESS_TOKEN
    
    if channel_name != 'your_channel_name' and token != 'your_access_token_here':
        try:
            channel_data['twitch_irc'] = TwitchIRCClient(channel_name, token)
            if channel_data['twitch_irc'].connect():
                # IRC-Listener in separatem Thread starten
                irc_thread = threading.Thread(target=channel_data['twitch_irc'].listen)
                irc_thread.daemon = True
                irc_thread.start()
                print(f"🎯 IRC-Chat Monitoring gestartet für #{channel_name}")
            else:
                print(f"⚠️ IRC-Verbindung fehlgeschlagen für #{channel_name}")
                channel_data['twitch_irc'] = None
        except Exception as e:
            print(f"⚠️ IRC-Setup fehlgeschlagen für #{channel_name}: {e}")
            channel_data['twitch_irc'] = None
    else:
        print(f"⚠️ Keine gültigen Twitch-Credentials für #{channel_name}")
        channel_data['twitch_irc'] = None
    
    end_time = channel_data['stream_start_time'] + timedelta(minutes=5)
    
    while datetime.now() < end_time and channel_data['is_collecting']:
        try:
            current_chatters = monitor.get_chatters(channel_name)
            
            for username in current_chatters:
                # Prüfe ob User schon gesammelt wurde (verhindert Duplikate beim Sammeln)
                if username not in channel_data['collected_users']:
                    user_info = monitor.get_user_info(username)
                    channel_data['chatters_queue'].append(user_info)
                    channel_data['collected_users'].add(username)
                    print(f"➕ Neuer Chatter gesammelt in #{channel_name}: {username}")
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"❌ Error in collect_chatters for #{channel_name}: {e}")
            time.sleep(5)
    
    # IRC-Verbindung beenden
    if channel_data['twitch_irc']:
        channel_data['twitch_irc'].disconnect()
        channel_data['twitch_irc'] = None
    
    channel_data['is_collecting'] = False
    print(f"✅ Sammlung beendet für #{channel_name}. Gesammelte Chatter: {len(channel_data['collected_users'])}")

def display_chatters(channel_name):
    """Display chatters every 5 seconds - zeige Begrüßung und erste Chat-Nachrichten"""
    channel_data = get_channel_data(channel_name)
    
    while True:
        try:
            # Sende nur erste Chat-Nachrichten neuer User (nur bei IRC-Verbindung)
            if channel_data['twitch_irc'] and channel_data['twitch_irc'].connected:
                # Iteriere über alle ersten Nachrichten und prüfe neue
                for username, msg_data in list(channel_data['twitch_irc'].first_messages.items()):
                    # Prüfe ob diese erste Nachricht schon gesendet wurde
                    msg_key = f"first_msg_{username}"
                    if msg_key not in channel_data['displayed_users']:
                        user_info = monitor.get_user_info(username)
                        chat_data = {
                            'username': username,
                            'message': msg_data['message'],
                            'timestamp': msg_data['timestamp'].isoformat(),
                            'profile_image': user_info['profile_image'],
                            'channel': channel_name
                        }
                        socketio.emit('chat_message', chat_data)
                        channel_data['displayed_users'].add(msg_key)
                        
                        # User auch zur Queue hinzufügen für Begrüßungs-Anzeige
                        if username not in channel_data['collected_users'] and channel_data['is_collecting']:
                            channel_data['chatters_queue'].append(user_info)
                            channel_data['collected_users'].add(username)
                            print(f"💬 Neuer Chatter aus IRC in #{channel_name}: {username}")
            
            # Zeige Begrüßung für User in der Queue
            if channel_data['chatters_queue']:
                current_user = channel_data['chatters_queue'].popleft()
                username = current_user['username']
                
                # Prüfe ob User-Begrüßung schon angezeigt wurde
                user_key = f"user_{username}"
                if user_key not in channel_data['displayed_users']:
                    channel_data['displayed_users'].add(user_key)
                    current_user['channel'] = channel_name
                    socketio.emit('new_user', current_user)
                    print(f"📺 Zeige Begrüßung in #{channel_name}: {username}")
                    time.sleep(5)
                else:
                    print(f"⏭️ Begrüßung für {username} in #{channel_name} bereits angezeigt, überspringe")
                    continue  # Zum nächsten User ohne zu warten
            else:
                # If no more users, show welcome message
                if channel_data['is_collecting']:
                    socketio.emit('no_users', {'message': 'Warte auf neue Chatter... 💬', 'channel': channel_name})
                else:
                    socketio.emit('no_users', {'message': 'Willkommen im Stream! 🎮', 'channel': channel_name})
                time.sleep(2)  # Häufiger prüfen für bessere Responsivität
                
        except Exception as e:
            print(f"❌ Error in display_chatters for #{channel_name}: {e}")
            time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<channel_name>')
def index_channel(channel_name):
    return render_template('index.html', channel_name=channel_name)

@app.route('/sound_test')
def sound_test():
    return render_template('sound_test.html')

@app.route('/<channel_name>/start_collection')
def start_collection(channel_name):
    """Start collecting chatters for 5 minutes"""
    channel_data = get_channel_data(channel_name)
    
    if not channel_data['is_collecting']:
        # Reset everything für neue Sammlung
        channel_data['chatters_queue'].clear()
        channel_data['displayed_users'].clear()
        channel_data['collected_users'].clear()
        
        print(f"🔄 Reset: Alle Listen geleert für neue Sammlung in #{channel_name}")
        
        # Start collection in background thread
        collection_thread = threading.Thread(target=collect_chatters, args=(channel_name,))
        collection_thread.daemon = True
        collection_thread.start()
        
        # Start display thread if not already running for this channel
        display_thread = threading.Thread(target=display_chatters, args=(channel_name,))
        display_thread.daemon = True
        display_thread.start()
        
        return jsonify({
            'status': 'started', 
            'message': f'Chatter collection started for #{channel_name} for 5 minutes',
            'channel': channel_name,
            'note': 'Alle bisherigen User wurden zurückgesetzt'
        })
    else:
        return jsonify({
            'status': 'already_running', 
            'message': f'Collection already in progress for #{channel_name}',
            'channel': channel_name
        })

@app.route('/<channel_name>/stop_collection')
def stop_collection(channel_name):
    """Stop collecting chatters"""
    channel_data = get_channel_data(channel_name)
    
    channel_data['is_collecting'] = False
    
    # IRC-Verbindung beenden falls vorhanden
    if channel_data['twitch_irc']:
        channel_data['twitch_irc'].disconnect()
        channel_data['twitch_irc'] = None
    
    return jsonify({
        'status': 'stopped', 
        'message': f'Chatter collection stopped for #{channel_name}',
        'channel': channel_name
    })

@app.route('/<channel_name>/status')
def status(channel_name):
    """Get current status"""
    channel_data = get_channel_data(channel_name)
    
    if channel_data['stream_start_time'] and channel_data['is_collecting']:
        elapsed = datetime.now() - channel_data['stream_start_time']
        remaining = timedelta(minutes=5) - elapsed
        return jsonify({
            'channel': channel_name,
            'is_collecting': channel_data['is_collecting'],
            'queue_length': len(channel_data['chatters_queue']),
            'collected_chatters': len(channel_data['collected_users']),
            'displayed_chatters': len(channel_data['displayed_users']),
            'irc_connected': channel_data['twitch_irc'].connected if channel_data['twitch_irc'] else False,
            'time_remaining': str(remaining).split('.')[0] if remaining.total_seconds() > 0 else "Finished"
        })
    else:
        return jsonify({
            'channel': channel_name,
            'is_collecting': channel_data['is_collecting'],
            'queue_length': len(channel_data['chatters_queue']),
            'collected_chatters': len(channel_data['collected_users']),
            'displayed_chatters': len(channel_data['displayed_users']),
            'irc_connected': channel_data['twitch_irc'].connected if channel_data['twitch_irc'] else False,
            'time_remaining': "Not started"
        })

@app.route('/<channel_name>/debug')
def debug(channel_name):
    """Debug endpoint to inspect current state"""
    channel_data = get_channel_data(channel_name)
    
    return jsonify({
        'channel': channel_name,
        'queue': [user['username'] for user in list(channel_data['chatters_queue'])],
        'collected_users': list(channel_data['collected_users']),
        'displayed_users': list(channel_data['displayed_users']),
        'queue_length': len(channel_data['chatters_queue']),
        'collected_count': len(channel_data['collected_users']),
        'displayed_count': len(channel_data['displayed_users']),
        'irc_status': {
            'connected': channel_data['twitch_irc'].connected if channel_data['twitch_irc'] else False,
            'chatters_found': len(channel_data['twitch_irc'].chatters) if channel_data['twitch_irc'] else 0,
            'first_messages_count': len(channel_data['twitch_irc'].first_messages) if channel_data['twitch_irc'] else 0
        }
    })

@app.route('/<channel_name>/reset_users')
def reset_users(channel_name):
    """Reset all user lists and feed"""
    channel_data = get_channel_data(channel_name)
    
    # Alle Listen zurücksetzen
    channel_data['chatters_queue'].clear()
    channel_data['displayed_users'].clear()
    channel_data['collected_users'].clear()
    
    # IRC erste Nachrichten auch zurücksetzen
    if channel_data['twitch_irc']:
        channel_data['twitch_irc'].first_messages.clear()
    
    print(f"🔄 User-Listen wurden zurückgesetzt für #{channel_name}")
    
    # Frontend über Reset informieren
    socketio.emit('users_reset', {
        'message': f'User-Listen wurden zurückgesetzt für #{channel_name}',
        'channel': channel_name
    })
    
    return jsonify({
        'status': 'reset', 
        'message': f'Alle User-Listen wurden zurückgesetzt für #{channel_name} (inkl. erste Nachrichten)',
        'channel': channel_name,
        'cleared': {
            'queue': 0,
            'displayed': 0,
            'collected': 0
        }
    })

@app.route('/<channel_name>/test_chat')
def test_chat(channel_name):
    """Test endpoint - only works with real IRC connection"""
    channel_data = get_channel_data(channel_name)
    
    if channel_data['twitch_irc'] and channel_data['twitch_irc'].connected:
        first_messages_count = len(channel_data['twitch_irc'].first_messages)
        return jsonify({
            'status': 'info',
            'message': f'IRC verbunden für #{channel_name}. {first_messages_count} erste Nachrichten erfasst.',
            'channel': channel_name,
            'irc_connected': True,
            'first_messages_count': first_messages_count
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Keine IRC-Verbindung für #{channel_name}. Starte zuerst die Sammlung mit echten Twitch-Credentials.',
            'channel': channel_name,
            'irc_connected': False
        })

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("5MinutenGang Twitch Chatter Display gestartet!")
    print("Multi-Channel Support aktiviert!")
    print("Verwende: http://localhost:5000/<channel_name> um einen spezifischen Channel zu öffnen")
    print("Beispiel: http://localhost:5000/mychannel")
    print("Verwende: http://localhost:5000/<channel_name>/start_collection um die Sammlung zu starten")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
