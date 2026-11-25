# Netbrain Lookup 1.0.0

Herramienta de solo consulta para localizar endpoints por IPv4 o MAC mediante NetBrain. Migración de la versión de desarrollo 2.6.4 RC4.

## Instalación
```powershell
py -m pip install -e .
Netbrain_Lookup --version
```
Después de publicar, `py -m pip install netbrain-lookup`.

## CLI y TUI
```powershell
Netbrain_Lookup
Netbrain_Lookup -ho 192.0.2.10 -u USERNAME
Netbrain_Lookup -hf examples/hosts.txt -u USERNAME -o Report.csv
Netbrain_Lookup -hf examples/hosts.txt --interactive
Netbrain_Lookup -hf examples/hosts.txt --workers 5 --fast
Netbrain_Lookup --oneip-info -u USERNAME
```
Sin argumentos abre Textual en la terminal integrada de VS Code o Windows Terminal. Con argumentos usa CLI; --interactive fuerza TUI. Password oculto. En TUI, si hay varios tenants/domains, indica su nombre o ID en los campos correspondientes y vuelve a ejecutar; no se selecciona un dominio arbitrariamente. Si existe un log de un intento fallido, selecciona overwrite o cambia la ruta.

Modo automatizado: especifica --url, -u, -ho/-hf, --tenant/--domain si hay varias opciones, --non-interactive y proporciona NETBRAIN_PASSWORD mediante un mecanismo de secretos. No guardes contraseñas en comandos o archivos. TLS por defecto; --ca-file para CA corporativa; --insecure solo para laboratorio.

Fast deshabilita la verificación secundaria MAC; Standard la habilita; Deep añade el escaneo global opcional para IP. No garantiza cobertura completa. Workers 1-20, default 5; auto MAC notation fuerza ejecución secuencial. Fallback de particiones es secuencial.

Reportes CSV + LOG, JSON opcional con --raw-json ruta.json. Los resultados son datos almacenados por NetBrain y no prueban conectividad actual. La TUI mantiene filtros y secciones contraíbles, sin modificar los reportes. Exit durante búsqueda se deshabilita lógicamente para permitir limpieza de sesión.

Limitaciones: IPv4/MAC solamente, TXT de entrada. El motor conserva un resultado principal por target y marca conflictos de observaciones, no exporta todas las coincidencias independientes; usar RAW para investigar. No incluye Excel ni perfiles persistentes. Pruebas live requeridas antes de producción.
