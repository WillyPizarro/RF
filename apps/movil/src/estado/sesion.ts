import { create } from 'zustand';

import type { Perfil } from '../api/sesion';

/** Aviso que muestra el login al volver (AUTH-03) o al fallar (AUTH-02, AUTH-04, otro error). */
export type Aviso =
  | { tipo: 'vacios' }
  | { tipo: 'inactividad' }
  | { tipo: 'credenciales' }
  | { tipo: 'bloqueo'; hasta: string }
  | { tipo: 'error' };

export type Pantalla = 'cargando' | 'login' | 'inicio' | 'sin_permiso';

type EstadoSesion = {
  pantalla: Pantalla;
  perfil: Perfil | null;
  aviso: Aviso | null;
  /** Cambia en cada cierre de sesion: el login se vuelve a montar vacio. */
  generacion: number;
  mostrar: (pantalla: Pantalla) => void;
  entrar: (perfil: Perfil) => void;
  salir: (aviso: Aviso | null) => void;
  avisar: (aviso: Aviso | null) => void;
};

/** Store minimo en memoria (ADR-0013): perfil y pantalla. Sin persistencia. */
export const usarSesion = create<EstadoSesion>((set) => ({
  pantalla: 'cargando',
  perfil: null,
  aviso: null,
  generacion: 0,
  mostrar: (pantalla) => set({ pantalla }),
  entrar: (perfil) => set({ perfil, aviso: null, pantalla: 'inicio' }),
  salir: (aviso) =>
    set((estado) => ({ perfil: null, aviso, pantalla: 'login', generacion: estado.generacion + 1 })),
  avisar: (aviso) => set({ aviso }),
}));
