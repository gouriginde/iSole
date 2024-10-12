import firebase_admin
from firebase_admin import auth, credentials, firestore, initialize_app
from datetime import datetime

cred = credentials.Certificate("i-sole-111bc-firebase-adminsdk-f1xl8-c99396fd2b.json")
firebase_admin.initialize_app(cred)

db=firestore.client()

def initialize_user_thread_counter(username): # need to call at creation of each account
    # Reference to the user's thread counter document
    counter_ref = db.collection('users').document(username).collection('feedback').document('thread_counter')
    
    # Set the initial value of the counter
    counter_ref.set({'last_thread_number': 0})


@firestore.transactional
def increment_counter(transaction, counter_ref):
    snapshot = counter_ref.get(transaction=transaction)
    last_number = snapshot.get('last_thread_number')

    if last_number is None:
        last_number = 0
        transaction.set(counter_ref, {'last_thread_number': last_number})

    new_number = last_number + 1
    transaction.update(counter_ref, {'last_thread_number': new_number})
    return new_number

def start_new_thread_with_message(username, message):
    counter_ref = db.collection('users').document(username).collection('feedback').document('thread_counter')
    new_thread_number = increment_counter(db.transaction(), counter_ref)

    new_thread = "thread" + str(new_thread_number)
    now = datetime.now()
    date_str = now.strftime("%d %B %Y")
    time_str = now.strftime("%I:%M %p")

    message_data = {
        'message': message,
        'date': date_str,
        'time': time_str,
        'sender': username
    }

    doc_ref = db.collection('users').document(username).collection('feedback').document(new_thread)
    doc_ref.set({'messages': [message_data]})




def add_message_to_conversation(username, index, message):
    desired_thread = "thread" + str(index)
    # Get the current datetime
    now = datetime.now()
    # Format date and time (12-hour clock with AM/PM)
    date_str = now.strftime("%d %B %Y")
    time_str = now.strftime("%I:%M %p")  # Format for 12-hour clock with AM/PM

    # Prepare the message data with separate date and time
    message_data = {
        'message': message,
        'date': date_str,
        'time': time_str,
        'sender': username
    }

    # Get a reference to the document
    doc_ref = db.collection('users').document(username).collection('feedback').document(desired_thread)

    # Use set with merge=True to update if exists or create if not exists
    doc_ref.set({'messages': firestore.ArrayUnion([message_data])}, merge=True)

def get_all_conversations(username):
    # Array to hold the 0th message from each thread
    first_messages = []

    # Reference to the user's feedback collection
    feedback_ref = db.collection('users').document(username).collection('feedback')

    # Get all documents (threads) in the feedback collection
    threads = feedback_ref.stream()

    for thread in threads:
        # Get the thread data
        thread_data = thread.to_dict()

        # Check if 'messages' field exists and has at least one message
        if 'messages' in thread_data and thread_data['messages']:
            # Append the 0th message to the array
            first_messages.append(thread_data['messages'][0])

    return first_messages

def get_one_conversation(username, index):
    # Construct the thread ID from the index
    desired_thread = "thread" + str(index)

    # Reference to the specific document (thread) in the user's feedback collection
    thread_ref = db.collection('users').document(username).collection('feedback').document(desired_thread)

    # Attempt to get the document
    thread_doc = thread_ref.get()

    # Check if the document exists and return the 'messages' array if it does
    if thread_doc.exists:
        thread_data = thread_doc.to_dict()
        return thread_data.get('messages', [])  # Return the messages array or an empty array if not found

    # Return None or an empty array if the document does not exist
    return None


# initialize_user_thread_counter('Zeeshan')

# start_new_thread_with_message('Zeeshan', 'wassup')


add_message_to_conversation("Zeeshan", 1, "Hello Mr. Hamdaan Younus, we are calling to inform you that your credit card details from RBC Bank, Alberta have been compromised")

# # print(get_all_conversations("Zeeshan"))
# # # print()
# # # print(get_one_conversation("Zeeshan", 2))