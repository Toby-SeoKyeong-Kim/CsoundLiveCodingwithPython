import socket
import threading

def send_messages(sock):

    while True:
        lines = []
        while True:
            message = input()
            lines.append(message)
            if message.endswith(';'):
                break
        fullMessage = "\n".join(lines)
        fullMessage = fullMessage[:-1]
        sock.sendall(fullMessage.encode())
        if fullMessage.lower() == 'quit':
            print("Client stopping.")
            break

def receive_messages(sock):

    while True:
        data = sock.recv(1024)
        if not data:
            print("Server disconnected.")
            break
        print(f"Received from server: \n{data.decode()}")

def main():
    host = '127.0.0.1'
    port = 65432
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        print("Connected to server.")

        # Start thread for sending messages
        thread_send = threading.Thread(target=send_messages, args=(client_socket,))
        thread_send.start()

        # Start thread for receiving messages
        thread_receive = threading.Thread(target=receive_messages, args=(client_socket,))
        thread_receive.start()

        # Wait for the send thread to finish
        thread_send.join()
        # If send thread is done, the client wants to stop. Close receive thread.
        client_socket.close()

if __name__ == '__main__':
    main()