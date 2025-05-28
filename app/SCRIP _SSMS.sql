USE CATEQUESIS;
GO

-- Esquema para tablas
CREATE SCHEMA sch_datos AUTHORIZATION dbo;
GO

-- Esquema para procedimientos almacenados
CREATE SCHEMA sch_procs AUTHORIZATION dbo;
GO


--MODIFICACI�N DE TABLAS

IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Catequizando' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    ALTER SCHEMA sch_datos TRANSFER dbo.Catequizando;
END

IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Representante' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    ALTER SCHEMA sch_datos TRANSFER dbo.Representante;
END
GO

-- 4. PROCEDIMIENTOS ALMACENADOS
use CATEQUESIS
GO
SELECT *FROM [sch_datos].[Catequizando]

CREATE OR ALTER PROCEDURE sch_procs.sp_crear_catequizando
    @Nombre NVARCHAR(100),
    @FechaNac DATE,
    @Cedula NVARCHAR(20),
    @Direccion NVARCHAR(200),
    @ParroquiaId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO sch_datos.Catequizando (
            NombreCompleto, 
            FechaNacimiento, 
            Cedula, 
            Direccion, 
            ParroquiaId
        )
        VALUES (
            @Nombre, 
            @FechaNac, 
            @Cedula, 
            @Direccion, 
            @ParroquiaId
        );

        SELECT SCOPE_IDENTITY() AS UsuarioId;
        
        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH
END
GO

-- Procedimiento para crear representante
CREATE OR ALTER PROCEDURE sch_procs.sp_crear_representante
    @UsuarioId INT,
    @Nombre NVARCHAR(100),
    @Parentesco NVARCHAR(50),
    @Telefono NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO sch_datos.Representante (
            UsuarioId,
            NombreCompleto, 
            Parentesco, 
            Telefono
        )
        VALUES (
            @UsuarioId,
            @Nombre, 
            @Parentesco, 
            @Telefono
        );
        
        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH
END
GO

-- 5. PERMISOS Y SEGURIDAD

GRANT EXECUTE ON SCHEMA::sch_procs TO pythonconsultor;
GO

-- Permisos CRUD en tablas
GRANT SELECT, INSERT, UPDATE, DELETE ON sch_datos.Catequizando TO pythonconsultor;
GRANT SELECT, INSERT, UPDATE, DELETE ON sch_datos.Representante TO pythonconsultor;
GO



-- Eliminar constraint existente si existe
DECLARE @ConstraintName NVARCHAR(128);
SELECT @ConstraintName = name 
FROM sys.foreign_keys 
WHERE parent_object_id = OBJECT_ID('sch_datos.Representante') 
AND referenced_object_id = OBJECT_ID('sch_datos.Catequizando');

IF @ConstraintName IS NOT NULL
BEGIN
    EXEC('ALTER TABLE sch_datos.Representante DROP CONSTRAINT ' + @ConstraintName);
END
GO

-- Verificar objetos en esquemas
SELECT 
    OBJECT_NAME(object_id) AS Objeto,
    type_desc AS Tipo,
    SCHEMA_NAME(schema_id) AS Esquema
FROM sys.objects
WHERE schema_id IN (SCHEMA_ID('sch_datos'), SCHEMA_ID('sch_procs'))
ORDER BY Esquema, Tipo;
GO

-- Verificar permisos del usuario
SELECT 
    perm.permission_name,
    perm.state_desc,
    obj.name AS objeto,
    SCHEMA_NAME(obj.schema_id) AS esquema
FROM sys.database_permissions perm
JOIN sys.objects obj ON perm.major_id = obj.object_id
JOIN sys.database_principals prin ON perm.grantee_principal_id = prin.principal_id
WHERE prin.name = 'pythonconsultor';
GO


SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

USE CATEQUESIS;
GO

CREATE TRIGGER sch_datos.tr_ValidarEdadInscripcion  -- Nombre corregido del esquema
ON sch_datos.Catequizando                          -- Esquema y tabla validados
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @EdadMinima INT = 6;
    DECLARE @EdadMaxima INT = 17;

    IF EXISTS (
        SELECT 1
        FROM inserted
        WHERE 
            DATEDIFF(YEAR, FechaNacimiento, GETDATE()) - 
            CASE 
                WHEN MONTH(GETDATE()) < MONTH(FechaNacimiento) 
                     OR (MONTH(GETDATE()) = MONTH(FechaNacimiento) 
                     AND DAY(GETDATE()) < DAY(FechaNacimiento)) 
                THEN 1 
                ELSE 0 
            END NOT BETWEEN @EdadMinima AND @EdadMaxima
    )
    BEGIN
        ROLLBACK TRANSACTION;  -- Primero hacer rollback
        RAISERROR('Error: La edad debe estar entre 5 y 17 a�os para la inscripci�n', 16, 1);
    END
END
GO
-- Permisos para el usuario
GRANT ALTER ON SCHEMA::sch_procs TO pythonconsultor;
GRANT INSERT ON sch_datos.Catequizando TO pythonconsultor;


EXEC sch_procs.sp_crear_catequizando 
    @Nombre = 'Juana Narvaez',
    @FechaNac = '2009-03-20',	
    @Cedula = '123453390',
    @Direccion = 'homero salas',
    @ParroquiaId = 1;

-- Insert inv�lido (edad 5 a�os)
EXEC sch_procs.sp_crear_catequizando 
    @Nombre = 'Ana Garc�a',
    @FechaNac = '2019-05-15',
    @Cedula = '0987654321',
    @Direccion = 'Avenida Test 456',
    @ParroquiaId = 1;

	-- Listar todos los catequizandos
CREATE OR ALTER PROCEDURE sch_procs.sp_listar_catequizando
AS
BEGIN
    SET NOCOUNT ON;
    SELECT * FROM sch_datos.Catequizando;
END
GO

-- Obtener un catequizando por ID
CREATE OR ALTER PROCEDURE sch_procs.sp_obtener_catequizando
    @UsuarioId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT * FROM sch_datos.Catequizando WHERE UsuarioId = @UsuarioId;
END
GO

-- Actualizar un catequizando
CREATE OR ALTER PROCEDURE sch_procs.sp_actualizar_catequizando
    @UsuarioId INT,
    @Nombre NVARCHAR(100),
    @FechaNac DATE,
    @Cedula NVARCHAR(20),
    @Direccion NVARCHAR(200),
    @ParroquiaId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        UPDATE sch_datos.Catequizando
        SET NombreCompleto = @Nombre,
            FechaNacimiento = @FechaNac,
            Cedula = @Cedula,
            Direccion = @Direccion,
            ParroquiaId = @ParroquiaId
        WHERE UsuarioId = @UsuarioId;

        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH
END
GO

-- Eliminar un catequizando
CREATE OR ALTER PROCEDURE sch_procs.sp_eliminar_catequizando
    @UsuarioId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DELETE FROM sch_datos.Catequizando WHERE UsuarioId = @UsuarioId;

        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH
END
GO
-- Crear representante
CREATE OR ALTER PROCEDURE sch_procs.sp_representante_crear
    @Nombre NVARCHAR(100),
    @Parentesco NVARCHAR(50),
    @Telefono NVARCHAR(20),
    @UsuarioId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO sch_datos.Representante (
            NombreCompleto,
            Parentesco,
            Telefono,
            UsuarioId
        )
        VALUES (
            @Nombre,
            @Parentesco,
            @Telefono,
            @UsuarioId
        );

        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH
END
GO

-- Eliminar representante
CREATE OR ALTER PROCEDURE sch_procs.sp_representante_eliminar
    @RepresentanteId INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        DELETE FROM sch_datos.Representante WHERE RepresentanteId = @RepresentanteId;

        COMMIT;
    END TRY
    BEGIN CATCH
        ROLLBACK;
        THROW;
    END CATCH
END
GO

-- Listar representantes por usuario
CREATE OR ALTER PROCEDURE sch_procs.sp_representante_listar
    @UsuarioId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT * FROM sch_datos.Representante WHERE UsuarioId = @UsuarioId;
END
GO