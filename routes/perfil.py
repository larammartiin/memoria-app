from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models.models import PerfilMayor
from models.models import db


perfil = Blueprint('perfil', __name__)

@perfil.route('/inicio')
@login_required
def inicio():
    perfiles = PerfilMayor.query.filter_by(familiar_id=current_user.id).all()
    return render_template('inicio.html', perfiles=perfiles)


@perfil.route('/perfil/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_perfil():
    if request.method == 'POST':
        nuevo = PerfilMayor(
            familiar_id=current_user.id,
            nombre=request.form.get('nombre'),
            edad=request.form.get('edad'),
            ciudad_natal=request.form.get('ciudad_natal'),
            nombre_pareja=request.form.get('nombre_pareja'),
            nombres_hijos=request.form.get('nombres_hijos'),
            nombres_nietos=request.form.get('nombres_nietos'),
            nombre_mejor_amigo=request.form.get('nombre_mejor_amigo'),
            lugar_veraneo=request.form.get('lugar_veraneo'),
            viajes_favoritos=request.form.get('viajes_favoritos'),
            aficiones=request.form.get('aficiones'),
            comida_favorita=request.form.get('comida_favorita'),
            pelicula_favorita=request.form.get('pelicula_favorita'),
            recuerdos_especiales=request.form.get('recuerdos_especiales'),
            nombre_mascota=request.form.get('nombre_mascota'),
            tipo_mascota=request.form.get('tipo_mascota'),
            informacion_adicional=request.form.get('informacion_adicional'),
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('perfil.seleccion_rol'))

    return render_template('perfil_form.html', perfil=None)


@perfil.route('/perfil/editar/<int:perfil_id>', methods=['GET', 'POST'])
@login_required
def editar_perfil(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)

    if p.familiar_id != current_user.id:
        return redirect(url_for('perfil.inicio'))

    if request.method == 'POST':
        p.nombre = request.form.get('nombre')
        p.edad = request.form.get('edad')
        p.ciudad_natal = request.form.get('ciudad_natal')
        p.nombre_pareja = request.form.get('nombre_pareja')
        p.nombres_hijos = request.form.get('nombres_hijos')
        p.nombres_nietos = request.form.get('nombres_nietos')
        p.nombre_mejor_amigo = request.form.get('nombre_mejor_amigo')
        p.lugar_veraneo = request.form.get('lugar_veraneo')
        p.viajes_favoritos = request.form.get('viajes_favoritos')
        p.aficiones = request.form.get('aficiones')
        p.comida_favorita = request.form.get('comida_favorita')
        p.pelicula_favorita = request.form.get('pelicula_favorita')
        p.recuerdos_especiales = request.form.get('recuerdos_especiales')
        p.nombre_mascota = request.form.get('nombre_mascota')
        p.tipo_mascota = request.form.get('tipo_mascota')
        p.informacion_adicional = request.form.get('informacion_adicional')

        db.session.commit()
        return redirect(url_for('perfil.seleccion_rol'))

    return render_template('perfil_form.html', perfil=p)


@perfil.route('/perfil/eliminar/<int:perfil_id>')
@login_required
def eliminar_perfil(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)

    if p.familiar_id != current_user.id:
        return redirect(url_for('perfil.inicio'))

    db.session.delete(p)
    db.session.commit()
    return redirect(url_for('perfil.inicio'))

from models.models import Sesion
from datetime import datetime, timedelta

@perfil.route('/historial/<int:perfil_id>')
@login_required
def historial(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)

    if p.familiar_id != current_user.id:
        return redirect(url_for('perfil.inicio'))

    sesiones = Sesion.query.filter_by(perfil_id=perfil_id).order_by(Sesion.fecha.desc()).all()
    from datetime import timezone, timedelta
    zona_espana = timedelta(hours=2)
    for s in sesiones:
        s.fecha = s.fecha + zona_espana

    # Separar sesiones por tipo
    sesiones_rosco = [s for s in sesiones if s.tipo_juego in ('rosco', 'trivial', 'intruso')]
    sesiones_ahorcado = [s for s in sesiones if s.tipo_juego == 'ahorcado']

    # Agrupar ahorcado por día
    from collections import defaultdict
    ahorcado_por_dia = defaultdict(lambda: {'correctas': 0, 'incorrectas': 0, 'total': 0, 'fecha': None})
    for s in sesiones_ahorcado:
        dia = s.fecha.date().strftime('%Y-%m-%d')
        ahorcado_por_dia[dia]['correctas'] += s.respuestas_correctas
        ahorcado_por_dia[dia]['incorrectas'] += s.respuestas_incorrectas
        ahorcado_por_dia[dia]['total'] += 1
        ahorcado_por_dia[dia]['fecha'] = s.fecha

    # Convertir a lista ordenada
    ahorcado_agrupado = sorted(
        [{'dia': dia, **datos} for dia, datos in ahorcado_por_dia.items()],
        key=lambda x: x['dia'],
        reverse=True
    )

    # Datos para la gráfica — agrupar por día todos los juegos
    from collections import defaultdict
    datos_por_dia = defaultdict(lambda: {'correctas': 0, 'total': 0})
    for s in sesiones:
        dia = s.fecha.strftime('%d/%m')
        datos_por_dia[dia]['correctas'] += s.respuestas_correctas
        datos_por_dia[dia]['total'] += s.total_preguntas if s.total_preguntas > 0 else 1

    from datetime import datetime as dt
    dias_ordenados = sorted(datos_por_dia.keys(), key=lambda d: dt.strptime(d, '%d/%m'))
    ultimos_dias = dias_ordenados[-10:]

    grafica_fechas = ultimos_dias
    grafica_porcentajes = [
        round((datos_por_dia[dia]['correctas'] / datos_por_dia[dia]['total']) * 100)
        if datos_por_dia[dia]['total'] > 0 else 0
        for dia in ultimos_dias
    ]

    # Calendario últimos 30 días
    from datetime import datetime, timedelta
    hoy = datetime.utcnow().date()
    calendario = {}
    for i in range(30):
        dia = hoy - timedelta(days=i)
        calendario[dia.strftime('%Y-%m-%d')] = 0

    for s in sesiones:
        dia_str = s.fecha.date().strftime('%Y-%m-%d')
        if dia_str in calendario:
            calendario[dia_str] += 1

    # Informe semanal
    hace_7_dias = datetime.utcnow() - timedelta(days=7)
    sesiones_semana = [s for s in sesiones if s.fecha >= hace_7_dias]
    total_semana = len(sesiones_semana)
    correctas_semana = sum(s.respuestas_correctas for s in sesiones_semana)
    total_preguntas_semana = sum(s.total_preguntas for s in sesiones_semana)
    porcentaje_semana = round((correctas_semana / total_preguntas_semana * 100)) if total_preguntas_semana > 0 else 0

    # Mejor sesión rosco
    sesiones_validas = [s for s in sesiones_rosco if s.total_preguntas > 0]
    mejor_sesion = max(sesiones_validas, key=lambda s: s.respuestas_correctas / s.total_preguntas) if sesiones_validas else None

    return render_template('historial.html',
        perfil=p,
        sesiones=sesiones_rosco,
        ahorcado_agrupado=ahorcado_agrupado,
        grafica_fechas=grafica_fechas,
        grafica_porcentajes=grafica_porcentajes,
        calendario=calendario,
        total_semana=total_semana,
        porcentaje_semana=porcentaje_semana,
        correctas_semana=correctas_semana,
        total_preguntas_semana=total_preguntas_semana,
        mejor_sesion=mejor_sesion,
        hoy=hoy,
    )
@perfil.route('/seleccion')
@login_required
def seleccion_rol():
    perfiles = PerfilMayor.query.filter_by(familiar_id=current_user.id).all()
    if not perfiles:
        return redirect(url_for('perfil.nuevo_perfil'))
    return render_template('seleccion_rol.html', perfiles=perfiles, nombre=current_user.nombre)


@perfil.route('/responsable/<int:perfil_id>')
@login_required
def responsable(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)
    return render_template('inicio.html', perfiles=[p])


@perfil.route('/usuario/<int:perfil_id>')
@login_required
def usuario(perfil_id):
    p = PerfilMayor.query.get_or_404(perfil_id)
    return render_template('usuario_juegos.html', perfil=p)