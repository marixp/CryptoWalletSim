import pickle
import socket
#from socket import *

# Initialize server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 12345)
server_socket.bind(server_address)

# Initialize lists for users and transactions
users = [{'username': 'A', 'password': 'A', 'balance': 10, 'txs': []},
         {'username': 'B', 'password': 'B', 'balance': 10, 'txs': []},
         {'username': 'C', 'password': 'C', 'balance': 10, 'txs': []},
         {'username': 'D', 'password': 'D', 'balance': 10, 'txs': []}]
transactions = []

# Handle user authentication request from client
def authenticate_user(username, password):
    print(f"\nReceived authentication request from user {username}...")
    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    return None

# Function to handle transaction process
def process_transaction(tx):
    payer = tx['payer']
    amount = tx['amount']
    payee1 = tx['payee1']
    amt_rec_payee1 = tx['amt_rec_payee1']
    payee2 = tx.get('payee2')
    amt_rec_payee2 = tx.get('amt_rec_payee2')
    print(f"\nReceived transaction request from user {payer}...")
    user = next((user for user in users if user['username'] == payer), None)
    if user['balance'] >= amount:
        user['balance'] -= amount
        payee1_user = next((user for user in users if user['username'] == payee1), None)
        payee1_user['balance'] += amt_rec_payee1
        if payee2:
            payee2_user = next((user for user in users if user['username'] == payee2),
                                None)
            payee2_user['balance'] += amt_rec_payee2
        transactions.append(tx)
        tx['status'] = 'confirmed'
        return True, user['balance']
    else:
        transactions.append(tx)
        tx['status'] = 'rejected'
        return False, user['balance']

# Function to find the highest transaction id for a user
def find_highest_tx_id(user):
    user_txs = [tx for tx in transactions if tx['payer'] == user['username']]
    if user_txs:
        return max(user_txs, key=lambda x: x['id'])['id'] + 1
    else:
        if user['username'] == 'A':
            return 100
        elif user['username'] == 'B':
            return 200
        elif user['username'] == 'C':
            return 300
        elif user['username'] == 'D':
            return 400


# Main server loop
print("Server is running...")
while True:
    data, client_address = server_socket.recvfrom(1024)
    message = pickle.loads(data)
    
    # Authentication request
    if message['type'] == 'auth':
        username = message['username']
        password = message['password']
        user = authenticate_user(username, password)
        if user:
            response = {'authenticated': True, 'balance': user['balance'], 
                   'transactions': user['txs'], 'users': users}
            print(f"\nUser {username} is authenticated.")
        else:
            response = {'authenticated': False}
            print(f"\nAuthentication failed for user {username}")
        server_socket.sendto(pickle.dumps(response), client_address)
    
    # Make transaction request
    elif message['type'] == 'tx':
        tx = message['tx']
        tx['id'] = find_highest_tx_id(user)
        success, new_balance= process_transaction(tx)
        if success:
            response = {'confirmed': True, 'balance': new_balance}
            print(f"\nTransaction CONFIRMED for user {tx['payer']}...")
            print(f"{tx['amount']} BTC successfully sent!")
            print(f"-> {tx['amt_rec_payee1']} BTC sent to user {tx['payee1']}")
            if tx.get('payee2'):
                print(f"-> {tx['amt_rec_payee2']} BTC sent to user {tx['payee2']}")
            else:
                print("No payee2")
            tx['status'] = 'confirmed'
        else:
            response = {'confirmed': False, 'balance': new_balance}
            print(f"\nTransaction REJECTED for user: {tx['payer']}")
            tx['status'] = 'rejected'
        server_socket.sendto(pickle.dumps(response), client_address)

    # Transaction history request
    elif message['type'] == 'fetch_tx':
        username = message['username']
        user_txs = [tx for tx in transactions if tx['payer'] == username 
                    or tx['payee1'] == username or tx.get('payee2') == username]
        response = {'balance': user['balance'], 'transactions': user_txs}
        print(f"\nFetching transaction history for user {username}...")
        server_socket.sendto(pickle.dumps(response), client_address)
