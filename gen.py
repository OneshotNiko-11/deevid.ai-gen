import requests
import random
import string
import threading
import time
import os
import re
from colorama import init, Fore

init()

def load_proxies():
    try:
        with open("proxies.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
            if proxies:
                print(Fore.YELLOW + f"[*] loaded {len(proxies)} proxies")
            return proxies
    except:
        return []

def get_proxy(proxies, index):
    if not proxies:
        return None
    return proxies[index % len(proxies)]

def setup_session_proxy(session, proxy_str, use_proxies):
    if use_proxies and proxy_str:
        try:
            session.proxies.update({
                'http': f'socks5://{proxy_str}',
                'https': f'socks5://{proxy_str}'
            })
        except:
            pass
    return session

def create_temp_inbox(session):
    try:
        url = 'https://api.internal.temp-mail.io/api/v3/email/new'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        payload = {"min_name_length": 10, "max_name_length": 10}
        response = session.post(url, headers=headers, json=payload, timeout=15)

        if response.status_code != 200:
            return None

        data = response.json()
        email = data.get('email')
        token = data.get('token')

        if not email or not token:
            return None

        return {'address': email, 'token': token}
    except:
        return None

def check_inbox_with_retry(session, token, email):
    try:
        url = f'https://api.internal.temp-mail.io/api/v3/email/{email}/messages'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

        print(Fore.YELLOW + "[*] waiting for verification email...")

        for attempt in range(10):
            try:
                response = session.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    messages = response.json()

                    if messages:
                        for msg in messages:
                            subject = str(msg.get('subject', '')).lower()

                            if 'confirm' in subject and 'deevid' in str(msg).lower():
                                print(Fore.GREEN + f"[+] found deevid email!")

                                body_text = msg.get('body_text', '')

                                if body_text:
                                    lines = body_text.split('\n')
                                    for line in lines:
                                        if 'sp.deevid.ai/auth/v1/verify' in line:
                                            start = line.find('(')
                                            end = line.find(')', start)
                                            if start != -1 and end != -1:
                                                url_part = line[start+1:end].strip()
                                                url_end = min(
                                                    url_part.find(' ') if url_part.find(' ') != -1 else len(url_part),
                                                    url_part.find('\n') if url_part.find('\n') != -1 else len(url_part)
                                                )
                                                return url_part[:url_end]

                                body_html = msg.get('body_html', '')
                                if body_html:
                                    match = re.search(r'href="(https://sp\.deevid\.ai/auth/v1/verify\?[^"]+)"', body_html)
                                    if match:
                                        return match.group(1)

                print(Fore.YELLOW + f"[*] check {attempt + 1}/10 - no email yet, retrying in 5s...")
                time.sleep(5)

            except Exception as e:
                print(Fore.RED + f"[!] check error: {e}")
                time.sleep(5)

        print(Fore.RED + "[-] timeout waiting for verification email")
        return None

    except Exception as e:
        print(Fore.RED + f"[!] inbox check error: {e}")
        return None

def generate_password():
    uppercase = random.choice(string.ascii_uppercase)
    lowercase = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
    number = random.choice(string.digits)
    symbol = random.choice('!@#$%^&*')

    password = uppercase + lowercase + number + symbol
    password_list = list(password)
    random.shuffle(password_list)
    return ''.join(password_list)

def create_account(proxies, target_accounts, accounts_created, lock, running, proxy_index_counter, use_proxies):
    while running[0]:
        with lock:
            if accounts_created[0] >= target_accounts:
                break
            proxy_index = proxy_index_counter[0]
            proxy_index_counter[0] += 1

        proxy = get_proxy(proxies, proxy_index) if use_proxies else None
        session = requests.Session()
        session = setup_session_proxy(session, proxy, use_proxies)

        try:
            temp_mail = create_temp_inbox(session)
            if not temp_mail or 'address' not in temp_mail or 'token' not in temp_mail:
                continue

            email = temp_mail['address']
            token = temp_mail['token']

            print(Fore.GREEN + "[*] (temp email success) " + Fore.LIGHTMAGENTA_EX + f"({email})")

            password = generate_password()

            url = 'https://sp.deevid.ai/auth/v1/signup?redirect_to=https%3A%2F%2Fdeevid.ai'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': 'https://deevid.ai',
                'Referer': 'https://deevid.ai/',
                # had to add these headers otherwise it would return 401, expires in 4 years lol
                'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzM0OTY5NjAwLAogICJleHAiOiAxODkyNzM2MDAwCn0.4NnK23LGYvKPGuKI5rwQn2KbLMzzdE4jXpHwbGCqPqY',
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzM0OTY5NjAwLAogICJleHAiOiAxODkyNzM2MDAwCn0.4NnK23LGYvKPGuKI5rwQn2KbLMzzdE4jXpHwbGCqPqY'
            }

            payload = {
                "email": email,
                "password": password,
                "data": {},
                "gotrue_meta_security": {},
                "code_challenge": None,
                "code_challenge_method": None
            }

            response = session.post(url, headers=headers, json=payload, timeout=15)

            if response.status_code == 200:
                print(Fore.GREEN + "[+] registered! checking inbox...")

                verification_link = check_inbox_with_retry(session, token, email)

                if verification_link:
                    print(Fore.CYAN + "[*] verifying email...")
                    verify_response = session.get(verification_link, timeout=10)
                    if verify_response.status_code == 200:
                        with lock:
                            if accounts_created[0] < target_accounts:
                                accounts_created[0] += 1
                                with open("accs.txt", "a") as f:
                                    f.write(f"{email}:{password}\n")
                                print(Fore.CYAN + "[+] (account made) " + Fore.LIGHTMAGENTA_EX + f"({email}:{password})")
                    else:
                        print(Fore.RED + f"[-] verification failed: {verify_response.status_code}")
                else:
                    print(Fore.RED + "[-] no verification email found")
            else:
                print(Fore.RED + f"[-] (failed) {response.status_code}")
                if response.text:
                    print(Fore.YELLOW + f"[debug] {response.text[:200]}")

        except Exception as e:
            print(Fore.RED + f"[!] error: {e}")
            continue

def main():
    os.system('cls' if os.name == 'nt' else 'clear')

    print(Fore.LIGHTYELLOW_EX + "DeeVid.ai Account Generator")

    proxies = []
    use_proxies = False

    use_proxy_input = input(Fore.LIGHTCYAN_EX + "Use proxies? (y/n): " + Fore.WHITE).lower()
    if use_proxy_input == 'y':
        proxies = load_proxies()
        if not proxies:
            print(Fore.RED + "[!] no proxies found")
            return
        use_proxies = True
        print(Fore.GREEN + "[+] using proxies")
    else:
        print(Fore.YELLOW + "[*] running without proxies")

    try:
        target_accounts = int(input(Fore.LIGHTCYAN_EX + "Accounts to make: " + Fore.WHITE))
        threads_count = int(input(Fore.LIGHTCYAN_EX + "Threads: " + Fore.WHITE))
    except:
        return

    accounts_created = [0]
    running = [True]
    lock = threading.Lock()
    proxy_index_counter = [0]
    threads = []

    for i in range(threads_count):
        thread = threading.Thread(target=create_account, args=(proxies, target_accounts, accounts_created, lock, running, proxy_index_counter, use_proxies), daemon=True)
        threads.append(thread)
        thread.start()

    try:
        while any(t.is_alive() for t in threads):
            time.sleep(0.5)
            if accounts_created[0] >= target_accounts:
                running[0] = False
                break
    except KeyboardInterrupt:
        running[0] = False
        print(Fore.RED + "\n[!] stopping...")

    print(Fore.LIGHTGREEN_EX + f"\n✅ created {accounts_created[0]} accounts successfully")
    print(Fore.LIGHTBLUE_EX + "[*] saved to accs.txt (email:password)")

if __name__ == "__main__":
    main()
