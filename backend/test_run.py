try:
    from app.main import app
    print("Успішно! З імпортами все супер.")
except Exception as e:
    import traceback
    traceback.print_exc()