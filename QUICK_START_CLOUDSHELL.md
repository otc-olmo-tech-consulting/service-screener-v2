# OTC Service Screener - Guía de Inicio Rápido (CloudShell y CLI Local)

## Descripción General

Esta guía proporciona instrucciones paso a paso para desplegar y ejecutar la herramienta de evaluación de infraestructura AWS, ya sea en **AWS CloudShell** o desde una **terminal local con AWS CLI** (Windows, macOS o Linux) cuando no se dispone de acceso a CloudShell. La herramienta realiza un análisis integral de su entorno AWS contra las mejores prácticas del Well-Architected Framework, generando un reporte de evaluación con hallazgos y recomendaciones de remediación.

**Tiempo Requerido:** Aproximadamente 30 minutos  
**Entorno:** AWS CloudShell (incluido en AWS Free Tier) o terminal local con AWS CLI + Python 3.9+  
**Prerequisitos:** Cuenta AWS válida con permisos IAM apropiados

---

## Prerequisitos

Antes de comenzar, asegúrese de tener:

1. **Acceso a Cuenta AWS** - con permisos de solo lectura apropiados
2. **Permisos IAM** - se requieren los siguientes:
   - `ec2:Describe*` (para evaluación de infraestructura)
   - `iam:Get*` e `iam:List*` (para revisión de configuración de seguridad)
   - `s3:GetBucketPolicy`, `s3:ListBucket` (para evaluación de almacenamiento)
   - Política completa recomendada: `ReadOnlyAccess` (política administrada por AWS)

3. **Recursos en al menos una región AWS** - la herramienta puede escanear entornos vacíos, pero los resultados son más significativos con cargas de trabajo desplegadas

---

## Instalación y Configuración

### Paso 1: Inicializar Entorno (5 minutos)

Copie y pegue los siguientes comandos en AWS CloudShell:

```bash
# Crear entorno Python aislado
cd /tmp
python3 -m venv assessment-env
source assessment-env/bin/activate
python3 -m pip install --upgrade pip

# Clonar y preparar la herramienta de evaluación
rm -rf service-screener-v2
git clone https://github.com/otc-olmo-tech-consulting/service-screener-v2
cd service-screener-v2

# Instalar dependencias
pip install -r requirements.txt

# Crear alias de comando conveniente
alias screener='python3 $(pwd)/main.py'
```

**Resultado Esperado:**
```
Cloning into 'service-screener-v2'...
Successfully installed boto3-1.35.x, packaging-23.1.x, ...
(No deberían aparecer errores)
```

---

## Alternativa: Ejecutar desde una Terminal Local con AWS CLI (Windows / macOS / Linux)

Use esta opción cuando **no tenga acceso a AWS CloudShell** (por ejemplo, por restricciones de permisos). CloudShell es solo un entorno de conveniencia; la herramienta funciona igual en cualquier terminal con Python 3.9+ y credenciales AWS. Los pasos siguientes cubren el flujo completo: iniciar sesión con el CLI, preparar la herramienta, ejecutar el escaneo y abrir el reporte.

> **Nota para Windows:** el `main.py` incluye un ajuste de compatibilidad con Windows para el manejo de procesos (`multiprocessing`). Este mismo archivo sigue funcionando en CloudShell/Linux sin cambios.

### Paso L1: Iniciar sesión con el AWS CLI

Elija la opción que corresponda a cómo obtiene acceso a AWS. Verifique siempre al final con `aws sts get-caller-identity`.

**Opción A — IAM Identity Center / SSO (recomendada):**
```bat
:: Configuración inicial (solo la primera vez)
aws configure sso
:: Iniciar sesión (cada vez que expire la sesión)
aws sso login --profile mi-perfil
```

**Opción B — Access keys de usuario IAM:**
```bat
aws configure
:: AWS Access Key ID, Secret Access Key, región (ej: us-east-1), formato: json
```

**Opción C — Credenciales temporales (STS / rol asumido):**
```bat
:: Windows CMD
set AWS_ACCESS_KEY_ID=...
set AWS_SECRET_ACCESS_KEY=...
set AWS_SESSION_TOKEN=...
```

**Verificar la sesión:**
```bat
aws sts get-caller-identity
```
Debe devolver `Account`, `UserId` y `Arn`. Si esto responde, ya está autenticado.

> **Permisos:** no se requiere permiso de CloudShell. Basta con permisos de **solo lectura** sobre la cuenta; se recomienda la política administrada `ReadOnlyAccess` (o `SecurityAudit`).

### Paso L2: Preparar la herramienta

```bat
:: Ubicarse en la carpeta donde quiere trabajar y clonar (si aún no lo tiene)
git clone https://github.com/otc-olmo-tech-consulting/service-screener-v2
cd service-screener-v2

:: Crear entorno virtual e instalar dependencias
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

> **PowerShell:** para activar el entorno use `.venv\Scripts\Activate.ps1` en vez de `activate.bat`. Si PowerShell bloquea el script, ejecute antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

### Paso L3: Ejecutar el escaneo (modo secuencial)

En una terminal local **debe** usar el flag `--sequential true`. Esto evita el modelo de procesos paralelos, que en Windows no comparte la sesión de AWS entre procesos. Todos los flags de esta herramienta requieren un valor explícito (`true`, `yes`, `y` o `1` para activarlos).

```bat
:: Prueba corta: un solo servicio, para validar que todo corre
py main.py --regions us-east-1 --services ec2 --sequential true

:: Escaneo completo de una región
py main.py --regions us-east-1 --sequential true

:: Con nombre de cliente para el branding del reporte
py main.py --regions us-east-1 --client "Acme Corporation" --sequential true
```

> Si su sesión SSO expira a mitad del proceso (error `Token has expired`), vuelva a ejecutar `aws sso login --profile mi-perfil` y repita el escaneo.

### Paso L4: Ubicar y abrir el reporte

A diferencia de CloudShell, en una terminal local **el archivo NO está en `/tmp`**: se genera en la **raíz de la carpeta del proyecto** (`service-screener-v2`), con el nombre `{CLIENTE}_{FECHA}_findings.zip` (por ejemplo `OTC_20260911_findings.zip`).

```bat
:: Descomprimir el reporte (tar viene incluido en Windows 10/11)
tar -xf OTC_20260911_findings.zip -C reporte

:: El punto de entrada del reporte es index.html dentro de la carpeta extraída
:: Ábralo en su navegador:
start reporte\index.html
```

Como alternativa, haga clic derecho sobre el `.zip` en el Explorador de Windows → **Extraer todo**, y luego abra `index.html`. Si el reporte usa varias cuentas, el `index.html` estará dentro de `aws\<ID_de_cuenta>\`.

A partir de aquí, las secciones siguientes (interpretación del reporte, opciones avanzadas, solución de problemas) aplican por igual para CloudShell y para el CLI local.

---

## Ejecutar su Primera Evaluación

### Paso 2: Ejecutar Evaluación Inicial (10-15 minutos)

Ejecute un escaneo de su infraestructura AWS:

```bash
# Escanear una sola región con servicios principales
screener --regions us-east-1 --services ec2,iam,s3,rds,lambda

# Alternativa: Escanear todas las regiones (mayor tiempo de ejecución)
screener --regions ALL

# Para resultados más rápidos con alcance limitado:
screener --regions us-east-1 --services iam
```

**Resultado Esperado:**
```
[STATUS] Scanning EC2 in us-east-1...
[STATUS] Scanning IAM...
[STATUS] Scanning S3...
[STATUS] Assessment complete
[DONE] Output generated: output.zip
```

La evaluación típicamente toma 5-15 minutos dependiendo del número de recursos y regiones escaneadas.

---

### Paso 3: Revisar Resultados (5 minutos)

Una vez que el escaneo se completa, verifique que la salida fue generada:

```bash
# Confirmar que el archivo de salida existe
ls -lh output.zip

# Extraer el reporte de evaluación
unzip -q output.zip

# Verificar que los archivos del reporte fueron creados
find adminlte/aws -name "*.html" -type f | head -5
```

**Resultado Esperado:**
```
-rw-r--r-- 1 user user 2.5M output.zip
index.html
ec2.html
iam.html
s3.html
```

---

### Paso 4: Descargar Reporte de Evaluación

Su reporte de evaluación está listo para descargar:

#### Opción A: Descargar vía UI de CloudShell (Recomendado)
1. En la ventana de CloudShell, haga clic en el botón **Actions** (esquina superior derecha)
2. Seleccione **Download file**
3. Ingrese la ruta del archivo: `output/adminlte/aws/index.html`
4. Abra el archivo HTML descargado en su navegador web

#### Opción B: Descargar vía Línea de Comandos
```bash
# Si tiene AWS CLI configurado con acceso a S3 (opcional):
aws s3 cp output.zip s3://su-bucket/evaluaciones/
```

---

## Entendiendo su Reporte de Evaluación

### Contenido del Reporte

Su reporte de evaluación incluye:

**Dashboard Ejecutivo:**
- Puntaje de salud general de la infraestructura (0-100)
- Distribución de riesgos por severidad (Alto, Medio, Bajo)
- Top 5 hallazgos críticos que requieren atención
- Evaluación por pilar del Well-Architected Framework

**Evaluaciones por Servicio:**
- Hallazgos individuales para cada servicio AWS (EC2, IAM, S3, RDS, Lambda, etc.)
- Problemas de configuración de seguridad
- Preocupaciones de confiabilidad y disponibilidad
- Oportunidades de optimización de costos
- Recomendaciones de excelencia operacional

**Guía de Remediación:**
- Pasos específicos para abordar cada hallazgo
- Enlaces a documentación de servicios AWS
- Recomendaciones de mejores prácticas
- Elementos de acción basados en prioridad

---

## Opciones Avanzadas

### Personalización con Nombre del Cliente

Personalice el reporte con el nombre de su organización:

```bash
screener --regions us-east-1 --client "Acme Corporation"
```

El archivo de salida será nombrado: `Acme-Corporation_20250115_findings.zip`

### Uso de Archivo de Supresiones

Excluya hallazgos conocidos y aceptados del reporte:

```bash
# Crear suppressions.json
cat > suppressions.json << 'EOF'
{
  "metadata": {
    "version": "1.0",
    "description": "Excepciones aprobadas para Acme Corp"
  },
  "suppressions": [
    {
      "service": "s3",
      "rule": "BucketVersioning"
    },
    {
      "service": "ec2",
      "rule": "SecurityGroupOpenToAll"
    }
  ]
}
EOF

# Ejecutar evaluación con supresiones
screener --regions us-east-1 --suppress_file ./suppressions.json
```

### Filtrado de Recursos por Tags

Evalúe solo recursos que coincidan con tags específicos:

```bash
# Escanear solo recursos de producción
screener --regions us-east-1 --tags env=production

# Múltiples filtros de tags
screener --regions us-east-1 --tags env=prod%department=infrastructure
```

---

## Solución de Problemas

### Problema: Error de "Access Denied"

**Problema:** La evaluación falla con mensajes de permiso denegado

**Solución:**
1. Verifique que su usuario IAM tiene la política `ReadOnlyAccess` adjunta
2. Verifique credenciales de sesión:
   ```bash
   aws sts get-caller-identity
   ```
3. Si las credenciales faltan, reinicie CloudShell. En terminal local, vuelva a iniciar sesión con `aws sso login --profile mi-perfil` (o reconfigure con `aws configure`)

### Problema: La Evaluación Toma Demasiado Tiempo

**Problema:** El escaneo parece detenerse o ejecutarse indefinidamente

**Solución:**
1. Presione `Ctrl+C` para detener el escaneo actual
2. Ejecute con menos regiones/servicios:
   ```bash
   screener --regions us-east-1 --services iam
   ```
3. Verifique problemas de red

### Problema: Datos de Reporte Vacíos o Faltantes

**Problema:** La evaluación se completa pero el reporte no muestra hallazgos

**Solución:**
1. Verifique que existen recursos en las regiones escaneadas:
   ```bash
   aws ec2 describe-instances --region us-east-1
   aws iam list-users
   ```
2. Si existen recursos, ejecute con salida de debug:
   ```bash
   screener --regions us-east-1 --debug True
   ```

### Problema: El Archivo de Reporte No Se Descarga

**Problema:** El botón de descarga de CloudShell no está disponible

**Solución:**
1. Desde el menú de CloudShell, seleccione **Upload/Download**
2. Navegue manualmente a la ubicación del archivo de salida
3. Alternativamente, proporcione la ruta del archivo directamente en el diálogo de descarga

### Problema (solo terminal local): Error de multiprocessing en Windows

**Problema:** En Windows aparece `RuntimeError: An attempt has been made to start a new process...` o `AttributeError: 'bool' object has no attribute 'client'`.

**Solución:** Ejecute siempre con `--sequential true`. En una terminal local de Windows este flag es obligatorio; evita el modelo de procesos paralelos que no comparte la sesión de AWS entre procesos.
```bat
py main.py --regions us-east-1 --services ec2 --sequential true
```

### Problema (solo terminal local): No encuentro el output.zip

**Problema:** Buscó el archivo en `/tmp` y no existe.

**Solución:** En terminal local el reporte NO va a `/tmp` (esa ruta es solo de CloudShell). Se genera en la **raíz del proyecto** con el nombre `{CLIENTE}_{FECHA}_findings.zip`. Búsquelo así:
```bat
dir *_findings.zip
```

---

## Referencia Rápida

### Escenarios Comunes de Evaluación

#### Evaluación de Seguridad Básica (Más Rápido)
```bash
screener --regions us-east-1 --services iam,ec2
```
Duración: ~3-5 minutos | Enfoque: Postura de seguridad

#### Auditoría Completa de Infraestructura
```bash
screener --regions ALL
```
Duración: ~30-45 minutos | Enfoque: Revisión comprehensiva de todos los servicios y regiones

#### Evaluación de Cumplimiento
```bash
screener --regions us-east-1,eu-west-1 --services ec2,iam,s3,rds
```
Duración: ~10-15 minutos | Enfoque: Dominios principales de cumplimiento

#### Revisión de Optimización de Costos
```bash
screener --regions ALL --services ec2,rds,lambda,s3
```
Duración: ~20-30 minutos | Enfoque: Oportunidades de eficiencia de costos

### Comandos Esenciales

```bash
# Ver todas las opciones disponibles
screener --help

# Activar el entorno de evaluación
source /tmp/assessment-env/bin/activate

# Desactivar entorno
deactivate

# Verificar progreso de evaluación actual
ps aux | grep screener

# Limpiar evaluaciones previas
rm -rf output output.zip adminlte/aws/*
```

---

## Criterios de Éxito

Su evaluación está completa y exitosa cuando:

- La herramienta de evaluación se completa sin errores
- El archivo de salida (`output.zip`) es generado
- El archivo de reporte HTML (`index.html`) es accesible
- El reporte muestra:
  - Puntaje de salud de la infraestructura
  - Evaluaciones por servicio
  - Descripciones de hallazgos con pasos de remediación
  - Evaluación del Well-Architected Framework

---

## Pasos Siguientes Después de la Evaluación

### 1. Revisar Dashboard Ejecutivo
- Examinar puntaje de salud general y distribución de riesgos
- Identificar los 5 hallazgos más críticos
- Notar elementos de acción prioritarios

### 2. Priorizar Remediación
- Revisar hallazgos por severidad (Alto → Medio → Bajo)
- Identificar victorias rápidas (mejoras fáciles de implementar)
- Planificar asignación de recursos para esfuerzos de remediación

### 3. Crear Plan de Acción
- Asignar hallazgos a equipos responsables
- Establecer cronograma para remediación
- Definir métricas de éxito para cada elemento de acción

### 4. Seguimiento de Progreso
- Programar evaluaciones de seguimiento regulares
- Monitorear progreso de remediación
- Re-ejecutar evaluación para validar mejoras

---

## Soporte y Documentación

Para información detallada sobre hallazgos específicos o pasos de remediación:

1. Haga clic en el enlace "Learn More" en cualquier hallazgo
2. Revise la documentación del AWS Well-Architected Framework
3. Consulte las guías de mejores prácticas específicas por servicio de AWS

---

## Privacidad de Datos de la Evaluación

La herramienta de evaluación:

- **Nunca modifica** ningún recurso AWS (acceso de solo lectura)
- **No recopila ni transmite** datos sensibles externamente
- **Genera reportes** que deben almacenarse de forma segura
- **Requiere alojamiento local** de reportes HTML (no accesibles por internet)

Todos los datos permanecen dentro de su cuenta AWS. Ninguna métrica o hallazgo se comparte con servicios externos.

---

## Preguntas Frecuentes

**P: ¿Con qué frecuencia debo ejecutar evaluaciones?**  
R: Se recomienda trimestralmente para entornos regulares, o después de cambios significativos de infraestructura.

**P: ¿Puedo ejecutar esto en un entorno de producción?**  
R: Sí. La herramienta es de solo lectura y no realiza modificaciones. Es segura para entornos de producción.

**P: ¿Qué regiones AWS están soportadas?**  
R: Todas las regiones AWS estándar. Regiones especializadas (China, GovCloud) pueden tener limitaciones.

**P: ¿Cómo se calcula el puntaje de salud?**  
R: El puntaje usa un algoritmo ponderado: hallazgos de severidad Alta (peso 3x) + hallazgos Medios (peso 1.5x) + hallazgos Bajos (peso 0.5x).

**P: ¿Puedo personalizar el reporte?**  
R: Sí. Puede agregar el nombre de su organización usando el parámetro `--client` y suprimir excepciones conocidas con un archivo de supresiones.

**P: ¿Esta herramienta está aprobada para auditorías de cumplimiento?**  
R: Proporciona documentación de soporte para revisiones de cumplimiento. Siempre consulte con su equipo de cumplimiento o auditoría para requisitos formales.

---

**¿Preguntas o problemas?** Revise la sección de solución de problemas arriba o contacte a su equipo de soporte de TI.

---

*Última Actualización: Septiembre 2026 (añadido flujo de CLI local)*  
*Versión de la Herramienta: 2.5.0*  
*Estado: Producción*
