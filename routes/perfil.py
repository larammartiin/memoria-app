from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models.models import PerfilMayor
from app import db

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
