import { create } from 'zustand';

import type { Perfil } from '../api/sesion';

/** Aviso que muestra el login al volver (AUTH-03) o al fallar (AUTH-02, AUTH-04, otro error). */
export type Aviso =
  | { tipo: 'vacios' }
  | { tipo: 'inactividad' }
  | { tipo: 'credenciales' }
  | { tipo: 'bloqueo'; hasta: string }
  | { tipo: 'error' };

/** 'placa' = PLA-01 a PLA-08 (HU-03); 'bitacora' = BIT-01 y BIT-02 (HU-07). */
export type Pantalla = 'cargando' | 'login' | 'inicio' | 'sin_permiso' | 'placa' | 'bitacora';

type EstadoSesion = {
  pantalla: Pantalla;
  perfil: Perfil | null;
  aviso: Aviso | null;
  /** Cambia en cada cierre de sesion: el login se vuelve a montar vacio. */
  generacion: number;
  /** El agente ya toco "Entendido" en el aviso de ML Kit en esta sesion (CONTRATO-HU-04 v5). */
  avisoMlkitVisto: boolean;
  marcarAvisoMlkitVisto: () => void;
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
  avisoMlkitVisto: false,
  marcarAvisoMlkitVisto: () => set({ avisoMlkitVisto: true }),
  mostrar: (pantalla) => set({ pantalla }),
  entrar: (perfil) => set({ perfil, aviso: null, pantalla: 'inicio' }),
  salir: (aviso) =>
    set((estado) => ({
      perfil: null,
      aviso,
      pantalla: 'login',
      generacion: estado.generacion + 1,
      avisoMlkitVisto: false, // el aviso vuelve a aparecer en la sesion siguiente
    })),
  avisar: (aviso) => set({ aviso }),
}));
