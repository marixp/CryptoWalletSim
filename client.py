import pickle
import socket
from tabulate import tabulate

# Initialize client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 12345)

# Send and receive data from server
def send_receive(data):
    client_socket.sendto(pickle.dumps(data), server_address)
    response, _ = client_socket.recvfrom(1024)
    return pickle.loads(response)

# Function for user authentication
def authenticate(username, password):
    data = {'type': 'auth', 'username': username, 'password': password}
    return send_receive(data)

# Function to make a transaction
def make_transaction(username, amount, payee1, amt_rec_payee1, 
                     payee2=None, amt_rec_payee2=0.0):
    data = {'type': 'tx', 'tx': {'payer': username, 'amount': amount, 'payee1': payee1, 
             'amt_rec_payee1': amt_rec_payee1}}
    #check if payee2 is provided, if so add to transaction data
    if payee2 and amt_rec_payee2:
        data['tx']['payee2'] = payee2
        data['tx']['amt_rec_payee2'] = amt_rec_payee2
    return send_receive(data)

# Fetch transaction history for current user
def fetch_transactions(username):
    data = {'type': 'fetch_tx', 'username': username}
    response = send_receive(data)  
    return response

# Display user info and transactions as tables
def display_user_info(username, balance, transactions):
    user_info = [{'User ID': username, 'Balance': balance}]
    print("\nUser Information:")
    print(tabulate(user_info, headers="keys", tablefmt="simple_grid"))
  # If there are transactions in the user's list, show them
    if transactions:
        display_transactions(transactions)
    else:
        print(f"\nNo transaction history yet for user {username}...")

# Display transaction history as a table
def display_transactions(transactions):
    headers = ["Payer", "Status", "TX ID", "Amount", "Payee1", 
               "Payee1 Received", "Payee2", "Payee2 Received"]
    table_data = []
    for tx in transactions:
        status = "confirmed" if tx['status'] == 'confirmed' else "rejected"
        table_data.append([tx['payer'], status, tx['id'], tx['amount'], 
                          tx['payee1'], tx['amt_rec_payee1'], 
                          tx.get('payee2'), tx.get('amt_rec_payee2')])

    print("\nTransaction History:")
    print(tabulate(table_data, headers=headers, tablefmt="mixed_grid"))

# Main client loop
def main():
  # User welcome & credential entering
  print("\nWelcome to the Bitcoin Wallet!")
  while True:
      username = input("\nEnter your username: ")
      password = input("Enter your password: ")
    
    # Authentication request to server
      auth_response = authenticate(username, password)
    # If user authenticated, display user info and transactions
      if auth_response['authenticated']:
        print(f"Your current balance is: {auth_response['balance']} BTC")
        transactions = auth_response['transactions']
        user_txs = fetch_transactions(username)
        display_user_info(username, auth_response['balance'], user_txs['transactions'])
        break
      # If user NOT authenticated, give 2 options: retry or exit
      else:
        while True:
            print("\nOptions: ")
            print("1. Retry login")
            print("2. Quit program")
            option = input("Select an option from above: ")
            if option == '1':
                print("\n***HINT*** \nuser = A, B, C, or D \npass = A, B, C, or D")
                break
            elif option == '2':
                print("Exiting the program. Goodbye!")
                return
            else:
                print("ERROR: Invalid choice. Try again.")
  # Main menu for users
  while True:
            print("\nMain Menu:")
            print("1. Make a transaction")
            print("2. List transaction history")
            print("3. Login as another user")
            print("4. Quit program")
            choice = input("Enter your choice: ")
		
          # User chooses to make a transaction
            if choice == '1':
              # Ask user for transaction details
              while True:
                try:		
                  amount = float(input("\nEnter amount to transfer: "))
                  break
							# Handle invalid amount entries
                except ValueError:
                  print("ERROR: Invalid input. Please enter a numerical amount.")
							# Get & show list of available payees
              available_payees= [user['username'] for user in auth_response['users'] 
                                  if user['username'] != username]
              print("\nAvailable Payees:")
              for index, payee in enumerate(available_payees, 1):
                  print(f"{index}. {payee}")
            # Let user choose payee(s)
              while True:
                  try:
                      payee1_index = int(input("\nSelect Payee1: ")) #- 1
                      if 1<= payee1_index <= len(available_payees):
                          payee1 = available_payees[payee1_index - 1]
                          break
                    # Handle invalid payee1 user choice
                      else:
                          print("ERROR: Invalid input. Select a valid payee.")
                  except ValueError:
                      print("ERROR: Invalid input. Enter a valid payee number.")
            # User enters amount to transfer to payee1
              while True:
                  try:
                      amt_rec_payee1 = float(input(
                           f"Enter amount to send to user {payee1}: "))
                      if 0 <= amt_rec_payee1 <= amount:
                          break
                    # Handle invalid payee1 transfer amount
                      else:
                          print("ERROR: Invalid amount. Please enter a valid amount.")
                          print(f"Maximum amount possible: {amount} BTC")
                  except ValueError:
                      print("ERROR: Invalid input. Please enter a numerical amount.")
            # Calculate amount to transfer to payee2
              amt_rec_payee2 = amount - amt_rec_payee1
            # Check if there is amount for payee2, if so ask for payee2 choice
              if amt_rec_payee2 > 0:
                  while True:
                      try:
                          payee2_index = int(input("Select Payee2: "))
                          if 1 <= payee2_index <= len(available_payees):
                              payee2 = available_payees[payee2_index - 1]
                              break
                        # Handle invalid payee2 user choice
                          else:
                              print("ERROR: Invalid choice. Select a valid payee.")
                      except ValueError:
                          print("ERROR: Invalid input. Enter valid payee number.")
            # If no payee2, return nothing
              else:
                  payee2 = None
                  amt_rec_payee2 = 0.0
            # Store tx as temporary
              temp_tx = {'payer': username, 'amount': amount, 'payee1': payee1, 
                         'amt_rec_payee1': amt_rec_payee1,
                         'status': 'temporary'}
              if amt_rec_payee2 > 0:
                  temp_tx['payee2'] = payee2
                  temp_tx['amt_rec_payee2'] = amt_rec_payee2
              transactions.append(temp_tx)
            # Make transaction request to server
              tx_response = make_transaction(username, amount, payee1, amt_rec_payee1, 
                                             payee2, amt_rec_payee2)
            # Update transaction status based on server response
            # If transaction is confirmed, display new balance
              if tx_response['confirmed']:
                    print(f"Your new balance is: {tx_response['balance']} BTC")
                    temp_tx['status'] = 'confirmed'
            # If transaction is rejected, display reason & current balance
              else:
                    print("Insufficient balance.")
                    print(f"Your current balance is: {tx_response['balance']} BTC")
                    temp_tx['status'] = 'rejected'
          # User chooses to view transaction history
            elif choice == '2':
              # Fetch transaction history for current user, then display as table
                tx_history = fetch_transactions(username)
                display_user_info(username, tx_history['balance'], 
                     tx_history['transactions'])
		
          # User chooses to login as another user
            elif choice == '3':
                print("\nReturning to login screen...")
                return main()
		
          # User chooses to quit program
            elif choice == '4':
                print("\nThank you for using the Bitcoin Wallet! Goodbye.")
                return
		
          # User enters invalid menu choice
            else:
                print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()