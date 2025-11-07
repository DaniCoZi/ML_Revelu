from app import create_app

# Crear la instancia de la aplicación Flask usando la función create_app
app = create_app()

if __name__ == "__main__":
    # Usa el servidor de desarrollo de Flask para pruebas locales
    app.run(debug=True, host='0.0.0.0', port=5000)
