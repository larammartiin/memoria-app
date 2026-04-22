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
        return redirect(url_for('perfil.inicio'))

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
        return redirect(url_for('perfil.inicio'))

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

    # Todas las sesiones ordenadas por fecha
    sesiones = Sesion.query.filter_by(perfil_id=perfil_id).order_by(Sesion.fecha.desc()).all()

    # Datos para la gráfica (últimas 10 sesiones)
    ultimas = sesiones[:10][::-1]
    grafica_fechas = [s.fecha.strftime('%d/%m') for s in ultimas]
    grafica_porcentajes = [
        round((s.respuestas_correctas / s.total_preguntas * 100)) if s.total_preguntas > 0 else 0
        for s in ultimas
    ]

    # Calendario últimos 30 días
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

    # Mejor sesión
    mejor_sesion = None
    if sesiones:
        sesiones_validas = [s for s in sesiones if s.total_preguntas > 0]
        mejor_sesion = max(sesiones_validas, key=lambda s: s.respuestas_correctas / s.total_preguntas) if sesiones_validas else None
        
    return render_template('historial.html',
        perfil=p,
        sesiones=sesiones,
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
