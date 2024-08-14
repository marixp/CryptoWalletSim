import os
import subprocess
import time

# run server in subprocess
print("Starting server...")
server_process = subprocess.Popen(['python', 'server.py'])

# wait for server to run
time.sleep(1)

# run client in subprocess
print("Starting client...")
client_process = subprocess.Popen(['python', 'client.py'])

def main():
    #wait for both processes to finish

    client_process.wait()
    server_process.kill()

if __name__ == "__main__":
    main()
