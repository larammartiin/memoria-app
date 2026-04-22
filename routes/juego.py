from flask import Blueprint, render_template, redirect, url_for, request, jsonify, session
from flask_login import login_required, current_user
from models.models import PerfilMayor, Sesion, Pregunta
from models.models import db
from openai import OpenAI
import os
import json

juego = Blueprint('juego', __name__)

LETRAS = ['A','B','C','D','E','F','G','H','I','J','K','L','M',
          'N','O','P','Q','R','S','T','U','V','W','X','Y','Z']

def generar_pregunta_ia(perfil, letra, preguntas_usadas):
    cliente = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Construir diccionario de datos reales del perfil
    datos_perfil = {
        'A': [],
        'B': [], 'C': [], 'D': [], 'E': [], 'F': [], 'G': [],
        'H': [], 'I': [], 'J': [], 'K': [], 'L': [], 'M': [],
        'N': [], 'O': [], 'P': [], 'Q': [], 'R': [], 'S': [],
        'T': [], 'U': [], 'V': [], 'W': [], 'X': [], 'Y': [], 'Z': []
    }

    # Lista plana de todos los datos del perfil con su contexto
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

    # Filtrar datos cuya respuesta contiene la letra buscada
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

    contexto_letra = ""
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
    cliente = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    if tipo == 'inicio':
        prompt = f"""Eres un asistente cálido y motivador para personas mayores.

Genera un mensaje de bienvenida corto y afectuoso (máximo 3 frases) para {perfil.nombre} que va a hacer sus ejercicios de memoria.
Usa información personal para hacerlo más cercano:
- Aficiones: {perfil.aficiones}
- Familia: hijos ({perfil.nombres_hijos}), nietos ({perfil.nombres_nietos})
- Lugar favorito: {perfil.lugar_veraneo}

El mensaje debe ser cálido, motivador y natural. Como si fuera un amigo cercano.
Responde ÚNICAMENTE con el texto del mensaje, sin comillas ni explicaciones."""

    else:
        porcentaje = round((correctas / total * 100)) if total > 0 else 0
        prompt = f"""Eres un asistente cálido y motivador para personas mayores.

Genera un mensaje de felicitación corto y afectuoso (máximo 3 frases) para {perfil.nombre} que acaba de terminar sus ejercicios de memoria.
Resultados: {correctas} correctas de {total} preguntas ({porcentaje}%).

El mensaje debe:
- Felicitarle por haber jugado
- Mencionar algo positivo de su resultado
- Animarle a seguir practicando mañana
- Ser muy cálido y cercano

Responde ÚNICAMENTE con el texto del mensaje, sin comillas ni explicaciones."""

    respuesta = cliente.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )

    return respuesta.choices[0].message.content.strip()
@juego.route('/juego/bienvenida/<int:perfil_id>')
@login_required
def bienvenida(perfil_id):
    from datetime import datetime
    from models.models import Sesion

    p = PerfilMayor.query.get_or_404(perfil_id)

    mensaje = generar_mensaje_motivador(p, 'inicio')

    ultima_sesion = Sesion.query.filter_by(perfil_id=perfil_id)\
        .order_by(Sesion.fecha.desc()).first()

    dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
    meses = ['enero','febrero','marzo','abril','mayo','junio',
             'julio','agosto','septiembre','octubre','noviembre','diciembre']
    hoy = datetime.now()
    fecha_hoy = f"{dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

    return render_template('bienvenida.html',
        nombre_mayor=p.nombre,
        mensaje=mensaje,
        fecha_hoy=fecha_hoy,
        ultima_sesion=ultima_sesion,
        url_juego=url_for('juego.iniciar_juego', perfil_id=perfil_id),
    )


@juego.route('/juego/bienvenida_mayor/<int:perfil_id>')
@login_required
def bienvenida_mayor(perfil_id):
    from datetime import datetime
    from models.models import Sesion

    p = PerfilMayor.query.get_or_404(perfil_id)

    mensaje = generar_mensaje_motivador(p, 'inicio')

    ultima_sesion = Sesion.query.filter_by(perfil_id=perfil_id)\
        .order_by(Sesion.fecha.desc()).first()

    dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
    meses = ['enero','febrero','marzo','abril','mayo','junio',
             'julio','agosto','septiembre','octubre','noviembre','diciembre']
    hoy = datetime.now()
    fecha_hoy = f"{dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

    return render_template('bienvenida.html',
        nombre_mayor=p.nombre,
        mensaje=mensaje,
        fecha_hoy=fecha_hoy,
        ultima_sesion=ultima_sesion,
        url_juego=url_for('juego.iniciar_juego_mayor', perfil_id=perfil_id),
    )

@juego.route('/juego/<int:perfil_id>')
@login_required
def iniciar_juego(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)

    nueva_sesion = Sesion(perfil_id=p.id)
    db.session.add(nueva_sesion)
    db.session.commit()

    session['sesion_id'] = nueva_sesion.id
    session['perfil_id'] = perfil_id
    session['letra_actual'] = 0
    session['correctas'] = 0
    session['incorrectas'] = 0
    session['pasadas'] = 0
    session['preguntas_usadas'] = []
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

    import math
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

    session['sesion_id'] = nueva_sesion.id
    session['perfil_id'] = perfil_id
    session['letra_actual'] = 0
    session['correctas'] = 0
    session['incorrectas'] = 0
    session['pasadas'] = 0
    session['preguntas_usadas'] = []
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

    import math
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