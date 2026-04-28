from flask import Blueprint, render_template, redirect, url_for, request, jsonify, session
from flask_login import login_required, current_user
from models.models import PerfilMayor, Sesion, Pregunta
from models.models import db
from openai import OpenAI
import os
import json
import math

juego = Blueprint('juego', __name__)

LETRAS = ['A','B','C','D','E','F','G','H','I','J','K','L','M',
          'N','O','P','Q','R','S','T','U','V','W','X','Y','Z']

def generar_pregunta_ia(perfil, letra, preguntas_usadas):
    cliente = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    datos_concretos = []

    if perfil.nombre_pareja:
        datos_concretos.append(f"Su pareja se llama {perfil.nombre_pareja}")
    if perfil.nombres_hijos:
        for hijo in perfil.nombres_hijos.split(','):
            hijo = hijo.strip()
            if hijo:
                datos_concretos.append(f"Tiene un hijo/a que se llama {hijo}")
    if perfil.nombres_nietos:
        for nieto in perfil.nombres_nietos.split(','):
            nieto = nieto.strip()
            if nieto:
                datos_concretos.append(f"Tiene un nieto/a que se llama {nieto}")
    if perfil.nombre_mejor_amigo:
        datos_concretos.append(f"Su mejor amigo/a se llama {perfil.nombre_mejor_amigo}")
    if perfil.ciudad_natal:
        datos_concretos.append(f"Nació en {perfil.ciudad_natal}")
    if perfil.lugar_veraneo:
        datos_concretos.append(f"Veranea en {perfil.lugar_veraneo}")
    if perfil.viajes_favoritos:
        for viaje in perfil.viajes_favoritos.split(','):
            viaje = viaje.strip()
            if viaje:
                datos_concretos.append(f"Ha viajado a {viaje}")
    if perfil.aficiones:
        for aficion in perfil.aficiones.split(','):
            aficion = aficion.strip()
            if aficion:
                datos_concretos.append(f"Le gusta {aficion}")
    if perfil.comida_favorita:
        datos_concretos.append(f"Su comida favorita es {perfil.comida_favorita}")
    if perfil.pelicula_favorita:
        datos_concretos.append(f"Su película favorita es {perfil.pelicula_favorita}")
    if perfil.nombre_mascota:
        datos_concretos.append(f"Su mascota se llama {perfil.nombre_mascota} y es un/a {perfil.tipo_mascota}")
    if perfil.informacion_adicional:
        datos_concretos.append(perfil.informacion_adicional)

    datos_con_letra = []
    for dato in datos_concretos:
        palabras = dato.split()
        for palabra in palabras:
            palabra_limpia = palabra.strip('.,;:()¿?¡!').upper()
            if palabra_limpia.startswith(letra) or letra in palabra_limpia:
                datos_con_letra.append(dato)
                break

    historial = ""
    if preguntas_usadas:
        historial = f"NO repitas estas preguntas ya hechas:\n" + "\n".join(f"- {p}" for p in preguntas_usadas)

    if datos_con_letra:
        contexto_letra = f"""
DATOS DEL PERFIL RELACIONADOS CON LA LETRA "{letra}":
{chr(10).join(f'- {d}' for d in datos_con_letra)}

IMPORTANTE: La respuesta correcta DEBE ser exactamente uno de los datos reales listados arriba.
No inventes ni cambies los datos. Usa exactamente los nombres y lugares tal como aparecen.
"""
    else:
        contexto_letra = f"""
No hay datos del perfil cuya respuesta empiece por o contenga la letra "{letra}".
En este caso genera una pregunta de cultura general sencilla cuya respuesta contenga la letra "{letra}".
"""

    prompt = f"""Eres un terapeuta cognitivo especializado en estimulación de memoria episódica en personas mayores.

Estás generando preguntas personalizadas para {perfil.nombre}, de {perfil.edad} años.

{contexto_letra}

{historial}

Genera UNA sola pregunta de memoria para la letra "{letra}".
- La pregunta debe ser cálida, afectuosa y fácil de entender.
- La respuesta debe contener la letra "{letra}".
- El campo "indicacion" debe ser "Empieza por {letra}" si la respuesta empieza por esa letra, o "Contiene la {letra}" si la contiene en otra posición.
- La pista debe ayudar a recordar sin dar directamente la respuesta.

Responde ÚNICAMENTE con este JSON exacto:
{{
    "indicacion": "Empieza por {letra}",
    "pregunta": "texto de la pregunta",
    "respuesta": "respuesta correcta",
    "pista": "pista breve"
}}"""

    respuesta = cliente.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""Eres un asistente que genera preguntas de memoria personalizadas.
REGLA ABSOLUTA: Si se te proporcionan datos del perfil para una letra, la respuesta SIEMPRE debe ser exactamente uno de esos datos reales.
NUNCA inventes datos. NUNCA uses información que no esté en el perfil.
Si no hay datos del perfil para esa letra, genera cultura general sencilla."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=300,
        temperature=0,
        response_format={"type": "json_object"}
    )

    datos = json.loads(respuesta.choices[0].message.content)
    return datos


def generar_mensaje_motivador(perfil, tipo, correctas=0, incorrectas=0, pasadas=0, total=0):
    porcentaje = round((correctas / total * 100)) if total > 0 else 0

    if porcentaje >= 80:
        return f"¡Excelente trabajo, {perfil.nombre}! Tu memoria está en gran forma hoy. 🌟"
    elif porcentaje >= 60:
        return f"¡Muy bien, {perfil.nombre}! Sigue practicando cada día. 👍"
    elif porcentaje >= 40:
        return f"¡Buen esfuerzo, {perfil.nombre}! Cada día que practicas mejoras un poco más. 💪"
    else:
        return f"¡Lo importante es participar, {perfil.nombre}! Mañana lo harás aún mejor. 🤗"


@juego.route('/juego/<int:perfil_id>')
@login_required
def iniciar_juego(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)

    nueva_sesion = Sesion(perfil_id=p.id)
    db.session.add(nueva_sesion)
    db.session.commit()

    session.pop('sesion_id', None)
    session.pop('perfil_id', None)
    session.pop('letra_actual', None)
    session.pop('correctas', None)
    session.pop('incorrectas', None)
    session.pop('pasadas', None)
    session.pop('preguntas_usadas', None)
    session.pop('pregunta_actual', None)
    session.pop('letra_actual_texto', None)
    session.pop('estados_letras', None)

    session['sesion_id'] = nueva_sesion.id
    session['perfil_id'] = perfil_id
    session['letra_actual'] = 0
    session['correctas'] = 0
    session['incorrectas'] = 0
    session['pasadas'] = 0
    session['preguntas_usadas'] = []

    return redirect(url_for('juego.pregunta'))


@juego.route('/juego/pregunta')
@login_required
def pregunta():
    letra_index = session.get('letra_actual', 0)

    if letra_index >= len(LETRAS):
        return redirect(url_for('juego.resultado'))

    letra = LETRAS[letra_index]
    perfil_id = session.get('perfil_id')
    p = PerfilMayor.query.get(perfil_id)

    preguntas_usadas = session.get('preguntas_usadas', [])
    datos = generar_pregunta_ia(p, letra, preguntas_usadas)

    session['pregunta_actual'] = datos
    session['letra_actual_texto'] = letra

    posiciones = []
    total = len(LETRAS)
    for i, l in enumerate(LETRAS):
        angle = (i * (360 / total) - 90) * (math.pi / 180)
        x = 152 + 145 * math.cos(angle)
        y = 152 + 145 * math.sin(angle)
        if i < letra_index:
            estado = 'pasada'
        elif i == letra_index:
            estado = 'activa'
        else:
            estado = 'pendiente'
        posiciones.append({'letra': l, 'x': x, 'y': y, 'estado': estado})

    return render_template('juego.html',
        letra=letra,
        letra_index=letra_index,
        total_letras=len(LETRAS),
        indicacion=datos['indicacion'],
        pregunta=datos['pregunta'],
        pista=datos['pista'],
        correctas=session.get('correctas', 0),
        incorrectas=session.get('incorrectas', 0),
        pasadas=session.get('pasadas', 0),
        nombre_mayor=p.nombre,
        letras=LETRAS,
        posiciones=posiciones,
    )


@juego.route('/juego/responder', methods=['POST'])
@login_required
def responder():
    respuesta_usuario = request.form.get('respuesta', '').strip().upper()
    accion = request.form.get('accion')

    datos = session.get('pregunta_actual')
    letra = session.get('letra_actual_texto')
    sesion_id = session.get('sesion_id')

    es_correcta = False
    if accion == 'pasar':
        session['pasadas'] = session.get('pasadas', 0) + 1
    else:
        respuesta_correcta = datos['respuesta'].upper()
        es_correcta = respuesta_usuario.startswith(letra) and \
                      any(palabra in respuesta_correcta for palabra in respuesta_usuario.split())

        if es_correcta:
            session['correctas'] = session.get('correctas', 0) + 1
        else:
            session['incorrectas'] = session.get('incorrectas', 0) + 1

    nueva_pregunta = Pregunta(
        sesion_id=sesion_id,
        letra=letra,
        texto_pregunta=datos['pregunta'],
        respuesta_correcta=datos['respuesta'],
        respuesta_usuario=respuesta_usuario if accion != 'pasar' else None,
        es_correcta=es_correcta,
        pista=datos['pista']
    )
    db.session.add(nueva_pregunta)

    sesion_db = Sesion.query.get(sesion_id)
    sesion_db.total_preguntas = session.get('letra_actual', 0) + 1
    sesion_db.respuestas_correctas = session.get('correctas', 0)
    sesion_db.respuestas_incorrectas = session.get('incorrectas', 0)
    sesion_db.preguntas_pasadas = session.get('pasadas', 0)
    db.session.commit()

    preguntas_usadas = session.get('preguntas_usadas', [])
    preguntas_usadas.append(datos['pregunta'])
    session['preguntas_usadas'] = preguntas_usadas
    session['letra_actual'] = session.get('letra_actual', 0) + 1

    return redirect(url_for('juego.pregunta'))


@juego.route('/juego/resultado')
@login_required
def resultado():
    correctas = session.get('correctas', 0)
    incorrectas = session.get('incorrectas', 0)
    pasadas = session.get('pasadas', 0)
    total = len(LETRAS)
    porcentaje = round((correctas / total) * 100)

    perfil_id = session.get('perfil_id')
    p = PerfilMayor.query.get(perfil_id)

    mensaje_final = generar_mensaje_motivador(
        p, 'fin',
        correctas=correctas,
        incorrectas=incorrectas,
        pasadas=pasadas,
        total=total
    )

    return render_template('resultado.html',
        correctas=correctas,
        incorrectas=incorrectas,
        pasadas=pasadas,
        total=total,
        porcentaje=porcentaje,
        nombre_mayor=p.nombre,
        perfil_id=perfil_id,
        mensaje_final=mensaje_final,
    )


@juego.route('/juego/mayor/<int:perfil_id>')
@login_required
def iniciar_juego_mayor(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)

    nueva_sesion = Sesion(perfil_id=p.id)
    db.session.add(nueva_sesion)
    db.session.commit()

    session.pop('sesion_id', None)
    session.pop('perfil_id', None)
    session.pop('letra_actual', None)
    session.pop('correctas', None)
    session.pop('incorrectas', None)
    session.pop('pasadas', None)
    session.pop('preguntas_usadas', None)
    session.pop('pregunta_actual', None)
    session.pop('letra_actual_texto', None)
    session.pop('estados_letras', None)

    session['sesion_id'] = nueva_sesion.id
    session['perfil_id'] = perfil_id
    session['letra_actual'] = 0
    session['correctas'] = 0
    session['incorrectas'] = 0
    session['pasadas'] = 0
    session['preguntas_usadas'] = []
    session['estados_letras'] = ['pendiente'] * len(LETRAS)

    return redirect(url_for('juego.pregunta_mayor'))


@juego.route('/juego/pregunta_mayor')
@login_required
def pregunta_mayor():
    letra_index = session.get('letra_actual', 0)

    if letra_index >= len(LETRAS):
        return redirect(url_for('juego.resultado'))

    letra = LETRAS[letra_index]
    perfil_id = session.get('perfil_id')
    p = PerfilMayor.query.get(perfil_id)

    preguntas_usadas = session.get('preguntas_usadas', [])
    datos = generar_pregunta_ia(p, letra, preguntas_usadas)

    session['pregunta_actual'] = datos
    session['letra_actual_texto'] = letra

    posiciones = []
    estados = session.get('estados_letras', ['pendiente'] * len(LETRAS))
    for i, l in enumerate(LETRAS):
        angle = (i * (360 / len(LETRAS)) - 90) * (math.pi / 180)
        x = 152 + 145 * math.cos(angle)
        y = 152 + 145 * math.sin(angle)
        if i == letra_index:
            estado = 'activa'
        else:
            estado = estados[i]
        posiciones.append({'letra': l, 'x': x, 'y': y, 'estado': estado})

    return render_template('juego_mayor.html',
        letra=letra,
        letra_index=letra_index,
        total_letras=len(LETRAS),
        indicacion=datos['indicacion'],
        pregunta=datos['pregunta'],
        pista=datos['pista'],
        correctas=session.get('correctas', 0),
        incorrectas=session.get('incorrectas', 0),
        pasadas=session.get('pasadas', 0),
        nombre_mayor=p.nombre,
        posiciones=posiciones,
        perfil_id=perfil_id,
    )


@juego.route('/juego/responder_mayor', methods=['POST'])
@login_required
def responder_mayor():
    respuesta_usuario = request.form.get('respuesta', '').strip().upper()
    accion = request.form.get('accion')

    datos = session.get('pregunta_actual')
    letra = session.get('letra_actual_texto')
    sesion_id = session.get('sesion_id')
    letra_index = session.get('letra_actual', 0)
    estados = session.get('estados_letras', ['pendiente'] * len(LETRAS))

    es_correcta = False
    if accion == 'pasar':
        session['pasadas'] = session.get('pasadas', 0) + 1
        estados[letra_index] = 'pasada'
    else:
        respuesta_correcta = datos['respuesta'].upper()
        es_correcta = respuesta_usuario.startswith(letra) and \
                      any(palabra in respuesta_correcta for palabra in respuesta_usuario.split())
        if es_correcta:
            session['correctas'] = session.get('correctas', 0) + 1
            estados[letra_index] = 'correcta'
        else:
            session['incorrectas'] = session.get('incorrectas', 0) + 1
            estados[letra_index] = 'incorrecta'

    session['estados_letras'] = estados

    nueva_pregunta = Pregunta(
        sesion_id=sesion_id,
        letra=letra,
        texto_pregunta=datos['pregunta'],
        respuesta_correcta=datos['respuesta'],
        respuesta_usuario=respuesta_usuario if accion != 'pasar' else None,
        es_correcta=es_correcta,
        pista=datos['pista']
    )
    db.session.add(nueva_pregunta)

    sesion_db = Sesion.query.get(sesion_id)
    sesion_db.total_preguntas = letra_index + 1
    sesion_db.respuestas_correctas = session.get('correctas', 0)
    sesion_db.respuestas_incorrectas = session.get('incorrectas', 0)
    sesion_db.preguntas_pasadas = session.get('pasadas', 0)
    db.session.commit()

    preguntas_usadas = session.get('preguntas_usadas', [])
    preguntas_usadas.append(datos['pregunta'])
    session['preguntas_usadas'] = preguntas_usadas
    session['letra_actual'] = letra_index + 1

    return redirect(url_for('juego.pregunta_mayor'))


@juego.route('/ahorcado/<int:perfil_id>')
@login_required
def ahorcado(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)
    return render_template('ahorcado.html', perfil=p)


@juego.route('/ahorcado/generar', methods=['POST'])
@login_required
def ahorcado_generar():
    perfil_id = request.json.get('perfil_id')
    p = PerfilMayor.query.get_or_404(perfil_id)

    cliente = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    datos = f"""
    Nombre: {p.nombre}, Edad: {p.edad}, Ciudad natal: {p.ciudad_natal},
    Pareja: {p.nombre_pareja}, Hijos: {p.nombres_hijos}, Nietos: {p.nombres_nietos},
    Mejor amigo/a: {p.nombre_mejor_amigo}, Lugar de veraneo: {p.lugar_veraneo},
    Viajes: {p.viajes_favoritos}, Aficiones: {p.aficiones},
    Comida favorita: {p.comida_favorita}, Película favorita: {p.pelicula_favorita},
    Mascota: {p.nombre_mascota}, Info adicional: {p.informacion_adicional}
    """

    respuesta = cliente.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un experto en estimulación cognitiva para personas mayores. Responde ÚNICAMENTE con JSON válido, sin texto extra."
            },
            {
                "role": "user",
                "content": f"""Basándote en estos datos biográficos: {datos}

Elige UNA palabra clave ALEATORIA de la vida de esta persona (máximo 10 letras, sin tildes, en mayúsculas).
REGLAS ESTRICTAS:
- NUNCA uses el nombre de la persona ({p.nombre.split()[0]})
- Cada vez que se llame esta función elige una palabra DIFERENTE
- Rota entre estas categorías: nombres de familiares, ciudades visitadas, aficiones, comidas, mascotas, películas, trabajos, recuerdos especiales
- No repitas la misma palabra dos veces seguidas
- Si hay varios datos en una categoría elige uno distinto cada vez

Genera una pista corta y cariñosa que ayude a recordar sin revelar directamente la palabra.

Responde ÚNICAMENTE con este JSON exacto:
{{"palabra": "PALABRA", "pista": "Frase de pista cariñosa"}}"""
            }
        ],
        max_tokens=100,
        temperature=0.9,
        response_format={"type": "json_object"}
    )

    datos_json = json.loads(respuesta.choices[0].message.content)
    palabra = datos_json['palabra'].upper().strip()
    import unicodedata
    palabra = ''.join(c for c in unicodedata.normalize('NFD', palabra) if unicodedata.category(c) != 'Mn')

    return jsonify({
        'palabra': palabra,
        'pista': datos_json['pista']
    })


@juego.route('/ahorcado/resultado', methods=['POST'])
@login_required
def ahorcado_resultado():
    datos = request.json
    perfil_id = datos.get('perfil_id')
    ganado = datos.get('ganado')

    nueva_sesion = Sesion(
        perfil_id=perfil_id,
        total_preguntas=1,
        respuestas_correctas=1 if ganado else 0,
        respuestas_incorrectas=0 if ganado else 1,
        preguntas_pasadas=0,
        tipo_juego='ahorcado'
    )
    db.session.add(nueva_sesion)
    db.session.commit()

    return jsonify({'ok': True})

@juego.route('/trivial/<int:perfil_id>')
@login_required
def trivial(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)
    return render_template('trivial.html', perfil=p)


@juego.route('/trivial/generar', methods=['POST'])
@login_required
def trivial_generar():
    perfil_id = request.json.get('perfil_id')
    p = PerfilMayor.query.get_or_404(perfil_id)

    cliente = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    datos = f"""
    Nombre: {p.nombre}, Edad: {p.edad}, Ciudad natal: {p.ciudad_natal},
    Pareja: {p.nombre_pareja}, Hijos: {p.nombres_hijos}, Nietos: {p.nombres_nietos},
    Mejor amigo/a: {p.nombre_mejor_amigo}, Lugar de veraneo: {p.lugar_veraneo},
    Viajes: {p.viajes_favoritos}, Aficiones: {p.aficiones},
    Comida favorita: {p.comida_favorita}, Película favorita: {p.pelicula_favorita},
    Mascota: {p.nombre_mascota}, Info adicional: {p.informacion_adicional}
    """

    respuesta = cliente.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un experto en estimulación cognitiva para personas mayores. Responde ÚNICAMENTE con JSON válido, sin texto extra ni backticks."
            },
            {
                "role": "user",
                "content": f"""Basándote en estos datos biográficos: {datos}

Genera 5 preguntas de trivial personalizadas con 3 opciones cada una.
Las preguntas deben ser sobre la vida real de esta persona usando sus datos biográficos.
Deben ser cálidas, afectuosas y apropiadas para personas mayores.

Responde ÚNICAMENTE con este JSON exacto:
[
    {{
        "pregunta": "texto de la pregunta",
        "opciones": ["opción A", "opción B", "opción C"],
        "correcta": 0,
        "explicacion": "explicación breve y cariñosa"
    }}
]"""
            }
        ],
        max_tokens=800,
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    contenido = respuesta.choices[0].message.content
    datos_json = json.loads(contenido)
    if isinstance(datos_json, dict):
        preguntas = list(datos_json.values())[0]
    else:
        preguntas = datos_json

    return jsonify({'preguntas': preguntas})


@juego.route('/trivial/resultado', methods=['POST'])
@login_required
def trivial_resultado():
    datos = request.json
    perfil_id = datos.get('perfil_id')
    correctas = datos.get('correctas', 0)
    total = datos.get('total', 5)

    nueva_sesion = Sesion(
        perfil_id=perfil_id,
        total_preguntas=total,
        respuestas_correctas=correctas,
        respuestas_incorrectas=total - correctas,
        preguntas_pasadas=0,
        tipo_juego='trivial'
    )
    db.session.add(nueva_sesion)
    db.session.commit()

    return jsonify({'ok': True})


@juego.route('/intruso/<int:perfil_id>')
@login_required
def intruso(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)
    return render_template('intruso.html', perfil=p)


@juego.route('/intruso/generar', methods=['POST'])
@login_required
def intruso_generar():
    perfil_id = request.json.get('perfil_id')
    p = PerfilMayor.query.get_or_404(perfil_id)

    cliente = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    datos = f"""
    Nombre: {p.nombre}, Edad: {p.edad}, Ciudad natal: {p.ciudad_natal},
    Pareja: {p.nombre_pareja}, Hijos: {p.nombres_hijos}, Nietos: {p.nombres_nietos},
    Mejor amigo/a: {p.nombre_mejor_amigo}, Lugar de veraneo: {p.lugar_veraneo},
    Viajes: {p.viajes_favoritos}, Aficiones: {p.aficiones},
    Comida favorita: {p.comida_favorita}, Película favorita: {p.pelicula_favorita},
    Mascota: {p.nombre_mascota}, Info adicional: {p.informacion_adicional}
    """

    respuesta = cliente.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un experto en estimulación cognitiva para personas mayores. Responde ÚNICAMENTE con JSON válido, sin texto extra ni backticks."
            },
            {
                "role": "user",
                "content": f"""Basándote en estos datos biográficos: {datos}

Genera 4 rondas del juego "Encuentra al intruso".
Cada ronda tiene un tema relacionado con la vida de esta persona.
Genera 3 elementos reales de su vida y 1 intruso que no pertenezca.

Responde ÚNICAMENTE con este JSON exacto:
{{
    "rondas": [
        {{
            "tema": "tema de la ronda",
            "elementos": ["elemento1", "elemento2", "elemento3", "intruso"],
            "intruso": "intruso",
            "refuerzo": "explicación cariñosa de por qué el intruso no encaja"
        }}
    ]
}}"""
            }
        ],
        max_tokens=600,
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    datos_json = json.loads(respuesta.choices[0].message.content)
    return jsonify(datos_json)


@juego.route('/intruso/resultado', methods=['POST'])
@login_required
def intruso_resultado():
    datos = request.json
    perfil_id = datos.get('perfil_id')
    correctas = datos.get('correctas', 0)
    total = datos.get('total', 4)

    nueva_sesion = Sesion(
        perfil_id=perfil_id,
        total_preguntas=total,
        respuestas_correctas=correctas,
        respuestas_incorrectas=total - correctas,
        preguntas_pasadas=0,
        tipo_juego='intruso'
    )
    db.session.add(nueva_sesion)
    db.session.commit()

    return jsonify({'ok': True})