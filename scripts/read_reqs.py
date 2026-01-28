
try:
    with open('requirements.txt', 'r', encoding='utf-16') as f:
        print(f.read())
except Exception as e:
    print(f"Error reading with utf-16: {e}")
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            print(f.read())
    except Exception as e:
        print(f"Error reading with utf-8: {e}")
