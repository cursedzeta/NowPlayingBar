# NowPlayingBar 🎵🖥️

¿Alguna vez sentiste la necesidad de saber qué está reproduciendo Spotify en todo momento?  
**NowPlayingBar** es una barra **minimalista, liviana y agradable a la vista** que muestra solo lo justo y necesario, sin consumir recursos innecesarios y pensada para integrarse naturalmente a tu escritorio de Windows.

---

## ✨ ¿Qué es NowPlayingBar?
Es una aplicación de escritorio hecha en **Python** que muestra en tiempo real la canción que estás escuchando en **Spotify**, mediante una barra flotante simple, limpia y discreta.

No agrega ruido visual, no sobrecarga la PC y cumple una sola función:  
**mostrar qué está sonando, de forma elegante y constante.**

---

## ✅ Requisitos
Antes de empezar, asegurate de tener:

- **Windows 10 u 11**
- **Spotify Desktop** instalado e iniciado sesión
- **Python 3.10 o superior**
- Conexión a internet

---

## 🚀 Instalación y ejecución (paso a paso)

Seguí estos pasos en orden. No hace falta ningún conocimiento previo.

---

### 1️⃣ Descargar el proyecto

Abrí una terminal y ejecutá:

```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
````

O bien:

* Tocá **Code → Download ZIP**
* Descomprimí el archivo
* Abrí una terminal dentro de la carpeta del proyecto

---

### 2️⃣ Crear un entorno virtual

Dentro de la carpeta del proyecto:

```bash
python -m venv .venv
```

---

### 3️⃣ Activar el entorno virtual

**PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**CMD:**

```bat
.\.venv\Scripts\activate.bat
```

Si PowerShell muestra un error de permisos, ejecutá una sola vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

### 4️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

Esperá a que termine la instalación.

---

### 5️⃣ Ejecutar la aplicación

1. Abrí **Spotify Desktop**
2. Reproducí cualquier canción
3. Ejecutá:

```bash
python main.py
```

La barra aparecerá automáticamente en pantalla.

---

## 🔁 Ejecutar automáticamente al iniciar Windows

Si querés que NowPlayingBar se ejecute siempre al prender la PC:

1. Presioná `Win + R`
2. Escribí:

```
shell:startup
```

3. En esa carpeta, creá un archivo llamado `NowPlayingBar.bat`
4. Pegá lo siguiente (ajustá la ruta si es necesario):

```bat
@echo off
cd /d "C:\RUTA\A\TU\PROYECTO"
call ".venv\Scripts\activate.bat"
python main.py
```

Listo. A partir de ahora se abrirá automáticamente.

---

## 🛠️ Problemas comunes

### No aparece la canción

* Verificá que Spotify esté abierto y reproduciendo algo
* Cerrá y volvé a abrir Spotify
* Revisá tu conexión a internet

### Error de módulos

Asegurate de haber instalado las dependencias:

```bash
pip install -r requirements.txt
```

---

## 🤝 Contribuciones

Cualquier mejora, idea o corrección es bienvenida.
Issues y Pull Requests abiertos.

---

## 📄 Licencia

Proyecto bajo licencia MIT.

```

Si querés, en el próximo mensaje puedo:
- Ajustarlo **exacto al nombre real del repo**
- Adaptarlo a **inglés**
- Simplificar aún más para usuarios no técnicos
- O hacerlo más “pro” para recruiters de GitHub 👌
```
