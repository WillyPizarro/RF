# Llave SSH dedicada para el VPS

El VPS se administra **solo con llave SSH**, nunca con clave (DESPLIEGUE-01, decisión 3). Se usan
dos llaves distintas, y **ninguna** va al repositorio:

| Llave | Dónde vive la parte privada | Para qué |
|---|---|---|
| **Llave de despliegue** | Esta PC: `C:\Users\<usuario>\.ssh\movil_vps` | Entrar al VPS (y la usa `scripts/desplegar.ps1`) |
| **Deploy key de GitHub** | El VPS: `~/.ssh/movil_github` | Que el VPS lea el repositorio privado (solo lectura) |

## 1. Crear la llave de despliegue (en esta PC)

En PowerShell:

```
ssh-keygen -t ed25519 -C "movil-vps-despliegue" -f $HOME\.ssh\movil_vps
```

- Ponga una **frase de paso** cuando la pida, y guárdela en su gestor de claves.
- Se crean `movil_vps` (privada, **nunca se comparte**) y `movil_vps.pub` (pública).

## 2. Autorizarla en el VPS

- **Al crear el VPS:** la mayoría de los proveedores permite pegar una llave pública. Pegue el contenido de `movil_vps.pub`, que se ve con:

  ```
  Get-Content $HOME\.ssh\movil_vps.pub
  ```

- **Si el VPS ya existe:** entre una vez con el acceso que dio el proveedor y agregue esa línea al final de `~/.ssh/authorized_keys` del usuario de despliegue (ver `MANUAL-DESPLIEGUE.md`, paso 2).

Pruebe la llave:

```
ssh -i $HOME\.ssh\movil_vps deploy@<IP-del-VPS>
```

Para no repetir los datos, el script los toma de dos variables de la sesión:

```
$env:MOVIL_VPS = "deploy@<IP-del-VPS>"
$env:MOVIL_VPS_LLAVE = "$HOME\.ssh\movil_vps"
```

## 3. Deploy key de GitHub (en el VPS)

En el VPS, como el usuario `deploy`:

```
ssh-keygen -t ed25519 -C "movil-vps-github" -f ~/.ssh/movil_github -N ""
cat ~/.ssh/movil_github.pub
```

1. En GitHub, en el repositorio, entre a **Settings › Deploy keys › Add deploy key**.
2. Pegue la llave pública, póngale el título "VPS Movil Buscador" y deje **sin marcar** "Allow write access" (solo lectura).
3. En el VPS, cree el archivo `~/.ssh/config` con este contenido:

   ```
   Host github.com
     IdentityFile ~/.ssh/movil_github
     IdentitiesOnly yes
   ```

4. Pruebe la conexión: `ssh -T git@github.com` tiene que saludar con el nombre del repositorio.

## 4. Revocar al cierre del proyecto

1. **GitHub:** en **Settings › Deploy keys**, borre "VPS Movil Buscador".
2. **VPS:** se elimina entero, con sus discos (ver `MANUAL-DESPLIEGUE.md`, borrado). Así desaparecen `authorized_keys` y la deploy key.
3. **Esta PC:** borre la llave de despliegue:

   ```
   Remove-Item $HOME\.ssh\movil_vps, $HOME\.ssh\movil_vps.pub
   ```

   Quite también la línea del VPS en `$HOME\.ssh\known_hosts`, con `ssh-keygen -R <IP-del-VPS>`.
4. Si alguna llave privada pudo haberse filtrado antes del cierre, revóquela **de inmediato** (pasos 1 y 2) y cree una nueva.

Estos pasos van en el acta de eliminación.
