Use master
go
CREATE LOGIN pythonconsultor WITH PASSWORD = 'UDLA';
GO

use CATEQUESIS
go
CREATE USER pythonconsultor FOR LOGIN pythonconsultor
GO
GRANT SELECT ON [dbo].[Catequizando] TO [pythonconsultor]
GRANT INSERT ON [dbo].[Catequizando] TO [pythonconsultor]
GRANT UPDATE ON [dbo].[Catequizando] TO [pythonconsultor]
GRANT DELETE ON [dbo].[Catequizando] TO [pythonconsultor]
PRINT 'Permisos CRUD concedidos sobre la tabla Catequizando'
GO
GRANT SELECT ON [dbo].[Representante] TO [pythonconsultor]
GRANT INSERT ON [dbo].[Representante] TO [pythonconsultor]
GRANT UPDATE ON [dbo].[Representante] TO [pythonconsultor]
GRANT DELETE ON [dbo].[Representante] TO [pythonconsultor]
PRINT 'Permisos CRUD concedidos sobre la tabla [Representante]'
GO
-- Verificar los permisos concedidos
SELECT 
    perm.permission_name,
    perm.state_desc,
    obj.name AS object_name,
    prin.name AS principal_name
FROM sys.database_permissions perm
JOIN sys.objects obj ON perm.major_id = obj.object_id
JOIN sys.database_principals prin ON perm.grantee_principal_id = prin.principal_id
WHERE prin.name = 'pythonconsultor'
GO
-- Primero elimina la restricción existente (EN ESTA PARTE )
DECLARE @ConstraintName NVARCHAR(128)
SELECT @ConstraintName = name 
FROM sys.foreign_keys 
WHERE parent_object_id = OBJECT_ID('Representante') 
AND referenced_object_id = OBJECT_ID('Catequizando')

EXEC('ALTER TABLE [Representante] DROP CONSTRAINT ' + @ConstraintName)

-- Vuelve a crear la restricción con ON DELETE CASCADE
ALTER TABLE [Representante] 
ADD CONSTRAINT FK_Representante_Catequizando 
FOREIGN KEY (UsuarioId) 
REFERENCES [Catequizando](UsuarioId) 
ON DELETE CASCADE