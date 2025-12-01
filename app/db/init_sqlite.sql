PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS topic (
    topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS vocabulary (
    word_id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    synonym TEXT,
    antonym TEXT,
    part_of_speech TEXT,
    word_level TEXT,
    topic_id INTEGER,
    FOREIGN KEY(topic_id) REFERENCES topic(topic_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    current_level TEXT,
    start_date DATE,
    target_level TEXT
);

CREATE TABLE IF NOT EXISTS exercise (
    exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem TEXT NOT NULL,
    media_url TEXT,
    type TEXT NOT NULL,
    exercise_level TEXT,
    rule_id INTEGER,
    topic_id INTEGER,
    FOREIGN KEY(topic_id) REFERENCES topic(topic_id) ON DELETE SET NULL,
    FOREIGN KEY(rule_id) REFERENCES grammar_rule(rule_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS grammar_rule (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT, 
    example TEXT,
    grammar_level TEXT,
    topic_id INTEGER,
    FOREIGN KEY(topic_id) REFERENCES topic(topic_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS definition (
  definition_id INTEGER PRIMARY KEY AUTOINCREMENT,
  word_id INTEGER,
  ru_translation TEXT,
  def TEXT,
  example TEXT,
  FOREIGN KEY(word_id) REFERENCES vocabulary(word_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exercise_answer (
  answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  exercise_id INTEGER,
  answer_text TEXT NOT NULL,
  part_number INTEGER DEFAULT 1,
  FOREIGN KEY(exercise_id) REFERENCES exercise(exercise_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_exercise_answer (
  user_answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  exercise_id INTEGER,
  answer_text TEXT NOT NULL,
  part_number INTEGER DEFAULT 1,
  is_complete BOOLEAN DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY(exercise_id) REFERENCES exercise(exercise_id) ON DELETE CASCADE
);

-- DELETE FROM table_name;
-- VACUUM;

-- -- DELETE FROM table_name;
-- -- DELETE FROM sqlite_sequence WHERE name='table_name';
-- VACUUM;


CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    current_level TEXT,
    start_date DATE,
    target_level TEXT,
    hashed_password TEXT NOT NULL  -- ← новое поле
);


CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    current_level TEXT,
    start_date DATE,
    target_level TEXT,
    hashed_password TEXT NOT NULL,
    admin_token_hash TEXT  -- ← может быть NULL (для студентов)
);
