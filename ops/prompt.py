import os


class Prompt:
    def __init__(self):
        # Get initial URLs to scrape
        initial_urls = input("Enter the initial URLs to scrape, separated by commas:\n- ").split(',')
        self.initial_urls = [url.strip() for url in initial_urls if url.strip()]

        # Check if valid URLs were provided
        if not self.initial_urls:
            print("No valid URLs provided. Exiting.")
            return

        # Ask the user to select an option for what to scrape
        try:
            self.user_selected = int(input(
                "Which option would you like:\n"
                "1. All\n2. Photos\n3. Videos\n4. Page Structs\n5. Photos and Videos\n- "
            ))
        except ValueError:
            print("Invalid selection. Please enter a number from 1 to 5.")
            return

        # Define base directory to store pages
        base_dir = input("What would you like to name the main output folder?\n- ")

        # Create directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        self.base_dir = base_dir

        print("Setup complete.")

# To create an instance of the Prompt class, uncomment the following line:
# prompt_instance = Prompt()
