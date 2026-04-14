# MemorIA - Ejercicios de memoria personalizados

App web para refuerzo de memoria en personas mayores mediante ejercicios personalizados con información personal del usuario.

## Requisitos
- Python 3.10 o superior
- Una clave de API de OpenAI

## Instalación

1. Clona el repositorio:
git clone https://github.com/tu-usuario/memoria-app.git
cd memoria-app

2. Crea el entorno virtual:
python -m venv venv
venv\Scripts\activate

3. Instala las dependencias:
pip install -r requirements.txt

4. Crea el archivo .env con tus claves:
SECRET_KEY=clave_secreta_que_quieras
OPENAI_API_KEY=sk-tu-clave-de-openai
DATABASE_URL=sqlite:///memoria.db

5. Arranca la app:
python app.py

6. Abre el navegador en:
http://127.0.0.1:5000
