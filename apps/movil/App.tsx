import { StatusBar } from 'expo-status-bar';

import PantallaEstado from './src/pantallas/PantallaEstado';

export default function App() {
  return (
    <>
      <PantallaEstado />
      <StatusBar style="auto" />
    </>
  );
}
