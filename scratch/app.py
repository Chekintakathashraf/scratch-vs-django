import socket
import sqlite3
from urllib.parse import parse_qs

# Database connection function
def get_db():
    return sqlite3.connect('database.db')

# Simple session management using a dictionary
sessions = {}

# User login validation
def validate_user(username, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user[1] == password:
        return user[0]  # return user id if password matches
    return None

# User authentication routes
def signup(username, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def login(username, password):
    user_id = validate_user(username, password)
    if user_id:
        session_id = str(user_id)  # Using user ID as session token
        sessions[session_id] = user_id
        return session_id
    return None

def logout(session_id):
    if session_id in sessions:
        del sessions[session_id]

# Fetching models
def get_schools():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schools")
    schools = cursor.fetchall()
    conn.close()
    return schools

def get_teachers(school_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teachers WHERE school_id=?", (school_id,))
    teachers = cursor.fetchall()
    conn.close()
    return teachers

def get_students(school_id, teacher_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE school_id=? AND teacher_id=?", (school_id, teacher_id))
    students = cursor.fetchall()
    conn.close()
    return students

# Parsing request manually (simplified)
def parse_request(request):
    """ Parse the raw HTTP request string into method and body (if any) """
    lines = request.splitlines()
    method, path, _ = lines[0].split(' ')

    # If it's a POST request, the body might be in the lines after the headers
    body = None
    if method == "POST":
        content_length = next((line for line in lines if line.startswith("Content-Length")), None)
        if content_length:
            length = int(content_length.split(":")[1].strip())
            body = request[-length:]
    
    return method, path, body

# Handle routes and views
def handle_request(request):
    method, path, body = parse_request(request)

    # Handle POST requests
    if method == "POST":
        form = parse_qs(body) if body else {}
        action = form.get("action", [None])[0]
        
        if action == "signup":
            username = form.get("username", [""])[0]
            password = form.get("password", [""])[0]
            signup(username, password)
            return "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nUser registered successfully!"
        
        elif action == "login":
            username = form.get("username", [""])[0]
            password = form.get("password", [""])[0]
            session_id = login(username, password)
            if session_id:
                return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nWelcome, {username}!"
            else:
                return "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nInvalid login credentials!"
    
    # Handle GET requests
    elif method == "GET":
        if path == "/login":
            try:
                return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + open("templates/login.html", "r").read()
            except FileNotFoundError:
                return "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nLogin template not found."
        elif path == "/signup":
            try:
                return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + open("templates/signup.html", "r").read()
            except FileNotFoundError:
                return "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nSignup template not found."
        elif path == "/":
            try:
                return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + open("templates/index.html", "r").read()
            except FileNotFoundError:
                return "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nHome page template not found."
        else:
            return "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\n404 Not Found"

    return "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nInvalid Request Method"

# Running the server
def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8000))
    server_socket.listen(5)
    print("Server running on http://localhost:8000")
    
    while True:
        client_socket, client_address = server_socket.accept()
        request = client_socket.recv(1024).decode('utf-8')
        print(f"Received request: {request}")  # Debugging line to see the raw request
        response = handle_request(request)
        
        if response is None:  # Ensure a valid response is always returned
            response = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nServer Error"
        
        client_socket.sendall(response.encode('utf-8'))
        client_socket.close()

# Start the server
run_server()
