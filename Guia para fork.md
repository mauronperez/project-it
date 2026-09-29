# Git: forkear el repo y mantenerlo actualizado

## 1. Configuración inicial (una sola vez)

1. Hacer **Fork** del repo.
2. Clonar **tu** fork:
   ```bash
   git clone https://github.com/TU_USUARIO/NOMBRE_REPO.git
   cd NOMBRE_REPO
   ```
3. Agregar el repo del profesor como `upstream`:
   ```bash
   git remote add upstream https://github.com/USUARIO_PROFESOR/NOMBRE_REPO.git
   git remote -v 
   ```

## 2. Cada vez que el profesor suba algo

### Opción A: desde GitHub (la más fácil)

En tu fork, botón **Sync fork** → **Update branch**. Luego, en local:

```bash
git pull
```

### Opción B: desde la terminal

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main   # opcional: actualiza también tu fork en GitHub
```

## 3. Recomendaciones para evitar conflictos

- Trabaja en una **rama propia** y deja `main` limpia:
  ```bash
  git checkout -b mis-ejercicios
  ```
- Para modificar un archivo (por ejemplo `extract.py`), trabajá sobre una **copia con otro nombre** (`extract_mio.py`). Así, al sincronizar, no habrá conflictos.