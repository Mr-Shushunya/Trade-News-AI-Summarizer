import requests
import time

def send_message(message: str, sender_id: str, receiver_id: str, int_array: list[int] = None, server_ip: str = "http://192.168.1.100:8000"):
    url = f"{server_ip}/receive"
    data = {
        "text": message,
        "sender_id": sender_id,
        "receiver_id": receiver_id
    }
    if int_array is not None:
        data["int_array"] = int_array
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        print(f"Server response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

def check_messages(client_id: str, server_ip: str = "http://192.168.1.100:8000"):
    url = f"{server_ip}/messages/{client_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        messages = response.json()
        if messages:
            print(f"New messages for {client_id}:")
            for msg in messages:
                array_info = f" | Array: {msg['int_array']}" if msg.get('int_array') else ""
                print(f"From: {msg['sender_id']} | Text: {msg['text']}{array_info}")
        else:
            print(f"No new messages for {client_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error checking messages: {e}")

if __name__ == "__main__":
    client_id = "client3"  # Фиксированный ID клиента
    server_ip = input("Enter server IP (e.g., http://192.168.1.100:8000): ") or "http://192.168.1.100:8000"
    
    print(f"Client ID: {client_id}")
    print("Commands: 'send' to send a message, 'check' to check messages, 'exit' to quit.")
    
    while True:
        command = input("Enter command (send/check/exit): ").lower()
        if command == 'exit':
            break
        elif command == 'send':
            message = input("Enter message: ")
            receiver_id = input("Enter receiver ID (e.g., client1 or client2): ")
            array_input = input("Enter array of integers (e.g., 1,2,3): ")  # Обязательный ввод массива для client3
            try:
                int_array = [int(x) for x in array_input.split(',')]
            except ValueError:
                print("Invalid array format. Please use comma-separated integers (e.g., 1,2,3).")
                continue
            send_message(message, client_id, receiver_id, int_array, server_ip)

        elif command == 'check':
            check_messages(client_id, server_ip)
        else:
            print("Unknown command. Use 'send', 'check', or 'exit'.")
