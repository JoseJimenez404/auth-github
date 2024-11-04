import requests
import webbrowser
from flask import Flask, request, redirect
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from threading import Thread
from kivy.core.window import Window
from kivy.clock import Clock  # Importar Clock para gestionar los hilos correctamente

# Configuración de Flask para manejar la respuesta de GitHub
app_flask = Flask(__name__)
Window.size = (350, 550)

# Variables de GitHub OAuth
CLIENT_ID = 'Ov23li7qHQlXEVdYATpD'
CLIENT_SECRET = 'cfd123916aab4ca35d78b44d975328d12740716d'
REDIRECT_URI = 'http://localhost:8000/callback'
GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USER_URL = 'https://api.github.com/user'

# Clase principal de la app en Kivy
class LoginScreen(BoxLayout):
    pass

class MyApp(App):
    user_data = None  # Variable para almacenar los datos del usuario

    def build(self):
        # Cargar la interfaz de Kivy
        return Builder.load_file('login.kv')

    def login_with_github(self):
        # Iniciar el proceso de autenticación con GitHub en un hilo separado
        Thread(target=self.start_authentication).start()

    def start_authentication(self):
        # Paso 1: Redirigir al usuario a la URL de autorización de GitHub
        auth_url = f"{GITHUB_AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
        webbrowser.open(auth_url)

        # Paso 2: Iniciar el servidor Flask para manejar la respuesta
        app_flask.run(port=8000)

    def on_successful_login(self, user_data):
        # Usar Clock.schedule_once para ejecutar la actualización en el hilo principal
        Clock.schedule_once(lambda dt: self.update_ui_after_login(user_data))

    def update_ui_after_login(self, user_data):
        # Actualizar el texto del mensaje de bienvenida
        welcome_label = self.root.ids.welcome_label
        welcome_label.text = f"Bienvenido {user_data['name']}\nUsuario: {user_data['login']}"

        # Ocultar el botón de inicio de sesión
        login_button = self.root.ids.login_button
        login_button.opacity = 0  # Ocultar el botón
        login_button.disabled = True  # Deshabilitar el botón para evitar que se pueda interactuar

# Rutas de Flask para manejar la autenticación
@app_flask.route('/callback')
def github_callback():
    code = request.args.get('code')
    if code:
        # Intercambiar el código por un token de acceso
        token_response = requests.post(GITHUB_TOKEN_URL, headers={'Accept': 'application/json'}, data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI,
        })
        token_json = token_response.json()
        access_token = token_json.get('access_token')

        # Usar el token de acceso para obtener datos del usuario
        user_response = requests.get(GITHUB_USER_URL, headers={
            'Authorization': f'token {access_token}',
            'Accept': 'application/json',
        })
        user_data = user_response.json()

        # Llamar al método de la app Kivy para actualizar la interfaz
        App.get_running_app().on_successful_login(user_data)

        # Cerrar el servidor Flask y redirigir al usuario a una página de éxito
        shutdown_server()
        return redirect("https://localhost:8000/success")

    return "Error: no se pudo autenticar con GitHub."

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()

if __name__ == '__main__':
    MyApp().run()
