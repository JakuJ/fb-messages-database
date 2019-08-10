import sqlite3
import json
import os

DB_NAME = './database.db'
DB_SCRIPT_PATH = './create_tables.sql'

DATA_DIR = './messages'
TARGET_DIRS = [os.path.join(DATA_DIR, folder) for folder in ['inbox', 'archived_threads', 'message_requests']]

if __name__ == "__main__":
    # * remove DB if already exists, it's fast anyway
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        # * create tables
        with open(DB_SCRIPT_PATH, 'r') as f:
            conn.executescript(f.read())

        # * load data
        for top_level in TARGET_DIRS:
            for directory in os.listdir(top_level):
                messages_file = os.path.join(top_level, directory, 'message_1.json')
                if os.path.exists(messages_file):
                    with open(messages_file, "r") as f:
                        convo = json.loads(f.read().encode('raw_unicode_escape').decode('utf-8'))

                        # * insert data into Conversations
                        title = convo['title'].encode('raw_unicode_escape').decode('utf-8')
                        conn.execute('INSERT INTO Conversations (Title) VALUES (?);', [title])
                        convo_id = c.execute('SELECT ID from Conversations where Title = ?;', [title]).fetchone()[0]

                        for obj in convo['participants']:
                            name = obj['name'].encode('raw_unicode_escape').decode('utf-8')

                            # * insert data into Users
                            already_in = c.execute('SELECT Name from Users where Name = ?;', [name]).fetchone()
                            if not already_in:
                                conn.execute('INSERT INTO USERS (Name) VALUES (?);', [name])

                            # * insert data into Participants
                            conn.execute('INSERT INTO Participants (Conversation_ID, User_Name) VALUES (?, ?);', [convo_id, name])

                        # * insert messages
                        for message in convo['messages']:
                            if message['type'] == "Generic" and 'content' in message:
                                name = message['sender_name'].encode('raw_unicode_escape').decode('utf-8')
                                content = message['content'].encode('raw_unicode_escape').decode('utf-8')
                                try:
                                    conn.execute('INSERT INTO Messages (Conversation_Id, User_Name, Timestamp, Content) VALUES (?, ?, ?, ?)', [
                                        convo_id, name, message['timestamp_ms'], content
                                    ])
                                except Exception as e:
                                    # * sender must have left the conversation
                                    conn.execute('INSERT INTO USERS (Name) VALUES (?);', [name])
                                    # * try again
                                    conn.execute('INSERT INTO Messages (Conversation_Id, User_Name, Timestamp, Content) VALUES (?, ?, ?, ?)', [
                                        convo_id, name, message['timestamp_ms'], content
                                    ])
    
    print("Database created successfully")
