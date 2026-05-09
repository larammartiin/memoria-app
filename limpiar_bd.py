import psycopg2

conn = psycopg2.connect('postgresql://postgres:FqbmjvljtWyadkQkejqyBURNPFJneypq@shinkansen.proxy.rlwy.net:58327/railway')
cur = conn.cursor()

cur.execute('DELETE FROM preguntas')
cur.execute('DELETE FROM sesiones')
cur.execute('DELETE FROM perfiles_mayores')
cur.execute('DELETE FROM usuarios')

conn.commit()
cur.close()
conn.close()
print('Base de datos limpiada correctamente')
