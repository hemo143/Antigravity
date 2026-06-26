"""
Start Django + ngrok tunnel for Apex Events website.
Run: python start_ngrok.py
"""
import subprocess
import time
import os

NGROK_TOKEN = "38d73ut7yQQpOFuOqiGlpPCDRYf_77xhzWJ2AP2CuC5a2hvkj"

def main():
    print("\n ==========================================")
    print("   Apex Events - Starting Live Server")
    print(" ==========================================\n")

    print("[1/3] Checking database...")
    os.system("venv\\Scripts\\python.exe manage.py migrate --run-syncdb -v 0")

    print("[2/3] Starting Django server...")
    django = subprocess.Popen(
        ["venv\\Scripts\\python.exe", "manage.py", "runserver", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)

    print("[3/3] Creating public URL with ngrok...\n")
    try:
        from pyngrok import ngrok
        ngrok.set_auth_token(NGROK_TOKEN)
        tunnel = ngrok.connect(8000, "http")
        url = tunnel.public_url.replace("http://", "https://")

        print(" ==========================================")
        print("   YOUR PUBLIC URL:")
        print(f"   {url}/en/")
        print(" ==========================================")
        print("\n Share this link with your team.")
        print(" No IP needed - opens directly!")
        print(" Press Ctrl+C to stop.\n")

        django.wait()

    except KeyboardInterrupt:
        print("\n Shutting down...")
        ngrok.kill()
        django.terminate()
    except Exception as e:
        print(f" Error: {e}")
        django.terminate()

if __name__ == "__main__":
    main()
