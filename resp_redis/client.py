import socket
import threading
import time

HOST = "127.0.0.1"   # Change to your server
PORT = 6379          # Change to your port (Redis default = 6379)
NUM_CONNECTIONS = 100

connections = []


def worker(conn_id):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        connections.append(s)

        print(f"[+] Connection {conn_id} established")

        while True:
            # Send Redis PING command (RESP format)
            ping_cmd = b"*1\r\n$4\r\nPING\r\n"

            s.sendall(ping_cmd)

            try:
                response = s.recv(1024)
                print(f"[{conn_id}] Response: {response}")
            except:
                print(f"[{conn_id}] No response")

            time.sleep(5)  # Adjust frequency

    except Exception as e:
        print(f"[!] Connection {conn_id} failed: {e}")


threads = []

for i in range(NUM_CONNECTIONS):
    t = threading.Thread(target=worker, args=(i,))
    t.start()
    threads.append(t)

# Keep main thread alive
for t in threads:
    t.join()