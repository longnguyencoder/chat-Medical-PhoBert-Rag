from src import create_app

app = create_app()

if __name__ == '__main__':
    # Run on all interfaces to allow localhost and local IP connections
    app.run(
        debug=True,
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,
        threaded=True
    )