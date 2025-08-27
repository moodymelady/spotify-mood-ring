from utils import get_spotify_client

def main():
    sp = get_spotify_client()
    user = sp.current_user()
    print("Logged in as:", user["display_name"])

if __name__ == "__main__":
    main()

