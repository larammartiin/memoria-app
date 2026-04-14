from flask import Blueprint, render_template, redirect, url_for, request, jsonify, session
from flask_login import login_required, current_user
from models.models import PerfilMayor, Sesion, Pregunta
from app import db
from openai import OpenAI
import os
import json

juego = Blueprint('juego', __name__)

LETRAS = ['A','B','C','D','E','F','G','H','I','J','K','L','M',
          'N','O','P','Q','R','S','T','U','V','W','X','Y','Z']

def generar_pregunta_ia(perfil, letra):
    cliente = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    prompt = f"""Eres un terapeuta cognitivo especializado en estimulación de memoria episódica en personas mayores.

Perfil del usuario:
- Nombre: {perfil.nombre}
- Edad: {perfil.edad} años
- Ciudad natal: {perfil.ciudad_natal}
- Pareja: {perfil.nombre_pareja}
- Hijos: {perfil.nombres_hijos}
- Nietos: {perfil.nombres_nietos}
- Mejor amigo/a: {perfil.nombre_mejor_amigo}
- Lugar de veraneo: {perfil.lugar_veraneo}
- Viajes favoritos: {perfil.viajes_favoritos}
- Aficiones: {perfil.aficiones}
- Comida favorita: {perfil.comida_favorita}
- Película favorita: {perfil.pelicula_favorita}
- Recuerdos especiales: {perfil.recuerdos_especiales}
- Mascota: {perfil.nombre_mascota} ({perfil.tipo_mascota})

Tarea: Genera una pregunta de memoria para la letra "{letra}" usando información del perfil anterior.

REGLAS IMPORTANTES:
1. Decide si la respuesta EMPIEZA por "{letra}" o CONTIENE la letra "{letra}" en cualquier posición.
2. El campo "tipo" debe ser exactamente "empieza" si la respuesta empieza por "{letra}", o "contiene" si la contiene en otra posición.
3. El campo "indicacion" debe ser exactamente:
   - Si empieza: "Empieza por {letra}"
   - Si contiene: "Contiene la {letra}"
4. La pregunta debe ser cálida, afectuosa y apropiada para alguien con deterioro cognitivo leve.
5. Usa información del perfil siempre que sea posible. Si no hay datos para esa letra, genera una pregunta de cultura general sencilla.
6. La respuesta debe ser una sola palabra o nombre corto.

Responde ÚNICAMENTE con un JSON con este formato exacto, sin texto extra:
{{
    "indicacion": "Empieza por {letra}",
    "pregunta": "texto de la pregunta aquí",
    "respuesta": "respuesta correcta aquí",
    "pista": "una pista breve"
}}"""

    respuesta = cliente.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        response_format={"type": "json_object"}
    )

    datos = json.loads(respuesta.choices[0].message.content)
    return datos 


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

    datos = generar_pregunta_ia(p, letra)

    session['pregunta_actual'] = datos
    session['letra_actual_texto'] = letra

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

    return render_template('resultado.html',
        correctas=correctas,
        incorrectas=incorrectas,
        pasadas=pasadas,
        total=total,
        porcentaje=porcentaje,
        nombre_mayor=p.nombre,
        perfil_id=perfil_id,
    )
