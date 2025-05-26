import pyodbc 
from datetime import datetime


class ConexionDB:
    def __init__(self):
        self.server = r'PAULPOOL_'
        self.database = 'CATEQUESIS'
        self.username = 'pythonconsultor'
        self.password = 'UDLA'
        self.conn = None
        self.cursor = None

    def conectar(self):
        try:
            self.conn = pyodbc.connect(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={self.server};DATABASE={self.database};'
                f'UID={self.username};PWD={self.password}'
            )
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False

    def cerrar(self):
        if self.conn:
            self.conn.close()

class Catequizando:
    def __init__(self, cursor, conn, representante_obj):
        self.cursor = cursor
        self.conn = conn
        self.representante = representante_obj

    def crear(self):
        print("\n--- NUEVO CATEQUIZANDO ---")
        try:
            nombre = input("Nombre completo: ")
            fecha_nac = input("Fecha nacimiento (YYYY-MM-DD): ")
            cedula = input("Cédula: ")
            direccion = input("Dirección: ")
            parroquia_id = input("ID Parroquia: ")

            self.cursor.execute("BEGIN TRANSACTION")
            self.cursor.execute("CREATE TABLE #TempID (ID INT)")

            query = """
            INSERT INTO Catequizando (NombreCompleto, FechaNacimiento, Cedula, Direccion, ParroquiaId)
            OUTPUT INSERTED.UsuarioId INTO #TempID
            VALUES (?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, nombre, fecha_nac, cedula, direccion, parroquia_id)

            self.cursor.execute("SELECT ID FROM #TempID")
            usuario_id = self.cursor.fetchone()[0]
            self.cursor.execute("DROP TABLE #TempID")

            self.representante.crear(usuario_id, principal=True)

            self.conn.commit()
            print(f"\nCatequizando creado con ID: {usuario_id}")
            return usuario_id
        except Exception as e:
            self.conn.rollback()
            try:
                self.cursor.execute("IF OBJECT_ID('tempdb..#TempID') IS NOT NULL DROP TABLE #TempID")
            except:
                pass
            print(f"\nError al crear catequizando: {e}")
            return None

    def listar(self):
        try:
            query = """
            SELECT c.UsuarioId, c.NombreCompleto, c.Cedula, 
                   COUNT(r.RepresentanteId) as num_representantes
            FROM Catequizando c
            LEFT JOIN Representante r ON c.UsuarioId = r.UsuarioId
            GROUP BY c.UsuarioId, c.NombreCompleto, c.Cedula
            ORDER BY c.NombreCompleto
            """
            self.cursor.execute(query)
            resultados = self.cursor.fetchall()

            print("\nLISTA DE CATEQUIZANDOS")
            print("-" * 60)
            print("{:<8} {:<30} {:<15} {:<10}".format(
                "ID", "Nombre", "Cédula", "Representantes"))
            print("-" * 60)

            for row in resultados:
                print("{:<8} {:<30} {:<15} {:<10}".format(
                    row.UsuarioId, row.NombreCompleto, row.Cedula, row.num_representantes))

            print(f"\nTotal: {len(resultados)} catequizandos")
            return resultados
        except Exception as e:
            print(f"\nError al listar catequizandos: {e}")
            return None

    def ver_detalle(self, usuario_id):
        try:
            query_cat = """
            SELECT UsuarioId, NombreCompleto, FechaNacimiento, Cedula, Direccion, ParroquiaId
            FROM Catequizando
            WHERE UsuarioId = ?
            """
            self.cursor.execute(query_cat, usuario_id)
            catequizando = self.cursor.fetchone()

            if not catequizando:
                print("\nCatequizando no encontrado")
                return None

            query_rep = """
            SELECT RepresentanteId, NombreCompleto, Parentesco, Telefono
            FROM Representante
            WHERE UsuarioId = ?
            ORDER BY CASE WHEN Parentesco = 'Padre' THEN 1
                         WHEN Parentesco = 'Madre' THEN 2
                         ELSE 3 END
            """
            self.cursor.execute(query_rep, usuario_id)
            representantes = self.cursor.fetchall()

            print("\nDETALLE DEL CATEQUIZANDO")
            print("-" * 50)
            print(f"ID: {catequizando.UsuarioId}")
            print(f"Nombre: {catequizando.NombreCompleto}")
            print(f"Nacimiento: {catequizando.FechaNacimiento}")
            print(f"Cédula: {catequizando.Cedula}")
            print(f"Dirección: {catequizando.Direccion}")
            print(f"Parroquia ID: {catequizando.ParroquiaId}")

            print("\nREPRESENTANTES:")
            if representantes:
                for rep in representantes:
                    print(f" - {rep.Parentesco}: {rep.NombreCompleto} (Tel: {rep.Telefono})")
            else:
                print("No tiene representantes registrados")

            return (catequizando, representantes)
        except Exception as e:
            print(f"\nError al obtener detalles: {e}")
            return None

    def actualizar(self, usuario_id):
        try:
            datos_actuales = self.ver_detalle(usuario_id)
            if not datos_actuales:
                return False

            print("\nIngrese nuevos valores (dejar vacío para mantener el actual):")
            nombre = input(f"Nuevo nombre [{datos_actuales[0].NombreCompleto}]: ") or None
            fecha = input(f"Nueva fecha nacimiento [{datos_actuales[0].FechaNacimiento}]: ") or None
            cedula = input(f"Nueva cédula [{datos_actuales[0].Cedula}]: ") or None
            direccion = input(f"Nueva dirección [{datos_actuales[0].Direccion}]: ") or None
            parroquia = input(f"Nuevo ID parroquia [{datos_actuales[0].ParroquiaId}]: ") or None

            query = "UPDATE Catequizando SET "
            params = []
            updates = []

            if nombre:
                updates.append("NombreCompleto = ?")
                params.append(nombre)
            if fecha:
                updates.append("FechaNacimiento = ?")
                params.append(fecha)
            if cedula:
                updates.append("Cedula = ?")
                params.append(cedula)
            if direccion:
                updates.append("Direccion = ?")
                params.append(direccion)
            if parroquia:
                updates.append("ParroquiaId = ?")
                params.append(parroquia)

            if not updates:
                print("\nNo se realizaron cambios")
                return False

            query += ", ".join(updates) + " WHERE UsuarioId = ?"
            params.append(usuario_id)

            self.cursor.execute(query, *params)
            self.conn.commit()
            print("\nCatequizando actualizado correctamente")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"\nError al actualizar: {e}")
            return False

    def eliminar(self, usuario_id):
        try:
            datos = self.ver_detalle(usuario_id)
            if not datos:
                return False

            confirmar = input(f"\n¿Está seguro de eliminar a {datos[0].NombreCompleto}? (s/n): ")
            if confirmar.lower() != 's':
                print("Operación cancelada")
                return False

            query = "DELETE FROM Catequizando WHERE UsuarioId = ?"
            self.cursor.execute(query, usuario_id)
            self.conn.commit()

            if self.cursor.rowcount > 0:
                print("\nCatequizando y representantes eliminados correctamente")
                return True
            else:
                print("\nNo se pudo eliminar el catequizando")
                return False
        except Exception as e:
            self.conn.rollback()
            print(f"\nError al eliminar: {e}")
            return False

class Representante:
    def __init__(self, cursor, conn):
        self.cursor = cursor
        self.conn = conn

    def crear(self, usuario_id, principal=False):
        try:
            print("\n--- DATOS DEL REPRESENTANTE ---")
            nombre = input("Nombre completo: ")
            parentesco = input("Parentesco (Padre/Madre/Tutor/Otro): ")
            telefono = input("Teléfono: ")

            query = """
            INSERT INTO Representante (NombreCompleto, Parentesco, Telefono, UsuarioId)
            VALUES (?, ?, ?, ?)
            """
            self.cursor.execute(query, nombre, parentesco, telefono, usuario_id)

            if not principal:
                self.conn.commit()
                print("\nRepresentante agregado correctamente")
            return True
        except Exception as e:
            print(f"\nError al crear representante: {e}")
            return False

    def eliminar(self, representante_id):
        try:
            query_check = """
            SELECT COUNT(*) 
            FROM Representante 
            WHERE UsuarioId = (SELECT UsuarioId FROM Representante WHERE RepresentanteId = ?)
            """
            self.cursor.execute(query_check, representante_id)
            count = self.cursor.fetchone()[0]

            if count <= 1:
                print("\nNo se puede eliminar. Cada catequizando debe tener al menos un representante")
                return False

            query = "DELETE FROM Representante WHERE RepresentanteId = ?"
            self.cursor.execute(query, representante_id)
            self.conn.commit()

            if self.cursor.rowcount > 0:
                print("\nRepresentante eliminado correctamente")
                return True
            else:
                print("\nNo se encontró el representante")
                return False
        except Exception as e:
            self.conn.rollback()
            print(f"\nError al eliminar representante: {e}")
            return False

class CatequesisManager:
    def __init__(self):
        self.db = ConexionDB()

    def iniciar(self):
        if self.db.conectar():
            representante = Representante(self.db.cursor, self.db.conn)
            catequizando = Catequizando(self.db.cursor, self.db.conn, representante)
            self.menu_principal(catequizando, representante)
            self.db.cerrar()

    def menu_principal(self, cat, rep):
        while True:
            print("\n" + "="*50)
            print(" SISTEMA DE GESTIÓN DE CATEQUESIS ".center(50))
            print("="*50)
            print("1. Crear nuevo catequizando")
            print("2. Listar catequizandos")
            print("3. Ver detalle de catequizando")
            print("4. Actualizar catequizando")
            print("5. Eliminar catequizando")
            print("6. Gestionar representantes")
            print("7. Salir")

            opcion = input("\nSeleccione una opción: ")
            if opcion == "1":
                cat.crear()
            elif opcion == "2":
                cat.listar()
            elif opcion == "3":
                id = input("ID del catequizando: ")
                cat.ver_detalle(id)
            elif opcion == "4":
                id = input("ID del catequizando: ")
                cat.actualizar(id)
            elif opcion == "5":
                id = input("ID del catequizando: ")
                cat.eliminar(id)
            elif opcion == "6":
                self.menu_representantes(cat, rep)
            elif opcion == "7":
                print("\n¡Hasta pronto!")
                break
            else:
                print("\nOpción no válida")
            input("\nPresione Enter para continuar...")

    def menu_representantes(self, cat, rep):
        usuario_id = input("\nID del catequizando: ")
        detalle = cat.ver_detalle(usuario_id)
        if not detalle:
            return

        while True:
            print("\n" + "="*50)
            print(f" GESTIÓN DE REPRESENTANTES ".center(50))
            print(f" Catequizando: {detalle[0].NombreCompleto} ".center(50))
            print("="*50)
            print("1. Agregar representante")
            print("2. Eliminar representante")
            print("3. Volver")

            opcion = input("\nSeleccione una opción: ")
            if opcion == "1":
                rep.crear(usuario_id)
            elif opcion == "2":
                if not detalle[1]:
                    print("\nNo tiene representantes")
                    continue
                for i, r in enumerate(detalle[1], 1):
                    print(f"{i}. {r.NombreCompleto} ({r.Parentesco}) - Tel: {r.Telefono}")
                try:
                    i = int(input("Seleccione: ")) - 1
                    rep.eliminar(detalle[1][i].RepresentanteId)
                except:
                    print("Selección inválida")
            elif opcion == "3":
                break
            else:
                print("\nOpción no válida")
            detalle = cat.ver_detalle(usuario_id)
            if not detalle:
                break
            input("\nPresione Enter para continuar...")

# Ejecución principal
if __name__ == "__main__":
    app = CatequesisManager()
    app.iniciar()
