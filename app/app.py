from flask import Flask, render_template, request, redirect, url_for, flash
import pyodbc
import json
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'UDLA'


ruta_config = os.path.join(os.path.dirname(__file__), '..', 'config.json')
with open(ruta_config) as f:
    config = json.load(f)

app.secret_key = config['secret_key']

def requiere_permiso(permiso):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if permiso not in config['permisos']:
                flash('Acceso no autorizado', 'danger')
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return wrapper
    return decorador

# ============== GESTIÓN DE CONEXIÓN ==============
class ConexionDB:
    _instancia = None
    #esquema = config['esquema']

    def __new__(cls):
        if not cls._instancia:
            cls._instancia = super().__new__(cls)
            cls._instancia.conectar()
        return cls._instancia

    def conectar(self):
        try:
            self.conn = pyodbc.connect(
                f"DRIVER={config['driver']};"
                f"SERVER={config['server']};"
                f"DATABASE={config['database']};"
                f"UID={config['user']};"
                f"PWD={config['password']}"
            )
            self.conn.autocommit = False
        except pyodbc.Error as e:
            raise RuntimeError(f"Error de conexión: {str(e)}")

    @property
    def cursor(self):
        return self.conn.cursor()

    def cerrar(self):
        if self.conn:
            self.conn.close()
            self._instancia = None

# ============== MODELO BASE ==============
class ModeloBase:
    def __init__(self):
        self.db = ConexionDB()
    
    def ejecutar_sp(self, nombre_sp, parametros):
        try:
            cursor = self.db.cursor
            params = ', '.join(['?'] * len(parametros))
            
            cursor.execute(f"{{call sch_procs.{nombre_sp}({params})}}", parametros)
            resultado = cursor.fetchall()
            self.db.conn.commit()
            return resultado
        except pyodbc.Error as e:
            self.db.conn.rollback()
            raise
        finally:
            cursor.close()

# ============== MODELO CATEQUIZANDO ==============
class Catequizando(ModeloBase):
    @requiere_permiso('lectura')
    def listar(self):
        # El procedimiento debe existir en sch_procs
        return self.ejecutar_sp('sp_listar_catequizando', [])

    @requiere_permiso('escritura')
    def crear(self, datos):
        params = [
            datos['nombre'],
            datos['fecha_nac'],
            datos['cedula'],
            datos['direccion'],
            datos['parroquia_id']
        ]
        # El procedimiento correcto según tu script es sp_crear_catequizando
        return self.ejecutar_sp('sp_crear_catequizando', params)

    @requiere_permiso('escritura')
    def actualizar(self, usuario_id, datos):
        # Debes crear este procedimiento en tu base de datos si no existe
        params = [
            datos['nombre'],
            datos['fecha_nac'],
            datos['cedula'],
            datos['direccion'],
            datos['parroquia_id'],
            usuario_id
        ]
        return self.ejecutar_sp('sp_actualizar_catequizando', params)

# ============== MODELO REPRESENTANTE ==============
class Representante(ModeloBase):
    @requiere_permiso('escritura')
    def crear(self, usuario_id, datos):
        params = [
            datos['nombre'],
            datos['parentesco'],
            datos['telefono'],
            usuario_id
        ]
        return self.ejecutar_sp('sp_representante_crear', params)
    
    @requiere_permiso('administracion')
    def eliminar(self, representante_id):
        return self.ejecutar_sp('sp_representante_eliminar', [representante_id])
    
    def listar_por_usuario(self, usuario_id):
        return self.ejecutar_sp('sp_representante_listar', [usuario_id])

# ============== RUTAS ==============
@app.route('/')
@requiere_permiso('lectura')
def index():
    try:
        modelo = Catequizando()
        return render_template('index.html', catequizandos=modelo.listar())
    except Exception as e:
        flash(f'Error al cargar datos: {str(e)}', 'danger')
        return render_template('index.html')

@app.route('/crear', methods=['GET', 'POST'])
@requiere_permiso('escritura')
def crear():
    if request.method == 'POST':
        datos = {
            'nombre': request.form.get('nombre'),
            'fecha_nac': request.form.get('fecha_nac'),
            'cedula': request.form.get('cedula'),
            'direccion': request.form.get('direccion'),
            'parroquia_id': request.form.get('parroquia_id')
        }
        
        datos_rep = {
            'nombre': request.form.get('rep_nombre'),
            'parentesco': request.form.get('rep_parentesco'),
            'telefono': request.form.get('rep_telefono')
        }

        try:
            cat = Catequizando()
            rep = Representante()
            
            resultado = cat.crear(datos)
            if resultado:
                rep.crear(resultado[0][0], datos_rep)
                flash('Registro creado exitosamente', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        
        return redirect(url_for('index'))
    
    return render_template('crear.html')

@app.route('/editar/<int:usuario_id>', methods=['GET', 'POST'])
@requiere_permiso('escritura')
def editar(usuario_id):
    try:
        cat = Catequizando()
        rep = Representante()
        
        if request.method == 'POST':
            nuevos_datos = {
                'nombre': request.form.get('nombre'),
                'fecha_nac': request.form.get('fecha_nac'),
                'cedula': request.form.get('cedula'),
                'direccion': request.form.get('direccion'),
                'parroquia_id': request.form.get('parroquia_id')
            }
            
            if cat.actualizar(usuario_id, nuevos_datos):
                flash('Actualización exitosa', 'success')
            return redirect(url_for('index'))
        
        datos = cat.obtener(usuario_id)
        representantes = rep.listar_por_usuario(usuario_id)
        return render_template('editar.html', datos=datos[0], representantes=representantes)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/eliminar/<int:usuario_id>', methods=['POST'])
@requiere_permiso('administracion')
def eliminar(usuario_id):
    try:
        cat = Catequizando()
        if cat.eliminar(usuario_id):
            flash('Registro eliminado', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/reportes')
@requiere_permiso('reportes')
def reportes():
    try:
        cat = Catequizando()
        return render_template('reportes.html', estadisticas=cat.reportes())
    except Exception as e:
        flash(f'Error generando reportes: {str(e)}', 'danger')
        return redirect(url_for('index'))

# ============== EJECUCIÓN ==============
if __name__ == '__main__':
    app.run(debug=config['debug'])