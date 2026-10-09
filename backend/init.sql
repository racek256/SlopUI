CREATE TABLE IF NOT EXISTS users (
	id INTEGER PRIMARY KEY,
	discord_id INTEGER,
	username TEXT NOT NULL UNIQUE,
	password_hash TEXT,
	last_model TEXT
);
CREATE TABLE IF NOT EXISTS chats (
	id INTEGER PRIMARY KEY,
	user_id INTEGER NOT NULL,
	name TEXT,
	last_model TEXT,
	last_used TEXT DEFAULT 'unknown',
	pinned INTEGER NOT NULL DEFAULT 0,
	current_message_id INTEGER,
	FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS messages ( 
	id INTEGER PRIMARY KEY, 
	chat_id INTEGER NOT NULL,
	content TEXT, 
	chain TEXT,
	role TEXT NOT NULL,
	parent_message_id INTEGER,
	files TEXT,
	FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
);

create table if not exists memories (
	id INTEGER PRIMARY KEY,
	created_time TEXT DEFAULT NULL,
	content TEXT NOT NULL,
	embed BLOB NOT NULL
);
