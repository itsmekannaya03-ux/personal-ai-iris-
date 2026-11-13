# Notepad Application

class Notepad:
    def __init__(self):
        self.text = ""

    def open_file(self, filename):
        try:
            with open(filename, 'r') as file:
                self.text = file.read()
                print(f"File '{filename}' opened successfully.")
        except FileNotFoundError:
            print(f"File '{filename}' not found.")

    def save_file(self, filename):
        with open(filename, 'w') as file:
            file.write(self.text)
            print(f"File '{filename}' saved successfully.")

    def display_text(self):
        print(self.text)

    def clear_text(self):
        self.text = ""
        print("Text cleared.")

def main():
    notepad = Notepad()
    
    while True:
        print("\nNotepad Menu:")
        print("1. Open file")
        print("2. Save file")
        print("3. Display text")
        print("4. Clear text")
        print("5. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == '1':
            filename = input("Enter file name: ")
            notepad.open_file(filename)
        elif choice == '2':
            filename = input("Enter file name: ")
            notepad.save_file(filename)
        elif choice == '3':
            notepad.display_text()
        elif choice == '4':
            notepad.clear_text()
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()